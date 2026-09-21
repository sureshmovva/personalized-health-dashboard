"""Normalized Document Store (Unified JSON Records - Layer 2).

Provides high-performance semi-structured storage with strict (user_id, timestamp) indexing,
denormalized daily views for dashboard queries, and full traceability back to Layer 1 raw files.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pipeline.models_unified import UnifiedHealthRecord, DenormalizedDailyHealthSummary
from pipeline.storage.bronze import DEFAULT_BRONZE_DIR, DEFAULT_MANIFEST_PATH

DEFAULT_DOCUMENT_DB_PATH = Path("data/health_store.db")


def get_doc_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target_path = Path(db_path or DEFAULT_DOCUMENT_DB_PATH)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def init_document_store(db_path: Optional[Path] = None) -> None:
    """Initialize relational JSON document store and denormalized rollup tables."""
    conn = get_doc_connection(db_path)
    cursor = conn.cursor()

    # 1. Primary Unified JSON Document Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unified_health_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            timestamp_utc TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_name TEXT NOT NULL,
            metric_category TEXT NOT NULL,
            data_json TEXT NOT NULL,
            raw_file_id TEXT NOT NULL,
            confidence_score REAL DEFAULT 1.0,
            metadata_json TEXT,
            ingested_at_utc TEXT NOT NULL
        );
    """)

    # High-performance composite indices per user_id & timestamp
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_unified_user_timestamp
        ON unified_health_records(user_id, timestamp_utc);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_unified_user_category_timestamp
        ON unified_health_records(user_id, metric_category, timestamp_utc);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_unified_raw_file_id
        ON unified_health_records(raw_file_id);
    """)

    # 2. Denormalized Daily Summary Table (for low-latency single-fetch dashboard loads)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unified_daily_rollups (
            user_id TEXT NOT NULL,
            date TEXT NOT NULL,
            glucose_mean_mg_dl REAL,
            glucose_min_mg_dl REAL,
            glucose_max_mg_dl REAL,
            glucose_time_in_range_pct REAL,
            glucose_readings_count INTEGER DEFAULT 0,
            weight_lbs REAL,
            weight_kg REAL,
            body_fat_pct REAL,
            steps INTEGER,
            resting_heart_rate_bpm INTEGER,
            traceability_raw_file_ids_json TEXT,
            updated_at_utc TEXT NOT NULL,
            PRIMARY KEY (user_id, date)
        );
    """)

    conn.commit()
    conn.close()


def insert_unified_records(
    records: list[UnifiedHealthRecord],
    db_path: Optional[Path] = None,
) -> int:
    """Insert standardized unified JSON records in a transactional batch."""
    if not records:
        return 0

    init_document_store(db_path)
    conn = get_doc_connection(db_path)
    cursor = conn.cursor()
    now_utc = datetime.now(timezone.utc).isoformat()

    rows = []
    affected_users: set[str] = set()
    for r in records:
        affected_users.add(r.user_id)
        rows.append((
            r.user_id,
            r.timestamp.isoformat(),
            r.source_type,
            r.source_name,
            r.metric_category,
            json.dumps(r.data),
            r.raw_file_id or "manual_entry",
            r.confidence_score,
            json.dumps(r.metadata),
            now_utc,
        ))

    cursor.executemany("""
        INSERT INTO unified_health_records (
            user_id, timestamp_utc, source_type, source_name, metric_category,
            data_json, raw_file_id, confidence_score, metadata_json, ingested_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, rows)

    conn.commit()
    conn.close()

    # Recompute denormalized daily summaries for affected users
    for uid in affected_users:
        recompute_daily_rollups(user_id=uid, db_path=db_path)

    return len(rows)


def query_unified_records(
    user_id: str,
    metric_category: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 500,
    db_path: Optional[Path] = None,
) -> list[UnifiedHealthRecord]:
    """Query normalized document records using composite user_id and timestamp filters."""
    init_document_store(db_path)
    conn = get_doc_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM unified_health_records WHERE user_id = ?"
    params: list[Any] = [user_id]

    if metric_category:
        query += " AND metric_category = ?"
        params.append(metric_category)

    if start_time:
        query += " AND timestamp_utc >= ?"
        params.append(start_time.isoformat())

    if end_time:
        query += " AND timestamp_utc <= ?"
        params.append(end_time.isoformat())

    query += " ORDER BY timestamp_utc ASC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results: list[UnifiedHealthRecord] = []
    for row in rows:
        results.append(
            UnifiedHealthRecord(
                user_id=row["user_id"],
                timestamp=datetime.fromisoformat(row["timestamp_utc"]),
                source_type=row["source_type"],
                source_name=row["source_name"],
                metric_category=row["metric_category"],
                data=json.loads(row["data_json"]),
                metadata=json.loads(row["metadata_json"] or "{}"),
            )
        )
    return results


def recompute_daily_rollups(
    user_id: str,
    db_path: Optional[Path] = None,
) -> int:
    """Rebuild denormalized daily aggregates for fast single-roundtrip dashboard rendering."""
    conn = get_doc_connection(db_path)
    cursor = conn.cursor()

    # Group all records by date
    cursor.execute("""
        SELECT substr(timestamp_utc, 1, 10) as date_str, metric_category, data_json, raw_file_id
        FROM unified_health_records
        WHERE user_id = ?
        ORDER BY timestamp_utc ASC;
    """, (user_id,))
    rows = cursor.fetchall()

    daily_buckets: dict[str, dict[str, Any]] = {}
    for r in rows:
        d = r["date_str"]
        if d not in daily_buckets:
            daily_buckets[d] = {
                "glucose_values": [],
                "weight_lbs": None,
                "weight_kg": None,
                "body_fat_pct": None,
                "steps": None,
                "raw_file_ids": set(),
            }

        cat = r["metric_category"]
        data = json.loads(r["data_json"])
        if r["raw_file_id"]:
            daily_buckets[d]["raw_file_ids"].add(r["raw_file_id"])

        if cat == "blood_glucose" and "value" in data:
            daily_buckets[d]["glucose_values"].append(float(data["value"]))
        elif cat == "body_weight":
            if "value_lbs" in data:
                daily_buckets[d]["weight_lbs"] = float(data["value_lbs"])
            elif "value" in data and data.get("unit") in ("lbs", "lb"):
                daily_buckets[d]["weight_lbs"] = float(data["value"])
            if "value_kg" in data:
                daily_buckets[d]["weight_kg"] = float(data["value_kg"])
            if "body_fat_pct" in data:
                daily_buckets[d]["body_fat_pct"] = float(data["body_fat_pct"])

    # Upsert daily rollups
    now_utc = datetime.now(timezone.utc).isoformat()
    upsert_rows = []
    for d, bucket in daily_buckets.items():
        g_vals = bucket["glucose_values"]
        mean_g = sum(g_vals) / len(g_vals) if g_vals else None
        min_g = min(g_vals) if g_vals else None
        max_g = max(g_vals) if g_vals else None
        tir = (sum(1 for v in g_vals if 70.0 <= v <= 140.0) / len(g_vals) * 100.0) if g_vals else None

        upsert_rows.append((
            user_id,
            d,
            round(mean_g, 1) if mean_g is not None else None,
            min_g,
            max_g,
            round(tir, 1) if tir is not None else None,
            len(g_vals),
            bucket["weight_lbs"],
            bucket["weight_kg"],
            bucket["body_fat_pct"],
            bucket["steps"],
            None,
            json.dumps(list(bucket["raw_file_ids"])),
            now_utc,
        ))

    cursor.executemany("""
        INSERT INTO unified_daily_rollups (
            user_id, date, glucose_mean_mg_dl, glucose_min_mg_dl, glucose_max_mg_dl,
            glucose_time_in_range_pct, glucose_readings_count, weight_lbs, weight_kg,
            body_fat_pct, steps, resting_heart_rate_bpm, traceability_raw_file_ids_json, updated_at_utc
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, date) DO UPDATE SET
            glucose_mean_mg_dl = excluded.glucose_mean_mg_dl,
            glucose_min_mg_dl = excluded.glucose_min_mg_dl,
            glucose_max_mg_dl = excluded.glucose_max_mg_dl,
            glucose_time_in_range_pct = excluded.glucose_time_in_range_pct,
            glucose_readings_count = excluded.glucose_readings_count,
            weight_lbs = excluded.weight_lbs,
            weight_kg = excluded.weight_kg,
            body_fat_pct = excluded.body_fat_pct,
            steps = excluded.steps,
            traceability_raw_file_ids_json = excluded.traceability_raw_file_ids_json,
            updated_at_utc = excluded.updated_at_utc;
    """, upsert_rows)

    conn.commit()
    conn.close()
    return len(upsert_rows)


def get_denormalized_daily_summaries(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 30,
    db_path: Optional[Path] = None,
) -> list[DenormalizedDailyHealthSummary]:
    """Fetch pre-aggregated daily records so the UI gets unified metrics in 1 roundtrip."""
    init_document_store(db_path)
    conn = get_doc_connection(db_path)
    cursor = conn.cursor()

    query = "SELECT * FROM unified_daily_rollups WHERE user_id = ?"
    params: list[Any] = [user_id]

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results: list[DenormalizedDailyHealthSummary] = []
    for r in rows:
        results.append(
            DenormalizedDailyHealthSummary(
                user_id=r["user_id"],
                date=r["date"],
                glucose_mean_mg_dl=r["glucose_mean_mg_dl"],
                glucose_min_mg_dl=r["glucose_min_mg_dl"],
                glucose_max_mg_dl=r["glucose_max_mg_dl"],
                glucose_time_in_range_pct=r["glucose_time_in_range_pct"],
                glucose_readings_count=r["glucose_readings_count"],
                weight_lbs=r["weight_lbs"],
                weight_kg=r["weight_kg"],
                body_fat_pct=r["body_fat_pct"],
                steps=r["steps"],
                resting_heart_rate_bpm=r["resting_heart_rate_bpm"],
                traceability_raw_file_ids=json.loads(r["traceability_raw_file_ids_json"] or "[]"),
            )
        )
    return results


def get_traceability_link(
    raw_file_id: str,
    manifest_path: Optional[Path] = None,
) -> Optional[dict[str, Any]]:
    """Lookup the Layer 1 raw file receipt from bronze manifest by raw_file_id."""
    target_manifest = Path(manifest_path or DEFAULT_MANIFEST_PATH)
    if not target_manifest.exists():
        return None

    try:
        with open(target_manifest, "r", encoding="utf-8") as f:
            records = json.load(f)
            for item in records:
                if item.get("file_id") == raw_file_id or item.get("sha256", "").startswith(raw_file_id):
                    return item
    except Exception:
        return None
    return None

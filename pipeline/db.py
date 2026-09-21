"""Embedded database persistence layer for health metrics.

Uses a zero-configuration SQLite/DuckDB storage engine with strict typing,
indexing on UTC timestamps, and transactional upserts for secure local storage.
"""

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pipeline.models import (
    ActivityRecord,
    ClinicalLabRecord,
    GlucoseReading,
    ScaleRecord,
    SourceType,
)

DEFAULT_DB_DIR = Path("data")
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "health_store.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Create a connection with foreign keys and row factory enabled."""
    target_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(target_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")  # High concurrency Write-Ahead Logging
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """Initialize relational tables and indices for all health metrics."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Glucose Readings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS glucose_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                glucose_mg_dl REAL NOT NULL,
                trend_arrow TEXT,
                source TEXT NOT NULL,
                device_serial TEXT,
                ingested_at_utc TEXT NOT NULL,
                CONSTRAINT uq_glucose_time_source UNIQUE(timestamp_utc, source)
            );
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_glucose_timestamp 
            ON glucose_readings(timestamp_utc);
        """)

        # 2. Scale Records Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scale_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                weight_kg REAL NOT NULL,
                weight_lbs REAL NOT NULL,
                body_fat_pct REAL,
                muscle_mass_kg REAL,
                metabolic_age INTEGER,
                source TEXT NOT NULL,
                ingested_at_utc TEXT NOT NULL,
                CONSTRAINT uq_scale_time_source UNIQUE(timestamp_utc, source)
            );
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scale_timestamp 
            ON scale_records(timestamp_utc);
        """)

        # 3. Activity & Sleep Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                end_timestamp_utc TEXT,
                steps INTEGER DEFAULT 0,
                heart_rate_bpm REAL,
                active_calories REAL,
                sleep_minutes INTEGER,
                source TEXT NOT NULL,
                ingested_at_utc TEXT NOT NULL,
                CONSTRAINT uq_activity_time_source UNIQUE(timestamp_utc, source)
            );
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_activity_timestamp 
            ON activity_records(timestamp_utc);
        """)

        # 4. Clinical Lab Reports (A1C, Lipids, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clinical_lab_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                test_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                reference_range TEXT,
                physician_notes TEXT,
                source TEXT NOT NULL,
                ingested_at_utc TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_lab_timestamp 
            ON clinical_lab_records(timestamp_utc);
        """)

        # 5. Pipeline Audit Trail & Ingestion Log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp_utc TEXT NOT NULL,
                source TEXT NOT NULL,
                raw_count INTEGER NOT NULL,
                deduped_count INTEGER NOT NULL,
                conflicts_resolved INTEGER NOT NULL,
                status TEXT NOT NULL,
                message TEXT
            );
        """)
        conn.commit()


def save_glucose_readings(
    readings: list[GlucoseReading],
    db_path: Optional[Path] = None,
) -> int:
    """Upsert deduplicated glucose readings into the secure database."""
    if not readings:
        return 0

    init_db(db_path)
    now_utc = datetime.now(timezone.utc).isoformat()
    inserted = 0

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        for r in readings:
            cursor.execute("""
                INSERT INTO glucose_readings 
                (timestamp_utc, glucose_mg_dl, trend_arrow, source, device_serial, ingested_at_utc)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(timestamp_utc, source) DO UPDATE SET
                    glucose_mg_dl = excluded.glucose_mg_dl,
                    trend_arrow = excluded.trend_arrow,
                    ingested_at_utc = excluded.ingested_at_utc;
            """, (
                r.timestamp_utc.isoformat(),
                r.glucose_mg_dl,
                r.trend_arrow,
                r.source.value,
                r.device_serial,
                now_utc,
            ))
            inserted += 1
        conn.commit()
    return inserted


def save_scale_records(
    records: list[ScaleRecord],
    db_path: Optional[Path] = None,
) -> int:
    """Upsert deduplicated scale entries into the secure database."""
    if not records:
        return 0

    init_db(db_path)
    now_utc = datetime.now(timezone.utc).isoformat()
    inserted = 0

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        for s in records:
            cursor.execute("""
                INSERT INTO scale_records 
                (timestamp_utc, weight_kg, weight_lbs, body_fat_pct, muscle_mass_kg, metabolic_age, source, ingested_at_utc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(timestamp_utc, source) DO UPDATE SET
                    weight_kg = excluded.weight_kg,
                    weight_lbs = excluded.weight_lbs,
                    body_fat_pct = excluded.body_fat_pct,
                    muscle_mass_kg = excluded.muscle_mass_kg,
                    metabolic_age = excluded.metabolic_age,
                    ingested_at_utc = excluded.ingested_at_utc;
            """, (
                s.timestamp_utc.isoformat(),
                s.weight_kg,
                s.weight_lbs,
                s.body_fat_pct,
                s.muscle_mass_kg,
                s.metabolic_age,
                s.source.value,
                now_utc,
            ))
            inserted += 1
        conn.commit()
    return inserted


def log_audit_event(
    source: SourceType,
    raw_count: int,
    deduped_count: int,
    conflicts_resolved: int,
    status: str,
    message: str,
    db_path: Optional[Path] = None,
) -> None:
    """Record an audit trail event for ingested batches."""
    init_db(db_path)
    now_utc = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        conn.execute("""
            INSERT INTO ingestion_audit_logs 
            (timestamp_utc, source, raw_count, deduped_count, conflicts_resolved, status, message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            now_utc,
            source.value,
            raw_count,
            deduped_count,
            conflicts_resolved,
            status,
            message,
        ))
        conn.commit()


def get_all_glucose(db_path: Optional[Path] = None) -> list[GlucoseReading]:
    """Retrieve all glucose readings ordered by timestamp ascending."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        rows = conn.execute("""
            SELECT timestamp_utc, glucose_mg_dl, trend_arrow, source, device_serial
            FROM glucose_readings
            ORDER BY timestamp_utc ASC
        """).fetchall()

        return [
            GlucoseReading(
                timestamp_utc=row["timestamp_utc"],
                glucose_mg_dl=row["glucose_mg_dl"],
                trend_arrow=row["trend_arrow"],
                source=SourceType(row["source"]),
                device_serial=row["device_serial"],
            )
            for row in rows
        ]


def get_all_scale(db_path: Optional[Path] = None) -> list[ScaleRecord]:
    """Retrieve all scale records ordered by timestamp ascending."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        rows = conn.execute("""
            SELECT timestamp_utc, weight_kg, weight_lbs, body_fat_pct, muscle_mass_kg, metabolic_age, source
            FROM scale_records
            ORDER BY timestamp_utc ASC
        """).fetchall()

        return [
            ScaleRecord(
                timestamp_utc=row["timestamp_utc"],
                weight_kg=row["weight_kg"],
                weight_lbs=row["weight_lbs"],
                body_fat_pct=row["body_fat_pct"],
                muscle_mass_kg=row["muscle_mass_kg"],
                metabolic_age=row["metabolic_age"],
                source=SourceType(row["source"]),
            )
            for row in rows
        ]


def get_database_summary(db_path: Optional[Path] = None) -> dict[str, Any]:
    """Fetch counts and summary statistics across all tables."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        glucose_count = conn.execute("SELECT COUNT(*) FROM glucose_readings").fetchone()[0]
        scale_count = conn.execute("SELECT COUNT(*) FROM scale_records").fetchone()[0]
        activity_count = conn.execute("SELECT COUNT(*) FROM activity_records").fetchone()[0]
        labs_count = conn.execute("SELECT COUNT(*) FROM clinical_lab_records").fetchone()[0]
        audit_count = conn.execute("SELECT COUNT(*) FROM ingestion_audit_logs").fetchone()[0]

        return {
            "glucose_count": glucose_count,
            "scale_count": scale_count,
            "activity_count": activity_count,
            "labs_count": labs_count,
            "audit_logs_count": audit_count,
            "db_path": str(db_path or DEFAULT_DB_PATH),
        }

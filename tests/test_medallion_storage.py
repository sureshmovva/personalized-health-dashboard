"""Unit tests for Medallion Storage Architecture (Bronze, Silver, Gold)."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from pipeline.models import GlucoseReading, ScaleRecord, SourceType
from pipeline.storage.bronze import BronzeStorage
from pipeline.storage.silver import SilverStorage
from pipeline.storage.gold import GoldAnalytics


def test_bronze_layer_immutable_receipt():
    with tempfile.TemporaryDirectory() as tmpdir:
        bronze = BronzeStorage(base_dir=Path(tmpdir) / "bronze")
        sample_csv = b"Timestamp,Glucose\n2026-09-21T08:00:00Z,105\n"

        receipt = bronze.ingest_raw_file(
            file_or_bytes=sample_csv,
            filename="stelo_test.csv",
            source=SourceType.STELO_CGM,
        )

        assert receipt["sha256"] is not None
        assert Path(receipt["stored_path"]).exists()
        assert len(bronze.list_raw_files()) == 1


def test_silver_and_gold_layers():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "health.db"
        silver = SilverStorage(db_path=test_db)
        gold = GoldAnalytics(silver_storage=silver)

        # 1. Ingest into Silver
        ts1 = datetime(2026, 9, 21, 10, 0, 0, tzinfo=timezone.utc)
        ts2 = datetime(2026, 9, 21, 10, 15, 0, tzinfo=timezone.utc)
        readings = [
            GlucoseReading(timestamp_utc=ts1, glucose_mg_dl=100.0, source=SourceType.STELO_CGM),
            GlucoseReading(timestamp_utc=ts2, glucose_mg_dl=120.0, source=SourceType.STELO_CGM),
        ]
        res = silver.process_and_persist_glucose(readings, source=SourceType.STELO_CGM)
        assert res["saved_count"] == 2

        # 2. Compute Gold Analytics
        profile = gold.get_glycemic_profile(target_min=70.0, target_max=140.0)
        assert profile["reading_count"] == 2
        assert profile["time_in_range_pct"] == 100.0
        assert profile["mean_glucose_mg_dl"] == 110.0

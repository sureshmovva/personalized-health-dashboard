"""Unit tests for SQLite/DuckDB persistent database layer."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from pipeline.models import GlucoseReading, ScaleRecord, SourceType
from pipeline.db import (
    init_db,
    save_glucose_readings,
    save_scale_records,
    get_all_glucose,
    get_all_scale,
    get_database_summary,
    log_audit_event,
)


def test_database_initialization_and_crud():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db = Path(tmpdir) / "test_health.db"

        # 1. Initialize DB
        init_db(test_db)
        assert test_db.exists()

        # 2. Insert Glucose Reading
        ts1 = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)
        reading1 = GlucoseReading(
            timestamp_utc=ts1,
            glucose_mg_dl=102.5,
            trend_arrow="Flat",
            source=SourceType.STELO_CGM,
        )
        saved = save_glucose_readings([reading1], db_path=test_db)
        assert saved == 1

        # 3. Retrieve and assert
        retrieved_glucose = get_all_glucose(test_db)
        assert len(retrieved_glucose) == 1
        assert retrieved_glucose[0].glucose_mg_dl == 102.5
        assert retrieved_glucose[0].source == SourceType.STELO_CGM

        # 4. Insert Scale Record
        scale1 = ScaleRecord(
            timestamp_utc=ts1,
            weight_kg=79.5,
            weight_lbs=175.27,
            body_fat_pct=17.8,
            source=SourceType.WYZE_SCALE,
        )
        saved_scale = save_scale_records([scale1], db_path=test_db)
        assert saved_scale == 1

        retrieved_scale = get_all_scale(test_db)
        assert len(retrieved_scale) == 1
        assert retrieved_scale[0].weight_kg == 79.5

        # 5. Audit Logging
        log_audit_event(
            source=SourceType.STELO_CGM,
            raw_count=10,
            deduped_count=9,
            conflicts_resolved=1,
            status="SUCCESS",
            message="Cleaned 10 readings down to 9.",
            db_path=test_db,
        )

        # 6. Summary Stats
        stats = get_database_summary(test_db)
        assert stats["glucose_count"] == 1
        assert stats["scale_count"] == 1
        assert stats["audit_logs_count"] == 1

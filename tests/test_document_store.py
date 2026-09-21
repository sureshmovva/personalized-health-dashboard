"""Unit tests for Normalized Document Store (Layer 2) and Traceability Links (Layer 1)."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from pipeline.models import SourceType
from pipeline.models_unified import UnifiedHealthRecord
from pipeline.storage.bronze import BronzeStorage
from pipeline.document_store import (
    init_document_store,
    insert_unified_records,
    query_unified_records,
    get_denormalized_daily_summaries,
    get_traceability_link,
)


def test_unified_document_store_and_traceability():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "test_doc_store.db"
        bronze_dir = tmp_path / "bronze"

        # 1. Layer 1: Ingest raw CSV into Bronze Vault
        bronze = BronzeStorage(base_dir=bronze_dir)
        raw_payload = b"Timestamp,Glucose\n2026-09-21T16:00:00Z,105\n"
        receipt = bronze.ingest_raw_file(
            file_or_bytes=raw_payload,
            filename="stelo_sample.csv",
            source=SourceType.STELO_CGM,
        )
        raw_file_id = receipt["file_id"]
        assert raw_file_id is not None

        # 2. Layer 2: Insert Normalized Document Record conforming to schema
        record = UnifiedHealthRecord(
            user_id="usr_987654",
            timestamp=datetime(2026, 9, 21, 16, 0, 0, tzinfo=timezone.utc),
            source_type="cgm",
            source_name="Stelo CGM",
            metric_category="blood_glucose",
            data={
                "value": 105,
                "unit": "mg/dL",
                "trend_arrow": "flat",
            },
            metadata={
                "raw_file_id": raw_file_id,
                "confidence_score": 0.99,
            },
        )

        inserted_count = insert_unified_records([record], db_path=db_path)
        assert inserted_count == 1

        # 3. Query by user_id and timestamp index
        queried = query_unified_records(
            user_id="usr_987654",
            metric_category="blood_glucose",
            db_path=db_path,
        )
        assert len(queried) == 1
        assert queried[0].data["value"] == 105
        assert queried[0].metadata["raw_file_id"] == raw_file_id

        # 4. Verify Denormalized Daily Summary (single roundtrip fetch)
        daily = get_denormalized_daily_summaries(user_id="usr_987654", db_path=db_path)
        assert len(daily) == 1
        assert daily[0].date == "2026-09-21"
        assert daily[0].glucose_mean_mg_dl == 105.0
        assert raw_file_id in daily[0].traceability_raw_file_ids

        # 5. Verify Traceability Link back to Layer 1
        trace = get_traceability_link(raw_file_id=raw_file_id, manifest_path=bronze.manifest_path)
        assert trace is not None
        assert trace["original_filename"] == "stelo_sample.csv"
        assert Path(trace["stored_path"]).exists()

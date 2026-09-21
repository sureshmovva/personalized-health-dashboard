"""Silver Storage Layer: Schema enforcement, normalization, and deduplication.

Ingests records validated by Pydantic v2 schemas, executes conflict resolution,
and persists cleaned records to relational SQLite/DuckDB tables.
"""

from pathlib import Path
from typing import Optional

from pipeline.models import (
    ActivityRecord,
    ClinicalLabRecord,
    GlucoseReading,
    ScaleRecord,
    SourceType,
)
from pipeline.deduplicator import deduplicate_glucose, deduplicate_scale
from pipeline.db import (
    save_glucose_readings,
    save_scale_records,
    get_all_glucose,
    get_all_scale,
    log_audit_event,
)


class SilverStorage:
    """Manages cleaned, relational, deduplicated health metric storage."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path

    def process_and_persist_glucose(
        self,
        raw_readings: list[GlucoseReading],
        source: SourceType,
    ) -> dict:
        """Deduplicate raw readings and persist into the silver relational store."""
        raw_count = len(raw_readings)
        cleaned = deduplicate_glucose(raw_readings)
        deduped_count = len(cleaned)
        conflicts = raw_count - deduped_count

        saved_count = save_glucose_readings(cleaned, db_path=self.db_path)
        log_audit_event(
            source=source,
            raw_count=raw_count,
            deduped_count=deduped_count,
            conflicts_resolved=conflicts,
            status="SUCCESS",
            message=f"Silver layer: {saved_count} glucose readings persisted.",
            db_path=self.db_path,
        )

        return {
            "raw_count": raw_count,
            "cleaned_count": deduped_count,
            "conflicts_resolved": conflicts,
            "saved_count": saved_count,
        }

    def process_and_persist_scale(
        self,
        raw_records: list[ScaleRecord],
        source: SourceType,
    ) -> dict:
        """Deduplicate scale entries and persist into the silver relational store."""
        raw_count = len(raw_records)
        cleaned = deduplicate_scale(raw_records)
        deduped_count = len(cleaned)
        conflicts = raw_count - deduped_count

        saved_count = save_scale_records(cleaned, db_path=self.db_path)
        log_audit_event(
            source=source,
            raw_count=raw_count,
            deduped_count=deduped_count,
            conflicts_resolved=conflicts,
            status="SUCCESS",
            message=f"Silver layer: {saved_count} scale records persisted.",
            db_path=self.db_path,
        )

        return {
            "raw_count": raw_count,
            "cleaned_count": deduped_count,
            "conflicts_resolved": conflicts,
            "saved_count": saved_count,
        }

    def get_clean_glucose(self) -> list[GlucoseReading]:
        return get_all_glucose(db_path=self.db_path)

    def get_clean_scale(self) -> list[ScaleRecord]:
        return get_all_scale(db_path=self.db_path)

"""Unit tests for pipeline normalization, models, and deduplication."""

from datetime import datetime, timezone, timedelta
import pytest
from pipeline.models import GlucoseReading, ScaleRecord, SourceType
from pipeline.normalizer import lbs_to_kg, kg_to_lbs, parse_to_utc
from pipeline.deduplicator import deduplicate_glucose, deduplicate_scale


def test_normalizer_unit_conversions():
    assert lbs_to_kg(220.462) == 100.0
    assert kg_to_lbs(100.0) == 220.46


def test_parse_to_utc():
    # ISO string with Z
    dt1 = parse_to_utc("2026-09-21T10:00:00Z")
    assert dt1.tzinfo == timezone.utc
    assert dt1.hour == 10

    # Local datetime without tz gets assumed UTC
    dt2 = parse_to_utc("2026-09-21 15:30:00")
    assert dt2.tzinfo == timezone.utc
    assert dt2.hour == 15


def test_glucose_validation():
    # Valid glucose reading
    reading = GlucoseReading(
        timestamp_utc="2026-09-21T08:00:00Z",
        glucose_mg_dl=105.5,
        trend_arrow="Flat",
        source=SourceType.STELO_CGM,
    )
    assert reading.glucose_mg_dl == 105.5

    # Out of range should fail validation
    with pytest.raises(ValueError):
        GlucoseReading(
            timestamp_utc="2026-09-21T08:00:00Z",
            glucose_mg_dl=15.0,  # Below 20.0 physiological floor
            source=SourceType.STELO_CGM,
        )


def test_deduplicator_priority_conflict_resolution():
    t0 = datetime(2026, 9, 21, 8, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(minutes=1)  # within 2-minute window

    # Manual CSV entry
    manual_entry = GlucoseReading(
        timestamp_utc=t0,
        glucose_mg_dl=110.0,
        source=SourceType.MANUAL_CSV,
    )

    # Stelo CGM direct measurement with higher priority
    stelo_entry = GlucoseReading(
        timestamp_utc=t1,
        glucose_mg_dl=108.0,
        source=SourceType.STELO_CGM,
    )

    # When both are present, Stelo CGM must supersede Manual CSV
    deduped = deduplicate_glucose([manual_entry, stelo_entry])
    assert len(deduped) == 1
    assert deduped[0].source == SourceType.STELO_CGM
    assert deduped[0].glucose_mg_dl == 108.0

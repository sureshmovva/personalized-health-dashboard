"""Core Pydantic models for the health data pipeline.

Enforces strict typing, unit normalization, and metadata tracking across
heterogeneous sources: Stelo CGM, Wyze Scale, Google/Apple Health, and Clinical Notes.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class SourceType(str, Enum):
    """Enumeration of recognized health data sources with source priority rankings."""
    STELO_CGM = "stelo_cgm"
    WYZE_SCALE = "wyze_scale"
    GOOGLE_HEALTH = "google_health"
    APPLE_HEALTH = "apple_health"
    TELADOC_PDF = "teladoc_pdf"
    MANUAL_CSV = "manual_csv"


class DataSourcePriority:
    """Deterministic priority mapping (higher integer = higher precedence in conflict resolution)."""
    PRIORITY_MAP: dict[SourceType, int] = {
        SourceType.TELADOC_PDF: 100,     # Physician / official clinical labs take highest precedence
        SourceType.WYZE_SCALE: 80,       # Direct smart device measurements
        SourceType.STELO_CGM: 80,        # Continuous direct biometric sensor
        SourceType.APPLE_HEALTH: 60,     # Native health aggregator sync
        SourceType.GOOGLE_HEALTH: 60,    # Native health aggregator sync
        SourceType.MANUAL_CSV: 40,       # Self-reported / user-typed inputs
    }

    @classmethod
    def get_priority(cls, source: SourceType) -> int:
        return cls.PRIORITY_MAP.get(source, 10)


class GlucoseReading(BaseModel):
    """Normalized Continuous Glucose Monitor (CGM) sample."""
    timestamp_utc: datetime = Field(..., description="Measurement timestamp in UTC ISO-8601")
    glucose_mg_dl: float = Field(..., ge=20.0, le=600.0, description="Blood glucose level in mg/dL")
    trend_arrow: Optional[str] = Field(None, description="Dexcom/Stelo trend indicator (e.g., 'Flat', 'SingleUp')")
    source: SourceType = Field(default=SourceType.STELO_CGM)
    device_serial: Optional[str] = None
    raw_payload: Optional[dict[str, Any]] = None

    @field_validator("timestamp_utc", mode="before")
    @classmethod
    def ensure_utc(cls, v: Any) -> datetime:
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        elif isinstance(v, datetime):
            dt = v
        else:
            raise ValueError(f"Invalid timestamp format: {v}")
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


class ScaleRecord(BaseModel):
    """Normalized smart scale metric record."""
    timestamp_utc: datetime = Field(..., description="Weigh-in timestamp in UTC ISO-8601")
    weight_kg: float = Field(..., ge=20.0, le=300.0, description="Body weight in kilograms")
    weight_lbs: float = Field(..., ge=44.0, le=660.0, description="Body weight in pounds")
    body_fat_pct: Optional[float] = Field(None, ge=3.0, le=70.0, description="Body fat percentage")
    muscle_mass_kg: Optional[float] = Field(None, ge=10.0, le=150.0)
    metabolic_age: Optional[int] = Field(None, ge=10, le=120)
    source: SourceType = Field(default=SourceType.WYZE_SCALE)
    raw_payload: Optional[dict[str, Any]] = None

    @field_validator("timestamp_utc", mode="before")
    @classmethod
    def ensure_utc(cls, v: Any) -> datetime:
        if isinstance(v, str):
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        elif isinstance(v, datetime):
            dt = v
        else:
            raise ValueError(f"Invalid timestamp format: {v}")
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


class ActivityRecord(BaseModel):
    """Aggregated daily or interval activity metrics from Apple/Google Health."""
    timestamp_utc: datetime = Field(..., description="Start timestamp of interval in UTC")
    end_timestamp_utc: Optional[datetime] = None
    steps: int = Field(default=0, ge=0)
    heart_rate_bpm: Optional[float] = Field(None, ge=30.0, le=240.0)
    active_calories: Optional[float] = Field(None, ge=0.0)
    sleep_minutes: Optional[int] = Field(None, ge=0, le=1440)
    source: SourceType = Field(default=SourceType.GOOGLE_HEALTH)


class ClinicalLabRecord(BaseModel):
    """Biomarker or lab result extracted from Teladoc or PDF records."""
    timestamp_utc: datetime
    test_name: str = Field(..., description="e.g. 'Hemoglobin A1c', 'Total Cholesterol'")
    value: float
    unit: str = Field(..., description="e.g. '%', 'mg/dL'")
    reference_range: Optional[str] = None
    physician_notes: Optional[str] = None
    source: SourceType = Field(default=SourceType.TELADOC_PDF)


class UnifiedHealthDataset(BaseModel):
    """Consolidated in-memory dataset of deduplicated, normalized records."""
    glucose_readings: list[GlucoseReading] = Field(default_factory=list)
    scale_records: list[ScaleRecord] = Field(default_factory=list)
    activity_records: list[ActivityRecord] = Field(default_factory=list)
    lab_records: list[ClinicalLabRecord] = Field(default_factory=list)
    ingested_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

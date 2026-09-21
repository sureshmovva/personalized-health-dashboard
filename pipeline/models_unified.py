"""Unified Document Store Models.

Defines the normalized semi-structured schema for heterogeneous health metrics
across CGM, Smart Scales, Clinical Lab PDFs, and manual logs.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field


class UnifiedHealthRecord(BaseModel):
    """Normalized document model storing flexible metric payloads with strict root index keys."""

    user_id: str = Field(default="usr_default", description="Unique user identifier for multi-tenant isolation")
    timestamp: datetime = Field(description="ISO 8601 UTC timestamp of measurement")
    source_type: str = Field(description="Normalized source category (e.g. cgm, scale, activity, clinical_lab)")
    source_name: str = Field(description="Descriptive device/service name (e.g. Stelo CGM, Wyze Scale Ultra)")
    metric_category: str = Field(
        description="Standardized metric category (e.g. blood_glucose, body_weight, body_fat, hba1c, lipid_panel)"
    )
    data: dict[str, Any] = Field(
        description="Metric-specific payload with value, unit, and auxiliary telemetry"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Audit and traceability metadata including raw_file_id and confidence_score",
    )

    @property
    def raw_file_id(self) -> Optional[str]:
        return self.metadata.get("raw_file_id")

    @property
    def confidence_score(self) -> float:
        return float(self.metadata.get("confidence_score", 1.0))

    def to_json_dict(self) -> dict[str, Any]:
        """Serialize record into standard compliant JSON structure."""
        return {
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "source_type": self.source_type,
            "source_name": self.source_name,
            "metric_category": self.metric_category,
            "data": self.data,
            "metadata": self.metadata,
        }


class DenormalizedDailyHealthSummary(BaseModel):
    """Pre-aggregated daily health record for low-latency dashboard rendering."""

    user_id: str
    date: str  # YYYY-MM-DD
    glucose_mean_mg_dl: Optional[float] = None
    glucose_min_mg_dl: Optional[float] = None
    glucose_max_mg_dl: Optional[float] = None
    glucose_time_in_range_pct: Optional[float] = None
    glucose_readings_count: int = 0
    weight_lbs: Optional[float] = None
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    steps: Optional[int] = None
    resting_heart_rate_bpm: Optional[int] = None
    traceability_raw_file_ids: list[str] = Field(default_factory=list)

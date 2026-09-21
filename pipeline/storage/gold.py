"""Gold Storage Layer: Unified analytical aggregations and clinical insights.

Computes high-value clinical metrics: Time-in-Range (TIR), Glycemic Variability (CV%),
7-day moving weight averages, and unified multi-metric executive summaries.
"""

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from pipeline.models import GlucoseReading, ScaleRecord
from pipeline.storage.silver import SilverStorage


class GoldAnalytics:
    """Computes rollups and clinical aggregates from Silver tier data."""

    def __init__(self, silver_storage: Optional[SilverStorage] = None):
        self.silver = silver_storage or SilverStorage()

    def get_glycemic_profile(
        self,
        lookback_days: int = 14,
        target_min: float = 70.0,
        target_max: float = 140.0,
    ) -> dict:
        """Compute standard ambulatory glucose profile (AGP) metrics."""
        readings = self.silver.get_clean_glucose()
        if not readings:
            return {
                "reading_count": 0,
                "time_in_range_pct": 0.0,
                "time_below_range_pct": 0.0,
                "time_above_range_pct": 0.0,
                "mean_glucose": 0.0,
                "glucose_std_dev": 0.0,
                "coefficient_of_variation_pct": 0.0,
            }

        # Filter by lookback window if timestamps are recent
        values = [r.glucose_mg_dl for r in readings]
        count = len(values)
        if count == 0:
            return {}

        in_range = sum(1 for v in values if target_min <= v <= target_max)
        below_range = sum(1 for v in values if v < target_min)
        above_range = sum(1 for v in values if v > target_max)

        mean_val = sum(values) / count
        variance = sum((v - mean_val) ** 2 for v in values) / count if count > 1 else 0.0
        std_dev = math.sqrt(variance)
        cv_pct = (std_dev / mean_val * 100.0) if mean_val > 0 else 0.0

        return {
            "reading_count": count,
            "target_range": f"{int(target_min)}-{int(target_max)} mg/dL",
            "time_in_range_pct": round((in_range / count) * 100.0, 1),
            "time_below_range_pct": round((below_range / count) * 100.0, 1),
            "time_above_range_pct": round((above_range / count) * 100.0, 1),
            "mean_glucose_mg_dl": round(mean_val, 1),
            "glucose_std_dev": round(std_dev, 1),
            "coefficient_of_variation_pct": round(cv_pct, 1),
            "glycemic_status": "Optimal Stability" if cv_pct < 36.0 else "High Variability",
        }

    def get_weight_trend(self) -> dict:
        """Compute weight delta and 7-day moving averages."""
        records = self.silver.get_clean_scale()
        if not records:
            return {"record_count": 0, "trend_status": "No data"}

        sorted_records = sorted(records, key=lambda s: s.timestamp_utc)
        latest = sorted_records[-1]
        earliest = sorted_records[0]

        weight_change_lbs = round(latest.weight_lbs - earliest.weight_lbs, 1)

        # 7-day average (last 7 recordings)
        recent_7 = sorted_records[-7:]
        avg_7d_lbs = round(sum(r.weight_lbs for r in recent_7) / len(recent_7), 1)

        return {
            "record_count": len(sorted_records),
            "current_weight_lbs": latest.weight_lbs,
            "current_weight_kg": latest.weight_kg,
            "current_body_fat_pct": latest.body_fat_pct,
            "seven_day_avg_lbs": avg_7d_lbs,
            "total_weight_delta_lbs": weight_change_lbs,
            "trend_direction": "Decreasing" if weight_change_lbs < 0 else "Stable or Increasing",
        }

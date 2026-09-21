"""Streamlit metric display cards for key health indicators."""

from typing import Optional
import streamlit as st
from pipeline.models import GlucoseReading, ScaleRecord


def render_health_summary_cards(
    latest_glucose: Optional[GlucoseReading],
    glucose_avg_24h: Optional[float],
    latest_scale: Optional[ScaleRecord],
    total_samples: int,
):
    """Render top-level executive health metric summary cards in Streamlit."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if latest_glucose:
            delta_str = f"Trend: {latest_glucose.trend_arrow}" if latest_glucose.trend_arrow else "Stable"
            st.metric(
                label="Current Glucose",
                value=f"{int(latest_glucose.glucose_mg_dl)} mg/dL",
                delta=delta_str,
            )
        else:
            st.metric(label="Current Glucose", value="-- mg/dL", delta="No data")

    with col2:
        if glucose_avg_24h is not None:
            st.metric(
                label="24-Hour Avg Glucose",
                value=f"{glucose_avg_24h:.1f} mg/dL",
                delta="Normal Range: 70-120",
                delta_color="off",
            )
        else:
            st.metric(label="24-Hour Avg Glucose", value="--", delta="No data")

    with col3:
        if latest_scale:
            fat_str = f"Fat: {latest_scale.body_fat_pct:.1f}%" if latest_scale.body_fat_pct else "Weight Logged"
            st.metric(
                label="Latest Weight",
                value=f"{latest_scale.weight_lbs:.1f} lbs",
                delta=f"{latest_scale.weight_kg:.1f} kg ({fat_str})",
                delta_color="off",
            )
        else:
            st.metric(label="Latest Weight", value="-- lbs", delta="No data")

    with col4:
        st.metric(
            label="Cleaned Biometric Samples",
            value=f"{total_samples:,}",
            delta="Unified & Deduped",
            delta_color="normal",
        )

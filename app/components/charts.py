"""Interactive visualization charts using Plotly and Streamlit."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pipeline.models import GlucoseReading, ScaleRecord


def render_glucose_chart(readings: list[GlucoseReading]):
    """Render interactive glucose timeline with target glycemic zones."""
    if not readings:
        st.info("No glucose readings available to plot. Upload a Stelo CGM CSV export.")
        return

    df = pd.DataFrame([
        {
            "timestamp": r.timestamp_utc,
            "glucose": r.glucose_mg_dl,
            "trend": r.trend_arrow or "Normal",
            "source": r.source.value,
        }
        for r in readings
    ]).sort_values("timestamp")

    fig = go.Figure()

    # Target glycemic band (70 - 140 mg/dL)
    fig.add_hrect(
        y0=70,
        y1=140,
        line_width=0,
        fillcolor="rgba(34, 197, 94, 0.12)",
        annotation_text="Target Range (70-140 mg/dL)",
        annotation_position="top left",
    )

    # High glycemic threshold (>180 mg/dL)
    fig.add_hrect(
        y0=180,
        y1=300,
        line_width=0,
        fillcolor="rgba(239, 68, 68, 0.08)",
        annotation_text="Elevated (>180 mg/dL)",
        annotation_position="top right",
    )

    # Glucose trace line
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df["glucose"],
            mode="lines+markers",
            name="Glucose (mg/dL)",
            line=dict(color="#0284c7", width=2.5),
            marker=dict(size=4, color="#0369a1"),
            hovertemplate="<b>%{x|%b %d, %H:%M}</b><br>Glucose: %{y:.0f} mg/dL<extra></extra>",
        )
    )

    fig.update_layout(
        title="Continuous Glucose Trajectory (UTC)",
        xaxis_title="Time",
        yaxis_title="Glucose (mg/dL)",
        yaxis=dict(range=[40, 250]),
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20),
        height=380,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_scale_chart(records: list[ScaleRecord]):
    """Render interactive weight & body fat progress."""
    if not records:
        st.info("No scale logs available to plot. Upload a Wyze Scale CSV export.")
        return

    df = pd.DataFrame([
        {
            "timestamp": r.timestamp_utc,
            "weight_lbs": r.weight_lbs,
            "weight_kg": r.weight_kg,
            "body_fat_pct": r.body_fat_pct,
            "source": r.source.value,
        }
        for r in records
    ]).sort_values("timestamp")

    fig = px.line(
        df,
        x="timestamp",
        y="weight_lbs",
        markers=True,
        title="Body Weight Trajectory (lbs)",
        template="plotly_white",
    )
    fig.update_traces(line_color="#4f46e5", marker=dict(size=6))
    fig.update_layout(
        xaxis_title="Measurement Date",
        yaxis_title="Weight (lbs)",
        margin=dict(l=20, r=20, t=50, b=20),
        height=340,
    )

    st.plotly_chart(fig, use_container_width=True)

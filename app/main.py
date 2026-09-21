"""Streamlit Main Application Entry Point.

Unified health dashboard that ingests, normalizes, deduplicates, and visualizes
heterogeneous health metrics (Stelo CGM, Wyze Scale, Health Exports, and Manual CSVs).
"""

import os
from datetime import datetime, timedelta, timezone
from io import StringIO
import streamlit as st
import pandas as pd

from pipeline.models import (
    GlucoseReading,
    ScaleRecord,
    SourceType,
    UnifiedHealthDataset,
)
from pipeline.parsers.stelo_cgm import SteloCGMParser
from pipeline.parsers.wyze_scale import WyzeScaleParser
from pipeline.parsers.custom_csv import CustomCSVParser
from pipeline.deduplicator import deduplicate_glucose, deduplicate_scale
from app.components.metrics_cards import render_health_summary_cards
from app.components.charts import render_glucose_chart, render_scale_chart

st.set_page_config(
    page_title="Personalized Health Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    """Ensure persistent session state keys are instantiated."""
    if "dataset" not in st.session_state:
        st.session_state.dataset = UnifiedHealthDataset()
    if "pipeline_logs" not in st.session_state:
        st.session_state.pipeline_logs = []


def load_demo_data():
    """Populate realistic sample data for instant demonstration and verification."""
    now = datetime.now(timezone.utc)
    base_glucose = 98.0

    # 48 hours of simulated 15-minute CGM readings
    sample_cgm: list[GlucoseReading] = []
    for i in range(192):
        ts = now - timedelta(minutes=(192 - i) * 15)
        # diurnal curve simulation
        hour = ts.hour
        val = base_glucose + (25 if 8 <= hour <= 10 or 12 <= hour <= 14 or 18 <= hour <= 20 else 0)
        sample_cgm.append(
            GlucoseReading(
                timestamp_utc=ts,
                glucose_mg_dl=round(val + (i % 7) * 2.5 - 5, 1),
                trend_arrow="Flat" if i % 4 != 0 else "FortyFiveUp",
                source=SourceType.STELO_CGM,
            )
        )

    # 14 days of daily morning scale weigh-ins
    sample_scale: list[ScaleRecord] = []
    for day in range(14):
        ts = (now - timedelta(days=14 - day)).replace(hour=7, minute=15, second=0)
        lbs = 178.5 - (day * 0.2) + ((day % 3) * 0.15)
        sample_scale.append(
            ScaleRecord(
                timestamp_utc=ts,
                weight_lbs=round(lbs, 2),
                weight_kg=round(lbs * 0.45359237, 2),
                body_fat_pct=round(18.2 - (day * 0.05), 1),
                muscle_mass_kg=round(62.4 + (day * 0.02), 1),
                metabolic_age=31,
                source=SourceType.WYZE_SCALE,
            )
        )

    st.session_state.dataset.glucose_readings = sample_cgm
    st.session_state.dataset.scale_records = sample_scale
    st.session_state.pipeline_logs.append(
        f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] Loaded synthetic baseline dataset: {len(sample_cgm)} CGM points, {len(sample_scale)} scale weigh-ins."
    )


def main():
    init_session_state()

    st.title("🩺 Personalized Health Dashboard")
    st.caption("Unified multi-source pipeline: Dexcom Stelo CGM, Wyze Scale Ultra & Clinical Records")

    # --- Sidebar: Data Ingestion & Pipeline Controls ---
    with st.sidebar:
        st.header("📥 Data Source Ingest")

        if st.button("🚀 Load Baseline Demo Data", use_container_width=True):
            load_demo_data()
            st.success("Loaded demo dataset!")

        st.divider()

        # Source 1: Stelo CGM
        st.subheader("1. Stelo CGM CSV")
        stelo_file = st.file_uploader(
            "Upload Dexcom/Stelo Export",
            type=["csv"],
            key="stelo_upload",
            help="Upload raw Stelo Clarity or mobile CSV export.",
        )
        if stelo_file:
            try:
                parser = SteloCGMParser()
                parsed_cgm = parser.parse(stelo_file)
                before_count = len(parsed_cgm)
                cleaned_cgm = deduplicate_glucose(parsed_cgm)
                st.session_state.dataset.glucose_readings = cleaned_cgm
                msg = f"Parsed Stelo CGM: {before_count} rows -> {len(cleaned_cgm)} clean points after dedup."
                st.session_state.pipeline_logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] {msg}")
                st.sidebar.success(msg)
            except Exception as e:
                st.sidebar.error(f"Error parsing Stelo CSV: {e}")

        # Source 2: Wyze Scale
        st.subheader("2. Wyze Scale CSV")
        wyze_file = st.file_uploader(
            "Upload Wyze Scale Export",
            type=["csv"],
            key="wyze_upload",
            help="Upload CSV export from Wyze Body Scale Ultra.",
        )
        if wyze_file:
            try:
                parser = WyzeScaleParser()
                parsed_scale = parser.parse(wyze_file)
                cleaned_scale = deduplicate_scale(parsed_scale)
                st.session_state.dataset.scale_records = cleaned_scale
                msg = f"Parsed Wyze Scale: {len(parsed_scale)} rows -> {len(cleaned_scale)} clean weigh-ins."
                st.session_state.pipeline_logs.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] {msg}")
                st.sidebar.success(msg)
            except Exception as e:
                st.sidebar.error(f"Error parsing Wyze CSV: {e}")

        # Source 3: Custom / Manual Tracker CSV
        st.subheader("3. Manual CSV Tracker")
        custom_file = st.file_uploader(
            "Upload Manual Tracker Log",
            type=["csv"],
            key="custom_upload",
        )
        if custom_file:
            try:
                parser = CustomCSVParser()
                res = parser.parse(custom_file)
                if res["glucose"]:
                    st.session_state.dataset.glucose_readings.extend(res["glucose"])
                    st.session_state.dataset.glucose_readings = deduplicate_glucose(
                        st.session_state.dataset.glucose_readings
                    )
                if res["scale"]:
                    st.session_state.dataset.scale_records.extend(res["scale"])
                    st.session_state.dataset.scale_records = deduplicate_scale(
                        st.session_state.dataset.scale_records
                    )
                st.sidebar.success("Merged custom tracking data into unified pipeline.")
            except Exception as e:
                st.sidebar.error(f"Error parsing Custom CSV: {e}")

    # --- Metrics Section ---
    glucose_data = st.session_state.dataset.glucose_readings
    scale_data = st.session_state.dataset.scale_records

    latest_glucose = glucose_data[-1] if glucose_data else None
    avg_24h = (
        sum(r.glucose_mg_dl for r in glucose_data[-96:]) / min(len(glucose_data), 96)
        if glucose_data
        else None
    )
    latest_scale = scale_data[-1] if scale_data else None
    total_samples = len(glucose_data) + len(scale_data)

    render_health_summary_cards(
        latest_glucose=latest_glucose,
        glucose_avg_24h=avg_24h,
        latest_scale=latest_scale,
        total_samples=total_samples,
    )

    st.markdown("---")

    # --- Interactive Visualizations ---
    chart_tab1, chart_tab2, chart_tab3 = st.tabs([
        "📈 Continuous Glucose (CGM)",
        "⚖️ Weight & Body Composition",
        "⚙️ Pipeline Deduplication & Logs",
    ])

    with chart_tab1:
        render_glucose_chart(glucose_data)

    with chart_tab2:
        render_scale_chart(scale_data)

    with chart_tab3:
        st.subheader("Data Pipeline Deduplication & Audit Trail")
        st.markdown(
            """
            **Conflict & Deduplication Rules:**
            - **Glucose**: Sliding 2-minute time window; Stelo CGM overrides manual CSV.
            - **Scale**: Sliding 15-minute time window; Wyze direct measurement overrides manual entries.
            - **Clinical Records**: Physician lab panels (A1C, lipids) supersede OCR/wearable estimates.
            """
        )
        if st.session_state.pipeline_logs:
            for log in reversed(st.session_state.pipeline_logs):
                st.text(log)
        else:
            st.info("No pipeline events recorded yet. Upload a file or load demo data.")


if __name__ == "__main__":
    main()

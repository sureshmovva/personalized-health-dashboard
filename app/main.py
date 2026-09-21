"""Streamlit Main Application Entry Point.

Unified health dashboard that ingests, normalizes, deduplicates, and visualizes
heterogeneous health metrics with persistent SQLite/DuckDB storage.
"""

from datetime import datetime, timedelta, timezone
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
from pipeline.db import (
    init_db,
    save_glucose_readings,
    save_scale_records,
    get_all_glucose,
    get_all_scale,
    get_database_summary,
    log_audit_event,
)
from app.components.metrics_cards import render_health_summary_cards
from app.components.charts import render_glucose_chart, render_scale_chart

st.set_page_config(
    page_title="Personalized Health Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    """Ensure persistent session state keys are instantiated and hydrate from DB."""
    init_db()
    if "dataset" not in st.session_state:
        db_glucose = get_all_glucose()
        db_scale = get_all_scale()
        st.session_state.dataset = UnifiedHealthDataset(
            glucose_readings=db_glucose,
            scale_records=db_scale,
        )
    if "pipeline_logs" not in st.session_state:
        st.session_state.pipeline_logs = []


def load_demo_data():
    """Populate realistic sample data and persist to the secure database."""
    now = datetime.now(timezone.utc)
    base_glucose = 98.0

    # 48 hours of simulated 15-minute CGM readings
    sample_cgm: list[GlucoseReading] = []
    for i in range(192):
        ts = now - timedelta(minutes=(192 - i) * 15)
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

    # Save directly to database
    save_glucose_readings(sample_cgm)
    save_scale_records(sample_scale)
    log_audit_event(
        source=SourceType.STELO_CGM,
        raw_count=len(sample_cgm),
        deduped_count=len(sample_cgm),
        conflicts_resolved=0,
        status="SUCCESS",
        message="Generated and persisted synthetic baseline CGM dataset.",
    )

    st.session_state.dataset.glucose_readings = get_all_glucose()
    st.session_state.dataset.scale_records = get_all_scale()
    st.session_state.pipeline_logs.append(
        f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] Persisted demo dataset to database: {len(sample_cgm)} CGM points, {len(sample_scale)} scale weigh-ins."
    )


def main():
    init_session_state()

    st.title("🩺 Personalized Health Dashboard")
    st.caption("Unified multi-source pipeline: Dexcom Stelo CGM, Wyze Scale Ultra & SQLite/DuckDB Persistence")

    # --- Sidebar: Data Ingestion & Pipeline Controls ---
    with st.sidebar:
        st.header("📥 Data Source Ingest")

        if st.button("🚀 Load Baseline Demo Data", use_container_width=True):
            load_demo_data()
            st.success("Loaded & persisted demo dataset to local SQLite database!")

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
                save_glucose_readings(cleaned_cgm)
                log_audit_event(
                    source=SourceType.STELO_CGM,
                    raw_count=before_count,
                    deduped_count=len(cleaned_cgm),
                    conflicts_resolved=before_count - len(cleaned_cgm),
                    status="SUCCESS",
                    message="Ingested Stelo CGM CSV",
                )
                st.session_state.dataset.glucose_readings = get_all_glucose()
                msg = f"Saved Stelo CGM: {before_count} raw rows -> {len(cleaned_cgm)} clean points persisted to database."
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
                before_scale = len(parsed_scale)
                cleaned_scale = deduplicate_scale(parsed_scale)
                save_scale_records(cleaned_scale)
                log_audit_event(
                    source=SourceType.WYZE_SCALE,
                    raw_count=before_scale,
                    deduped_count=len(cleaned_scale),
                    conflicts_resolved=before_scale - len(cleaned_scale),
                    status="SUCCESS",
                    message="Ingested Wyze Scale CSV",
                )
                st.session_state.dataset.scale_records = get_all_scale()
                msg = f"Saved Wyze Scale: {before_scale} raw weigh-ins -> {len(cleaned_scale)} clean records persisted to database."
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
                    cleaned_manual_glucose = deduplicate_glucose(res["glucose"])
                    save_glucose_readings(cleaned_manual_glucose)
                    st.session_state.dataset.glucose_readings = get_all_glucose()
                if res["scale"]:
                    cleaned_manual_scale = deduplicate_scale(res["scale"])
                    save_scale_records(cleaned_manual_scale)
                    st.session_state.dataset.scale_records = get_all_scale()
                st.sidebar.success("Merged and persisted custom tracking data into database.")
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

    # --- Interactive Visualizations & Database Explorer ---
    chart_tab1, chart_tab2, chart_tab3, chart_tab4 = st.tabs([
        "📈 Continuous Glucose (CGM)",
        "⚖️ Weight & Body Composition",
        "🗄️ Database Explorer (SQLite)",
        "⚙️ Pipeline Deduplication & Logs",
    ])

    with chart_tab1:
        render_glucose_chart(glucose_data)

    with chart_tab2:
        render_scale_chart(scale_data)

    with chart_tab3:
        st.subheader("Persistent SQLite Database Schema & Tables")
        db_stats = get_database_summary()
        col_db1, col_db2, col_db3, col_db4 = st.columns(4)
        col_db1.metric("Database Storage", "data/health_store.db")
        col_db2.metric("Stored Glucose Records", f"{db_stats['glucose_count']:,}")
        col_db3.metric("Stored Scale Records", f"{db_stats['scale_count']:,}")
        col_db4.metric("Audit Trail Events", f"{db_stats['audit_logs_count']:,}")

        st.markdown("#### Table: `glucose_readings`")
        if glucose_data:
            g_df = pd.DataFrame([
                {
                    "Timestamp (UTC)": r.timestamp_utc.isoformat(),
                    "Glucose (mg/dL)": r.glucose_mg_dl,
                    "Trend": r.trend_arrow,
                    "Source": r.source.value,
                }
                for r in glucose_data[-50:]
            ])
            st.dataframe(g_df, use_container_width=True)
        else:
            st.info("No records in `glucose_readings` table.")

        st.markdown("#### Table: `scale_records`")
        if scale_data:
            s_df = pd.DataFrame([
                {
                    "Timestamp (UTC)": r.timestamp_utc.isoformat(),
                    "Weight (lbs)": r.weight_lbs,
                    "Weight (kg)": r.weight_kg,
                    "Body Fat %": r.body_fat_pct,
                    "Muscle Mass (kg)": r.muscle_mass_kg,
                    "Metabolic Age": r.metabolic_age,
                    "Source": r.source.value,
                }
                for r in scale_data[-50:]
            ])
            st.dataframe(s_df, use_container_width=True)
        else:
            st.info("No records in `scale_records` table.")

    with chart_tab4:
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

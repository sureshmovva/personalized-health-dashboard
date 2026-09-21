"""Streamlit Main Application Entry Point.

Unified health dashboard implementing the Medallion Storage Architecture:
- Bronze Layer: Immutable raw file storage with SHA-256 receipt tracking (data/bronze/)
- Silver Layer: Schema-enforced, normalized, deduplicated relational store (data/health_store.db)
- Gold Layer: High-performance clinical rollups (Time-in-Range, Glycemic CV%, 7-Day Weight Avg)
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
from pipeline.storage.bronze import BronzeStorage
from pipeline.storage.silver import SilverStorage
from pipeline.storage.gold import GoldAnalytics
from pipeline.db import get_database_summary
from app.components.metrics_cards import render_health_summary_cards
from app.components.charts import render_glucose_chart, render_scale_chart

st.set_page_config(
    page_title="Personalized Health Dashboard",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    """Ensure persistent session state keys are instantiated and hydrate from Silver layer."""
    bronze = BronzeStorage()
    silver = SilverStorage()
    gold = GoldAnalytics(silver_storage=silver)

    if "dataset" not in st.session_state:
        st.session_state.dataset = UnifiedHealthDataset(
            glucose_readings=silver.get_clean_glucose(),
            scale_records=silver.get_clean_scale(),
        )
    if "pipeline_logs" not in st.session_state:
        st.session_state.pipeline_logs = []


def load_demo_data():
    """Generate synthetic data and flow through Bronze, Silver, and Gold tiers."""
    now = datetime.now(timezone.utc)
    base_glucose = 98.0
    bronze = BronzeStorage()
    silver = SilverStorage()

    # 48 hours of simulated 15-minute CGM readings
    sample_cgm: list[GlucoseReading] = []
    cgm_raw_csv_lines = ["Timestamp,Glucose Value (mg/dL),Trend Arrow"]
    for i in range(192):
        ts = now - timedelta(minutes=(192 - i) * 15)
        hour = ts.hour
        val = base_glucose + (25 if 8 <= hour <= 10 or 12 <= hour <= 14 or 18 <= hour <= 20 else 0)
        reading_val = round(val + (i % 7) * 2.5 - 5, 1)
        trend = "Flat" if i % 4 != 0 else "FortyFiveUp"

        sample_cgm.append(
            GlucoseReading(
                timestamp_utc=ts,
                glucose_mg_dl=reading_val,
                trend_arrow=trend,
                source=SourceType.STELO_CGM,
            )
        )
        cgm_raw_csv_lines.append(f"{ts.isoformat()},{reading_val},{trend}")

    # 1. Bronze: Store raw simulated payload
    bronze.ingest_raw_file(
        file_or_bytes="\n".join(cgm_raw_csv_lines).encode("utf-8"),
        filename="stelo_cgm_baseline_demo.csv",
        source=SourceType.STELO_CGM,
        metadata={"note": "Baseline synthetic CGM data"},
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

    # 2. Silver: Deduplicate & persist
    silver.process_and_persist_glucose(sample_cgm, source=SourceType.STELO_CGM)
    silver.process_and_persist_scale(sample_scale, source=SourceType.WYZE_SCALE)

    st.session_state.dataset.glucose_readings = silver.get_clean_glucose()
    st.session_state.dataset.scale_records = silver.get_clean_scale()
    st.session_state.pipeline_logs.append(
        f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] Medallion Pipeline Flow: Ingested to Bronze -> Enforced in Silver -> Generated Gold Analytics."
    )


def main():
    init_session_state()
    bronze = BronzeStorage()
    silver = SilverStorage()
    gold = GoldAnalytics(silver_storage=silver)

    st.title("🩺 Personalized Health Dashboard")
    st.caption("Medallion Architecture: Bronze (Raw Blob) ──► Silver (Normalized) ──► Gold (Clinical Analytics)")

    # --- Sidebar: Ingestion into Medallion Pipeline ---
    with st.sidebar:
        st.header("📥 Data Source Ingest")

        if st.button("🚀 Load Baseline Demo Data", use_container_width=True):
            load_demo_data()
            st.success("Loaded & persisted demo dataset across Bronze, Silver & Gold tiers!")

        st.divider()

        # Source 1: Stelo CGM
        st.subheader("1. Stelo CGM CSV")
        stelo_file = st.file_uploader(
            "Upload Dexcom/Stelo Export",
            type=["csv"],
            key="stelo_upload",
            help="Raw CSV export is archived immutably in Bronze layer and parsed into Silver.",
        )
        if stelo_file:
            try:
                # Bronze Layer: Store raw
                stelo_bytes = stelo_file.getvalue()
                bronze_receipt = bronze.ingest_raw_file(
                    file_or_bytes=stelo_bytes,
                    filename=stelo_file.name,
                    source=SourceType.STELO_CGM,
                )

                # Silver Layer: Parse, deduplicate, persist
                parsed_cgm = SteloCGMParser().parse(stelo_file)
                res = silver.process_and_persist_glucose(parsed_cgm, source=SourceType.STELO_CGM)
                st.session_state.dataset.glucose_readings = silver.get_clean_glucose()

                msg = f"Bronze receipt {bronze_receipt['sha256'][:8]} -> Silver: {res['saved_count']} clean readings."
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
            help="Raw CSV export from Wyze Body Scale Ultra.",
        )
        if wyze_file:
            try:
                wyze_bytes = wyze_file.getvalue()
                bronze_receipt = bronze.ingest_raw_file(
                    file_or_bytes=wyze_bytes,
                    filename=wyze_file.name,
                    source=SourceType.WYZE_SCALE,
                )
                parsed_scale = WyzeScaleParser().parse(wyze_file)
                res = silver.process_and_persist_scale(parsed_scale, source=SourceType.WYZE_SCALE)
                st.session_state.dataset.scale_records = silver.get_clean_scale()

                msg = f"Bronze receipt {bronze_receipt['sha256'][:8]} -> Silver: {res['saved_count']} weigh-ins."
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
                bronze.ingest_raw_file(
                    file_or_bytes=custom_file.getvalue(),
                    filename=custom_file.name,
                    source=SourceType.MANUAL_CSV,
                )
                res = CustomCSVParser().parse(custom_file)
                if res["glucose"]:
                    silver.process_and_persist_glucose(res["glucose"], source=SourceType.MANUAL_CSV)
                    st.session_state.dataset.glucose_readings = silver.get_clean_glucose()
                if res["scale"]:
                    silver.process_and_persist_scale(res["scale"], source=SourceType.MANUAL_CSV)
                    st.session_state.dataset.scale_records = silver.get_clean_scale()
                st.sidebar.success("Ingested manual CSV into Bronze and Silver layers.")
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

    # --- Interactive Visualizations & Medallion Explorer ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Continuous Glucose (CGM)",
        "⚖️ Weight & Body Composition",
        "🏆 Gold Clinical Analytics",
        "🏛️ Medallion Storage Inspector (Bronze / Silver)",
    ])

    with tab1:
        render_glucose_chart(glucose_data)

    with tab2:
        render_scale_chart(scale_data)

    with tab3:
        st.subheader("Gold Layer: Ambulatory Glucose Profile & Metabolic Rollups")
        profile = gold.get_glycemic_profile(target_min=70.0, target_max=140.0)
        weight_trend = gold.get_weight_trend()

        if profile.get("reading_count", 0) > 0:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Time-In-Range (70-140 mg/dL)", f"{profile['time_in_range_pct']}%", delta="Target: >70%")
            c2.metric("Mean Glucose", f"{profile['mean_glucose_mg_dl']} mg/dL")
            c3.metric("Glycemic Variability (CV%)", f"{profile['coefficient_of_variation_pct']}%", delta=profile["glycemic_status"])
            c4.metric("Time Above Range (>140 mg/dL)", f"{profile['time_above_range_pct']}%")

            st.markdown("#### Weight & Body Composition Trajectory")
            w1, w2, w3 = st.columns(3)
            w1.metric("Current Weight", f"{weight_trend.get('current_weight_lbs', '--')} lbs")
            w2.metric("7-Day Moving Avg", f"{weight_trend.get('seven_day_avg_lbs', '--')} lbs")
            w3.metric("Net Weight Delta", f"{weight_trend.get('total_weight_delta_lbs', '--')} lbs", delta=weight_trend.get("trend_direction"))
        else:
            st.info("No glucose or weight records in Silver layer to generate Gold analytics.")

    with tab4:
        st.subheader("Medallion Multi-Tier Storage Inspector")
        st.markdown(
            """
            - **Bronze Layer (`data/bronze/`)**: Cryptographically verified immutable raw blobs with SHA-256 receipts.
            - **Silver Layer (`data/health_store.db`)**: Normalized Pydantic models with sliding-window deduplication.
            - **Gold Layer**: Materialized analytical aggregates and clinical indices.
            """
        )

        st.markdown("#### Bronze Raw Ingestion Manifest")
        raw_files = bronze.list_raw_files()
        if raw_files:
            b_df = pd.DataFrame(raw_files)[["file_id", "source", "original_filename", "sha256", "size_bytes", "ingested_at_utc"]]
            st.dataframe(b_df, use_container_width=True)
        else:
            st.info("No raw files ingested into Bronze layer yet.")

        st.markdown("#### Silver Deduplicated Records Summary")
        db_stats = get_database_summary()
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("Silver Database", "data/health_store.db")
        col_s2.metric("Deduplicated Glucose", f"{db_stats['glucose_count']:,}")
        col_s3.metric("Deduplicated Scale Logs", f"{db_stats['scale_count']:,}")


if __name__ == "__main__":
    main()

"""Streamlit Main Application Entry Point.

Unified health dashboard implementing:
- Layer 1: Unstructured Raw Vault (Object storage with SHA-256 receipts)
- Layer 2: Normalized Document Store (Unified JSON Records, composite (user_id, timestamp) indexing)
- Denormalized Daily Aggregates for single-query dashboard loads
- End-to-end Traceability Links from charts/metrics back to Layer 1 original files
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path regardless of execution directory or platform
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datetime import datetime, timedelta, timezone
import json
import streamlit as st
import pandas as pd

from pipeline.models import (
    GlucoseReading,
    ScaleRecord,
    SourceType,
    UnifiedHealthDataset,
)
from pipeline.models_unified import UnifiedHealthRecord
from pipeline.parsers.stelo_cgm import SteloCGMParser
from pipeline.parsers.wyze_scale import WyzeScaleParser
from pipeline.parsers.custom_csv import CustomCSVParser
from pipeline.storage.bronze import BronzeStorage
from pipeline.storage.silver import SilverStorage
from pipeline.storage.gold import GoldAnalytics
from pipeline.document_store import (
    insert_unified_records,
    query_unified_records,
    get_denormalized_daily_summaries,
    get_traceability_link,
)
from app.components.metrics_cards import render_health_summary_cards
from app.components.charts import render_glucose_chart, render_scale_chart

DEFAULT_USER_ID = "usr_987654"

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

    if "dataset" not in st.session_state:
        st.session_state.dataset = UnifiedHealthDataset(
            glucose_readings=silver.get_clean_glucose(),
            scale_records=silver.get_clean_scale(),
        )
    if "pipeline_logs" not in st.session_state:
        st.session_state.pipeline_logs = []
    if "current_user_id" not in st.session_state:
        st.session_state.current_user_id = DEFAULT_USER_ID


def load_demo_data():
    """Generate synthetic data across Layer 1 Vault, Layer 2 Document Store, and Gold Tier."""
    now = datetime.now(timezone.utc)
    base_glucose = 98.0
    bronze = BronzeStorage()
    silver = SilverStorage()
    user_id = st.session_state.current_user_id

    # 1. Ingest simulated raw files into Layer 1 Vault
    cgm_raw_csv_lines = ["Timestamp,Glucose Value (mg/dL),Trend Arrow"]
    sample_cgm: list[GlucoseReading] = []
    unified_records: list[UnifiedHealthRecord] = []

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

    # Store in Layer 1
    receipt_cgm = bronze.ingest_raw_file(
        file_or_bytes="\n".join(cgm_raw_csv_lines).encode("utf-8"),
        filename="stelo_cgm_baseline_export.csv",
        source=SourceType.STELO_CGM,
        metadata={"user_id": user_id},
    )

    # 14 days of scale weigh-ins
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

    receipt_scale = bronze.ingest_raw_file(
        file_or_bytes=b"Date,Weight_lbs,BodyFat_pct\n2026-09-21,178.2,18.1\n",
        filename="wyze_scale_history.csv",
        source=SourceType.WYZE_SCALE,
        metadata={"user_id": user_id},
    )

    # Layer 2: Convert to Unified JSON Records with Traceability Link
    for r in sample_cgm:
        unified_records.append(
            UnifiedHealthRecord(
                user_id=user_id,
                timestamp=r.timestamp_utc,
                source_type="cgm",
                source_name="Stelo CGM",
                metric_category="blood_glucose",
                data={
                    "value": r.glucose_mg_dl,
                    "unit": "mg/dL",
                    "trend_arrow": r.trend_arrow,
                },
                metadata={
                    "raw_file_id": receipt_cgm["file_id"],
                    "confidence_score": 0.99,
                },
            )
        )

    for s in sample_scale:
        unified_records.append(
            UnifiedHealthRecord(
                user_id=user_id,
                timestamp=s.timestamp_utc,
                source_type="scale",
                source_name="Wyze Scale Ultra",
                metric_category="body_weight",
                data={
                    "value_lbs": s.weight_lbs,
                    "value_kg": s.weight_kg,
                    "body_fat_pct": s.body_fat_pct,
                    "muscle_mass_kg": s.muscle_mass_kg,
                    "metabolic_age": s.metabolic_age,
                    "unit": "lbs",
                },
                metadata={
                    "raw_file_id": receipt_scale["file_id"],
                    "confidence_score": 1.0,
                },
            )
        )

    # Persist in Layer 2 Document Store (automatically updates daily denormalized rollups)
    insert_unified_records(unified_records)

    # Also persist to Silver table for legacy compatibility
    silver.process_and_persist_glucose(sample_cgm, source=SourceType.STELO_CGM)
    silver.process_and_persist_scale(sample_scale, source=SourceType.WYZE_SCALE)

    st.session_state.dataset.glucose_readings = silver.get_clean_glucose()
    st.session_state.dataset.scale_records = silver.get_clean_scale()
    st.session_state.pipeline_logs.append(
        f"[{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}] Ingested {len(unified_records)} Unified JSON records to Layer 2 with Layer 1 Traceability links."
    )


def main():
    init_session_state()
    bronze = BronzeStorage()
    silver = SilverStorage()
    gold = GoldAnalytics(silver_storage=silver)
    user_id = st.session_state.current_user_id

    st.title("🩺 Personalized Health Dashboard")
    st.caption("Layer 1 (Raw Vault) ──► Layer 2 (Normalized JSON Document Store) ──► Layer 3 (Clinical Rollups)")

    # --- Sidebar: User Partition & Ingest ---
    with st.sidebar:
        st.header("👤 User Context & Ingest")
        st.text_input("Active User ID (Partition Key)", value=user_id, key="current_user_id")

        if st.button("🚀 Load Baseline Demo Data", use_container_width=True):
            load_demo_data()
            st.success("Loaded & persisted across Layer 1 Vault & Layer 2 Document Store!")

        st.divider()

        # Ingest 1: Stelo CGM
        st.subheader("1. Stelo CGM CSV")
        stelo_file = st.file_uploader("Upload Dexcom/Stelo Export", type=["csv"], key="stelo_upload")
        if stelo_file:
            try:
                # Layer 1 Vault
                receipt = bronze.ingest_raw_file(
                    file_or_bytes=stelo_file.getvalue(),
                    filename=stelo_file.name,
                    source=SourceType.STELO_CGM,
                    metadata={"user_id": user_id},
                )
                parsed = SteloCGMParser().parse(stelo_file)
                silver.process_and_persist_glucose(parsed, source=SourceType.STELO_CGM)

                # Layer 2 Unified Documents
                doc_records = [
                    UnifiedHealthRecord(
                        user_id=user_id,
                        timestamp=r.timestamp_utc,
                        source_type="cgm",
                        source_name="Stelo CGM",
                        metric_category="blood_glucose",
                        data={"value": r.glucose_mg_dl, "unit": "mg/dL", "trend_arrow": r.trend_arrow},
                        metadata={"raw_file_id": receipt["file_id"], "confidence_score": 0.99},
                    )
                    for r in parsed
                ]
                insert_unified_records(doc_records)
                st.session_state.dataset.glucose_readings = silver.get_clean_glucose()
                st.sidebar.success(f"Archived in Layer 1 ({receipt['file_id']}) and saved {len(doc_records)} Unified JSON docs!")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

        # Ingest 2: Wyze Scale
        st.subheader("2. Wyze Scale CSV")
        wyze_file = st.file_uploader("Upload Wyze Scale Export", type=["csv"], key="wyze_upload")
        if wyze_file:
            try:
                receipt = bronze.ingest_raw_file(
                    file_or_bytes=wyze_file.getvalue(),
                    filename=wyze_file.name,
                    source=SourceType.WYZE_SCALE,
                    metadata={"user_id": user_id},
                )
                parsed_scale = WyzeScaleParser().parse(wyze_file)
                silver.process_and_persist_scale(parsed_scale, source=SourceType.WYZE_SCALE)

                doc_records = [
                    UnifiedHealthRecord(
                        user_id=user_id,
                        timestamp=s.timestamp_utc,
                        source_type="scale",
                        source_name="Wyze Scale Ultra",
                        metric_category="body_weight",
                        data={
                            "value_lbs": s.weight_lbs,
                            "value_kg": s.weight_kg,
                            "body_fat_pct": s.body_fat_pct,
                            "unit": "lbs",
                        },
                        metadata={"raw_file_id": receipt["file_id"], "confidence_score": 1.0},
                    )
                    for s in parsed_scale
                ]
                insert_unified_records(doc_records)
                st.session_state.dataset.scale_records = silver.get_clean_scale()
                st.sidebar.success(f"Archived in Layer 1 ({receipt['file_id']}) and saved {len(doc_records)} Unified Scale docs!")
            except Exception as e:
                st.sidebar.error(f"Error: {e}")

    # --- Top Health Summary Cards ---
    glucose_data = st.session_state.dataset.glucose_readings
    scale_data = st.session_state.dataset.scale_records
    latest_glucose = glucose_data[-1] if glucose_data else None
    avg_24h = (
        sum(r.glucose_mg_dl for r in glucose_data[-96:]) / min(len(glucose_data), 96)
        if glucose_data
        else None
    )
    latest_scale = scale_data[-1] if scale_data else None

    render_health_summary_cards(
        latest_glucose=latest_glucose,
        glucose_avg_24h=avg_24h,
        latest_scale=latest_scale,
        total_samples=len(glucose_data) + len(scale_data),
    )

    st.markdown("---")

    # --- Multi-Tab Experience ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Continuous Glucose (CGM)",
        "⚖️ Weight & Body Composition",
        "📄 Layer 2: Unified Document Store & Traceability",
        "🏆 Denormalized Daily Dashboard Summaries",
    ])

    with tab1:
        render_glucose_chart(glucose_data)

    with tab2:
        render_scale_chart(scale_data)

    with tab3:
        st.subheader("Normalized Document Store (Unified JSON Schema)")
        st.markdown(
            f"Filtered by indexed keys: `user_id = '{user_id}'` with composite `(user_id, timestamp_utc)` indexing."
        )

        records = query_unified_records(user_id=user_id, limit=50)
        if records:
            # Display JSON sample
            st.markdown("#### Sample Standardized JSON Record Layout")
            st.json(records[-1].to_json_dict())

            st.markdown("#### Indexed Document Records with Traceability Link")
            df = pd.DataFrame([
                {
                    "timestamp": r.timestamp.isoformat(),
                    "source_name": r.source_name,
                    "metric_category": r.metric_category,
                    "value": r.data.get("value") or r.data.get("value_lbs"),
                    "unit": r.data.get("unit"),
                    "raw_file_id (Layer 1 Link)": r.raw_file_id,
                    "confidence_score": r.confidence_score,
                }
                for r in reversed(records)
            ])
            st.dataframe(df, use_container_width=True)

            # Traceability Inspector
            st.markdown("#### Layer 1 Traceability Provenance Lookup")
            sample_file_id = records[-1].raw_file_id
            if sample_file_id:
                trace_receipt = get_traceability_link(sample_file_id)
                if trace_receipt:
                    st.success(f"Verified Traceability: Metric links directly to Layer 1 Raw Vault!")
                    st.json(trace_receipt)
        else:
            st.info("No unified documents found for this user. Click 'Load Baseline Demo Data' in the sidebar.")

    with tab4:
        st.subheader("Denormalized Daily Health Summary (Single-Fetch Dashboard Table)")
        st.markdown(
            "Pre-aggregated records stored in `unified_daily_rollups`. The UI fetches daily glucose averages, TIR%, and scale metrics without running runtime joins across disparate tables."
        )
        daily_summaries = get_denormalized_daily_summaries(user_id=user_id)
        if daily_summaries:
            d_df = pd.DataFrame([
                {
                    "Date": d.date,
                    "Mean Glucose (mg/dL)": d.glucose_mean_mg_dl,
                    "TIR (70-140 mg/dL)": f"{d.glucose_time_in_range_pct}%" if d.glucose_time_in_range_pct else "--",
                    "Min Glucose": d.glucose_min_mg_dl,
                    "Max Glucose": d.glucose_max_mg_dl,
                    "Readings Count": d.glucose_readings_count,
                    "Weight (lbs)": d.weight_lbs,
                    "Body Fat %": f"{d.body_fat_pct}%" if d.body_fat_pct else "--",
                    "Layer 1 Source Files": ", ".join(d.traceability_raw_file_ids),
                }
                for d in daily_summaries
            ])
            st.dataframe(d_df, use_container_width=True)
        else:
            st.info("No daily summaries computed yet.")


if __name__ == "__main__":
    main()

# Personalized Health Dashboard — Architecture Guide

## 1. System Overview & The Medallion Storage Pattern
When processing heterogeneous health data (unstructured clinical PDFs, lab reports, continuous 5-minute CGM streams, daily scale weigh-ins, and manual tracking spreadsheets), no single database format handles every requirement efficiently. 

We implement the industry-standard **Medallion Multi-Tier Storage Architecture**:

```
+-----------------------------------------------------------------------------------------+
|                                BRONZE LAYER (Raw Ingestion)                             |
|  - Immutable archive of incoming payloads (raw PDFs, unmodified CSV exports, JSON)       |
|  - Cryptographic SHA-256 fingerprinting & manifest cataloging in data/bronze/manifest.json |
|  - Guarantees 100% auditability; allows reprocessing if parsing or OCR logic improves   |
+--------------------------------------------+--------------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                        SILVER LAYER (Extraction & Schema Enforcement)                   |
|  - Pydantic v2 schema enforcement (UTC timestamps, unit conversions: lbs<->kg, mg/dL)   |
|  - Sliding-window deduplication (2m CGM window, 15m scale window)                       |
|  - Deterministic priority conflict resolution (Lab > Sensor > Aggregator > Manual)      |
|  - Persisted in structured relational tables (data/health_store.db: SQLite / DuckDB)    |
+--------------------------------------------+--------------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                          GOLD LAYER (Unified Query & Clinical Insights)                 |
|  - Standardized Ambulatory Glucose Profile (AGP): Time-in-Range (70-140 mg/dL), TAR, TBR|
|  - Glycemic variability analytics: Mean Glucose, Standard Deviation, and CV%            |
|  - Body composition trends: 7-day moving averages and net mass deltas                   |
|  - High-performance query interfaces for Streamlit frontend and clinical report exports |
+-----------------------------------------------------------------------------------------+
```

## 2. Directory Layout & Storage Hierarchy

```
data/
├── bronze/                             # Raw immutable files
│   ├── manifest.json                   # SHA-256 catalog and provenance receipt index
│   ├── stelo_cgm/YYYY/MM/DD/           # Date-partitioned raw CGM CSVs
│   ├── wyze_scale/YYYY/MM/DD/          # Date-partitioned raw scale CSVs
│   └── teladoc_pdf/YYYY/MM/DD/         # Raw clinical PDFs & lab reports
├── silver/                             # Structured relational data
│   └── health_store.db                 # SQLite database (WAL mode, relational constraints)
└── gold/                               # Materialized analytical rollups and cached aggregates
```

## 3. Storage Layer Modules

### Bronze Storage (`pipeline/storage/bronze.py`)
- Calculates SHA-256 hash upon ingestion.
- Date-partitions payloads into `data/bronze/{source}/YYYY/MM/DD/`.
- Appends receipt metadata (file ID, timestamp, byte size, origin) to `data/bronze/manifest.json`.

### Silver Storage (`pipeline/storage/silver.py`)
- Executes sliding-window deduplication:
  - **Glucose**: 2-minute sliding window; hardware sensor overrides manual CSV.
  - **Scale**: 15-minute sliding window; bioimpedance scale overrides manual weight.
- Persists normalized Pydantic records into SQLite with `UNIQUE(timestamp_utc, source)` constraints.

### Gold Analytics (`pipeline/storage/gold.py`)
- Ambulatory Glucose Profile (AGP) metrics:
  - **Time-in-Range (TIR)**: `%` of readings between 70.0 and 140.0 mg/dL.
  - **Glycemic Variability (CV%)**: `(std_dev / mean) * 100` (target `< 36%` for optimal stability).
  - **7-day Moving Weight Average**: Smooths daily water weight fluctuations.

## 4. Conflict Resolution Hierarchy
1. **Source Precedence**: Direct hardware sensors (Stelo CGM, Wyze Scale) override third-party aggregators and manual logs.
2. **Clinical Supremacy**: Physician lab reports (A1C, lipid panels) override wearable estimates.
3. **Temporal Ordering**: Identical source priorities retain the most recently recorded measurement.

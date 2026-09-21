# Personalized Health Dashboard — Architecture Guide

## 1. System Overview
The Personalized Health Dashboard is a Python-native data ingestion, normalization, and visualization pipeline designed to harmonize heterogeneous health metrics from smart sensors, wearables, smart scales, clinical lab records, and user spreadsheets into a unified chronological data model.

```
+------------------------------------------------------------------------+
|                          Data Source Ingestion                         |
|  +---------------+   +------------------+   +-----------------------+  |
|  | Stelo CGM CSV |   | Wyze Scale Ultra |   | Google / Apple Health |  |
|  +-------+-------+   +--------+---------+   +-----------+-----------+  |
|          |                    |                         |              |
+----------|--------------------|-------------------------|--------------+
           v                    v                         v
+------------------------------------------------------------------------+
|                     Normalization Engine (Pydantic v2)                 |
|  - Parse timestamps to ISO 8601 UTC                                   |
|  - Standardize units: lbs <-> kg, mg/dL <-> mmol/L                    |
|  - Validate biometric physiological floors & ceilings                  |
+-----------------------------------+------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                 Deduplication & Conflict Resolution                    |
|  - Sliding time-window heuristics (2m CGM, 15m Scale)                  |
|  - Deterministic Source Priority Hierarchy:                           |
|    Clinical Lab / PDF (100) > CGM / Scale (80) > Aggregator (60) >     |
|    Manual CSV (40)                                                     |
+-----------------------------------+------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|                       Streamlit Frontend UI                            |
|  - Live metric summary cards (Current Glucose, 24h Average, Scale)     |
|  - Interactive Plotly visualizations (Target glycemic range bands)     |
|  - Audit logging of conflict resolutions and data deduplication        |
+------------------------------------------------------------------------+
```

## 2. Core Data Models (`pipeline/models.py`)

- **`GlucoseReading`**: UTC timestamp, `glucose_mg_dl` (constrained 20.0–600.0), optional trend arrow (`Flat`, `SingleUp`, etc.), and source identifier.
- **`ScaleRecord`**: UTC timestamp, `weight_lbs`, `weight_kg`, body fat percentage, muscle mass, metabolic age.
- **`ActivityRecord`**: Steps, resting/active heart rate, active calories burned, and sleep duration.
- **`ClinicalLabRecord`**: Physician lab values (A1C, lipid profile) extracted with high-precedence metadata.

## 3. Conflict Resolution Hierarchy
When records from multiple sources fall within the same temporal window:
1. **Source Precedence**: Direct continuous biometric hardware sensors (Stelo CGM, Wyze Scale) override third-party aggregators and manual logs.
2. **Clinical Supremacy**: Physician lab reports (e.g., A1C from Teladoc/PDF) override indirect estimates.
3. **Temporal Ordering**: Identical source priorities retain the most recently recorded measurement.

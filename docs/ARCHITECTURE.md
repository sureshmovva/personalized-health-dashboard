# Personalized Health Dashboard — Architecture Guide

## 1. System Overview & The Multi-Layer Storage Architecture
When building a health application that ingests unstructured files (PDFs, clinical notes) alongside structured continuous streams (CSVs, CGM feeds, scale metrics), no single database format handles everything efficiently.

We implement a multi-layer storage architecture with end-to-end traceability:

```
Layer 1: Unstructured Raw Vault (Object Storage)
  (PDFs, CSVs, Notes preserved immutably with SHA-256 hash in data/bronze/)
                            |
                            v
Layer 2: Normalized Document Store (Unified JSON Records)
  (Pydantic v2 / Unified JSON with (user_id, timestamp) composite indices in data/health_store.db)
                            |
                            v
Layer 3: Denormalized Daily Rollups & Unified Query Layer
  (Single-roundtrip dashboard fetch across glucose, weight, and steps without joins)
```

---

## 2. Layer 1: Unstructured Raw Vault (Object Storage)
- **Storage Format**: Local filesystem or S3-compatible Blob Storage (`data/bronze/{source}/YYYY/MM/DD/`).
- **What to store**: Original PDF clinical records, raw CSV files, and unparsed text notes.
- **Why**: Preserves the immutable source-of-truth. If parsing heuristics, OCR models, or AI extraction prompts improve, original files can be re-processed without data loss.
- **Receipts**: Cryptographically verified SHA-256 checksums cataloged in `data/bronze/manifest.json`.

---

## 3. Layer 2: Normalized Document Store (Unified JSON Records)
- **Storage Format**: SQLite with JSON extension / PostgreSQL JSONB in table `unified_health_records`.
- **What to store**: Extracted metrics and events standardized into a single, unified schema using ISO 8601 UTC timestamps.
- **Standardized Unified JSON Schema**:
```json
{
  "user_id": "usr_987654",
  "timestamp": "2026-09-21T16:00:00Z",
  "source_type": "cgm",
  "source_name": "Stelo CGM",
  "metric_category": "blood_glucose",
  "data": {
    "value": 105,
    "unit": "mg/dL",
    "trend_arrow": "flat"
  },
  "metadata": {
    "raw_file_id": "stelo_cgm_a48f91.csv",
    "confidence_score": 0.99
  }
}
```

---

## 4. Key Retrieval Rules for Health Dashboards

1. **Partition/Index by `(user_id, timestamp)`**: Every query on the dashboard filters by `user_id` and date ranges. We maintain composite B-Tree indices:
   - `idx_unified_user_timestamp` on `(user_id, timestamp_utc)`
   - `idx_unified_user_category_timestamp` on `(user_id, metric_category, timestamp_utc)`
   - `idx_unified_raw_file_id` on `(raw_file_id)`

2. **Denormalize for Dashboard Views**: Stored in `unified_daily_rollups`. When loading the dashboard, fetch pre-aggregated daily records so the UI doesn't have to join separate tables for weight, glucose, and steps.

3. **Traceability Link**: Every metric embeds a `raw_file_id` in its `metadata` pointing directly back to the original raw file (PDF/CSV) in Layer 1. Users clicking on a chart metric can view the exact source file and doctor's note it came from.

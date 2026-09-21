# Personalized Health Dashboard — User Guide

## 1. Quick Start & Local Execution

### Prerequisites
- Python 3.10 or newer installed
- Git

### Automated Setup & Launch
```bash
# Clone the repository
git clone https://github.com/sureshmovva/personalized-health-dashboard.git
cd personalized-health-dashboard

# Run the automated setup and launch scripts
./setup.sh
./run.sh
```

### Manual Command Launch
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app/main.py
```
Access the dashboard at `http://localhost:8501`.

---

## 2. The Multi-Layer Storage Flow

### Ingestion Walkthrough:
1. **Upload**: Select your Stelo CGM, Wyze Scale, or Medical PDF report.
2. **Layer 1 Vault**: The file is stored unmodified in `data/bronze/` with a unique `raw_file_id` and SHA-256 fingerprint.
3. **Layer 2 Unified Document Store**: Metrics are parsed into the unified JSON schema (`blood_glucose`, `body_weight`, `hba1c`) and indexed by `(user_id, timestamp)`.
4. **Denormalized Daily Rollups**: A daily summary row is immediately updated so the dashboard loads in a single database query.
5. **Traceability**: Click on any metric to view its origin filename, SHA-256 hash, and extraction confidence score.

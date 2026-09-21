# Personalized Health Dashboard — User Guide

## 1. Quick Start & Local Execution

### Prerequisites
- Python 3.10 or newer installed
- Git

### One-Click Local Setup & Launch
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
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the Streamlit dashboard
streamlit run app/main.py
```
Open your browser at `http://localhost:8501`.

---

## 2. Ingesting Your Health Data (Medallion Pipeline)

### Dexcom / Stelo Continuous Glucose Monitor (CGM)
1. In the Dexcom Clarity or Stelo mobile app, export your glucose log as a CSV.
2. In the sidebar under **1. Stelo CGM CSV**, click **Browse files** and upload.
3. **What happens under the hood:**
   - **Bronze**: Raw CSV is archived with a cryptographic SHA-256 hash in `data/bronze/stelo_cgm/`.
   - **Silver**: Pydantic v2 normalizes timestamps to ISO 8601 UTC, deduplicates points within a 2-minute sliding window, and saves to `data/health_store.db`.
   - **Gold**: Automatically updates your Time-in-Range (TIR) and Glycemic Variability (CV%).

### Wyze Body Scale Ultra
1. In the Wyze app, go to **Scale > Data History > Export CSV**.
2. In the sidebar under **2. Wyze Scale CSV**, upload the file.
3. Stored in Bronze and Silver tiers, updating your 7-day moving weight average and body fat trajectory in the Gold tier.

---

## 3. Medallion Storage Inspector
Inside the Streamlit dashboard, switch between tabs:
- **📈 Continuous Glucose (CGM)**: Visual trajectory with target glycemic zones (70–140 mg/dL).
- **⚖️ Weight & Body Composition**: Scale history with lbs and kg tracking.
- **🏆 Gold Clinical Analytics**: Time-In-Range percentage, Mean Glucose, CV% stability, and moving averages.
- **🏛️ Medallion Storage Inspector**: Direct visibility into raw Bronze file receipts and Silver database counts.

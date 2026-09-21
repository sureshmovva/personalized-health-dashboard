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

## 2. Ingesting Your Health Data

### Dexcom / Stelo Continuous Glucose Monitor (CGM)
1. In the Dexcom Clarity or Stelo mobile app, export your glucose log as a CSV.
2. In the sidebar under **1. Stelo CGM CSV**, click **Browse files** and upload.
3. The dashboard normalizes timestamps to UTC, executes sliding-window deduplication, saves to `data/health_store.db`, and plots the trajectory against clinical glycemic target zones (70–140 mg/dL).

### Wyze Body Scale Ultra
1. In the Wyze app, go to **Scale > Data History > Export CSV**.
2. In the sidebar under **2. Wyze Scale CSV**, upload the file.
3. The pipeline standardizes weights across pounds and kilograms, computes body fat trends, and stores records in the `scale_records` table.

---

## 3. Database Explorer
Click on the **🗄️ Database Explorer (SQLite)** tab inside the dashboard to:
- Review total records saved in `data/health_store.db`.
- Inspect stored rows in `glucose_readings` and `scale_records`.
- Review the audit log of all raw vs. deduplicated records and resolved conflicts.

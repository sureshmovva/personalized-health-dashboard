# Personalized Health Dashboard — User Guide

## 1. Quick Start & Setup

### Prerequisites
- Python 3.10+
- `pip` or modern virtual environment manager (`venv`)

### Installation & Launch
```bash
# 1. Clone repository and navigate to root
git clone <your-repository-url>
cd health-dashboard

# 2. Create and activate a clean virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install core dependencies
pip install -r requirements.txt

# 4. Launch Streamlit interactive dashboard
streamlit run app/main.py
```

## 2. Ingesting Your Health Data

### Dexcom / Stelo Continuous Glucose Monitor (CGM)
1. Open the Dexcom Clarity or Stelo app on your mobile device.
2. Export your history as a CSV file.
3. In the sidebar under **1. Stelo CGM CSV**, click **Browse files** and select your CSV.
4. The system automatically converts timestamps to UTC, removes invalid sensor calibration noise, and updates the **Continuous Glucose** tab.

### Wyze Body Scale Ultra
1. In the Wyze app, navigate to **Scale > Data History > Export CSV**.
2. In the sidebar under **2. Wyze Scale CSV**, upload your file.
3. The pipeline detects whether readings are in pounds or kilograms, standardizes metric and imperial measurements, and charts weight trends and body fat percentage.

### Manual Logs & Custom Spreadsheets
1. Ensure your spreadsheet contains at least one column for date/time (e.g. `timestamp`, `date`) and metric columns like `glucose` or `weight`.
2. Upload under **3. Manual CSV Tracker**.
3. If an automated scale or CGM reading exists within the time window of a manual entry, the automated device data will be prioritized automatically.

## 3. Interpreting Glycemic Bands
- **Green Band (70 - 140 mg/dL)**: Standard target range for non-fasting euglycemia.
- **Red Shaded Zone (> 180 mg/dL)**: Postprandial glucose spike requiring attention.

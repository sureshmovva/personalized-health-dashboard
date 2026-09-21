# Personalized Health Dashboard — User Guide

## 1. Quick Start & Local Execution

### Prerequisites
- Python 3.10 or newer installed
- Git

### Automated Setup & Launch

#### Windows (Command Prompt / Explorer):
Double-click or run from Command Prompt (`cmd`):
```cmd
setup.bat
run.bat
```

#### Windows (PowerShell):
If script execution is restricted on your machine, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup.ps1
.\run.ps1
```

#### macOS / Linux:
```bash
./setup.sh
./run.sh
```

### Manual Command Launch (Windows)

#### Option A: Windows PowerShell
```powershell
# 1. Clone repository
git clone https://github.com/sureshmovva/personalized-health-dashboard.git
cd personalized-health-dashboard

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Launch Streamlit
streamlit run app/main.py
```

#### Option B: Windows Command Prompt (CMD)
```cmd
REM 1. Clone repository
git clone https://github.com/sureshmovva/personalized-health-dashboard.git
cd personalized-health-dashboard

REM 2. Create virtual environment
python -m venv .venv

REM 3. Activate virtual environment
.venv\Scripts\activate.bat

REM 4. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

REM 5. Launch Streamlit
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

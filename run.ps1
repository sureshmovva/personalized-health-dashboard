# run.ps1 - Windows PowerShell Launch Script
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Launching Personalized Health Dashboard (Streamlit)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not detected. Running setup.ps1 first..." -ForegroundColor Yellow
    & .\setup.ps1
}

& .\.venv\Scripts\Activate.ps1
Write-Host "Starting Streamlit dashboard on http://localhost:8501..." -ForegroundColor Green
streamlit run app/main.py

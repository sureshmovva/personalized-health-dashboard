# setup.ps1 - Windows PowerShell Setup Script
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "Setting up Personalized Health Dashboard on Windows" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# Check Python
try {
    $pyVer = python --version
    Write-Host "Found: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python was not found in PATH." -ForegroundColor Red
    Write-Host "Please install Python 3.10+ and ensure 'Add Python to PATH' is checked." -ForegroundColor Yellow
    exit 1
}

# Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment in .venv..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate & install requirements
Write-Host "Activating virtual environment & installing dependencies..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "`nSetup successfully finished! Launch the app using: .\run.ps1" -ForegroundColor Green

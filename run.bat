@echo off
echo ===================================================
echo Launching Personalized Health Dashboard (Streamlit)
echo ===================================================

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found. Running setup.bat first...
    call setup.bat
)

call .venv\Scripts\activate.bat

REM Ensure project root is in PYTHONPATH
set PYTHONPATH=%CD%;%PYTHONPATH%

echo Starting Streamlit app on http://localhost:8501...
streamlit run app/main.py

pause

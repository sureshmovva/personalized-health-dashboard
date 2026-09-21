@echo off
echo ===================================================
echo Setting up Personalized Health Dashboard on Windows
echo ===================================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not found in your PATH.
    echo Please install Python 3.10+ from https://www.python.org/ or the Microsoft Store.
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Create virtual environment if it does not exist
if not exist ".venv" (
    echo Creating virtual environment in .venv...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate virtual environment and install requirements
echo Activating virtual environment and installing dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ===================================================
echo Setup complete! To run the dashboard, execute:
echo   run.bat
echo ===================================================
pause

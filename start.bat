@echo off
echo ============================================
echo   Adaptive Engine - Windows Quick Start
echo ============================================
echo.

:: Check if venv exists
if not exist "venv" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    echo Done!
) else (
    echo [1/3] Virtual environment already exists. Skipping.
)

:: Activate
echo [2/3] Activating virtual environment...
call venv\Scripts\activate

:: Check if packages installed
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [3/3] Installing packages from requirements.txt ...
    echo This may take 5-10 minutes on first run. Please wait...
    pip install -r requirements.txt
) else (
    echo [3/3] Packages already installed. Skipping.
)

echo.
echo ============================================
echo   Starting server at http://localhost:8000
echo   Press Ctrl+C to stop
echo ============================================
echo.
uvicorn app.main:app --reload --port 8000

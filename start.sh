#!/bin/bash
echo "============================================"
echo "  Adaptive Engine - Mac/Linux Quick Start"
echo "============================================"
echo ""

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv venv
    echo "Done!"
else
    echo "[1/3] Virtual environment already exists. Skipping."
fi

# Activate
echo "[2/3] Activating virtual environment..."
source venv/bin/activate

# Install if needed
if ! pip show fastapi > /dev/null 2>&1; then
    echo "[3/3] Installing packages from requirements.txt..."
    echo "This may take 5-10 minutes on first run. Please wait..."
    pip install -r requirements.txt
else
    echo "[3/3] Packages already installed. Skipping."
fi

echo ""
echo "============================================"
echo "  Starting server at http://localhost:8000"
echo "  Press Ctrl+C to stop"
echo "============================================"
echo ""
uvicorn app.main:app --reload --port 8000

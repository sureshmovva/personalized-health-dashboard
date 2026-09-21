#!/usr/bin/env bash
set -e

echo "=== Setting up Personalized Health Dashboard ==="

# Check Python version
python3 -c 'import sys; assert sys.version_info >= (3, 10), "Python 3.10 or higher is required."'

# Create virtual environment if it does not exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment in .venv..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip and install dependencies
echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Setup complete! ==="
echo "To run the Streamlit dashboard, execute: ./run.sh"

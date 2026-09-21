#!/usr/bin/env bash
set -e

if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "Starting Streamlit Health Dashboard..."
streamlit run app/main.py

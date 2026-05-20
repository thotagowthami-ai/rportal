#!/bin/bash

# Navigate to backend directory
cd "$(dirname "$0")"

# Set PYTHONPATH
export PYTHONPATH="$PWD"

# Activate virtual environment and start uvicorn
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

#!/bin/bash

set -e

echo "Stopping all processes..."

# Stop streamlit processes
echo "Stopping Streamlit processes..."
pkill -f "streamlit run" || true

# Stop any Python processes related to this project
echo "Stopping Python processes..."
pkill -f "src/frontend/ui.py" || true
pkill -f "src/backend/api.py" || true

echo "All processes stopped."

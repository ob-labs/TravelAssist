#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Starting Travel Assist application..."

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Error: .env file not found. Please run 'make init' first."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please run 'make init' first."
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

# Start the streamlit application
echo "Launching Streamlit UI..."
uv run streamlit run --server.runOnSave false src/frontend/ui.py

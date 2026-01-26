#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Running tests..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please run 'make init' first."
    exit 1
fi

# Change to project root
cd "$PROJECT_ROOT"

# Run pytest with coverage
echo "Executing pytest..."
uv run pytest tests/ -v --tb=short

echo ""
echo "Tests completed!"

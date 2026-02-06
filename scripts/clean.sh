#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Starting cleanup..."

cd "$PROJECT_ROOT"

# Remove Python cache files
echo "Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
find . -type f -name "*$py.class" -delete 2>/dev/null || true

# Remove hidden .*.py files in src and tests directories
echo "Removing hidden .*.py files..."
find src tests -type f -name ".*.py" -delete 2>/dev/null || true

# Remove .venv directory
if [ -d "$PROJECT_ROOT/.venv" ]; then
    echo "Removing .venv directory..."
    rm -rf "$PROJECT_ROOT/.venv"
fi

# Remove build directories
echo "Removing build directories..."
rm -rf "$PROJECT_ROOT/dist" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/build" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/.uv" 2>/dev/null || true

# Remove egg-info directories
echo "Removing egg-info directories..."
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Remove compiled files
echo "Removing compiled files..."
find . -type f -name "*.so" -delete 2>/dev/null || true

# Remove test and coverage files
echo "Removing test and coverage files..."
rm -rf "$PROJECT_ROOT/.pytest_cache" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/.mypy_cache" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/.ruff_cache" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/.tox" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/htmlcov" 2>/dev/null || true
rm -f "$PROJECT_ROOT/.coverage"* 2>/dev/null || true
rm -f "$PROJECT_ROOT/coverage.xml" 2>/dev/null || true
rm -f "$PROJECT_ROOT"/*.cover 2>/dev/null || true

# Remove log files
if [ -d "$PROJECT_ROOT/logs" ]; then
    echo "Removing log files..."
    find "$PROJECT_ROOT/logs" -type f ! -name '.gitkeep' -delete 2>/dev/null || true
fi

# Remove database files
echo "Removing database files..."
find . -type f -name "*.db" -delete 2>/dev/null || true

# Remove wheel and tar files
echo "Removing wheel and tar files..."
find . -type f -name "*.whl" -delete 2>/dev/null || true
find . -type f -name "*.tar.gz" -delete 2>/dev/null || true

echo "Cleanup completed!"

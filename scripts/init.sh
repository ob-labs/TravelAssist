#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Starting project initialization..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Check Python version
echo "Checking Python version..."
REQUIRED_PYTHON_MAJOR=3
REQUIRED_PYTHON_MINOR=10

# Get current Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    echo "Current Python version: $PYTHON_VERSION"
else
    PYTHON_MAJOR=0
    PYTHON_MINOR=0
    echo "Python 3 is not installed."
fi

# Check if Python version is less than 3.10
if [ "$PYTHON_MAJOR" -lt "$REQUIRED_PYTHON_MAJOR" ] || \
   { [ "$PYTHON_MAJOR" -eq "$REQUIRED_PYTHON_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$REQUIRED_PYTHON_MINOR" ]; }; then
    echo "Python version is below 3.10. Installing Python 3.12 using uv..."
    
    # Install Python 3.12 using uv
    uv python install 3.12
    
    # Create virtual environment with Python 3.12
    echo "Creating virtual environment with Python 3.12..."
    cd "$PROJECT_ROOT"
    uv venv --python 3.12
    
    # Activate the virtual environment
    if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
        echo "Virtual environment activated with Python 3.12"
    else
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
    
    # Verify Python version in venv
    VENV_PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo "Virtual environment Python version: $VENV_PYTHON_VERSION"
else
    echo "Python version check passed: $PYTHON_VERSION"
fi

# Install dependencies
echo "Installing dependencies with uv..."
cd "$PROJECT_ROOT"
uv sync

# Check if .env file exists, if not copy from .env.example
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        echo "Creating .env file from .env.example..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        echo "Please edit .env file with your configuration before running the application."
    else
        echo "Warning: .env.example file not found. Please create .env file manually."
    fi
else
    echo ".env file already exists."
fi

# Create required directories if they don't exist
echo "Creating required directories..."
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/citydata"

echo ""
echo "Initialization completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your database and API configurations"
echo "2. Download dataset from https://www.kaggle.com/datasets/audreyhengruizhang/china-city-attraction-details"
echo "3. Place dataset files in the 'citydata' directory"
echo "4. Run 'make start' to launch the application"

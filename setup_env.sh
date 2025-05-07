#!/bin/bash
# Set up Python virtual environment with uv

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install uv if not already available
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Install project dependencies
echo "Installing dependencies with uv..."
uv pip install -r requirements.txt

# Create necessary directories
mkdir -p data/processed
mkdir -p data/reports

echo ""
echo "Setup complete! You can activate the virtual environment with:"
echo "source .venv/bin/activate"
echo ""
echo "Then run the analysis with:"
echo "python code/main.py" 
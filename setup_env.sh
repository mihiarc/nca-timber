#!/bin/bash
# Timber Asset Analysis Environment Setup Script
# Uses uv for package management as specified in the requirements

# Check if uv is installed
if ! command -v uv &> /dev/null
then
    echo "uv could not be found, installing it now..."
    if command -v pip &> /dev/null
    then
        pip install uv
    else
        echo "pip could not be found. Please install Python and pip first."
        exit 1
    fi
fi

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
else
    echo "Virtual environment already exists."
fi

# Install dependencies using uv
echo "Installing dependencies using uv..."
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
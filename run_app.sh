#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    pip install uv
fi

# Install dependencies with uv
uv pip install -r requirements.txt

# Run the Streamlit application
streamlit run app/app.py 
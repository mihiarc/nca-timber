#!/bin/bash

# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Run the Streamlit app
streamlit run app/app.py 
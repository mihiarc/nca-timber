# NCA Timber Data Explorer

A Streamlit application for visualizing and exploring timber data in the Southern United States.

## Features

- **Overview**: Get a quick summary of all available datasets
- **Price Analysis**: Explore timber prices across different states, products, and time periods
- **Species Analysis**: Analyze species distribution and compare species across states
- **Biomass Explorer**: Investigate merchantable and pre-merchantable biomass data by county and species

## Data Files

The application uses the following data files:

- `prices.csv`: Timber prices by state, area, and time period
- `south_species.csv`: Species information across southern states
- `south_bio_merch.csv`: Merchantable biomass data
- `south_bio_premerch.csv`: Pre-merchantable biomass data

## Setup

1. Create a virtual environment using uv:

```bash
uv venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
uv pip install -r requirements.txt
```

## Running the App

```bash
streamlit run app/app.py
```

The app will open in your default web browser at http://localhost:8501.

## Screenshots

- Overview page: Basic statistics and data preview
- Price Analysis: Interactive charts showing timber price trends
- Species Analysis: Species distribution and comparison visualizations
- Biomass Explorer: County-level biomass data exploration

## License

This project is licensed under the MIT License. 
# Timber Asset Analysis Project

This project analyzes timber data from two regions: South and Great Lakes. It processes raw data and generates standardized reports and visualizations.

## Project Structure

```
timber-assets/
├── code/
│   ├── main.py              # Orchestrates the workflow
│   ├── utils.py             # Shared utilities and constants
│   ├── south_assets.py      # South region data processing
│   ├── greatlakes_assets.py # Great Lakes region data processing
│   ├── table_reporting.py   # Report and visualization generation
│   └── archive/             # Deprecated code
├── data/
│   ├── input/               # Raw input data files
│   ├── processed/           # Output of data processing
│   └── reports/             # Generated reports
├── notebooks/               # Jupyter notebooks for exploration
└── docs/                    # Documentation
```

## Design Principles

This codebase follows the Single Responsibility Principle (SRP):

- Each module has a clear, singular purpose
- Region-specific logic is isolated in dedicated modules
- Data processing is separated from reporting
- Coordination happens in the main.py script

## Modules

### main.py
Orchestrates the entire workflow, coordinating between data processing and reporting modules.

### utils.py
Contains shared utilities, constants, data loading/formatting functions, and species lookup dictionaries.

### south_assets.py
Processes Southern region timber data.

### greatlakes_assets.py
Processes Great Lakes region timber data.

### table_reporting.py
Generates tables, charts, and reports from processed data, independent of region-specific logic.

## Getting Started

### Setup Environment

```bash
# Run the setup script to create a virtual environment and install dependencies
./setup_env.sh
```

### Run the Analysis

```bash
# Activate the virtual environment
source .venv/bin/activate

# Run the full workflow
python code/main.py

# Process specific regions
python code/main.py --regions south gl

# Only process data without generating reports
python code/main.py --process-only

# Only generate reports from previously processed data
python code/main.py --report-only
```

## Data Sources

The project uses timber data from two regions:
- South: Includes merchantable and pre-merchantable timber data
- Great Lakes: Regional timber asset data

## Adding New Regions

To add support for a new region:

1. Create a new module following the pattern of existing regional modules
2. Implement the region-specific processing logic
3. Update main.py to include the new region in processing
4. Update table_reporting.py to support the new region's data structure
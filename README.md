# Timber Asset Analysis Project

This project analyzes timber data from two regions: South and Great Lakes. It processes raw data and generates standardized reports and visualizations.

## Project Structure

```
timber-assets/
├── code/
│   ├── main.py                # Orchestrates the workflow
│   ├── geo_crosswalks.py      # Geographic data utilities and crosswalks
│   ├── species_crosswalks.py  # Species data utilities and crosswalks
│   ├── south_assets.py        # South region data processing
│   ├── greatlakes_assets.py   # Great Lakes region data processing
│   ├── table_reporting.py     # Report and visualization generation
│   ├── config.py              # Centralized configuration module
│   └── config_loader.py       # YAML configuration loader utility
├── tests/                     # Unit tests
│   └── test_species_crosswalks.py  # Tests for species_crosswalks module
├── data/
│   ├── input/                 # Raw input data files
│   ├── processed/             # Output of data processing
│   └── reports/               # Generated reports
├── archive/
│   └── crosswalks/            # Archived crosswalk data
├── docs/                      # Documentation
├── config.yaml                # YAML configuration file
└── setup_env.sh               # Environment setup script with uv
```

## Design Principles

This codebase follows the Single Responsibility Principle (SRP):

- Each module has a clear, singular purpose
- Region-specific logic is isolated in dedicated modules
- Data processing is separated from reporting
- Crosswalks are separated by domain (geography vs. species)
- Coordination happens in the main.py script
- Configuration is centralized in separate modules
- Type hints improve code readability and maintainability
- Unit tests ensure code quality and prevent regression
- Self-contained data approach with in-memory crosswalks and mock data generation

## Modules

### main.py
Orchestrates the entire workflow, coordinating between data processing and reporting modules.

### geo_crosswalks.py
Contains geographic data structures, FIPS code utilities, state/county mappings, and geographic reference crosswalks.

### species_crosswalks.py
Contains species data structures, timber species codes, conversion factors for volume and value, and species reference crosswalks.

### south_assets.py
Processes Southern region timber data.

### greatlakes_assets.py
Processes Great Lakes region timber data.

### table_reporting.py
Generates tables, charts, and reports from processed data, independent of region-specific logic.

### config.py
Centralizes configuration settings and constants for the project in a Python module.

### config_loader.py
Loads configuration from YAML files, providing a flexible way to manage project settings.

## Getting Started

### Setup Environment

```bash
# Run the setup script to create a virtual environment and install dependencies using uv
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

### Run the Tests

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_species_crosswalks.py

# Run tests with verbose output
pytest -v
```

## Configuration

The project uses both Python-based and YAML-based configuration:

### Python Configuration
The `code/config.py` module centralizes constants and settings for direct use in Python code.

### YAML Configuration
The `config.yaml` file provides a more user-friendly way to manage settings:

```yaml
# Example config section
regions:
  south_states: ['AL', 'AR', 'FL', 'GA', 'LA', 'MS', 'NC', 'SC', 'TN', 'TX', 'VA']
  great_lakes_states: ['MI', 'MN', 'WI']
```

This can be loaded using the `config_loader.py` module.

## Package Management

The project uses `uv`, a fast Python package installer and resolver:

- Faster dependency resolution than pip
- Compatible with requirements.txt
- Modern features like lockfiles for reproducible environments

## Data Sources

The project uses timber data from two regions:
- South: Includes merchantable and pre-merchantable timber data
- Great Lakes: Regional timber asset data

### Data Handling

The project is designed to be self-contained and can operate in two modes:

1. **With Real Data**: When the CSV and Excel data files are present, they are loaded and processed normally.

2. **Self-Contained Mode**: When data files are not present, the system automatically:
   - Uses hardcoded price region mappings instead of loading from CSV files
   - Generates mock data for prices, biomass, and other inputs
   - Creates placeholder processed data for reporting
   
This approach makes the codebase more portable and easier to test, as it can run without needing to download large data files.

### Crosswalks

Crosswalk data is managed in two ways:

1. **In-memory mappings**: Essential mappings like price regions, species dictionaries, and state FIPS codes are defined directly in code.

2. **Optional external files**: More detailed or frequently changing mappings can be loaded from external files when available.

Crosswalk files provide mappings between different data sources and formats:

**Geographic Crosswalks:**
- georef.csv: Geographic reference data
- crosswalk_micromarket_county.csv: Maps micromarkets to counties
- crosswalk_priceRegions.csv: Maps price regions to geographic areas
- crosswalk_tmsCounties.csv: Maps TMS data to counties

**Species Crosswalks:**
- speciesDict.csv: Maps species codes to names
- speciesGroupDict.csv: Maps species group codes to group names
- crosswalk_southSpecies.csv: South-specific species classification

## Adding New Regions

To add support for a new region:

1. Create a new module following the pattern of existing regional modules
2. Implement the region-specific processing logic
3. Update main.py to include the new region in processing
4. Update table_reporting.py to support the new region's data structure
5. Add unit tests for the new functionality
6. Update configuration in both config.py and config.yaml
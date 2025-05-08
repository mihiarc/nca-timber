#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration Module

This module centralizes configuration settings and constants for the timber assets project.
It simplifies maintenance by keeping configuration values in one place.
"""

import os
from pathlib import Path

# Path constants
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
INPUT_DIR = DATA_DIR / 'input'
CROSSWALKS_DIR = DATA_DIR / 'crosswalks'
PROCESSED_DIR = DATA_DIR / 'processed'
REPORTS_DIR = DATA_DIR / 'reports'

# Ensure directories exist
for directory in [DATA_DIR, INPUT_DIR, CROSSWALKS_DIR, PROCESSED_DIR, REPORTS_DIR]:
    directory.mkdir(exist_ok=True)

# Region definitions
SOUTH_STATES = ['AL', 'AR', 'FL', 'GA', 'LA', 'MS', 'NC', 'SC', 'TN', 'TX', 'VA']
GREAT_LAKES_STATES = ['MI', 'MN', 'WI']

# State FIPS code mapping
STATE_FIPS = {
    'AL': '01', 'AR': '05', 'FL': '12', 'GA': '13', 'LA': '22', 
    'MS': '28', 'NC': '37', 'SC': '45', 'TN': '47', 'TX': '48', 'VA': '51',
    'MI': '26', 'MN': '27', 'WI': '55'
}

# Unit conversion factors
CUBIC_FT_TO_MEGATONNE = 0.025713 / 1e6  # Convert cubic feet to megatonnes
DOLLARS_TO_BILLIONS = 1e-9  # Convert dollars to billions
TONS_TO_CUBIC_FEET = 40.0  # 1 ton = 40 cubic feet (for timber)

# Financial parameters
DISCOUNT_RATE = 0.05  # Discount rate for financial calculations
MERCHANTABLE_AGE = 15  # Age at which trees become merchantable

# Product types
PRODUCT_TYPES = {
    'saw': 'Sawtimber',
    'plp': 'Pulpwood',
    'pre': 'Pre-merchantable'
}

# File paths
PRICE_REGIONS_FILE = 'priceRegions.csv'
SOUTH_PRICES_FILE = 'Timber Prices/prices_south.csv'
GL_PRICES_FILE = 'Timber Prices/TMN/TMN_Price_Series_June2023.xlsx'
SOUTH_PREMERCH_FILE = 'Premerch Bio South by spp 08-28-2024.xlsx'
GL_BIOMASS_FILE = 'Merch Bio GLakes by spp 08-28-2024.xlsx' 
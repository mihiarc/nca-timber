#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Geography Crosswalks Module

This module contains geographic data structures, crosswalks, and utilities
for the timber assets analysis. It handles state/county mappings, FIPS codes,
and other geographic reference data.
"""

import pandas as pd
import os
from pathlib import Path

# Path constants - kept here to avoid circular imports
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
INPUT_DIR = DATA_DIR / 'input'
CROSSWALKS_DIR = DATA_DIR / 'crosswalks'
PROCESSED_DIR = DATA_DIR / 'processed'
REPORTS_DIR = DATA_DIR / 'reports'

# Region definitions
SOUTH_STATES = ['AL', 'AR', 'FL', 'GA', 'LA', 'MS', 'NC', 'SC', 'TN', 'TX', 'VA']
GREAT_LAKES_STATES = ['MI', 'MN', 'WI']

# State FIPS code mapping
STATE_FIPS = {
    'AL': '01', 'AR': '05', 'FL': '12', 'GA': '13', 'LA': '22', 
    'MS': '28', 'NC': '37', 'SC': '45', 'TN': '47', 'TX': '48', 'VA': '51',
    'MI': '26', 'MN': '27', 'WI': '55'
}

def format_fips(df, state_col='statecd', county_col='countycd', new_col='fips'):
    """Format state and county codes as FIPS codes.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing state and county codes
    state_col : str
        Column name containing state codes
    county_col : str
        Column name containing county codes
    new_col : str
        Name for the new FIPS column
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with properly formatted FIPS codes added
    """
    df_copy = df.copy()
    
    # Format state code (2 digits with leading zeros)
    df_copy[state_col] = df_copy[state_col].astype(str).str.zfill(2)
    
    # Format county code (3 digits with leading zeros)
    if county_col in df_copy.columns:
        df_copy[county_col] = df_copy[county_col].astype(str).str.zfill(3)
        df_copy[new_col] = df_copy[state_col] + df_copy[county_col]
    else:
        df_copy[new_col] = df_copy[state_col]
        
    return df_copy

def format_unit_code(df, unit_col='unitcd'):
    """Format unit codes with leading zeros.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing unit codes
    unit_col : str
        Column name containing unit codes
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with properly formatted unit codes
    """
    df_copy = df.copy()
    
    if unit_col in df_copy.columns:
        df_copy[unit_col] = df_copy[unit_col].fillna(0).astype(int)
        df_copy[unit_col] = df_copy[unit_col].astype(str).str.zfill(2)
        
    return df_copy

def get_state_abbr_from_fips(fips_code):
    """Get state abbreviation from FIPS code.
    
    Parameters:
    -----------
    fips_code : str
        FIPS code (first 2 digits are state code)
        
    Returns:
    --------
    str
        State abbreviation
    """
    state_code = str(fips_code)[:2]
    return {v: k for k, v in STATE_FIPS.items()}.get(state_code)

def load_georef():
    """Load geographic reference data"""
    return pd.read_csv(CROSSWALKS_DIR / 'georef.csv')

def load_crosswalk_micromarket_county():
    """Load micromarket to county mapping"""
    return pd.read_csv(CROSSWALKS_DIR / 'crosswalk_micromarket_county.csv')

def load_crosswalk_price_regions():
    """Load price region mappings"""
    return pd.read_csv(CROSSWALKS_DIR / 'crosswalk_priceRegions.csv')

def load_crosswalk_tms_counties():
    """Load TMS counties mapping"""
    return pd.read_csv(CROSSWALKS_DIR / 'crosswalk_tmsCounties.csv') 
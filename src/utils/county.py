#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
County and FIPS Code Utilities

This module contains functions related to county-level data processing,
including FIPS code formatting and validation.
"""

import pandas as pd
# We will import STATE_FIPS from config later if needed by format_fips
# Currently, format_fips does not directly use STATE_FIPS

def format_fips(df, state_col='statecd', county_col='countycd', new_col='fips'):
    """Format state and county codes as FIPS codes.
    
    Adds a new column with the combined FIPS code. Assumes state and county 
    code columns contain values that can be cast to string.
    Handles cases where county code might be missing (creates state FIPS).

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing state and county codes
    state_col : str, default 'statecd'
        Column name containing state codes
    county_col : str, default 'countycd'
        Column name containing county codes
    new_col : str, default 'fips'
        Name for the new FIPS column
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with properly formatted FIPS codes added
    """
    df_copy = df.copy()
    
    # Ensure state column exists
    if state_col not in df_copy.columns:
        raise ValueError(f"State column '{state_col}' not found in DataFrame.")

    # Format state code (2 digits with leading zeros)
    df_copy[state_col] = df_copy[state_col].astype(str).str.zfill(2)
    
    # Format county code (3 digits with leading zeros) if column exists
    if county_col in df_copy.columns:
        # Ensure county column is also string before zfill
        df_copy[county_col] = df_copy[county_col].astype(str).str.zfill(3)
        df_copy[new_col] = df_copy[state_col] + df_copy[county_col]
    else:
        # If county column doesn't exist, FIPS is just the state code
        print(f"Warning: County column '{county_col}' not found. Creating state-level FIPS.")
        df_copy[new_col] = df_copy[state_col]
        
    return df_copy 
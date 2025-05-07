#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Species Crosswalks Module

This module contains tree species data structures, crosswalks, and utilities
for the timber assets analysis. It handles species codes, groups, and
conversion factors for biomass and value calculations.
"""

import pandas as pd
import os
from pathlib import Path
from typing import Dict, Optional, Union

# Path constants - kept here to avoid circular imports
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
INPUT_DIR = DATA_DIR / 'input'
CROSSWALKS_DIR = DATA_DIR / 'crosswalks'

# Unit conversion factors
CUBIC_FT_TO_MEGATONNE = 0.025713 / 1e6  # Convert cubic feet to megatonnes
DOLLARS_TO_BILLIONS = 1e-9  # Convert dollars to billions
TONS_TO_CUBIC_FEET = 40.0  # 1 ton = 40 cubic feet (for timber)

# Product types
PRODUCT_TYPES = {
    'saw': 'Sawtimber',
    'plp': 'Pulpwood',
    'pre': 'Pre-merchantable'
}

# Species dictionary
speciesDict = {
    12: 'balsim fir',
    68: 'eastern redcedar',
    71: 'tamarack',
    91: 'Norway spruce',
    94: 'white spruce',
    95: 'black spruce',
    105: 'jack pine',
    110: 'shortleaf',
    111: 'slash',
    121: 'longleaf',
    125: 'red pine',
    129: 'eastern white pine',
    130: 'Scotch pine',
    131: 'loblolly',
    132: 'Virginia pine',
    221: 'baldcypress',
    313: 'boxelder',
    316: 'red maple',
    318: 'sugar maple',
    371: 'yellow birch',
    375: 'paper birch',
    402: 'butternut hickory',
    403: 'pignut hickory',
    404: 'pecan',
    405: 'shelbark hickory',
    407: 'shagbark hickory',
    409: 'mockernut hickory',
    462: 'hackberry',
    531: 'American beech',
    541: 'white ash',
    543: 'black ash',
    544: 'green ash',
    546: 'blue ash',
    601: 'butternut',
    602: 'black walnut',
    611: 'sweetgum',
    621: 'yellow-poplar',
    651: 'cucumber tree',
    652: 'southern magnolia',
    653: 'sweetbay',
    742: 'eastern cottonwood',
    743: 'bigtooth aspen',
    746: 'quaking aspen',
    762: 'black cherry',
    802: 'white oak',
    809: 'northern pin oak',
    812: 'southern red oak',
    822: 'overcup oak',
    830: 'pin oak',
    833: 'northern red oak',
    951: 'American basswood',
    972: 'American elm',
}

def get_species_name(spcd):
    """Return the species name for a given code."""
    return speciesDict.get(spcd, None)

# Species group dictionary
speciesGroupDict = {
    1: 'Longleaf and slash pines',
    2: 'Lobolly and shortleaf pines',
    3: 'Other yellow pines',
    4: 'Eastern white and red pines',
    5: 'Jack pine',
    6: 'Spruce and balsam fir',
    7: 'Eastern hemlock',
    8: 'Cypress',
    9: 'Other eastern softwoods',
    23: 'Woodland softwoods',
    25: 'Select white oaks',
    26: 'Select red oaks',
    27: 'Other white oaks',
    28: 'Other red oaks',
    29: 'Hickory',
    30: 'Yellow birch',
    31: 'Hard maple',
    32: 'Soft maple',
    33: 'Beech',
    34: 'Sweetgum',
    35: 'Tupelo and blackgum',
    36: 'Ash',
    37: 'Cottonwood and aspen',
    38: 'Basswood',
    39: 'Yellow-poplar',
    40: 'Black walnut',
    41: 'Other eastern soft hardwoods',
    42: 'Other eastern hard hardwoods',
    43: 'Eastern noncommericial hardwoods',
}

def get_species_group_name(spgrpcd):
    """Return the species group name for a given code."""
    return speciesGroupDict.get(spgrpcd, None)

def categorize_species_by_region(spcd):
    """Determine which region(s) a species belongs to.
    
    Parameters:
    -----------
    spcd : int
        Species code
        
    Returns:
    --------
    str
        'South', 'Great Lakes', or 'Both' based on species distribution
    """
    # This is a simplified version and should be expanded based on actual data
    south_species = [110, 111, 121, 131, 132, 221, 611, 621, 651, 652, 653, 812, 822, 830, 832]
    gl_species = [12, 71, 91, 94, 95, 105, 125, 126, 130, 313, 316, 371, 375, 462, 531, 543, 742, 743, 746, 809, 833, 951, 972, 977]
    
    if spcd in south_species and spcd in gl_species:
        return 'Both'
    elif spcd in south_species:
        return 'South'
    elif spcd in gl_species:
        return 'Great Lakes'
    else:
        return 'Unknown'

def convert_to_billions(df: pd.DataFrame, value_col: str = 'value') -> pd.DataFrame:
    """Convert dollar values to billions.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing value column
    value_col : str
        Column name containing values to convert
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with converted values
    """
    df_copy = df.copy()
    
    if value_col in df_copy.columns:
        df_copy[value_col] = df_copy[value_col] * DOLLARS_TO_BILLIONS
        
    return df_copy

def convert_to_megatonnes(df, volume_col='volume'):
    """Convert cubic feet to megatonnes.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing volume column
    volume_col : str
        Column name containing volumes to convert
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with converted volumes
    """
    df_copy = df.copy()
    
    if volume_col in df_copy.columns:
        df_copy[volume_col] = df_copy[volume_col] * CUBIC_FT_TO_MEGATONNE
        
    return df_copy

def convert_price_ton_to_cubic_feet(df, price_col='price', new_col='cuftPrice'):
    """Convert price per ton to price per cubic foot.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing price column
    price_col : str
        Column name containing prices to convert
    new_col : str
        Name for the new column with converted prices
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with converted prices
    """
    df_copy = df.copy()
    
    if price_col in df_copy.columns:
        df_copy[new_col] = df_copy[price_col] / TONS_TO_CUBIC_FEET
        
    return df_copy

def load_species_dict():
    """Load species dictionary mapping"""
    return pd.read_csv(CROSSWALKS_DIR / 'speciesDict.csv')

def load_species_group_dict():
    """Load species group dictionary mapping"""
    return pd.read_csv(CROSSWALKS_DIR / 'speciesGroupDict.csv')

def load_crosswalk_south_species():
    """Load Southern species crosswalk"""
    return pd.read_csv(CROSSWALKS_DIR / 'crosswalk_southSpecies.csv')

def load_southern_harvested_species():
    """Load Southern harvested species data"""
    return pd.read_excel(INPUT_DIR / 'southern_harvested_tree_species.csv')

def load_glakes_harvested_species():
    """Load Great Lakes harvested species data"""
    return pd.read_excel(INPUT_DIR / 'GLakes harvested tree species V2.xlsx')

def standardize_column_names(df):
    """Convert all column names to lowercase.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with column names to standardize
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with standardized column names
    """
    df_copy = df.copy()
    df_copy.columns = df_copy.columns.str.lower()
    return df_copy

# ===============================
# Data Loading Utilities
# ===============================

def load_csv(file_path, **kwargs):
    """Load CSV data with error handling.
    
    Parameters:
    -----------
    file_path : str
        Path to the CSV file
    **kwargs : 
        Additional arguments to pass to pd.read_csv()
        
    Returns:
    --------
    pandas.DataFrame
    """
    try:
        full_path = DATA_DIR / file_path if not os.path.isabs(file_path) else file_path
        return pd.read_csv(full_path, **kwargs)
    except FileNotFoundError:
        print(f"Error: File not found at {full_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return pd.DataFrame()

def load_excel(file_path, sheet_name=0, **kwargs):
    """Load Excel data with error handling.
    
    Parameters:
    -----------
    file_path : str
        Path to the Excel file
    sheet_name : str or int
        Sheet name or index
    **kwargs : 
        Additional arguments to pass to pd.read_excel()
        
    Returns:
    --------
    pandas.DataFrame
    """
    try:
        full_path = DATA_DIR / file_path if not os.path.isabs(file_path) else file_path
        return pd.read_excel(full_path, sheet_name=sheet_name, **kwargs)
    except FileNotFoundError:
        print(f"Error: File not found at {full_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return pd.DataFrame() 
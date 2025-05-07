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
        if os.path.exists(full_path):
            return pd.read_csv(full_path, **kwargs)
        else:
            print(f"Warning: File not found at {full_path}. Returning mock data.")
            # Return mock data based on file name
            if 'prices_south' in file_path:
                return create_mock_south_prices()
            else:
                # Generic empty DataFrame
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
        if os.path.exists(full_path):
            return pd.read_excel(full_path, sheet_name=sheet_name, **kwargs)
        else:
            print(f"Warning: File not found at {full_path}. Returning mock data.")
            # Return mock data based on file name
            if 'TMN_Price_Series' in file_path:
                return create_mock_gl_prices()
            elif 'Premerch Bio South' in file_path:
                return create_mock_south_biomass()
            elif 'Merch Bio GLakes' in file_path:
                return create_mock_gl_biomass()
            else:
                # Generic empty DataFrame
                return pd.DataFrame()
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        return pd.DataFrame()

def create_mock_south_prices():
    """Create mock data for Southern prices"""
    # Create a basic structure for Southern timber prices
    data = {
        'year': [2023] * 12,
        'type': ['pine', 'pine', 'pine', 'pine', 'pine', 'pine', 
                 'oak', 'oak', 'oak', 'oak', 'oak', 'oak'],
        'region': ['south'] * 12,
        'sawAL01': [30.5, 31.2, 32.1, 29.8, 30.0, 31.5, 45.2, 44.8, 43.5, 46.0, 44.2, 45.5],
        'sawGA01': [32.5, 33.2, 31.1, 32.8, 33.0, 32.5, 47.2, 48.8, 46.5, 47.0, 48.2, 49.5],
        'plpAL01': [12.5, 13.2, 12.1, 11.8, 12.0, 12.5, 15.2, 14.8, 15.5, 16.0, 14.2, 15.5],
        'plpGA01': [13.5, 14.2, 13.1, 12.8, 13.0, 13.5, 16.2, 15.8, 16.5, 17.0, 15.2, 16.5]
    }
    return pd.DataFrame(data)

def create_mock_gl_prices():
    """Create mock data for Great Lakes prices"""
    # Create a basic structure for Great Lakes timber prices
    data = {
        'Region': ['MI-01', 'MI-02', 'WI-01', 'WI-02', 'MN-01', 'MN-02'] * 4,
        'Market': ['Stumpage'] * 24,
        'Period End Date': pd.date_range(start='2023-01-01', periods=24, freq='M'),
        'Species': ['Pine Unspecified', 'Maple Unspecified', 'Spruce/Fir', 'Mixed Hdwd'] * 6,
        'Product': ['Sawtimber', 'Sawtimber', 'Pulpwood', 'Pulpwood'] * 6,
        '$ Per Unit': [25.5, 40.2, 10.5, 12.8, 22.3, 38.5, 9.5, 11.2,
                       26.1, 42.5, 11.2, 13.5, 24.8, 39.8, 10.8, 12.9,
                       27.3, 43.2, 11.8, 14.1, 25.9, 41.5, 10.2, 13.2],
        'Units': ['mbf', 'mbf', 'cord', 'cord'] * 6
    }
    return pd.DataFrame(data)

def create_mock_south_biomass():
    """Create mock data for Southern biomass"""
    # Create a basic structure for Southern biomass
    data = {
        'STATECD': ['01', '01', '01', '13', '13', '13'] * 2,
        'COUNTYCD': ['001', '002', '003', '001', '002', '003'] * 2,
        'PLOT': list(range(1, 13)),
        'SPCD': [110, 111, 121, 131, 110, 111, 121, 131, 110, 111, 121, 131],
        'SPGRPCD': [2, 1, 1, 2, 2, 1, 1, 2, 2, 1, 1, 2],
        'DIA': [4.5, 5.2, 6.1, 4.8, 5.0, 5.5, 5.2, 4.8, 5.5, 6.0, 4.2, 4.5],
        'SPCLASS': ['Softwood'] * 12,
        'SC 0001 (0-1"dbh)': [125, 130, 120, 135, 140, 145, 110, 115, 150, 155, 125, 130],
        'SC 0002 (1-3"dbh)': [225, 230, 220, 235, 240, 245, 210, 215, 250, 255, 225, 230],
        'SC 0003 (3-5"dbh)': [325, 330, 320, 335, 340, 345, 310, 315, 350, 355, 325, 330],
        'SC 0004 (5-7"dbh)': [425, 430, 420, 435, 440, 445, 410, 415, 450, 455, 425, 430]
    }
    return pd.DataFrame(data)

def create_mock_gl_biomass():
    """Create mock data for Great Lakes biomass"""
    # Create a basic structure for Great Lakes biomass
    data = {
        'STATECD': ['26', '26', '26', '27', '27', '27', '55', '55', '55'] * 2,
        'COUNTYCD': ['001', '002', '003', '001', '002', '003', '001', '002', '003'] * 2,
        'PLOT': list(range(1, 19)),
        'EVALID': ['232020'] * 18,
        'INVYR': [2023] * 18,
        'SPCD': [12, 71, 94, 95, 105, 130, 316, 371, 375,
                 12, 71, 94, 95, 105, 130, 316, 371, 375],
        'SPGRPCD': [6, 5, 6, 6, 5, 4, 32, 30, 30, 
                    6, 5, 6, 6, 5, 4, 32, 30, 30],
        'DIA': [10.5, 12.2, 11.1, 9.8, 11.0, 12.5, 14.2, 13.8, 12.5,
                11.5, 13.2, 12.1, 10.8, 12.0, 13.5, 15.2, 14.8, 13.5],
        'SPCLASS': ['Softwood', 'Softwood', 'Softwood', 'Softwood', 'Softwood', 'Softwood',
                   'Hardwood', 'Hardwood', 'Hardwood', 'Softwood', 'Softwood', 'Softwood',
                   'Softwood', 'Softwood', 'Softwood', 'Hardwood', 'Hardwood', 'Hardwood'],
        'SC 0101 (7-9"dbh)': [525, 530, 520, 535, 540, 545, 510, 515, 550, 
                             555, 525, 530, 520, 535, 540, 545, 510, 515],
        'SC 0102 (9-11"dbh)': [625, 630, 620, 635, 640, 645, 610, 615, 650,
                              655, 625, 630, 620, 635, 640, 645, 610, 615],
        'SC 0103 (11-13"dbh)': [725, 730, 720, 735, 740, 745, 710, 715, 750,
                               755, 725, 730, 720, 735, 740, 745, 710, 715],
        'SC 0104 (13-15"dbh)': [825, 830, 820, 835, 840, 845, 810, 815, 850,
                               855, 825, 830, 820, 835, 840, 845, 810, 815]
    }
    return pd.DataFrame(data) 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
South Asset Processing Module

This module processes data related to timber assets in the Southern United States.
It follows the single responsibility principle by focusing only on data processing
for the Southern region, with utilities and visualization handled separately.

The module processes the following data:
- Price regions and crosswalks
- Southern stumpage prices
- Pre-merchantable biomass
- Merchantable biomass
- Species classifications
- Volume and value calculations
"""

import pandas as pd
import numpy as np
from geo_crosswalks import (
    # Constants
    SOUTH_STATES, STATE_FIPS, DATA_DIR,
    # Data formatting
    format_fips, format_unit_code,
    # Loading functions
    load_crosswalk_price_regions
)
from species_crosswalks import (
    # Constants
    PRODUCT_TYPES,
    # Data loading
    load_csv, load_excel,
    # Data formatting
    standardize_column_names,
    # Data transformation
    convert_to_billions, convert_to_megatonnes, convert_price_ton_to_cubic_feet,
    # Species utilities
    speciesDict, get_species_name, speciesGroupDict, get_species_group_name
)


def load_price_regions():
    """
    Load and process price regions crosswalk data for the Southern states.
    
    Returns:
    --------
    pandas.DataFrame
        Processed price regions data
    """
    # Load price regions crosswalk
    price_regions = load_csv('priceRegions.csv')
    
    # Filter for Southern states only
    southern_states_fips = [STATE_FIPS[state] for state in SOUTH_STATES]
    price_regions = price_regions[price_regions['statecd'].isin(southern_states_fips)]
    
    # Ensure proper formatting
    price_regions = format_fips(price_regions)
    price_regions = format_unit_code(price_regions)
    
    return price_regions


def load_south_stumpage_prices():
    """
    Load and process Southern stumpage price data.
    
    Returns:
    --------
    pandas.DataFrame
        Processed stumpage price data
    """
    # Load southern prices
    prices_south = load_csv('Timber Prices/prices_south.csv')
    
    # Melt prices to long format
    prices_south = prices_south.melt(
        id_vars=prices_south.columns[0:3],
        value_vars=prices_south.columns[3:69],
        var_name='product',
        value_name='price'
    )
    
    # Extract components from product code
    prices_south['stateAbbr'] = prices_south['product'].str[3:5].str.upper()
    prices_south['priceRegion'] = prices_south['product'].str[5:].str.zfill(2)
    prices_south['product'] = prices_south['product'].str[:3]
    
    # Standardize product names
    prices_south['product'] = prices_south['product'].replace({
        'saw': 'Sawtimber',
        'plp': 'Pulpwood',
        'pre': 'Pre-merchantable'
    })
    
    # Standardize species class names
    prices_south['type'] = prices_south['type'].replace({
        'pine': 'Pine',
        'oak': 'Oak'
    })
    prices_south.rename(columns={'type': 'spclass'}, inplace=True)
    
    # Add state FIPS codes
    prices_south['statecd'] = prices_south['stateAbbr'].map(STATE_FIPS)
    
    # Aggregate prices
    prices_south = prices_south.groupby(
        ['statecd', 'stateAbbr', 'priceRegion', 'spclass', 'product']
    )['price'].mean().reset_index()
    
    # Convert price to dollars per cubic foot
    prices_south = convert_price_ton_to_cubic_feet(prices_south, price_col='price')
    prices_south.rename(columns={'product': 'Product'}, inplace=True)
    
    return prices_south


def calculate_premerchantable_prices(prices_south):
    """
    Calculate pre-merchantable timber prices based on pulpwood prices.
    
    Parameters:
    -----------
    prices_south : pandas.DataFrame
        Processed southern stumpage prices
        
    Returns:
    --------
    pandas.DataFrame
        Pre-merchantable prices for different size classes
    """
    # Make a copy to avoid modifying the original
    prices_south_premerch = prices_south.copy()
    
    # Filter for Pine species and Pulpwood product
    prices_south_premerch = prices_south_premerch[
        (prices_south_premerch['spclass'] == 'Pine') & 
        (prices_south_premerch['Product'] == 'Pulpwood')
    ]
    
    # Reshape data
    prices_south_premerch = prices_south_premerch.pivot_table(
        index=['statecd', 'stateAbbr', 'priceRegion'],
        columns='spclass', 
        values='cuftPrice'
    ).reset_index()
    
    # Calculate pre-merchantable prices for different size classes
    # Using the formula: pre-merchantable price = pulpwood price / (1 + r)^(Am-age)
    r = 0.05  # discount rate
    Am = 15   # merchantable age
    
    prices_south_premerch['0004'] = prices_south_premerch['Pine'] / (1 + r)**(Am - 12.264)
    prices_south_premerch['0003'] = prices_south_premerch['Pine'] / (1 + r)**(Am - 7.5)
    prices_south_premerch['0002'] = prices_south_premerch['Pine'] / (1 + r)**(Am - 2.736)
    prices_south_premerch['0001'] = prices_south_premerch['Pine'] / (1 + r)**(Am - 0.722)
    
    # Reshape back to long format
    prices_south_premerch = prices_south_premerch.melt(
        id_vars=['statecd', 'stateAbbr', 'priceRegion'],
        value_vars=['0004', '0003', '0002', '0001'],
        var_name='sizeclass',
        value_name='cuftPrice'
    )
    
    return prices_south_premerch


def load_south_premerch_biomass():
    """
    Load and process Southern pre-merchantable biomass data.
    
    Returns:
    --------
    pandas.DataFrame
        Processed pre-merchantable biomass data
    """
    # Load pre-merchantable biomass data
    biomass_south_premerch = load_excel('Premerch Bio South by spp 08-28-2024.xlsx', sheet_name=0)
    biomass_south_premerch.fillna(0, inplace=True)
    
    # Melt to long format
    biomass_south_premerch = biomass_south_premerch.melt(
        id_vars=biomass_south_premerch.columns[0:13],
        var_name='sizeClass',
        value_name='volume'
    )
    
    # Filter for softwood species only (pre-merchantable hardwood not tracked)
    biomass_south_premerch = biomass_south_premerch[biomass_south_premerch['SPCLASS'] != 'Hardwood']
    
    # Define marketable pine species
    marketable_species = [110, 111, 121, 131]  # shortleaf, slash, longleaf, loblolly
    biomass_south_premerch = biomass_south_premerch[biomass_south_premerch['SPCD'].isin(marketable_species)]
    
    # Process size class information
    biomass_south_premerch[['sizeClass', 'sizeRange']] = (
        biomass_south_premerch['sizeClass'].str.split(' ', n=1, expand=True)
    )
    biomass_south_premerch['sizeClass'] = biomass_south_premerch['sizeClass'].str[2:]
    biomass_south_premerch['sizeRange'] = biomass_south_premerch['sizeRange'].str[:-1]
    
    # Extract year from EVALID
    biomass_south_premerch['EVALID'] = biomass_south_premerch['EVALID'].astype(str).str.zfill(6)
    biomass_south_premerch['year'] = biomass_south_premerch['EVALID'].str[2:4].astype(int) + 2000
    
    # Format geographic identifiers
    biomass_south_premerch['STATECD'] = biomass_south_premerch['STATECD'].astype(str).str.zfill(2)
    biomass_south_premerch['COUNTYCD'] = biomass_south_premerch['COUNTYCD'].astype(str).str.zfill(3)
    biomass_south_premerch['fips'] = biomass_south_premerch['STATECD'] + biomass_south_premerch['COUNTYCD']
    biomass_south_premerch['UNITCD'] = biomass_south_premerch['UNITCD'].astype(str).str.zfill(2)
    
    # Standardize column names
    biomass_south_premerch = standardize_column_names(biomass_south_premerch)
    
    # Select needed columns
    biomass_south_premerch = biomass_south_premerch[[
        'year', 'statecd', 'fips', 'unitcd', 'spcd', 'spgrpcd', 'spclass', 
        'sizeclass', 'sizerange', 'volume'
    ]]
    
    return biomass_south_premerch


def load_south_harvested_species():
    """
    Load and process Southern harvested species data.
    
    Returns:
    --------
    pandas.DataFrame
        Processed harvested species data with species codes
    """
    # Load harvested species data
    harvest_species = load_csv('Southern harvested tree species.csv')
    
    # Filter for non-zero estimates
    harvest_species = harvest_species[harvest_species['ESTIMATE'] != 0]
    harvest_species = harvest_species.dropna(subset=['ESTIMATE'])
    
    # Extract state code and species code
    harvest_species['statecd'] = harvest_species['GRP2'].str[6:8]
    harvest_species['spcd'] = harvest_species['GRP1'].str[11:14]
    harvest_species['spcd'] = harvest_species['spcd'].astype('int64')
    
    # Rename volume column
    harvest_species.rename(columns={'ESTIMATE': 'volume'}, inplace=True)
    
    # Keep only needed columns
    harvest_species = harvest_species[['statecd', 'spcd']]
    
    # Define list of marketable species
    marketable_species = [
        68, 110, 111, 121, 129, 131, 132, 221, 314, 318, 409, 402, 403, 404, 407, 
        541, 544, 546, 601, 602, 611, 621, 651, 652, 653, 762, 802, 804, 812, 822, 
        823, 830, 832, 837
    ]
    
    return harvest_species, marketable_species


def load_south_merch_biomass(marketable_species):
    """
    Load and process Southern merchantable biomass data.
    
    Parameters:
    -----------
    marketable_species : list
        List of species codes for marketable species
        
    Returns:
    --------
    pandas.DataFrame
        Processed merchantable biomass data
    """
    # Load merchantable biomass
    biomass_south = load_excel('Merch Bio South by spp 08-28-2024.xlsx', sheet_name=0)
    biomass_south.fillna(0, inplace=True)
    
    # Melt to long format
    biomass_south = biomass_south.melt(
        id_vars=biomass_south.columns[0:13],
        value_vars=biomass_south.columns[13:29],
        var_name='size_class',
        value_name='volume'
    )
    
    # Filter for marketable species
    biomass_south = biomass_south[biomass_south['SPCD'].isin(marketable_species)]
    
    # Process size class information
    biomass_south[['size_class_code', 'size_class_range']] = (
        biomass_south['size_class'].str.split(' ', n=1, expand=True)
    )
    biomass_south['size_class_code'] = biomass_south['size_class_code'].str[2:]
    biomass_south['size_class_range'] = biomass_south['size_class_range'].str[:-1]
    
    # Determine product category based on size class
    conditions = [
        (biomass_south['size_class_code'].isin(['0001', '0002', '0003', '0004'])),
        (biomass_south['size_class_code'].isin(['0005', '0006', '0007', '0008', '0009', '0010', '0011'])),
        (biomass_south['size_class_code'].isin(['0012', '0013', '0014', '0015', '0016', '0017', '0018', '0019', '0020', '0021']))
    ]
    choices = ['Pre-merchantable', 'Pulpwood', 'Sawtimber']
    biomass_south['product'] = np.select(conditions, choices, default='Unknown')
    
    # Extract year from EVALID
    biomass_south['EVALID'] = biomass_south['EVALID'].astype(str).str.zfill(6)
    biomass_south['year'] = biomass_south['EVALID'].str[2:4].astype(int) + 2000
    
    # Format geographic identifiers
    biomass_south['STATECD'] = biomass_south['STATECD'].astype(str).str.zfill(2)
    biomass_south['COUNTYCD'] = biomass_south['COUNTYCD'].astype(str).str.zfill(3)
    biomass_south['fips'] = biomass_south['STATECD'] + biomass_south['COUNTYCD']
    biomass_south['UNITCD'] = biomass_south['UNITCD'].astype(str).str.zfill(2)
    
    # Standardize column names
    biomass_south = standardize_column_names(biomass_south)
    
    # Select needed columns
    biomass_south = biomass_south[[
        'year', 'statecd', 'fips', 'unitcd', 'spcd', 'spgrpcd', 'spclass', 
        'size_class_code', 'size_class_range', 'product', 'volume'
    ]]
    
    return biomass_south


def merge_price_biomass_data(prices_south, biomass_south, price_regions):
    """
    Merge price and biomass data to calculate timber values.
    
    Parameters:
    -----------
    prices_south : pandas.DataFrame
        Processed Southern stumpage prices
    biomass_south : pandas.DataFrame
        Processed Southern merchantable biomass data
    price_regions : pandas.DataFrame
        Price regions crosswalk data
        
    Returns:
    --------
    pandas.DataFrame
        Merged data with volume and value calculations
    """
    # Add price region to biomass data
    biomass_south = pd.merge(biomass_south, price_regions, on=['statecd', 'unitcd'])
    
    # Merge price data with biomass data
    # For merchantable timber
    merch_mask = biomass_south['product'].isin(['Pulpwood', 'Sawtimber'])
    biomass_south_merch = biomass_south[merch_mask].copy()
    
    # Prepare price data for merging
    prices_south_merch = prices_south.copy()
    
    # Merge based on state, price region, species class, and product
    table_south = pd.merge(
        biomass_south_merch,
        prices_south_merch,
        how='left',
        left_on=['statecd', 'priceRegion', 'spclass', 'product'],
        right_on=['statecd', 'priceRegion', 'spclass', 'Product']
    )
    
    # Calculate value
    table_south['value'] = table_south['volume'] * table_south['cuftPrice']
    
    # Select final columns
    table_south = table_south[[
        'statecd', 'unitcd', 'fips', 'spcd', 'spgrpcd', 'spclass', 'product', 
        'volume', 'cuftPrice', 'value'
    ]]
    
    return table_south


def process_south_data():
    """
    Main function to process all Southern region data.
    
    Returns:
    --------
    dict
        Dictionary containing processed dataframes
    """
    # Load data
    price_regions = load_price_regions()
    prices_south = load_south_stumpage_prices()
    prices_south_premerch = calculate_premerchantable_prices(prices_south)
    biomass_south_premerch = load_south_premerch_biomass()
    harvest_species, marketable_species = load_south_harvested_species()
    biomass_south = load_south_merch_biomass(marketable_species)
    
    # Merge and calculate
    table_south = merge_price_biomass_data(prices_south, biomass_south, price_regions)
    
    # Convert units for reporting
    table_south = convert_to_billions(table_south, value_col='value')
    table_south = convert_to_megatonnes(table_south, volume_col='volume')
    
    # Save processed data
    table_south.to_csv(DATA_DIR / 'processed' / 'table_south.csv', index=False)
    
    return {
        'price_regions': price_regions,
        'prices_south': prices_south,
        'biomass_south': biomass_south,
        'table_south': table_south
    }


if __name__ == "__main__":
    # Make sure processed directory exists
    (DATA_DIR / 'processed').mkdir(exist_ok=True)
    
    # Process Southern data
    result = process_south_data()
    print(f"Southern data processing complete. Processed {len(result['table_south'])} records.") 
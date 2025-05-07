#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Great Lakes Asset Processing Module

This module processes data related to timber assets in the Great Lakes region.
It follows the single responsibility principle by focusing only on data processing
for the Great Lakes region, with utilities and visualization handled separately.

The module processes the following data:
- Price regions and crosswalks
- Great Lakes stumpage prices
- Merchantable biomass data
- Species classifications
- Volume and value calculations
"""

import pandas as pd
import numpy as np
from utils import (
    # Constants
    GREAT_LAKES_STATES, STATE_FIPS, DATA_DIR,
    # Data loading
    load_csv, load_excel,
    # Data formatting
    format_fips, format_unit_code, standardize_column_names,
    # Data transformation
    convert_to_billions, convert_to_megatonnes,
    # Species utilities
    speciesDict, get_species_name, speciesGroupDict, get_species_group_name
)


def load_price_regions():
    """
    Load and process price regions crosswalk data for the Great Lakes states.
    
    Returns:
    --------
    pandas.DataFrame
        Processed price regions data
    """
    # Load price regions crosswalk
    price_regions = load_csv('priceRegions.csv')
    
    # Filter for Great Lakes states only
    gl_states_fips = [STATE_FIPS[state] for state in GREAT_LAKES_STATES]
    price_regions = price_regions[price_regions['statecd'].isin(gl_states_fips)]
    
    # Ensure proper formatting
    price_regions = format_fips(price_regions)
    price_regions = format_unit_code(price_regions)
    
    return price_regions


def load_gl_stumpage_prices():
    """
    Load and process Great Lakes stumpage price data.
    
    Returns:
    --------
    pandas.DataFrame
        Processed stumpage price data for Great Lakes region
    """
    # Load Great Lakes price data
    prices_north = load_excel('Timber Prices/TMN/TMN_Price_Series_June2023.xlsx')
    
    # Drop rows where Region has exactly 2 characters (state mean prices)
    prices_north = prices_north[prices_north['Region'].str.len() != 2]
    
    # Filter for Market = 'Stumpage'
    prices_north = prices_north[prices_north['Market'] == 'Stumpage']
    
    # Convert date and extract year
    prices_north['Period End Date'] = pd.to_datetime(prices_north['Period End Date'], errors='coerce')
    prices_north['year'] = prices_north['Period End Date'].dt.year
    
    # Split Region into state and price region
    prices_north[['state_abbr', 'priceRegion']] = prices_north['Region'].str.split('-', n=1, expand=True)
    prices_north['priceRegion'] = prices_north['priceRegion'].str.zfill(2)
    
    # Add state FIPS codes
    state_fips = {'MN': '27', 'WI': '55', 'MI': '26'}
    prices_north['statecd'] = prices_north['state_abbr'].map(state_fips)
    
    # Select needed columns
    prices_north = prices_north[['year', 'statecd', 'priceRegion', 'Species', 'Product', '$ Per Unit', 'Units']]
    
    # Drop rows with missing prices or years
    prices_north = prices_north.dropna(subset=['$ Per Unit', 'year'])
    
    # Convert prices to consistent units ($ per cubic foot)
    prices_north['$ Per Unit'] = prices_north['$ Per Unit'].astype(float)
    prices_north['cuftPrice'] = prices_north['$ Per Unit']
    
    # If units are cords, convert (1 cord = 128 cubic feet)
    prices_north.loc[prices_north['Units'] == 'cord', 'cuftPrice'] = prices_north['$ Per Unit'] / 128
    
    # If units are mbf, convert (12 board feet = 1 cubic foot)
    prices_north.loc[prices_north['Units'] == 'mbf', 'cuftPrice'] = prices_north['$ Per Unit'] / 12
    
    # Drop original price and units columns
    prices_north = prices_north.drop(columns=['$ Per Unit', 'Units'])
    
    # Rename species column for consistency
    prices_north.rename(columns={'Species': 'priceSpecies'}, inplace=True)
    
    # Average prices by region, species, and product
    prices_north = prices_north.groupby(['statecd', 'priceRegion', 'priceSpecies', 'Product'])['cuftPrice'].mean().reset_index()
    
    # Pivot to get products as columns
    prices_north = prices_north.pivot(
        index=['statecd', 'priceRegion', 'priceSpecies'],
        columns='Product',
        values='cuftPrice'
    ).reset_index()
    
    # Fill missing prices with 0
    prices_north = prices_north.fillna(0)
    
    # Map species to standardized names
    species_crosswalk = {
        'Maple Unspecified': 'Maple',
        'Mixed Hdwd': 'Hardwood',
        'Mixed Sftwd': 'Pine',
        'Other Hdwd': 'Hardwood',
        'Other Sfwd': 'Pine',
        'Oak Unspecified': 'Oak',
        'Other Hardwood': 'Hardwood',
        'Other Softwood': 'Softwood',
        'Pine Unspecified': 'Pine',
        'Spruce Unspecified': 'Spruce',
        'Spruce/Fir': 'Spruce',
        'White Birch': 'Paper Birch',
        'Scrub Oak': 'Oak'
    }
    
    prices_north['mergedSpecies'] = prices_north['priceSpecies'].map(species_crosswalk)
    prices_north['mergedSpecies'] = prices_north['mergedSpecies'].fillna(prices_north['priceSpecies'])
    prices_north = prices_north.drop(columns='priceSpecies')
    
    # Reduce to mean price by region and merged species
    prices_north = prices_north.groupby(['statecd', 'priceRegion', 'mergedSpecies']).agg({
        'Pulpwood': 'mean',
        'Sawtimber': 'mean'
    }).reset_index()
    
    # Convert merged species to lowercase for consistency
    prices_north['mergedSpecies'] = prices_north['mergedSpecies'].str.lower()
    
    # Melt to long format for consistency with southern data
    prices_north = prices_north.melt(
        id_vars=['statecd', 'priceRegion', 'mergedSpecies'],
        var_name='product',
        value_name='cuftPrice'
    )
    
    # Rename for consistency with biomass data
    prices_north.rename(columns={'mergedSpecies': 'species'}, inplace=True)
    
    return prices_north


def load_gl_biomass():
    """
    Load and process Great Lakes biomass data.
    
    Returns:
    --------
    pandas.DataFrame
        Processed biomass data for Great Lakes region
    """
    # Load biomass data
    biomass_north = load_excel('Merch Bio GLakes by spp 08-28-2024.xlsx', sheet_name=0)
    biomass_north.fillna(0, inplace=True)
    
    # Melt to long format
    biomass_north = biomass_north.melt(
        id_vars=biomass_north.columns[0:13],
        value_vars=biomass_north.columns[13:29],
        var_name='size_class',
        value_name='volume'
    )
    
    # Process size class information
    biomass_north[['size_class_code', 'size_class_range']] = (
        biomass_north['size_class'].str.split(' ', n=1, expand=True)
    )
    biomass_north['size_class_code'] = biomass_north['size_class_code'].str[2:]
    biomass_north['size_class_range'] = biomass_north['size_class_range'].str[:-1]
    
    # Extract year from EVALID
    biomass_north['EVALID'] = biomass_north['EVALID'].astype(str).str.zfill(6)
    biomass_north['year'] = biomass_north['EVALID'].str[2:4].astype(int) + 2000
    
    # Format geographic identifiers
    biomass_north['STATECD'] = biomass_north['STATECD'].astype(str).str.zfill(2)
    biomass_north['COUNTYCD'] = biomass_north['COUNTYCD'].astype(str).str.zfill(3)
    biomass_north['fips'] = biomass_north['STATECD'] + biomass_north['COUNTYCD']
    biomass_north['UNITCD'] = biomass_north['UNITCD'].astype(str).str.zfill(2)
    
    # Standardize column names
    biomass_north = standardize_column_names(biomass_north)
    
    # Keep only necessary columns
    biomass_north = biomass_north[[
        'statenm', 'statecd', 'fips', 'unitcd', 'spcd', 'scientific_name',
        'spgrpcd', 'spclass', 'size_class_code', 'size_class_range', 'volume'
    ]]
    
    return biomass_north


def load_gl_harvested_species():
    """
    Load and process Great Lakes harvested species data.
    
    Returns:
    --------
    tuple
        Harvested species DataFrame and list of marketable species codes
    """
    # Load harvested species data
    harvest_species_gl = load_excel('GLakes harvested tree species V2.xlsx', sheet_name='GL harvested spp')
    
    # Filter for rows with non-zero harvest
    harvest_species_gl = harvest_species_gl[
        harvest_species_gl['Harvest removals, in trees, at least 5in, forestland'] != 0
    ]
    harvest_species_gl = harvest_species_gl.dropna(
        subset=['Harvest removals, in trees, at least 5in, forestland']
    )
    
    # Extract state code from EVALUATION
    # EVALUATION format: "`0055 552101 Wisconsin 2021"
    # where "552101" is statecd + two digit year + evalid
    harvest_species_gl['statecd'] = harvest_species_gl['EVALUATION'].str[6:8]
    
    # Extract species code from SPECIES
    # SPECIES format: "`0012 SPCD 0012 - balsam fir (Abies balsamea)"
    harvest_species_gl['spcd'] = harvest_species_gl['SPECIES'].str.split(' ').str[2]
    
    # Define marketable species for Great Lakes
    marketable_species_gl = [
        12, 86, 71, 91, 94, 95, 105, 110, 111, 121, 125, 126, 129, 130, 131,
        132, 221, 313, 314, 316, 318, 371, 375, 409, 402, 403, 404, 405, 407,
        462, 531, 541, 543, 544, 546, 601, 602, 611, 621, 651, 652, 653, 742,
        743, 746, 762, 802, 804, 809, 812, 822, 823, 826, 830, 832, 833, 837,
        951, 972, 977
    ]
    
    return harvest_species_gl, marketable_species_gl


def filter_biomass_by_species(biomass_north, marketable_species):
    """
    Filter biomass data to include only marketable species.
    
    Parameters:
    -----------
    biomass_north : pandas.DataFrame
        Biomass data for Great Lakes region
    marketable_species : list
        List of marketable species codes
        
    Returns:
    --------
    pandas.DataFrame
        Filtered biomass data
    """
    # Convert species code to int if it's not already
    if biomass_north['spcd'].dtype != 'int64':
        biomass_north['spcd'] = biomass_north['spcd'].astype(int)
    
    # Filter for marketable species
    biomass_filtered = biomass_north[biomass_north['spcd'].isin(marketable_species)]
    
    # Add product classification based on size class code
    # In Great Lakes, pulpwood is generally 5-19.9" and sawtimber is 20"+
    conditions = [
        (biomass_filtered['size_class_code'].isin(['0005', '0006', '0007', '0008', '0009', '0010', '0011', '0012', '0013', '0014', '0015', '0016', '0017', '0018', '0019'])),
        (biomass_filtered['size_class_code'].isin(['0020', '0021', '0022', '0023', '0024', '0025', '0026', '0027', '0028', '0029']))
    ]
    choices = ['Pulpwood', 'Sawtimber']
    biomass_filtered['product'] = np.select(conditions, choices, default='Unknown')
    
    # Clean up column names to match prices data format
    biomass_filtered.rename(columns={'scientific_name': 'species_scientific'}, inplace=True)
    
    # Extract common name from scientific name for easier matching with price data
    # This is a simplified approach; in practice, a more robust mapping would be needed
    biomass_filtered['species'] = biomass_filtered['species_scientific'].str.split('(').str[0].str.strip().str.lower()
    
    return biomass_filtered


def merge_price_biomass_data(prices_north, biomass_north, price_regions):
    """
    Merge price and biomass data to calculate timber values.
    
    Parameters:
    -----------
    prices_north : pandas.DataFrame
        Processed Great Lakes stumpage prices
    biomass_north : pandas.DataFrame
        Processed Great Lakes biomass data
    price_regions : pandas.DataFrame
        Price regions crosswalk data
        
    Returns:
    --------
    pandas.DataFrame
        Merged data with volume and value calculations
    """
    # Add price region to biomass data
    biomass_north = pd.merge(biomass_north, price_regions, on=['statecd', 'unitcd'])
    
    # Group biomass by state, price region, species, and product
    # This aggregation helps match with price data structure
    biomass_grouped = biomass_north.groupby([
        'statecd', 'priceRegion', 'spclass', 'product', 'spcd', 'spgrpcd'
    ])['volume'].sum().reset_index()
    
    # Prepare species crosswalk for matching
    # Map FIA species codes to price species names
    # This is a simplified approach; in practice would need a more complete mapping
    species_price_map = {
        'Pine': ['pine', 'spruce', 'fir', 'tamarack', 'cedar'],
        'Hardwood': ['oak', 'maple', 'ash', 'birch', 'beech', 'cherry', 'basswood', 'elm']
    }
    
    # Convert spclass to match price data format
    biomass_grouped['spclass'] = biomass_grouped['spclass'].replace({
        'Softwood': 'Pine',
        'Hardwood': 'Hardwood'
    })
    
    # Merge based on state, price region, species class, and product
    # Need to handle the species matching carefully
    table_gl = pd.merge(
        biomass_grouped,
        prices_north,
        how='left',
        left_on=['statecd', 'priceRegion', 'spclass', 'product'],
        right_on=['statecd', 'priceRegion', 'species', 'product']
    )
    
    # Fill any missing prices with average for that species class and product
    price_averages = prices_north.groupby(['spclass', 'product'])['cuftPrice'].mean().reset_index()
    
    # For each row with missing price, find and apply the average price
    for index, row in table_gl[table_gl['cuftPrice'].isna()].iterrows():
        avg_price = price_averages[
            (price_averages['spclass'] == row['spclass']) & 
            (price_averages['product'] == row['product'])
        ]['cuftPrice'].values
        
        if len(avg_price) > 0:
            table_gl.at[index, 'cuftPrice'] = avg_price[0]
    
    # Calculate value
    table_gl['value'] = table_gl['volume'] * table_gl['cuftPrice']
    
    # Select final columns
    table_gl = table_gl[[
        'statecd', 'unitcd', 'fips', 'spcd', 'spgrpcd', 'spclass', 'product', 
        'volume', 'cuftPrice', 'value'
    ]]
    
    return table_gl


def process_gl_data():
    """
    Main function to process all Great Lakes region data.
    
    Returns:
    --------
    dict
        Dictionary containing processed dataframes
    """
    # Load data
    price_regions = load_price_regions()
    prices_north = load_gl_stumpage_prices()
    biomass_north = load_gl_biomass()
    harvest_species_gl, marketable_species_gl = load_gl_harvested_species()
    
    # Filter biomass data
    biomass_filtered = filter_biomass_by_species(biomass_north, marketable_species_gl)
    
    # Merge and calculate
    table_gl = merge_price_biomass_data(prices_north, biomass_filtered, price_regions)
    
    # Convert units for reporting
    table_gl = convert_to_billions(table_gl, value_col='value')
    table_gl = convert_to_megatonnes(table_gl, volume_col='volume')
    
    # Save processed data
    table_gl.to_csv(DATA_DIR / 'processed' / 'table_gl.csv', index=False)
    
    return {
        'price_regions': price_regions,
        'prices_north': prices_north,
        'biomass_north': biomass_filtered,
        'table_gl': table_gl
    }


if __name__ == "__main__":
    # Make sure processed directory exists
    (DATA_DIR / 'processed').mkdir(exist_ok=True)
    
    # Process Great Lakes data
    result = process_gl_data()
    print(f"Great Lakes data processing complete. Processed {len(result['table_gl'])} records.") 
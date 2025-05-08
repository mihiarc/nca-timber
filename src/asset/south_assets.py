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
import os
from src.utils.geo_crosswalks import (
    # Constants
    DATA_DIR, PROCESSED_DIR,
    # Data formatting
    format_unit_code,
    # Loading functions
    get_price_regions
)
from src.utils.species_crosswalks import (
    # Constants
    PRODUCT_TYPES,
    # Data loading
    load_csv,
    # Data formatting
    standardize_column_names,
    # Data transformation
    convert_price_ton_to_cubic_feet
)
from src.utils.county import format_fips
from src.config import STATE_FIPS


def load_price_regions():
    """
    Load and process price regions crosswalk data for the Southern states.
    
    Returns:
    --------
    pandas.DataFrame
        Processed price regions data
    """
    # Get price regions from the hardcoded function
    price_regions = get_price_regions(region='south')
    
    # Ensure proper formatting
    price_regions = format_fips(price_regions)
    price_regions = format_unit_code(price_regions)
    
    return price_regions


def load_south_stumpage_prices():
    """
    Load and process Southern stumpage price data from the consolidated file.

    Returns:
    --------
    pandas.DataFrame
        Processed stumpage price data with columns:
        statecd, stateAbbr, priceRegion, spclass, Product, cuftPrice
    """
    # Load consolidated prices
    prices_path = PROCESSED_DIR / 'tms_consolidated_prices.csv'
    prices_raw = load_csv(prices_path)

    if prices_raw.empty:
        print("Warning: Consolidated price data failed to load. Returning empty DataFrame.")
        return pd.DataFrame()

    # Filter for Stumpage prices and ensure Units are $/ton
    prices_raw = prices_raw[prices_raw['ReportType'] == 'Stumpage'].copy()
    if not prices_raw['Units'].str.contains(r'\$/ton', na=False).all():
        print("Warning: Price data units are not consistently $/ton. Conversion might be inaccurate.")
        # Attempt to filter for $/ton, handling potential errors
        prices_raw = prices_raw[prices_raw['Units'].str.contains(r'\$/ton', na=False)]
        if prices_raw.empty:
             print("Error: No $/ton data found after filtering. Cannot proceed.")
             return pd.DataFrame()


    # Rename and format necessary columns
    prices_raw.rename(columns={'State': 'stateAbbr', 'Area': 'priceRegion'}, inplace=True)
    prices_raw['statecd'] = prices_raw['stateAbbr'].map(STATE_FIPS)

    # Ensure priceRegion is a zero-padded string (handle potential non-numeric values)
    prices_raw['priceRegion'] = pd.to_numeric(prices_raw['priceRegion'], errors='coerce').fillna(0).astype(int)
    prices_raw['priceRegion'] = prices_raw['priceRegion'].astype(str).str.zfill(2)


    # Identify ID variables and price columns (value variables)
    id_vars = ['Year', 'statecd', 'stateAbbr', 'priceRegion']
    value_vars = [
        'Pine_Sawtimber_WR', 'Pine_Sawtimber_CNS', 'Pine_Sawtimber_Ply',
        'Oak_Sawtimber', 'MixHwd_Sawtimber',
        'Pine_Pulpwood', 'Hardwood_Pulpwood'
        # Ignoring Pine_Poles for now
    ]

    # Ensure price columns exist and convert to numeric (errors='coerce' turns failures into NaN)
    valid_value_vars = []
    for col in value_vars:
        if col in prices_raw.columns:
            prices_raw[col] = pd.to_numeric(prices_raw[col], errors='coerce')
            valid_value_vars.append(col)
        else:
            print(f"Warning: Price column '{col}' not found in {prices_path}. Skipping.")
            
    if not valid_value_vars:
        print(f"Error: No valid price columns found in {prices_path}. Cannot proceed.")
        return pd.DataFrame()

    # Melt the DataFrame
    prices_melted = prices_raw.melt(
        id_vars=id_vars,
        value_vars=valid_value_vars,
        var_name='Product_Species_Raw',
        value_name='price'
    )

    # Drop rows where price is NaN after melting/coercion
    prices_melted.dropna(subset=['price'], inplace=True)

    # Parse Product and Species Class from Product_Species_Raw
    def parse_product_species(raw_name):
        if 'Pine_Sawtimber' in raw_name:
            return 'Sawtimber', 'Pine'
        elif 'Oak_Sawtimber' in raw_name:
            return 'Sawtimber', 'Oak'
        elif 'MixHwd_Sawtimber' in raw_name:
            return 'Sawtimber', 'Hardwood'
        elif 'Pine_Pulpwood' in raw_name:
            return 'Pulpwood', 'Pine'
        elif 'Hardwood_Pulpwood' in raw_name:
            return 'Pulpwood', 'Hardwood'
        else:
            return None, None # Ignore other types like Pine_Poles for now

    prices_melted[['Product', 'spclass']] = prices_melted['Product_Species_Raw'].apply(
        lambda x: pd.Series(parse_product_species(x))
    )

    # Drop rows where parsing failed (e.g., Pine_Poles if not handled)
    prices_melted.dropna(subset=['Product', 'spclass'], inplace=True)

    # Aggregate prices (average over years and different Pine Sawtimber types)
    prices_agg = prices_melted.groupby(
        ['statecd', 'stateAbbr', 'priceRegion', 'spclass', 'Product']
    )['price'].mean().reset_index()

    # Convert price to dollars per cubic foot
    prices_final = convert_price_ton_to_cubic_feet(prices_agg, price_col='price')

    return prices_final


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
    biomass_south_premerch = load_csv(DATA_DIR / 'processed' / 'tableSouthPremerch.csv')
    biomass_south_premerch.fillna(0, inplace=True)

    if biomass_south_premerch.empty:
        print("Warning: tableSouthPremerch.csv loaded as empty. Skipping processing.")
        return pd.DataFrame()

    # Standardize column names (optional, but good practice)
    biomass_south_premerch = standardize_column_names(biomass_south_premerch)

    # Filter for softwood species only (pre-merchantable hardwood not tracked in original logic)
    # Check if 'spclass' exists after standardization
    if 'spclass' in biomass_south_premerch.columns:
        biomass_south_premerch = biomass_south_premerch[biomass_south_premerch['spclass'].str.lower() != 'hardwood']
    else:
        print("Warning: 'spclass' column not found in premerch data for filtering.")

    # Define marketable pine species (Optional: filter if needed, original logic kept)
    # Check if 'spcd' exists
    if 'spcd' in biomass_south_premerch.columns:
        marketable_species = [110, 111, 121, 131]  # shortleaf, slash, longleaf, loblolly
        biomass_south_premerch = biomass_south_premerch[biomass_south_premerch['spcd'].isin(marketable_species)]
    else:
         print("Warning: 'spcd' column not found in premerch data for filtering marketable species.")

    # Format FIPS code using the utility function
    # Standardize common variations of state/county column names first
    rename_dict = {
        'state': 'statecd', 
        'county': 'countycd'
    }
    # Rename only if the source column exists and the target doesn't
    cols_to_rename = {k: v for k, v in rename_dict.items() 
                      if k in biomass_south_premerch.columns and v not in biomass_south_premerch.columns}
    if cols_to_rename:
      biomass_south_premerch.rename(columns=cols_to_rename, inplace=True)
      
    try:
        biomass_south_premerch = format_fips(biomass_south_premerch, state_col='statecd', county_col='countycd')
    except ValueError as e:
        print(f"Error formatting FIPS in premerch data: {e}")
        biomass_south_premerch['fips'] = None # Set fips to None if formatting fails

    # Ensure statecd is a zero-padded string for consistency
    if 'statecd' in biomass_south_premerch.columns:
        biomass_south_premerch['statecd'] = biomass_south_premerch['statecd'].astype(str).str.zfill(2)

    # Select and rename final columns to match expected output structure
    # Ensure columns exist before selecting
    final_cols = {}
    mapping = {
        'statecd': 'statecd',
        'fips': 'fips',
        'unitcd': 'unitcd',
        'spcd': 'spcd',
        'spgrpcd': 'spgrpcd',
        'spclass': 'spclass',
        'sizerange': 'sizerange', # Assuming sizerange is the desired size identifier
        'volume': 'volume'
        # 'year' is no longer available
        # 'sizeclass' might need mapping from 'sizerange' if a code is needed
    }
    for target, source in mapping.items():
        if source in biomass_south_premerch.columns:
            final_cols[target] = biomass_south_premerch[source]
        else:
            print(f"Warning: Column '{source}' not found in premerch data for final selection.")
            final_cols[target] = None # Add placeholder or handle differently

    biomass_final = pd.DataFrame(final_cols)
    # Drop rows where essential columns ended up None due to missing source
    biomass_final.dropna(subset=['statecd', 'fips', 'spcd', 'volume'], inplace=True) 
    
    return biomass_final


def load_south_merch_biomass():
    """
    Load and process Southern merchantable biomass data.
    
    Returns:
    --------
    pandas.DataFrame
        Processed merchantable biomass data
    """
    # Load merchantable biomass
    biomass_south = load_csv(DATA_DIR / 'processed' / 'tableSouthMerch.csv')
    biomass_south.fillna(0, inplace=True)

    if biomass_south.empty:
        print("Warning: tableSouthMerch.csv loaded as empty. Skipping processing.")
        return pd.DataFrame()

    # Standardize column names
    biomass_south = standardize_column_names(biomass_south)

    # Ensure unitcd is consistently formatted as a string BEFORE FIPS formatting or selection
    if 'unitcd' in biomass_south.columns:
        biomass_south = format_unit_code(biomass_south, unit_col='unitcd')
    else:
        print("Warning: 'unitcd' column not found in merch data before FIPS/final selection.")

    # Format FIPS code using the utility function
    # Standardize common variations of state/county column names first
    rename_dict = {
        'state': 'statecd', 
        'county': 'countycd'
    }
    # Rename only if the source column exists and the target doesn't
    cols_to_rename = {k: v for k, v in rename_dict.items() 
                      if k in biomass_south.columns and v not in biomass_south.columns}
    if cols_to_rename:
      biomass_south.rename(columns=cols_to_rename, inplace=True)
      
    try:
      biomass_south = format_fips(biomass_south, state_col='statecd', county_col='countycd')
    except ValueError as e:
        print(f"Error formatting FIPS in merch data: {e}")
        biomass_south['fips'] = None # Set fips to None if formatting fails

    # Ensure statecd is a zero-padded string for consistency
    if 'statecd' in biomass_south.columns:
        biomass_south['statecd'] = biomass_south['statecd'].astype(str).str.zfill(2)

    # Select needed columns (using standardized names)
    # The input file already has 'product', 'volume', etc.
    final_cols = {}
    mapping = {
        # 'year' is not available from this CSV
        'statecd': 'statecd',
        'fips': 'fips',
        'unitcd': 'unitcd',
        'spcd': 'spcd',
        'spgrpcd': 'spgrpcd',
        'spclass': 'spclass',
        'size_class_code': 'size_class_code',
        'size_class_range': 'size_class_range',
        'product': 'product',
        'volume': 'volume'
    }
    for target, source in mapping.items():
        if source in biomass_south.columns:
            final_cols[target] = biomass_south[source]
        else:
             print(f"Warning: Column '{source}' not found in merch data for final selection.")
             final_cols[target] = None # Add placeholder or handle differently
             
    biomass_final = pd.DataFrame(final_cols)
    # Drop rows where essential columns ended up None
    biomass_final.dropna(subset=['statecd', 'fips', 'spcd', 'volume', 'product'], inplace=True)

    return biomass_final


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
    # Ensure dtypes for merge keys are consistent before merging
    if 'unitcd' in biomass_south.columns:
        biomass_south['unitcd'] = biomass_south['unitcd'].astype(str)
    if 'unitcd' in price_regions.columns:
        price_regions['unitcd'] = price_regions['unitcd'].astype(str)
    if 'statecd' in biomass_south.columns:
        biomass_south['statecd'] = biomass_south['statecd'].astype(str)
    if 'statecd' in price_regions.columns:
        price_regions['statecd'] = price_regions['statecd'].astype(str)

    biomass_merged_with_regions = pd.merge(biomass_south, price_regions, on=['statecd', 'unitcd'], how='left', suffixes=('', '_region'))

    # If 'fips_region' exists and 'fips' is missing, or if we want to prioritize fips from biomass_south if it exists
    # For now, we assume fips from biomass_south (left side of merge) is the one to keep if no suffixes were added. 
    # If suffixes were added, fips from biomass_south would be 'fips' and from price_regions would be 'fips_region'.
    # The default suffix '' for the left table means biomass_south's fips column remains 'fips'.
    # We can drop fips_region if it was created.
    if 'fips_region' in biomass_merged_with_regions.columns:
        biomass_merged_with_regions.drop(columns=['fips_region'], inplace=True)
    
    # Merge price data with biomass data
    # For merchantable timber
    merch_mask = biomass_merged_with_regions['product'].isin(['Pulpwood', 'Sawtimber'])
    biomass_south_merch = biomass_merged_with_regions[merch_mask].copy()
    
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
    # Ensure required columns exist before calculation
    if 'volume' in table_south.columns and 'cuftprice' in table_south.columns:
         table_south['value'] = table_south['volume'] * table_south['cuftprice']
    elif 'volume' in table_south.columns and 'cuftPrice' in table_south.columns:
         # Handle potential capitalization from right df if left merge failed 
         table_south['value'] = table_south['volume'] * table_south['cuftPrice']
    else:
        print("Warning: 'volume' or 'cuftprice'/'cuftPrice' missing after merge. Cannot calculate value.")
        table_south['value'] = pd.NA

    # Standardize column names after merge
    table_south = standardize_column_names(table_south)
    
    # Select final columns, checking for existence
    final_cols_list = [
        'statecd', 'unitcd', 'fips', 'spcd', 'spgrpcd', 'spclass', 'product', 
        'volume', 'cuftprice', 'value' 
    ]
    
    # Filter list based on columns actually present in table_south
    cols_to_select = [col for col in final_cols_list if col in table_south.columns]
    missing_cols = [col for col in final_cols_list if col not in table_south.columns]
    if missing_cols:
        print(f"Warning: Columns missing from final merged table: {missing_cols}")

    table_final = table_south[cols_to_select]
    
    return table_final


def process_south_data():
    """
    Process Southern data pipeline.
    
    This function orchestrates the entire data processing workflow
    for the Southern region.
    
    Returns:
    --------
    dict
        Dictionary containing the processed tables
    """
    try:
        # Create necessary directories
        os.makedirs(DATA_DIR / 'processed', exist_ok=True)
        
        # Load price regions crosswalk
        price_regions = load_price_regions()
        
        try:
            # Load stumpage prices
            prices_south = load_south_stumpage_prices()
            
            # Calculate pre-merchantable prices
            prices_south_premerch = calculate_premerchantable_prices(prices_south)
            
            # Load merchantable biomass (marketable_species logic removed)
            biomass_south = load_south_merch_biomass()
            
            # Load pre-merchantable biomass
            biomass_south_premerch = load_south_premerch_biomass()
            
            # Merge data
            table_south = merge_price_biomass_data(prices_south, biomass_south, price_regions)
            
            # Save to CSV
            table_south.to_csv(DATA_DIR / 'processed' / 'table_south.csv', index=False)
            
            return {
                'table_south': table_south,
                'price_regions': price_regions,
                'prices_south': prices_south,
                'biomass_south': biomass_south
            }
        except Exception as e:
            print(f"Error in South data processing: {e}")
            # Removed mock data fallback
            # print("Generating mock processed data instead.")
            # table_south = create_mock_south_table()
            # return {
            #     'table_south': table_south
            # }
            # Re-raise the exception or return an empty dict/None
            # depending on desired error handling
            print("South data processing failed. Returning empty result.")
            return {'table_south': pd.DataFrame()} # Return empty dataframe
            
    except Exception as e:
        raise Exception(f"Error in South data processing setup: {e}")


if __name__ == "__main__":
    # Make sure processed directory exists
    # (DATA_DIR / 'processed').mkdir(exist_ok=True) # This is now done in process_south_data
    
    # Process Southern data
    result = process_south_data()
    print(f"Southern data processing complete. Processed {len(result['table_south'])} records.") 
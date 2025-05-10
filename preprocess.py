#!/usr/bin/env python3
import yaml
import pandas as pd
import numpy as np
import logging
import argparse
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Process timber price data with configurable aggregation levels.')
    
    # Config file
    parser.add_argument('--config', type=str, default='price_config.yml', 
                        help='Path to the configuration YAML file')
    
    # Time levels
    parser.add_argument('--time-level', type=str, choices=['Year', 'Quarter', 'All', 'None'], default='All',
                        help='Time aggregation level')
    
    # Spatial levels
    parser.add_argument('--spatial-level', type=str, choices=['Region', 'State', 'Area', 'All', 'None'], default='All',
                        help='Spatial aggregation level')
    
    # Wood type options
    parser.add_argument('--wood-type', type=str, choices=['softwood', 'hardwood', 'Both', 'None'], default='Both',
                        help='Wood type to process')
    
    # Aggregation methods
    parser.add_argument('--agg-method', type=str, choices=['mean', 'sum', 'both'], default='mean',
                        help='Aggregation method to apply')
    
    return parser.parse_args()

def load_config(config_path="price_config.yml"):
    """Load the YAML configuration file."""
    logger.info(f"Loading configuration from {config_path}")
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        raise

def aggregate_time(df, time_config, level='All'):
    """Aggregate data by time dimensions."""
    if not time_config.get('enabled', False):
        return df
    
    logger.info(f"Performing time-based aggregation at level: {level}")
    
    # Filter time variables based on the selected level
    if level == 'All':
        time_vars = sorted(time_config['variables'], key=lambda x: x['level'])
    elif level == 'None':
        return df
    else:
        time_vars = [var for var in time_config['variables'] if var['name'] == level]
        if not time_vars:
            logger.warning(f"Time level '{level}' not found in configuration")
            return df
    
    agg_methods = time_config.get('aggregation_methods', ['mean'])
    
    # Create time-based grouping columns
    time_columns = [var['name'] for var in time_vars]
    
    # Group by time variables and apply aggregation
    value_columns = df.columns.difference(time_columns)
    agg_dict = {col: agg_methods for col in value_columns if pd.api.types.is_numeric_dtype(df[col])}
    
    if agg_dict:
        df_agg = df.groupby(time_columns, as_index=False).agg(agg_dict)
        logger.info(f"Aggregated data by time dimensions: {time_columns}")
        return df_agg
    
    return df

def aggregate_spatial(df, spatial_config, level='All'):
    """Aggregate data by spatial dimensions."""
    if not spatial_config.get('enabled', False):
        return df
    
    logger.info(f"Performing spatial-based aggregation at level: {level}")
    
    # Filter spatial variables based on the selected level
    if level == 'All':
        spatial_vars = sorted(spatial_config['variables'], key=lambda x: x['level'])
    elif level == 'None':
        return df
    else:
        spatial_vars = [var for var in spatial_config['variables'] if var['name'] == level]
        if not spatial_vars:
            logger.warning(f"Spatial level '{level}' not found in configuration")
            return df
    
    agg_methods = spatial_config.get('aggregation_methods', ['mean'])
    
    # Create spatial-based grouping columns
    spatial_columns = [var['name'] for var in spatial_vars if var['name'] in df.columns]
    
    # Group by spatial variables and apply aggregation
    value_columns = df.columns.difference(spatial_columns)
    agg_dict = {col: agg_methods for col in value_columns if pd.api.types.is_numeric_dtype(df[col])}
    
    if agg_dict and spatial_columns:
        df_agg = df.groupby(spatial_columns, as_index=False).agg(agg_dict)
        logger.info(f"Aggregated data by spatial dimensions: {spatial_columns}")
        return df_agg
    
    return df

def aggregate_wood_type(df, wood_type_config, wood_type='Both', agg_method='mean'):
    """Aggregate data by wood type."""
    if not wood_type_config.get('enabled', False):
        return df
    
    logger.info(f"Performing wood type aggregation for: {wood_type}, method: {agg_method}")
    
    # Filter wood types based on selection
    if wood_type == 'Both':
        wood_vars = wood_type_config['variables']
    elif wood_type == 'None':
        return df
    else:
        wood_vars = [var for var in wood_type_config['variables'] if var['name'] == wood_type]
        if not wood_vars:
            logger.warning(f"Wood type '{wood_type}' not found in configuration")
            return df
    
    # Determine which aggregation methods to use
    if agg_method == 'both':
        methods = ['mean', 'sum']
    else:
        methods = [agg_method]
    
    # Create new columns for each wood type by aggregating corresponding columns
    for wood_var in wood_vars:
        wood_name = wood_var['name']
        wood_columns = [col for col in wood_var['columns'] if col in df.columns]
        
        if wood_columns:
            logger.info(f"Creating aggregate column for {wood_name} from {wood_columns}")
            
            # For each aggregation method, create a new column
            for method in methods:
                if method == 'mean':
                    df[f"{wood_name}_mean"] = df[wood_columns].mean(axis=1)
                elif method == 'sum':
                    df[f"{wood_name}_sum"] = df[wood_columns].sum(axis=1)
    
    return df

def apply_cross_dimensional_aggregation(df, agg_config, args):
    """Apply aggregation across multiple dimensions based on command line arguments."""
    if not agg_config['cross_dimensional'].get('enabled', False):
        return df
    
    logger.info("Applying cross-dimensional aggregation")
    
    result_df = df.copy()
    agg_order = agg_config['cross_dimensional']['order']
    
    for dimension in agg_order:
        if dimension == 'temporal' and 'time' in agg_config:
            result_df = aggregate_time(result_df, agg_config['time'], args.time_level)
        elif dimension == 'spatial' and 'spatial' in agg_config:
            result_df = aggregate_spatial(result_df, agg_config['spatial'], args.spatial_level)
        elif dimension == 'wood_type' and 'wood_type' in agg_config:
            result_df = aggregate_wood_type(result_df, agg_config['wood_type'], args.wood_type, args.agg_method)
    
    logger.info(f"Completed cross-dimensional aggregation with final shape {result_df.shape}")
    return result_df

def main():
    """Main processing function."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Load configuration
        config = load_config(args.config)
        
        # Load data
        df = load_data(config)
        
        # Clean data
        df = clean_data(df, config)
        
        # Apply aggregations if enabled
        if 'aggregation' in config and config['aggregation'].get('enabled', False):
            # First apply wood type aggregation to create the necessary columns
            if 'wood_type' in config['aggregation']:
                df = aggregate_wood_type(df, config['aggregation']['wood_type'], args.wood_type, args.agg_method)
            
            # Then apply cross-dimensional aggregation if specified
            if 'cross_dimensional' in config['aggregation']:
                df = apply_cross_dimensional_aggregation(df, config['aggregation'], args)
            
            # Generate output filename based on selected options
            base_path = Path(config['output']['file_path'])
            filename_parts = []
            
            if args.time_level not in ('All', 'None'):
                filename_parts.append(args.time_level)
            if args.spatial_level not in ('All', 'None'):
                filename_parts.append(args.spatial_level)
            if args.wood_type not in ('Both', 'None'):
                filename_parts.append(args.wood_type)
            
            if filename_parts:
                new_filename = f"{base_path.stem}_{'-'.join(filename_parts)}{base_path.suffix}"
                config['output']['file_path'] = str(base_path.parent / new_filename)
                logger.info(f"Modified output filename: {config['output']['file_path']}")
        
        # Save processed data
        save_data(df, config)
        
        logger.info("Data processing completed successfully")
        
    except Exception as e:
        logger.error(f"Error in data processing: {e}")
        raise

if __name__ == "__main__":
    main() 
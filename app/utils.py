import pandas as pd
import yaml
from pathlib import Path
import plotly.express as px
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Data Cleaning and Transformation Functions
def clean_column_names(df):
    """Clean column names by removing spaces and special characters."""
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace('/', '_').str.replace('-', '_')
    return df

def extract_year_quarter(df):
    """Extract year and quarter from date columns if available."""
    if 'Year' in df.columns and 'Quarter' in df.columns:
        df['YearQuarter'] = df['Year'].astype(str) + '-Q' + df['Quarter'].astype(str)
    return df

def filter_price_columns(df):
    """Extract only columns that contain price data (typically have product names)."""
    non_price_cols = ['Year', 'Quarter', 'YearQuarter', 'State', 'Area', 'Region', 'ReportType', 'Units']
    price_cols = [col for col in df.columns if col not in non_price_cols]
    return price_cols

def calculate_average_prices(df, group_cols, price_cols):
    """Calculate average prices by grouping columns."""
    return df.groupby(group_cols)[price_cols].mean().reset_index()

def extract_species_info(df):
    """Extract and clean species information."""
    if 'Species' in df.columns:
        df['Species'] = df['Species'].str.strip().str.title()
    return df

# Visualization Functions
def create_time_series_plot(df, x_col, y_col, color_col, facet_col=None, title=None, labels=None):
    """Create a time series plot using Plotly."""
    fig = px.line(
        df, 
        x=x_col, 
        y=y_col, 
        color=color_col,
        facet_col=facet_col,
        title=title,
        labels=labels or {}
    )
    
    # Customize layout
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def create_bar_chart(df, x_col, y_col, color_col=None, barmode="group", title=None, labels=None):
    """Create a bar chart using Plotly."""
    fig = px.bar(
        df, 
        x=x_col, 
        y=y_col, 
        color=color_col,
        barmode=barmode,
        title=title,
        labels=labels or {}
    )
    
    # Customize layout
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def prepare_biomass_summary(df):
    """Prepare biomass data summary."""
    if df is not None and not df.empty:
        summary = df.describe().T
        return summary
    return None

# Preprocessing Functions
def load_preprocessing_config(config_path="price_config.yml"):
    """Load the YAML configuration file for preprocessing."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def load_raw_data(config):
    """Load raw data according to configuration."""
    if not config or 'input' not in config:
        return None
        
    input_config = config['input']
    file_path = input_config['file_path']
    file_type = input_config['file_type']
    encoding = input_config.get('encoding', 'utf-8')
    
    try:
        if file_type == 'csv':
            df = pd.read_csv(file_path, encoding=encoding)
        elif file_type == 'excel':
            sheet_name = input_config.get('sheet_name')
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            logger.error(f"Unsupported file type: {file_type}")
            return None
        
        return df
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return None

def clean_preprocessing_data(df, config):
    """Clean data according to configuration."""
    if df is None or not config or 'cleaning' not in config:
        return df
    
    cleaning_config = config['cleaning']
    
    # Drop specified columns
    if 'drop_columns' in cleaning_config:
        drop_cols = cleaning_config['drop_columns']
        df = df.drop(columns=[col for col in drop_cols if col in df.columns], errors='ignore')
    
    return df

def aggregate_time_dimension(df, time_config, level='All'):
    """Aggregate data by time dimensions."""
    if df is None or not time_config or not time_config.get('enabled', False):
        return df
    
    # Filter time variables based on the selected level
    if level == 'All':
        time_vars = sorted(time_config['variables'], key=lambda x: x['level'])
    elif level == 'None':
        return df
    else:
        time_vars = [var for var in time_config['variables'] if var['name'] == level]
        if not time_vars:
            return df
    
    agg_methods = time_config.get('aggregation_methods', ['mean'])
    
    # Create time-based grouping columns
    time_columns = [var['name'] for var in time_vars]
    
    # Group by time variables and apply aggregation
    value_columns = df.columns.difference(time_columns)
    agg_dict = {col: agg_methods for col in value_columns if pd.api.types.is_numeric_dtype(df[col])}
    
    if agg_dict:
        df_agg = df.groupby(time_columns, as_index=False).agg(agg_dict)
        return df_agg
    
    return df

def aggregate_spatial_dimension(df, spatial_config, level='All'):
    """Aggregate data by spatial dimensions."""
    if df is None or not spatial_config or not spatial_config.get('enabled', False):
        return df
    
    # Filter spatial variables based on the selected level
    if level == 'All':
        spatial_vars = sorted(spatial_config['variables'], key=lambda x: x['level'])
    elif level == 'None':
        return df
    else:
        spatial_vars = [var for var in spatial_config['variables'] if var['name'] == level]
        if not spatial_vars:
            return df
    
    agg_methods = spatial_config.get('aggregation_methods', ['mean'])
    
    # Create spatial-based grouping columns
    spatial_columns = [var['name'] for var in spatial_vars if var['name'] in df.columns]
    
    # Group by spatial variables and apply aggregation
    value_columns = df.columns.difference(spatial_columns)
    agg_dict = {col: agg_methods for col in value_columns if pd.api.types.is_numeric_dtype(df[col])}
    
    if agg_dict and spatial_columns:
        df_agg = df.groupby(spatial_columns, as_index=False).agg(agg_dict)
        return df_agg
    
    return df

def aggregate_wood_type_dimension(df, wood_type_config, wood_type='Both', agg_method='mean'):
    """Aggregate data by wood type."""
    if df is None or not wood_type_config or not wood_type_config.get('enabled', False):
        return df
    
    # Filter wood types based on selection
    if wood_type == 'Both':
        wood_vars = wood_type_config['variables']
    elif wood_type == 'None':
        return df
    else:
        wood_vars = [var for var in wood_type_config['variables'] if var['name'] == wood_type]
        if not wood_vars:
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
            # For each aggregation method, create a new column
            for method in methods:
                if method == 'mean':
                    df[f"{wood_name}_mean"] = df[wood_columns].mean(axis=1)
                elif method == 'sum':
                    df[f"{wood_name}_sum"] = df[wood_columns].sum(axis=1)
    
    return df

def preprocess_data(time_level='All', spatial_level='All', wood_type='Both', agg_method='mean', config_path='price_config.yml'):
    """Main function to preprocess data based on user selections."""
    # Load configuration
    config = load_preprocessing_config(config_path)
    if not config:
        return None, "Error loading configuration"
    
    # Load raw data
    df = load_raw_data(config)
    if df is None:
        return None, "Error loading raw data"
    
    # Clean data
    df = clean_preprocessing_data(df, config)
    
    # Apply aggregations if enabled
    if 'aggregation' in config and config['aggregation'].get('enabled', False):
        # First apply wood type aggregation to create the necessary columns
        if 'wood_type' in config['aggregation']:
            df = aggregate_wood_type_dimension(df, config['aggregation']['wood_type'], wood_type, agg_method)
        
        # Apply time aggregation
        if 'time' in config['aggregation']:
            df = aggregate_time_dimension(df, config['aggregation']['time'], time_level)
        
        # Apply spatial aggregation
        if 'spatial' in config['aggregation']:
            df = aggregate_spatial_dimension(df, config['aggregation']['spatial'], spatial_level)
    
    # Generate output filename based on selected options
    base_path = Path(config['output']['file_path'])
    filename_parts = []
    
    if time_level not in ('All', 'None'):
        filename_parts.append(time_level)
    if spatial_level not in ('All', 'None'):
        filename_parts.append(spatial_level)
    if wood_type not in ('Both', 'None'):
        filename_parts.append(wood_type)
    
    if filename_parts:
        output_filename = f"{base_path.stem}_{'-'.join(filename_parts)}{base_path.suffix}"
    else:
        output_filename = base_path.name
    
    # Save processed data if needed
    output_path = base_path.parent / output_filename
    try:
        df.to_csv(output_path, index=False)
        save_status = f"Data saved to {output_path}"
    except Exception as e:
        save_status = f"Error saving data: {e}"
    
    return df, save_status 
import pandas as pd
import yaml
from pathlib import Path
import plotly.express as px
import logging
import folium
import json
import requests

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

def create_state_map(data_dict, map_type="prices"):
    """
    Create a Folium map showing state-level data for the Southern US region.
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary of dataframes (prices, species, etc.)
    map_type : str
        Type of data to display (prices, species, bio_merch, bio_premerch)
        
    Returns:
    --------
    folium.Map object or None if data is not available
    """
    # Define the 13 southern states with standardized names
    southern_states = {
        "Alabama": ["Alabama", "AL", "01", "01 Alabama"],
        "Arkansas": ["Arkansas", "AR", "05", "05 Arkansas"],
        "Florida": ["Florida", "FL", "12", "12 Florida"],
        "Georgia": ["Georgia", "GA", "13", "13 Georgia"],
        "Louisiana": ["Louisiana", "LA", "22", "22 Louisiana"], 
        "Mississippi": ["Mississippi", "MS", "28", "28 Mississippi"],
        "North Carolina": ["North Carolina", "NC", "37", "37 North Carolina"],
        "South Carolina": ["South Carolina", "SC", "45", "45 South Carolina"],
        "Tennessee": ["Tennessee", "TN", "47", "47 Tennessee"],
        "Virginia": ["Virginia", "VA", "51", "51 Virginia"]
    }
    
    # Center of the Southern US region
    southern_center = [32.7, -83.5]  # Approximate center of the Southern states
    
    # Create a base map centered on the Southern region
    m = folium.Map(location=southern_center, zoom_start=5, tiles="CartoDB positron")
    
    # Dictionary to store detailed data by state for tooltips
    state_details = {}
    
    # Check which data to display
    if map_type == "prices" and data_dict["prices"] is not None:
        df = data_dict["prices"].copy()
        if "State" not in df.columns:
            return None
        
        # Function to normalize state names
        def normalize_state(state_str):
            for std_name, variants in southern_states.items():
                if state_str in variants:
                    return std_name
            return state_str
        
        # Normalize state names 
        df["State"] = df["State"].apply(normalize_state)
        
        # Filter for southern states only
        df = df[df["State"].isin(list(southern_states.keys()))]
        if df.empty:
            return None
            
        # Aggregate price data by state (mean of all price columns)
        price_cols = filter_price_columns(df)
        if not price_cols:
            return None
            
        # Make sure we only use numeric columns for calculation
        numeric_price_cols = []
        for col in price_cols:
            # Convert to numeric, coercing non-numeric values to NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if df[col].notna().any():  # Only include columns with at least some valid numbers
                numeric_price_cols.append(col)
        
        if not numeric_price_cols:
            return None
            
        # Create a new column with the mean of all price columns
        df["mean_price"] = df[numeric_price_cols].mean(axis=1)
        
        # Group by state and calculate mean
        state_data = df.groupby("State")["mean_price"].mean().reset_index()
        state_data.columns = ["state", "value"]
        
        # Create detailed data for tooltips
        for state in state_data["state"]:
            state_df = df[df["State"] == state]
            
            # Calculate additional metrics
            details = {
                "Mean Price": f"${state_data.loc[state_data['state'] == state, 'value'].values[0]:.2f}/ton",
                "Data Points": len(state_df),
                "Year Range": f"{state_df['Year'].min()}-{state_df['Year'].max()}"
            }
            
            # Format Products list with line breaks
            product_list = [col.replace('_', ' ') for col in numeric_price_cols[:5]]
            if len(numeric_price_cols) > 5:
                product_list.append(f"and {len(numeric_price_cols)-5} more")
            details["Products"] = "<br>".join(product_list)
            
            # Add top 3 most expensive products with line breaks
            product_means = {col: state_df[col].mean() for col in numeric_price_cols}
            sorted_products = sorted(product_means.items(), key=lambda x: x[1], reverse=True)[:3]
            top_products = [f"{p[0].replace('_', ' ')}: ${p[1]:.2f}" for p in sorted_products]
            details["Top Products"] = "<br>".join(top_products)
            
            state_details[state] = details
        
        # Title and description
        title = "Average Timber Prices by Southern State"
        legend_name = "Avg. Price ($/ton)"
        
    elif map_type == "species" and data_dict["species"] is not None:
        df = data_dict["species"].copy()
        
        # Check if GRP2 column exists (state information)
        if "GRP2" in df.columns:
            # Extract state name from GRP2 column which has format like "`0001 01 Alabama"
            def extract_state(grp2_str):
                if not isinstance(grp2_str, str):
                    return None
                    
                # Remove backticks
                clean_str = grp2_str.replace('`', '')
                
                # Try to extract state name
                for std_name, variants in southern_states.items():
                    for variant in variants:
                        if variant in clean_str or std_name in clean_str:
                            return std_name
                return None
            
            # Extract state from GRP2 column
            df["State"] = df["GRP2"].apply(extract_state)
        
        if "State" not in df.columns or "ESTIMATE" not in df.columns:
            return None
        
        # Filter for southern states only
        df = df[df["State"].isin(list(southern_states.keys()))]
        if df.empty:
            return None
            
        # Convert ESTIMATE to numeric, handling empty strings
        df["ESTIMATE"] = pd.to_numeric(df["ESTIMATE"], errors='coerce')
        
        # Group by state and sum estimates
        state_data = df.groupby("State")["ESTIMATE"].sum().reset_index()
        state_data.columns = ["state", "value"]
        
        # Create detailed data for tooltips
        for state in state_data["state"]:
            state_df = df[df["State"] == state]
            
            # Count unique species
            if "Species" in state_df.columns:
                unique_species = state_df["Species"].nunique()
                top_species = state_df.groupby("Species")["ESTIMATE"].sum().sort_values(ascending=False).head(3)
                
                details = {
                    "Total Estimate": f"{state_data.loc[state_data['state'] == state, 'value'].values[0]:,.0f}",
                    "Unique Species": unique_species,
                    "Data Points": len(state_df),
                    "Top Species": ", ".join([f"{sp}: {val:,.0f}" for sp, val in top_species.items()])
                }
            else:
                details = {
                    "Total Estimate": f"{state_data.loc[state_data['state'] == state, 'value'].values[0]:,.0f}",
                    "Data Points": len(state_df)
                }
            
            state_details[state] = details
        
        # Title and description
        title = "Species Estimates by Southern State"
        legend_name = "Total Estimate"
        
    elif map_type == "bio_merch" and data_dict["bio_merch"] is not None:
        df = data_dict["bio_merch"].copy()
        if "STATENM" not in df.columns:
            return None
            
        # Normalize state names
        def normalize_state(state_str):
            for std_name, variants in southern_states.items():
                if state_str in variants or std_name in state_str:
                    return std_name
            return state_str
            
        # Normalize state name
        df["State"] = df["STATENM"].apply(normalize_state)
            
        # Filter for southern states only
        df = df[df["State"].isin(list(southern_states.keys()))]
        if df.empty:
            return None
            
        # Count records by state
        state_data = df.groupby("State").size().reset_index()
        state_data.columns = ["state", "value"]
        
        # Create detailed data for tooltips
        for state in state_data["state"]:
            state_df = df[df["State"] == state]
            
            # Calculate additional metrics
            numeric_cols = state_df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                details = {
                    "Data Points": f"{state_data.loc[state_data['state'] == state, 'value'].values[0]:,}",
                    "Counties": state_df["COUNTYCD"].nunique() if "COUNTYCD" in state_df.columns else "N/A"
                }
                
                if "FIAPROTYPCD" in state_df.columns:
                    details["Forest Types"] = state_df["FIAPROTYPCD"].nunique()
            else:
                details = {
                    "Data Points": f"{state_data.loc[state_data['state'] == state, 'value'].values[0]:,}"
                }
            
            state_details[state] = details
        
        # Title and description
        title = "Merchantable Biomass Data Points by Southern State"
        legend_name = "Data Points"
        
    elif map_type == "bio_premerch" and data_dict["bio_premerch"] is not None:
        df = data_dict["bio_premerch"].copy()
        if "STATENM" not in df.columns:
            return None
            
        # Normalize state names
        def normalize_state(state_str):
            for std_name, variants in southern_states.items():
                if state_str in variants or std_name in state_str:
                    return std_name
            return state_str
            
        # Normalize state name
        df["State"] = df["STATENM"].apply(normalize_state)
            
        # Filter for southern states only
        df = df[df["State"].isin(list(southern_states.keys()))]
        if df.empty:
            return None
            
        # Count records by state
        state_data = df.groupby("State").size().reset_index()
        state_data.columns = ["state", "value"]
        
        # Create detailed data for tooltips
        for state in state_data["state"]:
            state_df = df[df["State"] == state]
            
            # Calculate additional metrics
            numeric_cols = state_df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                details = {
                    "Data Points": f"{state_data.loc[state_data['state'] == state, 'value'].values[0]:,}",
                    "Counties": state_df["COUNTYCD"].nunique() if "COUNTYCD" in state_df.columns else "N/A"
                }
                
                if "FIAPROTYPCD" in state_df.columns:
                    details["Forest Types"] = state_df["FIAPROTYPCD"].nunique()
            else:
                details = {
                    "Data Points": f"{state_data.loc[state_data['state'] == state, 'value'].values[0]:,}"
                }
            
            state_details[state] = details
        
        # Title and description
        title = "Pre-merchantable Biomass Data Points by Southern State"
        legend_name = "Data Points"
        
    else:
        return None
    
    # Load GeoJSON data for US states
    # Download the GeoJSON data for US states
    geojson_url = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/us-states.json"
    response = requests.get(geojson_url)
    us_states_geojson = json.loads(response.text)
    
    # Filter to only include southern states
    southern_geojson = {
        "type": "FeatureCollection",
        "features": [feature for feature in us_states_geojson["features"] 
                     if feature["properties"]["name"] in southern_states.keys()]
    }
    
    # Create a choropleth map with tooltips
    choropleth = folium.Choropleth(
        geo_data=southern_geojson,
        name="choropleth",
        data=state_data,
        columns=["state", "value"],
        key_on="feature.properties.name",
        fill_color="YlGn",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name=legend_name,
        highlight=True
    ).add_to(m)
    
    # Add a title
    title_html = f'''
        <h3 align="center" style="font-size:16px"><b>{title}</b></h3>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Add tooltips with detailed information
    tooltip_html = {}
    for state, details in state_details.items():
        html = f"<h4>{state}</h4>"
        
        # Get the value used for coloring from state_data
        value_row = state_data[state_data["state"] == state]
        if not value_row.empty:
            raw_value = value_row["value"].values[0]
            
            # Format based on map type
            if map_type == "prices":
                formatted_value = f"<div style='font-size:16px;color:#2c7fb8;font-weight:bold;margin:8px 0;'>${raw_value:.2f}/ton</div>"
            elif map_type == "species":
                formatted_value = f"<div style='font-size:16px;color:#2c7fb8;font-weight:bold;margin:8px 0;'>{raw_value:,.0f}</div>"
            else:
                formatted_value = f"<div style='font-size:16px;color:#2c7fb8;font-weight:bold;margin:8px 0;'>{raw_value:,}</div>"
            
            html += formatted_value
        
        html += "<table style='width:100%;'>"
        for key, value in details.items():
            html += f"<tr><td style='padding:4px;font-weight:bold;'>{key}:</td><td style='padding:4px;'>{value}</td></tr>"
        html += "</table>"
        tooltip_html[state] = html
    
    # Create new GeoJSON with tooltips
    style_function = lambda x: {
        'fillColor': '#00000000',  # Transparent fill
        'color': '#00000000',      # Transparent border
        'fillOpacity': 0.0,
        'weight': 0
    }
    
    # Add tooltip GeoJSON layer - using a different approach
    for feature in southern_geojson["features"]:
        state_name = feature["properties"]["name"]
        if state_name in tooltip_html:
            # Add tooltip HTML directly to the properties
            feature["properties"]["tooltip_html"] = tooltip_html[state_name]
    
    # Create GeoJson layer with tooltips
    folium.GeoJson(
        southern_geojson,
        name="tooltips",
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=["tooltip_html"],
            aliases=[""],
            style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;",
            sticky=True,
            labels=False,
            max_width=300,
        )
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    return m

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
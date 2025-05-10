import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional, Union

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Clean column names by stripping whitespace and special characters."""
    df.columns = [col.strip() for col in df.columns]
    return df

def extract_year_quarter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a year-quarter column for time series plotting.
    
    Args:
        df: DataFrame with 'Year' and 'Quarter' columns
        
    Returns:
        DataFrame with an additional 'YearQuarter' column
    """
    if 'Year' in df.columns and 'Quarter' in df.columns:
        df = df.copy()
        # Handle different formats of Quarter column (Q1, 1, etc.)
        if df['Quarter'].dtype == 'object':
            df['Quarter'] = df['Quarter'].str.replace('Q', '')
        df['YearQuarter'] = df['Year'].astype(str) + '-Q' + df['Quarter'].astype(str)
    return df

def filter_price_columns(df: pd.DataFrame) -> List[str]:
    """
    Get a list of columns that appear to contain price data.
    
    Args:
        df: DataFrame with price data
        
    Returns:
        List of column names that likely contain price data
    """
    return [col for col in df.columns if any(x in col for x in ['Pine', 'Oak', 'Hardwood'])]

def calculate_average_prices(
    df: pd.DataFrame, 
    group_cols: List[str], 
    price_cols: List[str]
) -> pd.DataFrame:
    """
    Calculate average prices grouped by specified columns.
    
    Args:
        df: DataFrame with price data
        group_cols: Columns to group by (e.g., ['Year', 'State'])
        price_cols: Price columns to average
        
    Returns:
        DataFrame with average prices
    """
    return df.groupby(group_cols)[price_cols].mean().reset_index()

def extract_species_info(species_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract species information from the species dataset.
    
    Args:
        species_df: DataFrame with species data
        
    Returns:
        DataFrame with extracted species and state information
    """
    df = species_df.copy()
    
    # Extract species name from GRP1 column
    if "GRP1" in df.columns:
        df["Species"] = df["GRP1"].str.extract(r'SPCD \d+ - (.+) \(')
    
    # Extract state name from GRP2 column
    if "GRP2" in df.columns:
        df["State"] = df["GRP2"].str.extract(r'\d+ (.+)')
    
    return df

def create_time_series_plot(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str,
    facet_col: Optional[str] = None,
    title: str = "Time Series Plot",
    labels: Optional[Dict[str, str]] = None
) -> go.Figure:
    """
    Create a time series plot using Plotly Express.
    
    Args:
        df: DataFrame with time series data
        x_col: Column to use for x-axis
        y_col: Column to use for y-axis
        color_col: Column to use for color
        facet_col: Optional column to use for faceting
        title: Plot title
        labels: Dictionary of axis labels
        
    Returns:
        Plotly figure object
    """
    fig = px.line(
        df, 
        x=x_col, 
        y=y_col, 
        color=color_col,
        facet_col=facet_col,
        facet_col_wrap=2 if facet_col else None,
        title=title,
        labels=labels or {},
        height=500
    )
    
    fig.update_xaxes(tickangle=45)
    return fig

def create_bar_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    barmode: str = "group",
    title: str = "Bar Chart",
    labels: Optional[Dict[str, str]] = None
) -> go.Figure:
    """
    Create a bar chart using Plotly Express.
    
    Args:
        df: DataFrame with bar chart data
        x_col: Column to use for x-axis
        y_col: Column to use for y-axis
        color_col: Optional column to use for color
        barmode: Bar mode ('group', 'stack', etc.)
        title: Plot title
        labels: Dictionary of axis labels
        
    Returns:
        Plotly figure object
    """
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        color=color_col,
        barmode=barmode,
        title=title,
        labels=labels or {}
    )
    
    return fig

def prepare_biomass_summary(
    df: pd.DataFrame,
    county_col: str = "COUNTYNM",
    species_col: str = "SPCLASS"
) -> pd.DataFrame:
    """
    Prepare biomass summary by county and species class.
    
    Args:
        df: DataFrame with biomass data
        county_col: Column name for counties
        species_col: Column name for species class
        
    Returns:
        DataFrame with biomass summary
    """
    return df.groupby([county_col, species_col]).size().reset_index(name="Count") 
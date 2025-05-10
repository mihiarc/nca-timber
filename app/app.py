import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
import os
from utils import (
    clean_column_names, 
    extract_year_quarter, 
    filter_price_columns,
    calculate_average_prices,
    extract_species_info,
    create_time_series_plot,
    create_bar_chart,
    prepare_biomass_summary
)

# Set page config
st.set_page_config(
    page_title="NCA Timber Data Explorer",
    page_icon="🌲",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 1rem;
    }
    h1, h2, h3 {
        color: #2c6e49;
    }
    </style>
""", unsafe_allow_html=True)

# App title and description
st.title("🌲 NCA Timber Data Explorer")
st.markdown("Explore timber prices, species, and inventory data across the Southern United States")

# Data loading function with caching
@st.cache_data
def load_data():
    data = {
        "prices": pd.read_csv("data/prices.csv"),
        "species": pd.read_csv("data/south_species.csv"),
        "bio_merch": pd.read_csv("data/south_bio_merch.csv"),
        "bio_premerch": pd.read_csv("data/south_bio_premerch.csv")
    }
    
    # Clean column names for all datasets
    for key in data:
        data[key] = clean_column_names(data[key])
    
    # Extract year-quarter from prices
    data["prices"] = extract_year_quarter(data["prices"])
    
    # Extract species info
    data["species"] = extract_species_info(data["species"])
    
    return data

# Load data with progress indicator
with st.spinner("Loading data..."):
    try:
        data = load_data()
        st.success("Data loaded successfully!")
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page",
    ["Overview", "Price Analysis", "Species Analysis", "Biomass Explorer"]
)

# Overview page
if page == "Overview":
    st.header("Dataset Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Available Datasets")
        for name, df in data.items():
            st.markdown(f"**{name.capitalize()}**: {df.shape[0]} rows × {df.shape[1]} columns")
    
    with col2:
        st.subheader("Data Preview")
        dataset = st.selectbox("Select a dataset to preview", list(data.keys()))
        st.dataframe(data[dataset].head(10))

    # Basic dataset statistics
    st.subheader("Dataset Information")
    tab1, tab2, tab3, tab4 = st.tabs(["Prices", "Species", "Bio Merch", "Bio Premerch"])
    
    with tab1:
        st.markdown("**Timber prices across states, areas and periods**")
        st.markdown("Key variables:")
        st.markdown("- Year, Quarter: Time period")
        st.markdown("- State, Area: Geographic location")
        st.markdown("- Price columns: Various timber products and their prices")
    
    with tab2:
        st.markdown("**Species data across southern states**")
        if "ESTIMATE" in data["species"].columns:
            total_species = data["species"]["ESTIMATE"].sum()
            st.metric("Total Species Estimate", f"{total_species:,.0f}")
    
    with tab3:
        st.markdown("**Biomass data for merchantable timber**")
        st.text("Large dataset with detailed biomass information by county and species")
    
    with tab4:
        st.markdown("**Biomass data for pre-merchantable timber**")
        st.text("Detailed pre-merchantable biomass information")

# Price Analysis page
elif page == "Price Analysis":
    st.header("Timber Price Analysis")
    
    # Data preparation for pricing
    prices_df = data["prices"]
    
    # Get unique states, products and periods
    states = sorted(prices_df["State"].unique())
    
    # Filter by price columns
    price_columns = filter_price_columns(prices_df)
    
    # Add filters
    col1, col2 = st.columns(2)
    
    with col1:
        selected_states = st.multiselect("Select States", states, default=states[:3])
    
    with col2:
        selected_products = st.multiselect("Select Products", price_columns, 
                                      default=price_columns[:3])
    
    # Filter data
    filtered_df = prices_df[prices_df["State"].isin(selected_states)]
    
    # Additional filters
    year_range = st.slider("Select Year Range", 
                         int(filtered_df["Year"].min()), 
                         int(filtered_df["Year"].max()), 
                         (int(filtered_df["Year"].min()), int(filtered_df["Year"].max())))
    
    filtered_df = filtered_df[(filtered_df["Year"] >= year_range[0]) & 
                             (filtered_df["Year"] <= year_range[1])]
    
    # Time-series plot
    st.subheader("Price Trends Over Time")
    
    # Group by year and state, calculate average prices
    if not filtered_df.empty and selected_products:
        # Group by year-quarter and state, calculate average price for each product
        avg_prices = calculate_average_prices(
            filtered_df, 
            ["YearQuarter", "State"], 
            selected_products
        )
        
        # Reshape for plotting
        melted_df = pd.melt(avg_prices, id_vars=["YearQuarter", "State"], 
                          value_vars=selected_products, 
                          var_name="Product", value_name="Price")
        
        # Create interactive plot
        fig = create_time_series_plot(
            melted_df, 
            x_col="YearQuarter", 
            y_col="Price", 
            color_col="Product", 
            facet_col="State",
            title="Timber Price Trends by State and Product",
            labels={"YearQuarter": "Year-Quarter", "Price": "Price ($/ton)"}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add a price comparison bar chart
        st.subheader("Average Price Comparison")
        avg_by_state_product = melted_df.groupby(["State", "Product"])["Price"].mean().reset_index()
        
        fig2 = create_bar_chart(
            avg_by_state_product, 
            x_col="Product", 
            y_col="Price", 
            color_col="State",
            barmode="group", 
            title="Average Price by State and Product",
            labels={"Price": "Average Price ($/ton)"}
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        
        # Show detailed data
        st.subheader("Filtered Price Data")
        st.dataframe(filtered_df[["Year", "Quarter", "State", "Area"] + selected_products])
    else:
        st.warning("Please select at least one product and ensure data is available for the selected filters.")

# Species Analysis page
elif page == "Species Analysis":
    st.header("Species Analysis")
    
    species_df = data["species"]
    
    # Filter out rows with missing data
    species_df = species_df.dropna(subset=["ESTIMATE"])
    
    # Group by species and state, calculate total estimates
    if "Species" in species_df.columns and "State" in species_df.columns:
        species_summary = species_df.groupby(["Species", "State"])["ESTIMATE"].sum().reset_index()
        
        # Top species by state
        st.subheader("Species Distribution by State")
        
        # Filter options
        states = sorted(species_summary["State"].dropna().unique())
        selected_state = st.selectbox("Select a State", states)
        
        # Filter by state
        state_data = species_summary[species_summary["State"] == selected_state]
        
        # Sort by estimate
        state_data = state_data.sort_values("ESTIMATE", ascending=False)
        
        # Plot top species
        top_n = st.slider("Number of top species to show", 5, 20, 10)
        top_species = state_data.head(top_n)
        
        fig = create_bar_chart(
            top_species, 
            x_col="Species", 
            y_col="ESTIMATE",
            title=f"Top {top_n} Species in {selected_state}",
            labels={"ESTIMATE": "Estimate", "Species": "Species"}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Species comparison across states
        st.subheader("Species Comparison Across States")
        
        # Get top overall species
        top_species_overall = species_summary.groupby("Species")["ESTIMATE"].sum().sort_values(ascending=False)
        top_species_list = top_species_overall.head(10).index.tolist()
        
        selected_species = st.multiselect("Select Species to Compare", top_species_list, default=top_species_list[:3])
        
        # Filter data for selected species
        species_comparison = species_summary[species_summary["Species"].isin(selected_species)]
        
        # Create comparison plot
        if not species_comparison.empty:
            fig2 = create_bar_chart(
                species_comparison, 
                x_col="State", 
                y_col="ESTIMATE", 
                color_col="Species",
                title="Species Comparison Across States",
                labels={"ESTIMATE": "Estimate", "State": "State"},
                barmode="group"
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("Please select at least one species to compare.")
    else:
        st.error("Required columns not found in the species data.")

# Biomass Explorer page
elif page == "Biomass Explorer":
    st.header("Biomass Data Explorer")
    
    # Select which biomass dataset to explore
    biomass_type = st.radio("Select Biomass Type", ["Merchantable", "Pre-merchantable"])
    
    if biomass_type == "Merchantable":
        df = data["bio_merch"]
        title = "Merchantable Biomass"
    else:
        df = data["bio_premerch"]
        title = "Pre-merchantable Biomass"
    
    st.subheader(f"{title} Data Sample")
    st.dataframe(df.head())
    
    # Extract state and county information
    if "STATENM" in df.columns and "COUNTYNM" in df.columns:
        # Get unique states
        states = sorted(df["STATENM"].unique())
        selected_state = st.selectbox(f"Select State for {biomass_type} Analysis", states)
        
        # Filter by state
        state_data = df[df["STATENM"] == selected_state]
        
        # Get counties for the selected state
        counties = sorted(state_data["COUNTYNM"].unique())
        selected_counties = st.multiselect(f"Select Counties in {selected_state}", counties, default=counties[:5])
        
        # Filter by counties
        county_data = state_data[state_data["COUNTYNM"].isin(selected_counties)]
        
        # Group by county and species class
        if "SPCLASS" in county_data.columns:
            # Summarize biomass by county and species class
            biomass_summary = prepare_biomass_summary(county_data)
            
            # Plot biomass distribution
            st.subheader(f"Biomass Distribution in {selected_state} by County and Species Class")
            
            fig = create_bar_chart(
                biomass_summary, 
                x_col="COUNTYNM", 
                y_col="Count", 
                color_col="SPCLASS",
                title=f"{biomass_type} Biomass Distribution",
                labels={"COUNTYNM": "County", "Count": "Count", "SPCLASS": "Species Class"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Species information in the selected counties
        if "SCIENTIFIC_NAME" in county_data.columns:
            species_counts = county_data["SCIENTIFIC_NAME"].value_counts().reset_index()
            species_counts.columns = ["Scientific Name", "Count"]
            
            st.subheader(f"Top Species in Selected Counties of {selected_state}")
            st.dataframe(species_counts.head(10))
    else:
        st.error("Required columns not found in the biomass data.")

# Add footer
st.markdown("---")
st.markdown("NCA Timber Data Explorer © 2023") 
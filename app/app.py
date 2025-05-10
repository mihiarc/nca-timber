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

# Sidebar for navigation and data filters
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page",
    ["Overview", "Price Analysis", "Species Analysis", "Biomass Explorer"]
)

# Data loading function with caching
@st.cache_data
def load_data():
    try:
        # Try to load preprocessed data if it exists
        prices_df = pd.read_csv("data/prices_data.csv") if os.path.exists("data/prices_data.csv") else pd.read_csv("data/raw_prices.csv")
    except Exception as e:
        st.error(f"Error loading price data: {e}")
        prices_df = None
    
    data = {
        "prices": prices_df,
        "species": pd.read_csv("data/south_species.csv") if os.path.exists("data/south_species.csv") else None,
        "bio_merch": pd.read_csv("data/south_bio_merch.csv") if os.path.exists("data/south_bio_merch.csv") else None,
        "bio_premerch": pd.read_csv("data/south_bio_premerch.csv") if os.path.exists("data/south_bio_premerch.csv") else None
    }
    
    # Clean column names for all datasets
    for key in data:
        if data[key] is not None:
            data[key] = clean_column_names(data[key])
    
    # Extract year-quarter from prices
    if data["prices"] is not None:
        data["prices"] = extract_year_quarter(data["prices"])
    
    # Extract species info if available
    if data["species"] is not None:
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

# Get prices data for filter controls
prices_df = data["prices"]

# ----------- Sidebar data filters -----------
st.sidebar.title("Data Filters")

# Only add filters if price data exists
if prices_df is not None:
    # Time filters
    st.sidebar.subheader("Time Filters")
    if "Year" in prices_df.columns:
        years = sorted(prices_df["Year"].unique())
        
        # Option to select all years or specific years
        year_filter_type = st.sidebar.radio("Year Selection", ["All Years", "Specific Years", "Year Range"], index=0)
        
        if year_filter_type == "All Years":
            selected_years = years
            show_year_mean = st.sidebar.checkbox("Show Mean of All Years", value=False)
        elif year_filter_type == "Specific Years":
            selected_years = st.sidebar.multiselect(
                "Select Years", 
                options=years,
                default=years[-3:] if len(years) > 3 else years
            )
            show_year_mean = False
        else:  # Year Range
            min_year, max_year = min(years), max(years)
            year_range = st.sidebar.slider(
                "Select Year Range", 
                min_value=min_year, 
                max_value=max_year,
                value=(max_year-2, max_year) if max_year-min_year >= 2 else (min_year, max_year)
            )
            selected_years = list(range(year_range[0], year_range[1]+1))
            show_year_mean = False
    else:
        selected_years = []
        show_year_mean = False
    
    # Quarter as a checkbox instead of multiselect
    if "Quarter" in prices_df.columns:
        show_quarters = st.sidebar.checkbox("Show Quarterly Data", value=False)
        # If quarters are shown, we don't aggregate by year
        if show_quarters and not show_year_mean:
            selected_quarters = sorted(prices_df["Quarter"].unique())
        else:
            # If quarters are hidden, we'll aggregate by year
            selected_quarters = []
    else:
        show_quarters = False
        selected_quarters = []

    # Spatial filters
    st.sidebar.subheader("Spatial Filters")
    if "State" in prices_df.columns:
        states = sorted(prices_df["State"].unique())
        
        # Option to select all states or specific states
        state_filter_type = st.sidebar.radio("State Selection", ["All States", "Specific States", "Single State with Areas"], index=0)
        
        if state_filter_type == "All States":
            selected_states = states
            show_state_mean = st.sidebar.checkbox("Show Mean of All States", value=False)
            selected_areas = []  # No areas when showing all states
        elif state_filter_type == "Specific States":
            selected_states = st.sidebar.multiselect(
                "Select States", 
                options=states,
                default=states[:3] if len(states) >= 3 else states
            )
            show_state_mean = False
            selected_areas = []  # No areas when showing multiple states
        else:  # Single State with Areas
            # Select just one state when we want to show areas
            selected_state = st.sidebar.selectbox("Select State", options=states)
            selected_states = [selected_state]
            show_state_mean = False
            
            # Show areas for the selected state
            if "Area" in prices_df.columns:
                areas = sorted(prices_df[prices_df["State"] == selected_state]["Area"].unique())
                
                # Area selection options
                area_filter_type = st.sidebar.radio("Area Selection", ["All Areas", "Specific Areas"], index=0)
                
                if area_filter_type == "All Areas":
                    selected_areas = areas
                    show_area_mean = st.sidebar.checkbox("Show Mean of All Areas", value=False)
                else:  # Specific Areas
                    selected_areas = st.sidebar.multiselect(
                        "Select Areas", 
                        options=areas,
                        default=areas[:min(3, len(areas))] if areas else []
                    )
                    show_area_mean = False
            else:
                selected_areas = []
                show_area_mean = False
    else:
        selected_states = []
        selected_areas = []
        show_state_mean = False
        show_area_mean = False

    # Wood type filters
    st.sidebar.subheader("Wood Type Filters")
    
    # Get softwood columns
    softwood_cols = [col for col in prices_df.columns if "Pine" in col]
    # Get hardwood columns
    hardwood_cols = [col for col in prices_df.columns if "Oak" in col or "Hwd" in col or "Hardwood" in col]
    
    # Option to select wood types
    wood_filter_type = st.sidebar.radio("Wood Type Selection", 
                                       ["All Wood Types", "Softwood Only", "Hardwood Only", "Specific Products"], 
                                       index=0)
    
    if wood_filter_type == "All Wood Types":
        selected_cols = softwood_cols + hardwood_cols
        show_wood_mean = st.sidebar.checkbox("Show Mean of All Wood Types", value=False)
    elif wood_filter_type == "Softwood Only":
        selected_cols = softwood_cols
        show_softwood_mean = st.sidebar.checkbox("Show Mean of All Softwood Products", value=False)
        show_wood_mean = False
    elif wood_filter_type == "Hardwood Only":
        selected_cols = hardwood_cols
        show_hardwood_mean = st.sidebar.checkbox("Show Mean of All Hardwood Products", value=False)
        show_wood_mean = False
    else:  # Specific Products
        # Allow selection of specific wood products
        st.sidebar.markdown("**Softwood Products**")
        selected_softwood = st.sidebar.multiselect(
            "Select Softwood Products",
            options=softwood_cols,
            default=softwood_cols[:min(2, len(softwood_cols))] if softwood_cols else []
        )
        
        st.sidebar.markdown("**Hardwood Products**")
        selected_hardwood = st.sidebar.multiselect(
            "Select Hardwood Products",
            options=hardwood_cols,
            default=hardwood_cols[:min(2, len(hardwood_cols))] if hardwood_cols else []
        )
        
        selected_cols = selected_softwood + selected_hardwood
        show_wood_mean = False
        show_softwood_mean = False
        show_hardwood_mean = False

    # Handle case when no wood types are selected
    if not selected_cols:
        st.sidebar.warning("No wood product columns selected!")
    
    # Set aggregation method to mean only
    aggr_method = "mean"

    # Apply filters to create filtered dataframe
    filtered_df = prices_df.copy()
    
    # Apply time filters
    if selected_years:
        filtered_df = filtered_df[filtered_df["Year"].isin(selected_years)]
    if selected_quarters:
        filtered_df = filtered_df[filtered_df["Quarter"].isin(selected_quarters)]
    
    # Apply spatial filters
    if selected_states:
        filtered_df = filtered_df[filtered_df["State"].isin(selected_states)]
    if selected_areas:
        filtered_df = filtered_df[filtered_df["Area"].isin(selected_areas)]
    
    # Handle wood type aggregation if showing means
    if show_wood_mean or (wood_filter_type == "Softwood Only" and show_softwood_mean) or (wood_filter_type == "Hardwood Only" and show_hardwood_mean):
        # Need to create aggregated columns first
        if show_wood_mean:
            # Average across all wood types
            if softwood_cols:
                filtered_df['All_Wood_Mean'] = filtered_df[softwood_cols + hardwood_cols].mean(axis=1)
            # Replace selected_cols to only include the mean column
            selected_cols = ['All_Wood_Mean']
        elif wood_filter_type == "Softwood Only" and show_softwood_mean:
            # Average across all softwood products
            if softwood_cols:
                filtered_df['Softwood_Mean'] = filtered_df[softwood_cols].mean(axis=1)
            # Replace selected_cols to only include the mean column
            selected_cols = ['Softwood_Mean']
        elif wood_filter_type == "Hardwood Only" and show_hardwood_mean:
            # Average across all hardwood products
            if hardwood_cols:
                filtered_df['Hardwood_Mean'] = filtered_df[hardwood_cols].mean(axis=1)
            # Replace selected_cols to only include the mean column
            selected_cols = ['Hardwood_Mean']

    # Apply aggregation if requested
    if show_year_mean or not show_quarters or show_state_mean or show_area_mean or show_wood_mean or (wood_filter_type == "Softwood Only" and show_softwood_mean) or (wood_filter_type == "Hardwood Only" and show_hardwood_mean):
        group_cols = []
        
        # Handle time aggregation
        if "Year" in filtered_df.columns:
            # Always keep Year in grouping unless showing mean of all years
            if not show_year_mean:
                group_cols.append("Year")
                
            # Add Quarter only if showing quarters and not aggregating time
            if show_quarters and "Quarter" in filtered_df.columns:
                group_cols.append("Quarter")
        
        # Handle spatial aggregation
        if "State" in filtered_df.columns:
            # Include State unless showing mean of all states
            if not show_state_mean:
                if state_filter_type != "Single State with Areas" or not show_area_mean:
                    # Include State in normal cases
                    group_cols.append("State")
        
        # Handle Area aggregation - only include if showing areas and not aggregating them
        if "Area" in filtered_df.columns and state_filter_type == "Single State with Areas" and not show_area_mean:
            group_cols.append("Area")
        
        # Generate Year-Quarter if needed and we're showing quarters
        if "Year" in group_cols and "Quarter" in group_cols and "YearQuarter" not in filtered_df.columns:
            filtered_df = extract_year_quarter(filtered_df)
            if "YearQuarter" in filtered_df.columns:
                group_cols.append("YearQuarter")
        
        # Only aggregate if we have grouping columns and aggregation is needed
        if group_cols:
            # Add all selected product columns
            agg_dict = {col: aggr_method for col in selected_cols if col in filtered_df.columns}
            
            # Perform aggregation
            if agg_dict:
                filtered_df = filtered_df.groupby(group_cols, as_index=False).agg(agg_dict)
                
                # Recreate YearQuarter if needed and we're showing quarters
                if "Year" in filtered_df.columns and "Quarter" in filtered_df.columns and "YearQuarter" not in filtered_df.columns and show_quarters:
                    filtered_df = extract_year_quarter(filtered_df)

# ----------- Begin app pages -----------

# Overview page
if page == "Overview":
    st.header("Dataset Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Available Datasets")
        for name, df in data.items():
            if df is not None:
                st.markdown(f"**{name.capitalize()}**: {df.shape[0]} rows × {df.shape[1]} columns")
    
    with col2:
        st.subheader("Data Preview")
        dataset = st.selectbox("Select a dataset to preview", [k for k, v in data.items() if v is not None])
        st.dataframe(data[dataset].head(10))

    # Basic dataset statistics
    st.subheader("Dataset Information")
    tabs = [tab for tab in ["Prices", "Species", "Bio Merch", "Bio Premerch"] 
            if data.get(tab.lower().replace(" ", "_")) is not None]
    
    if tabs:
        tab_objects = st.tabs(tabs)
        
        for i, tab in enumerate(tab_objects):
            with tab:
                tab_name = tabs[i].lower().replace(" ", "_")
                if tab_name == "prices":
                    st.markdown("**Timber prices across states, areas and periods**")
                    st.markdown("Key variables:")
                    st.markdown("- Year, Quarter: Time period")
                    st.markdown("- State, Area: Geographic location")
                    st.markdown("- Price columns: Various timber products and their prices")
                    
                    if show_softwood:
                        st.markdown(f"**Softwood products**: {', '.join(softwood_cols)}")
                    if show_hardwood:
                        st.markdown(f"**Hardwood products**: {', '.join(hardwood_cols)}")
                        
                elif tab_name == "species":
                    st.markdown("**Species data across southern states**")
                    if "ESTIMATE" in data["species"].columns:
                        total_species = data["species"]["ESTIMATE"].sum()
                        st.metric("Total Species Estimate", f"{total_species:,.0f}")
                elif tab_name == "bio_merch":
                    st.markdown("**Biomass data for merchantable timber**")
                    st.text("Large dataset with detailed biomass information by county and species")
                elif tab_name == "bio_premerch":
                    st.markdown("**Biomass data for pre-merchantable timber**")
                    st.text("Detailed pre-merchantable biomass information")

# Price Analysis page
elif page == "Price Analysis":
    st.header("Timber Price Analysis")
    
    # Check if we have filtered data
    if prices_df is None:
        st.error("No price data available")
        st.stop()
        
    if selected_cols:
        # If we have wood type means, use those directly
        if wood_filter_type == "All Wood Types" and show_wood_mean:
            selected_products = selected_cols  # This will be ['All_Wood_Mean']
        elif wood_filter_type == "Softwood Only" and show_softwood_mean:
            selected_products = selected_cols  # This will be ['Softwood_Mean']
        elif wood_filter_type == "Hardwood Only" and show_hardwood_mean:
            selected_products = selected_cols  # This will be ['Hardwood_Mean']
        else:
            # Selected products for price analysis
            selected_products = st.multiselect(
                "Select Products to Analyze",
                options=selected_cols,
                default=selected_cols[:3] if len(selected_cols) >= 3 else selected_cols
            )
        
        # If we have selected products, create visualizations
        if selected_products:
            # Time-series plot
            st.subheader("Price Trends Over Time")
            
            # Group by time and create time series plot
            if not filtered_df.empty:
                # Check if YearQuarter exists, if not create it
                if "YearQuarter" not in filtered_df.columns and "Year" in filtered_df.columns and "Quarter" in filtered_df.columns:
                    filtered_df = extract_year_quarter(filtered_df)
                
                # Prepare data for time series plot
                if "YearQuarter" in filtered_df.columns:
                    time_col = "YearQuarter"
                elif "Year" in filtered_df.columns:
                    time_col = "Year"
                else:
                    time_col = filtered_df.columns[0]  # Fallback
                
                # Prepare for plotting
                plot_df = filtered_df.copy()
                
                # Keep only relevant columns
                cols_to_keep = [col for col in [time_col, "State", "Area"] if col in plot_df.columns]
                plot_df = plot_df[cols_to_keep + [col for col in selected_products if col in plot_df.columns]]
                
                # Melt for plotting
                id_vars = cols_to_keep
                melted_df = pd.melt(plot_df, id_vars=id_vars, 
                                  value_vars=[col for col in selected_products if col in plot_df.columns], 
                                  var_name="Product", value_name="Price")
                
                # Create faceting column - use State if available
                facet_col = "State" if "State" in melted_df.columns and len(melted_df["State"].unique()) > 1 else None
                
                # Create time series plot
                fig = create_time_series_plot(
                    melted_df, 
                    x_col=time_col, 
                    y_col="Price", 
                    color_col="Product", 
                    facet_col=facet_col,
                    title="Timber Price Trends by Product",
                    labels={time_col: "Time Period", "Price": "Price ($/ton)"}
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Bar chart comparison
                st.subheader("Price Comparison")
                
                # Create grouping dimensions
                group_dims = []
                if "State" in melted_df.columns and len(melted_df["State"].unique()) > 1:
                    group_dims.append("State")
                group_dims.append("Product")
                
                # Calculate average prices
                if group_dims:
                    avg_prices = melted_df.groupby(group_dims)["Price"].mean().reset_index()
                    
                    # Create bar chart
                    fig2 = create_bar_chart(
                        avg_prices, 
                        x_col=group_dims[0], 
                        y_col="Price", 
                        color_col=group_dims[1] if len(group_dims) > 1 else None,
                        barmode="group", 
                        title="Average Price Comparison",
                        labels={"Price": "Average Price ($/ton)"}
                    )
                    
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Show data table
                st.subheader("Data Table")
                st.dataframe(filtered_df)
            else:
                st.warning("No data available for the selected filters")
        else:
            st.warning("Please select at least one product to analyze")
    else:
        st.warning("Please select at least one wood type in the sidebar")

# Species Analysis page
elif page == "Species Analysis":
    st.header("Species Analysis")
    
    species_df = data["species"]
    
    if species_df is None:
        st.error("Species data not available")
        st.stop()
    
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
    
    if df is None:
        st.error(f"{biomass_type} biomass data not available")
        st.stop()
    
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
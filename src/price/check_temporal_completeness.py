#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Checks the temporal completeness of the consolidated TMS report CSV file.

Verifies if all expected Year/Quarter combinations within a defined range
are present for a specific report type and unit.
"""

import pandas as pd
import argparse
import logging
from pathlib import Path
import sys

# --- Configuration ---
# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define defaults and expectations
DEFAULT_CSV_PATH = "data/processed/tms_consolidated_prices.csv"
START_YEAR = 2014
END_YEAR = 2024 # Inclusive
EXPECTED_QUARTERS = ['Q1', 'Q2', 'Q3', 'Q4']

# Define the specific data slice to check completeness for
TARGET_REPORT_TYPE = 'Stumpage'
TARGET_UNITS = '$/ton'
# --- End Configuration ---

def check_temporal_completeness(csv_path_str):
    """Loads CSV, filters data, checks for expected Year/Quarter pairs."""
    csv_path = Path(csv_path_str)
    if not csv_path.is_file():
        logger.error(f"Input CSV file not found: {csv_path}")
        return False

    try:
        # Read CSV, ensure Year is read as string initially
        df = pd.read_csv(csv_path, dtype={'Year': str, 'Quarter': str})
        logger.info(f"Successfully loaded {len(df)} total rows from {csv_path}")
    except FileNotFoundError:
        logger.error(f"File not found: {csv_path}")
        return False
    except Exception as e:
        logger.error(f"Error loading CSV {csv_path}: {e}")
        return False

    # Filter for the specific data we intended to parse and check
    try:
        df_filtered = df[(df['ReportType'] == TARGET_REPORT_TYPE) & (df['Units'] == TARGET_UNITS)].copy()
    except KeyError as e:
        logger.error(f"CSV file {csv_path} is missing required columns: {e}. Cannot perform check.")
        return False
        
    if df_filtered.empty:
         logger.warning(f"No rows found matching ReportType='{TARGET_REPORT_TYPE}' and Units='{TARGET_UNITS}'.")
         logger.warning("Cannot verify temporal completeness for the target data slice as it is missing.")
         # We consider this incomplete for the target slice.
         # If you wanted to check the whole file regardless, modify this logic.
         print("\n--- Temporal Completeness Check ---")
         print(f"Target: ReportType='{TARGET_REPORT_TYPE}', Units='{TARGET_UNITS}'")
         print(f"Result: FAILED (No data matching target found in CSV)")
         print("--- Check Complete ---")
         return False
    else:
         logger.info(f"Found {len(df_filtered)} rows matching target ReportType/Units for analysis.")

    # Ensure Year and Quarter are strings for consistent comparison
    df_filtered['Year'] = df_filtered['Year'].astype(str)
    df_filtered['Quarter'] = df_filtered['Quarter'].astype(str)

    # Get unique actual Year/Quarter pairs found in the filtered data
    actual_periods = set(tuple(row) for row in df_filtered[['Year', 'Quarter']].drop_duplicates().itertuples(index=False))
    
    # Generate expected Year/Quarter pairs
    expected_periods = set()
    for year in range(START_YEAR, END_YEAR + 1):
        for quarter in EXPECTED_QUARTERS:
            expected_periods.add((str(year), quarter))

    # --- Comparison and Reporting ---
    missing_periods = sorted(list(expected_periods - actual_periods))
    # Find periods present in data but not in our Q1-Q4 expectation (e.g., 'Annual')
    unexpected_periods = sorted(list(actual_periods - expected_periods)) 

    print("\n--- Temporal Completeness Check ---")
    print(f"Target: ReportType='{TARGET_REPORT_TYPE}', Units='{TARGET_UNITS}'")
    print(f"Checked Years: {START_YEAR}-{END_YEAR}")
    print(f"Expected Quarters per Year: {EXPECTED_QUARTERS}")
    print(f"Total Expected Year/Quarter Periods (Q1-Q4): {len(expected_periods)}")
    print(f"Unique Year/Quarter Periods Found in Target Data: {len(actual_periods)}")

    is_complete = True # Assume complete unless missing periods found
    
    if missing_periods:
        print("\nMISSING Expected Year/Quarter Periods:")
        for period in missing_periods:
            print(f"- {period[0]} {period[1]}")
        is_complete = False
    else:
        print("\nAll expected Year/Quarter periods (Q1-Q4) are present in the target data.")

    if unexpected_periods:
        print("\nUNEXPECTED Periods Found in Target Data (e.g., 'Annual'):")
        for period in unexpected_periods:
            print(f"- {period[0]} {period[1]}")
        # Presence of unexpected periods doesn't necessarily mean failure, just noting them.

    print("--- Check Complete ---")
    
    if is_complete:
         logger.info("Temporal check passed for expected Q1-Q4 periods.")
    else:
         logger.warning("Temporal check FAILED: Missing expected Q1-Q4 periods.")
         
    return is_complete


def main():
    parser = argparse.ArgumentParser(
        description=f"Check temporal completeness (Years {START_YEAR}-{END_YEAR}, Quarters {EXPECTED_QUARTERS}) "
                    f"for ReportType='{TARGET_REPORT_TYPE}' and Units='{TARGET_UNITS}' in a CSV file."
    )
    parser.add_argument("input_csv",
                        nargs='?', # Makes the argument optional
                        default=DEFAULT_CSV_PATH,
                        help=f"Path to the consolidated CSV file (default: {DEFAULT_CSV_PATH}).")
    args = parser.parse_args()

    logger.info(f"Starting temporal completeness check for: {args.input_csv}")
    complete = check_temporal_completeness(args.input_csv)

    # Optional: exit with non-zero status code if check fails
    # if not complete:
    #     sys.exit(1)

if __name__ == "__main__":
    main() 
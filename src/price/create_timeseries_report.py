#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parses processed JSON report files (split or original) to extract
structured price table data, consolidates it into a time-series
Pandas DataFrame, and exports it to CSV.
Focuses on files originating from 'South-wide Complete' reports.
"""

import os
import json
import re
import argparse
import logging
from pathlib import Path
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_INPUT_BASE_DIR = "data/processed/tms_reports_split"
DEFAULT_OUTPUT_CSV = "data/processed/tms_consolidated_prices.csv"
# Renamed global for clarity and to avoid UnboundLocalError in main
MODULE_LEVEL_TARGET_FILENAME_PATTERN = "South-wide"

# Define expected states to help find the start of data
EXPECTED_STATES = ["AL", "AR", "FL", "GA", "LA", "MS", "NC", "SC", "TN", "TX", "VA"]
# Define expected columns for the $/ton stumpage table
STUMPAGE_TON_HEADERS = [
    'State', 'Area', 'Pine_Sawtimber_WR', 'Pine_Sawtimber_CNS', 'Pine_Sawtimber_Ply',
    'Oak_Sawtimber', 'MixHwd_Sawtimber', 'Pine_Poles', 'Pine_Pulpwood', 'Hardwood_Pulpwood'
]
# Define final expected columns for the output CSV (includes time/meta cols)
EXPECTED_STUMPAGE_TON_COLUMNS = [
    'Year', 'Quarter', 'ReportType', 'Units', 'State', 'Area',
    'Pine_Sawtimber_WR', 'Pine_Sawtimber_CNS', 'Pine_Sawtimber_Ply',
    'Oak_Sawtimber', 'MixHwd_Sawtimber', 'Pine_Poles',
    'Pine_Pulpwood', 'Hardwood_Pulpwood', 'SourceFile'
]

def get_year_quarter_from_filename(filename):
    """Extracts Year (YYYY) and Quarter (Q[1-4]) from filename."""
    match_quarter = re.match(r"(\d{4})_Q(\d)", filename)
    if match_quarter:
        return match_quarter.group(1), f"Q{match_quarter.group(2)}"
    match_annual = re.match(r"(\d{4})_Annual", filename)
    if match_annual:
        return match_annual.group(1), "Annual"
    return None, None

def clean_price(price_str):
    """Cleans price string: removes $, commas, handles non-numeric."""
    if not isinstance(price_str, str):
        return pd.NA
    price_str = price_str.strip().replace('$', '').replace(',', '')
    if price_str in ('', '-', '.'):
        return pd.NA
    try:
        return float(price_str)
    except ValueError:
        return pd.NA

def parse_stumpage_ton_table(cells):
    """Parses the Stumpage Price Summary ($/ton) table structure.
       Returns a list of dictionaries, one per data row.
       Skips 'Avg' rows. Handles rows potentially missing the Area cell.
    """
    parsed_data = []
    headers = STUMPAGE_TON_HEADERS
    num_columns = len(headers)
    data_columns = headers[2:] # Price columns start from the 3rd header

    meaningful_cells = [cell.strip() for cell in cells if cell and cell.strip()]
    if not meaningful_cells:
        return []

    # Find the first state to start parsing
    start_index = -1
    for i, cell in enumerate(meaningful_cells):
        if cell in EXPECTED_STATES:
            start_index = i
            break

    if start_index == -1:
        logger.warning(f"Stumpage $/ton: Could not find start of data (State code). First few cells: {meaningful_cells[:20]}")
        return []

    cell_iterator = iter(meaningful_cells[start_index:])
    current_state = ""
    processed_row_count = 0
    
    current_cell = None # Initialize current_cell outside loop

    while True:
        try:
            # If current_cell is already consumed (e.g., from a previous iteration's lookahead or error handling)
            # get the next one. Otherwise, process the existing current_cell.
            if current_cell is None:
                 current_cell = next(cell_iterator)
            
            cell_to_process = current_cell
            current_cell = None # Assume consumed, will be reset if not

            if cell_to_process in EXPECTED_STATES:
                current_state = cell_to_process
                # State found, continue to next iteration to expect Area
                continue 
            
            # --- We expect an Area ('1', '2', 'Avg') or potentially the first price if Area is missing ---
            if not current_state:
                 # This shouldn't happen if start_index logic worked, but safety check.
                 logger.warning(f"Stumpage $/ton: Encountered cell '{cell_to_process}' without a current state context. Stopping parse for this table.")
                 break
            
            area = None
            price_cells = []

            if cell_to_process.isdigit() and cell_to_process in ['1', '2']:
                # Case 1: Found expected Area '1' or '2'
                area = cell_to_process
                try:
                    # Read the required number of price values
                    for _ in range(num_columns - 2): # State and Area known
                        price_cells.append(next(cell_iterator))
                    # Successfully read all prices for this standard row
                except StopIteration:
                    logger.warning(f"Stumpage $/ton: Incomplete row data for {current_state} {area}. Found only {len(price_cells)} price values after Area. Discarding row.")
                    break # Iterator exhausted, cannot continue

            elif cell_to_process == 'Avg':
                # Case 2: Found 'Avg' row, skip it
                logger.debug(f"Stumpage $/ton: Skipping 'Avg' row for state {current_state}.")
                try:
                    # Consume the remaining cells for this 'Avg' row
                    for _ in range(num_columns - 2):
                        next(cell_iterator)
                except StopIteration:
                    logger.debug(f"Stumpage $/ton: Reached end of cells while skipping 'Avg' row for {current_state}.")
                    # Fine, just means Avg was last. Iterator will end loop.
                continue # Continue to next iteration expecting a new state

            else:
                # Case 3: Didn't find '1', '2', or 'Avg'. Assume Area is missing and cell_to_process is the FIRST price.
                # Check if it looks like a price
                first_price_candidate = clean_price(cell_to_process)
                if not pd.isna(first_price_candidate):
                    logger.warning(f"Stumpage $/ton: Expected Area ('1', '2', 'Avg') for state '{current_state}', but found '{cell_to_process}'. Assuming Area is missing and this is the first price.")
                    area = "MISSING" # Placeholder for Area
                    price_cells.append(cell_to_process) # Use the current cell as the first price
                    try:
                        # Try to read the REMAINING price values (num_columns - 3)
                        for _ in range(num_columns - 3):
                            price_cells.append(next(cell_iterator))
                        # Successfully read remaining prices after assuming missing Area
                    except StopIteration:
                        logger.warning(f"Stumpage $/ton: Incomplete price data after assuming missing Area for {current_state}. Found {len(price_cells)} total prices. Discarding partial row.")
                        # Don't break here, allow loop to potentially find next state later if more data exists.
                        price_cells = [] # Clear price cells as row is invalid
                        area = None # Reset area
                else:
                    # Case 4: Genuinely unexpected cell (not state, not area, not 'Avg', not price-like)
                    logger.error(f"Stumpage $/ton: Unexpected cell '{cell_to_process}' encountered for state '{current_state}'. Cannot interpret as State, Area, or Price. Stopping parse for this table.")
                    # Log context (optional, similar to previous version)
                    context_cells = []
                    for _ in range(20):
                        try:
                            context_cells.append(next(cell_iterator))
                        except StopIteration:
                            break
                    if context_cells:
                        logger.error(f"Stumpage $/ton: Context following unexpected cell '{cell_to_process}': {context_cells}")
                    break # Stop parsing this table

            # --- Process the row if we collected enough data ---
            if area and len(price_cells) == (num_columns - 2 if area != "MISSING" else num_columns - 2): # Need full set of prices
                 row_values = [current_state, area] + price_cells
                 if len(row_values) == num_columns:
                      row_dict = dict(zip(headers, row_values))
                      for col in data_columns:
                           # Ensure cleaning happens here, especially for the first price if area was missing
                           row_dict[col] = clean_price(row_dict[col]) 
                      parsed_data.append(row_dict)
                      processed_row_count += 1
                 else:
                      # This check might be redundant now but good safety.
                      logger.warning(f"Stumpage $/ton: Internal logic error - row length mismatch. State: {current_state}, Area: {area}, Prices: {len(price_cells)}")

        except StopIteration:
            # End of iterator reached cleanly
            logger.debug("Stumpage $/ton: Reached end of cell iterator.")
            break
        except Exception as e:
            logger.error(f"Stumpage $/ton: Unexpected error during parsing: {e}", exc_info=True)
            break # Stop parsing on unexpected errors

    if processed_row_count > 0:
        logger.info(f"Parsed {processed_row_count} data rows from stumpage ton table.")
    return parsed_data

def parse_stumpage_unit_table(cells):
    logger.warning("parse_stumpage_unit_table logic not implemented yet.")
    return []

def parse_delivered_unit_table(cells):
    logger.warning("parse_delivered_unit_table logic not implemented yet.")
    return []

def find_and_parse_tables(file_path, year, quarter):
    all_parsed_rows = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f_in:
            data = json.load(f_in)
    except Exception as e:
        logger.error(f"Error loading or parsing JSON {file_path}: {e}")
        return all_parsed_rows

    if "pages_data" in data:
        pages_data = data.get("pages_data", [])
        original_filename = data.get("metadata", {}).get("original_filename", os.path.basename(file_path))
    else:
        pages_data = []
        original_tables = data.get("tables", [])
        for i, table_content in enumerate(original_tables):
             pages_data.append({"original_page_index": i, "table_content": table_content})
        original_filename = os.path.basename(file_path)

    logger.debug(f"Processing {len(pages_data)} pages/tables from {original_filename}")

    for page_info in pages_data:
        table_content = page_info.get("table_content", {})
        cells = table_content.get("data", [])

        if not cells or len(cells) < 20:
            continue

        parsed_rows = []
        table_type = "Unknown"
        units = "Unknown"
        table_text_lower = " ".join(cells).lower()

        keywords_stumpage = "standing timber"
        keywords_delivered = "delivered timber"
        keywords_per_ton = "(per ton)"
        keywords_trad_unit = "per traditional unit"
        keywords_state = "state"
        keywords_area = "area"

        headers_present = False
        header_cells_lower = [c.lower() for c in cells[:40]]
        if keywords_state in header_cells_lower and keywords_area in header_cells_lower:
             headers_present = True

        # Identify and parse based on keywords and headers
        # Adjusted condition for Stumpage $/ton to be more flexible
        if ("sawtimber" in table_text_lower or keywords_stumpage in table_text_lower) and \
           keywords_per_ton in table_text_lower and \
           headers_present:
            logger.debug(f"Identified Stumpage $/ton table in {original_filename}")
            parsed_rows = parse_stumpage_ton_table(cells)
            if parsed_rows:
                 table_type = "Stumpage"
                 units = "$/ton"
        elif keywords_stumpage in table_text_lower and keywords_trad_unit in table_text_lower and headers_present:
            logger.debug(f"Identified Stumpage Traditional Unit table in {original_filename}")
            parsed_rows = parse_stumpage_unit_table(cells)
            if parsed_rows:
                 table_type = "Stumpage"
                 units = "Traditional"
        elif keywords_delivered in table_text_lower and keywords_trad_unit in table_text_lower and headers_present:
             logger.debug(f"Identified Delivered Traditional Unit table in {original_filename}")
             parsed_rows = parse_delivered_unit_table(cells)
             if parsed_rows:
                  table_type = "Delivered"
                  units = "Traditional"

        if parsed_rows:
            for row in parsed_rows:
                row['Year'] = year
                row['Quarter'] = quarter
                row['ReportType'] = table_type
                row['Units'] = units
                row['SourceFile'] = original_filename
                all_parsed_rows.append(row)

    return all_parsed_rows

def create_timeseries(input_base_dir, output_csv):
    """Walks through input dirs, processes JSONs, consolidates data, saves CSV."""
    all_data = []
    processed_files_count = 0
    processed_origins = set() # Track original base files processed
    input_path = Path(input_base_dir)

    if not input_path.is_dir():
        logger.error(f"Input base directory not found: {input_base_dir}")
        return

    logger.info(f"Scanning for report files in {input_base_dir}... matching pattern *{MODULE_LEVEL_TARGET_FILENAME_PATTERN}*.json")

    # Iterate through sorted file paths for consistent processing order
    for filepath in sorted(input_path.rglob('*.json')):
        filename = filepath.name
        original_base_name_match = re.match(r'(.+?)(_part_\d+)?\.json$', filename)

        if not original_base_name_match:
             logger.debug(f"Skipping file with unexpected name format: {filename}")
             continue
        original_base_name = original_base_name_match.group(1)

        # Check if the file originates from the target report type
        if MODULE_LEVEL_TARGET_FILENAME_PATTERN.lower() not in original_base_name.lower():
            continue

        origin_key = (filepath.parent, original_base_name)
        logger.info(f"Processing target file: {filepath}")
        year, quarter = get_year_quarter_from_filename(original_base_name)

        if year and quarter:
            parsed_rows = find_and_parse_tables(filepath, year, quarter)
            if parsed_rows:
                 all_data.extend(parsed_rows)
                 processed_files_count += 1
                 processed_origins.add(origin_key)
        else:
             logger.warning(f"Could not determine year/quarter for base name '{original_base_name}' from file {filename}. Skipping.")

    if not all_data:
        logger.warning("No data parsed from any relevant files. Cannot create DataFrame.")
        return

    logger.info(f"Consolidating data from {len(processed_origins)} source reports ({processed_files_count} files/parts processed) into DataFrame...")
    df = pd.DataFrame(all_data)

    final_columns = list(df.columns)
    if all(col in df.columns for col in EXPECTED_STUMPAGE_TON_COLUMNS):
         try:
             df = df[EXPECTED_STUMPAGE_TON_COLUMNS]
             final_columns = EXPECTED_STUMPAGE_TON_COLUMNS
             logger.info("Reordered columns based on EXPECTED_STUMPAGE_TON_COLUMNS.")
         except KeyError as e:
             logger.warning(f"Could not reorder columns using expected list: {e}. Using default order.")
    else:
         logger.warning(f"DataFrame created with columns: {final_columns}. Some expected columns might be missing if only non-Stumpage $/ton tables were parsed or parsing was incomplete.")

    logger.info(f"Created DataFrame with {len(df)} rows and columns: {final_columns}")

    for col in STUMPAGE_TON_HEADERS[2:]:
         if col in df.columns:
              df[col] = pd.to_numeric(df[col], errors='coerce')
    logger.info("Attempted conversion of price columns to numeric.")

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_csv(output_csv, index=False)
        logger.info(f"Successfully saved consolidated data to {output_csv}")
    except Exception as e:
        logger.error(f"Error saving DataFrame to CSV {output_csv}: {e}")

def main():
    global MODULE_LEVEL_TARGET_FILENAME_PATTERN # Declare global at the very start of the function
    parser = argparse.ArgumentParser(description="Consolidate TimberMart-South price data from processed JSONs.")
    parser.add_argument("--input_dir",
                        default=DEFAULT_INPUT_BASE_DIR,
                        help=f"Base directory containing year-specific subfolders with processed JSON files (default: {DEFAULT_INPUT_BASE_DIR}).")
    parser.add_argument("--output_csv",
                        default=DEFAULT_OUTPUT_CSV,
                        help=f"Path to save the final consolidated CSV file (default: {DEFAULT_OUTPUT_CSV}).")
    parser.add_argument("--target_pattern",
                        default=MODULE_LEVEL_TARGET_FILENAME_PATTERN, # Use the updated global for default
                        help=f"Substring to identify relevant report files (default: '{MODULE_LEVEL_TARGET_FILENAME_PATTERN}').") # Updated help text

    args = parser.parse_args()
    MODULE_LEVEL_TARGET_FILENAME_PATTERN = args.target_pattern # This will modify the global

    create_timeseries(args.input_dir, args.output_csv)

if __name__ == "__main__":
    main() 
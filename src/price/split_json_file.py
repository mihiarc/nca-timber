#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Splits a large JSON file (expected to have a specific
structure with 'metadata', 'text', and 'tables' keys)
into smaller JSON files, each containing a chunk of the original data.
Attempts to keep important tables (e.g., Stumpage $/ton) together.
"""
import json
import os
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Max characters for the JSON content of the 'pages_data' part of each chunked file.
# This is an estimate to keep files manageable for LLMs.
# A typical token is ~4 chars. 25k chars is ~6k tokens.
DEFAULT_MAX_CHARS_PER_CHUNK = 25000
# Hard limit for a chunk, to allow important tables to stay together if slightly larger
HARD_MAX_CHARS_PER_CHUNK = int(DEFAULT_MAX_CHARS_PER_CHUNK * 1.5) 

# Keywords to identify the primary stumpage price table
STUMP_TON_KEYWORDS = ["stumpage", "(per ton)", "state", "area", "pine sawtimber"]
STUMP_TON_TABLE_TYPE_ID = "STUMP_TON"

def get_estimated_size(data_object):
    """Estimates the size of a Python object when serialized to JSON."""
    return len(json.dumps(data_object))

def get_table_type(table_content):
    """
    Rudimentary classification of a table based on its content.
    Focuses on identifying the main "Stumpage $/ton" table.
    Args:
        table_content (dict): A dictionary representing a single table,
                              expected to have a "data" key with list of cells.
    Returns:
        str: A type identifier (e.g., "STUMP_TON") or "UNKNOWN".
    """
    if not table_content or not isinstance(table_content, dict):
        return "UNKNOWN"
    
    cells = table_content.get("data", [])
    if not cells or not isinstance(cells, list) or len(cells) < 10: # Basic check
        return "UNKNOWN"

    # Check for presence of multiple keywords in the first N cells (e.g., first 50)
    # Flatten and lower-case a portion of the table for keyword search
    searchable_text = " ".join(str(cell).lower() for cell in cells[:50])
    
    match_count = 0
    for keyword in STUMP_TON_KEYWORDS:
        if keyword in searchable_text:
            match_count += 1
    
    # Heuristic: if most keywords are present, classify as STUMP_TON
    if match_count >= 3: # Adjust this threshold as needed
        logger.debug("Identified table as STUMP_TON.")
        return STUMP_TON_TABLE_TYPE_ID
    return "UNKNOWN"

def write_chunk_to_file(output_filepath, original_input_filename, part_number, 
                        chunk_pages_content, original_metadata, current_chunk_char_count):
    """Writes a collected chunk of pages/tables to a JSON file."""
    chunk_data_to_write = {
        "metadata": {
            "original_filename": original_input_filename,
            "part_number": part_number,
            "page_start_original_index": chunk_pages_content[0]["original_page_index"],
            "page_end_original_index": chunk_pages_content[-1]["original_page_index"],
            **original_metadata
        },
        "pages_data": chunk_pages_content
    }
    with open(output_filepath, 'w', encoding='utf-8') as f_out:
        json.dump(chunk_data_to_write, f_out, indent=2)
    logger.info(f"Written chunk {part_number} to {output_filepath} "
                f"({len(chunk_pages_content)} pages/tables, ~{current_chunk_char_count} chars)")

def split_json_file(input_filepath, output_dir, max_chars_per_chunk):
    """
    Splits the input JSON file into smaller chunks, aware of important table types.

    Args:
        input_filepath (str): Path to the large input JSON file.
        output_dir (str): Directory to save the split JSON files.
        max_chars_per_chunk (int): Target maximum estimated character size for each chunk's data.
    """
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f_in:
            original_data = json.load(f_in)
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_filepath}")
        return
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from file: {input_filepath}")
        return

    original_metadata = original_data.get("metadata", {})
    # Expecting tables to be the primary content as per docling output structure
    original_tables = original_data.get("tables", []) 
    # text_content = original_data.get("text", []) # If text also needs to be chunked

    if not original_tables:
        logger.warning(f"No tables found in {input_filepath}. No output files will be generated.")
        return

    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    base_input_filename = os.path.splitext(os.path.basename(input_filepath))[0]

    current_chunk_pages_content = []
    current_chunk_char_count = 0
    file_part_number = 1
    last_added_table_type = "UNKNOWN" # Track type of last table added to current chunk

    for i, table_obj in enumerate(original_tables):
        # Assuming table_obj is the dict like {"header": [], "data": [cells], "caption": ""}
        # The primary content for size estimation and splitting is the table itself.
        # If text needs to be associated, it would need to be handled here.
        
        page_data_for_chunk = {
            "original_page_index": i, # This index refers to the table's position in original_tables
            "table_content": table_obj 
            # "text_content": text_content[i] if i < len(text_content) else "" # Example
        }
        
        current_page_data_size = get_estimated_size(page_data_for_chunk["table_content"])
        current_table_type = get_table_type(page_data_for_chunk["table_content"])

        # Decision logic for chunking
        should_write_chunk = False
        
        if not current_chunk_pages_content:
            # If chunk is empty, add current page/table unless it alone exceeds HARD_MAX
            if current_page_data_size > HARD_MAX_CHARS_PER_CHUNK:
                logger.warning(f"Single table/page {i} data size ({current_page_data_size} chars) "
                               f"exceeds HARD_MAX_CHARS_PER_CHUNK ({HARD_MAX_CHARS_PER_CHUNK}). "
                               f"It will be saved in its own file.")
                # Add it, then immediately trigger write (it forms a chunk by itself)
                current_chunk_pages_content.append(page_data_for_chunk)
                current_chunk_char_count += current_page_data_size
                last_added_table_type = current_table_type
                should_write_chunk = True 
            # else: (handled by the 'else' block below for adding to current chunk)
        
        # If chunk is not empty or the oversized table case above didn't trigger an immediate write
        if not should_write_chunk:
            # Check if adding the current page/table would exceed limits
            potential_new_size = current_chunk_char_count + current_page_data_size
            
            # Condition 1: Standard size check
            exceeds_default_max = potential_new_size > max_chars_per_chunk
            # Condition 2: Hard size check (always triggers split if exceeded)
            exceeds_hard_max = potential_new_size > HARD_MAX_CHARS_PER_CHUNK
            # Condition 3: Attempt to keep important tables together
            is_continuation_of_important_table = (current_table_type == STUMP_TON_TABLE_TYPE_ID and \
                                                  last_added_table_type == STUMP_TON_TABLE_TYPE_ID)

            if exceeds_hard_max:
                # If hard limit exceeded, current chunk must be written (if not empty)
                if current_chunk_pages_content:
                    should_write_chunk = True
            elif exceeds_default_max:
                # Exceeds default, but not hard limit.
                # Only split if it's NOT a continuation of an important table.
                if not is_continuation_of_important_table:
                    if current_chunk_pages_content:
                        should_write_chunk = True
                # If it IS a continuation, we allow it to exceed default (up to hard_max)
                # So, no should_write_chunk = True here, it will be added below.

        # Perform write if needed, then reset chunk for the current page/table
        if should_write_chunk and current_chunk_pages_content: # Ensure there's something to write
            output_filename = f"{base_input_filename}_part_{file_part_number}.json"
            output_filepath = os.path.join(output_dir, output_filename)
            write_chunk_to_file(output_filepath, os.path.basename(input_filepath), file_part_number,
                                current_chunk_pages_content, original_metadata, current_chunk_char_count)
            
            file_part_number += 1
            current_chunk_pages_content = []
            current_chunk_char_count = 0
            last_added_table_type = "UNKNOWN" # Reset for new chunk
        
        # Add current page/table to the (potentially new) current chunk
        # This happens if:
        # 1. Chunk was empty and current page wasn't oversized beyond HARD_MAX.
        # 2. Chunk was not empty, and adding current page didn't trigger 'should_write_chunk'.
        #    This includes cases where it exceeded DEFAULT_MAX but was an important table continuation.
        current_chunk_pages_content.append(page_data_for_chunk)
        current_chunk_char_count += current_page_data_size
        last_added_table_type = current_table_type


    # Write any remaining data in the last chunk
    if current_chunk_pages_content:
        output_filename = f"{base_input_filename}_part_{file_part_number}.json"
        output_filepath = os.path.join(output_dir, output_filename)
        write_chunk_to_file(output_filepath, os.path.basename(input_filepath), file_part_number,
                            current_chunk_pages_content, original_metadata, current_chunk_char_count)

    logger.info("JSON splitting process complete.")

def main():
    parser = argparse.ArgumentParser(description="Split a large JSON file into smaller chunks, table-aware.")
    parser.add_argument("input_file", 
                        help="Path to the input JSON file.")
    parser.add_argument("--output_dir", 
                        default="data/processed/tms_reports_split", 
                        help="Directory to save the split JSON files.")
    parser.add_argument("--max_chars", 
                        type=int, 
                        default=DEFAULT_MAX_CHARS_PER_CHUNK, 
                        help=f"Target maximum estimated character size for the 'pages_data' of each chunk (default: {DEFAULT_MAX_CHARS_PER_CHUNK}).")
    
    args = parser.parse_args()

    # Modify output_dir to include a year-specific subfolder
    base_filename = os.path.basename(args.input_file)
    # Attempt to extract year (assuming format YYYY_...)
    year_part = base_filename.split('_')[0]
    final_output_dir = args.output_dir
    if year_part.isdigit() and len(year_part) == 4:
        final_output_dir = os.path.join(args.output_dir, year_part)
        logger.info(f"Year detected: {year_part}. Outputting to year-specific directory: {final_output_dir}")
    else:
        logger.warning(f"Could not reliably detect year from filename '{base_filename}'. Using default output directory: {args.output_dir}")
        
    split_json_file(args.input_file, final_output_dir, args.max_chars)

if __name__ == "__main__":
    main() 
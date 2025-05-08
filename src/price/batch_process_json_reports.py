#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Batch processes JSON report files from a source directory.
For each JSON file:
- If its main content (e.g., 'tables') is larger than a threshold,
  it's split into smaller, year-organized parts using split_json_file.py.
- Otherwise, it's copied directly to a year-organized target directory.
"""
import os
import json
import shutil
import argparse
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default threshold for content size (character count of the JSON string of 'tables')
# This should ideally match or be consistent with the one in split_json_file.py
DEFAULT_MAX_CONTENT_CHARS = 25000
DEFAULT_SOURCE_DIR = "data/processed/tms_reports"
DEFAULT_TARGET_BASE_DIR = "data/processed/tms_reports_split"
SPLITTER_SCRIPT_PATH = "code/split_json_file.py"

def get_json_content_char_count(data, content_key='tables'):
    """Estimates the character count of a specific key's content when serialized to JSON."""
    content = data.get(content_key, [])
    return len(json.dumps(content))

def get_year_from_filename(filename):
    """Extracts a 4-digit year from the start of a filename (e.g., YYYY_...)."""
    parts = os.path.basename(filename).split('_')
    if parts and parts[0].isdigit() and len(parts[0]) == 4:
        return parts[0]
    return None

def batch_process_reports(source_dir, target_base_dir, max_content_chars):
    """
    Processes JSON files from source_dir, splitting large ones and copying smaller ones.
    """
    if not os.path.isdir(source_dir):
        logger.error(f"Source directory not found: {source_dir}")
        return

    logger.info(f"Starting batch processing from {source_dir} to {target_base_dir}")

    for filename in os.listdir(source_dir):
        if not filename.lower().endswith('.json'):
            logger.debug(f"Skipping non-JSON file: {filename}")
            continue

        source_filepath = os.path.join(source_dir, filename)
        logger.info(f"Processing file: {source_filepath}")

        try:
            with open(source_filepath, 'r', encoding='utf-8') as f_in:
                data = json.load(f_in)
        except FileNotFoundError:
            logger.error(f"File disappeared during processing: {source_filepath}")
            continue
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from file: {source_filepath}. Skipping.")
            continue
        except Exception as e:
            logger.error(f"An unexpected error occurred opening or reading {source_filepath}: {e}. Skipping.")
            continue

        year = get_year_from_filename(filename)
        if not year:
            logger.warning(f"Could not determine year for {filename}. Placing in 'unknown_year' folder.")
            year = "unknown_year"
        
        target_year_dir = os.path.join(target_base_dir, year)
        os.makedirs(target_year_dir, exist_ok=True)

        content_char_count = get_json_content_char_count(data, content_key='tables')

        if content_char_count > max_content_chars:
            logger.info(f"File {filename} is large ({content_char_count} chars). Splitting...")
            try:
                # The split_json_file.py script handles creating the year-specific subfolder correctly
                # if its input filename contains the year and the output_dir is the base for splits.
                cmd = [
                    "python", SPLITTER_SCRIPT_PATH, 
                    source_filepath, 
                    "--output_dir", target_base_dir, # splitter script will make target_base_dir/year
                    "--max_chars", str(max_content_chars)
                ]
                logger.debug(f"Running command: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    logger.info(f"Successfully split {filename}. Output in {target_year_dir}.")
                    logger.debug(f"Splitter stdout:\n{result.stdout}")
                else:
                    logger.error(f"Failed to split {filename}. Error:\n{result.stderr}")
                    logger.debug(f"Splitter stdout (on error):\n{result.stdout}")

            except FileNotFoundError:
                logger.error(f"Splitter script {SPLITTER_SCRIPT_PATH} not found.")
            except Exception as e:
                logger.error(f"Error running splitter script for {filename}: {e}")
        else:
            logger.info(f"File {filename} is manageable ({content_char_count} chars). Copying...")
            destination_filepath = os.path.join(target_year_dir, filename)
            try:
                shutil.copy2(source_filepath, destination_filepath)
                logger.info(f"Copied {filename} to {destination_filepath}")
            except Exception as e:
                logger.error(f"Error copying {filename} to {destination_filepath}: {e}")
    
    logger.info("Batch processing complete.")

def main():
    parser = argparse.ArgumentParser(description="Batch process JSON report files.")
    parser.add_argument("--source_dir", 
                        default=DEFAULT_SOURCE_DIR, 
                        help=f"Source directory containing JSON files (default: {DEFAULT_SOURCE_DIR}).")
    parser.add_argument("--target_base_dir", 
                        default=DEFAULT_TARGET_BASE_DIR, 
                        help=f"Base target directory for processed files (default: {DEFAULT_TARGET_BASE_DIR}).")
    parser.add_argument("--max_content_chars", 
                        type=int, 
                        default=DEFAULT_MAX_CONTENT_CHARS, 
                        help=f"Threshold for 'tables' content size to trigger splitting (default: {DEFAULT_MAX_CONTENT_CHARS}).")
    
    args = parser.parse_args()

    if not os.path.exists(SPLITTER_SCRIPT_PATH):
        logger.error(f"Required splitter script not found at {SPLITTER_SCRIPT_PATH}. Please ensure it exists.")
        return

    batch_process_reports(args.source_dir, args.target_base_dir, args.max_content_chars)

if __name__ == "__main__":
    main() 
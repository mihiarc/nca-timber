#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF Processing Module

This module uses docling to process TimberMart-South PDF files and convert them
into usable formats for analysis.
"""

import os
import json
import logging
import yaml
from pathlib import Path
from docling.document_converter import DocumentConverter
import pandas as pd
import torch

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Force CPU mode
torch.cuda.is_available = lambda: False
os.environ['CUDA_VISIBLE_DEVICES'] = ''

def load_config():
    """Load configuration from config.yaml"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        raise FileNotFoundError("config.yaml not found")
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Use absolute path for TMS directory
    tms_dir = "/media/mihiarc/RPA1TB/TimberMart_South"
    if not os.path.exists(tms_dir):
        raise FileNotFoundError(f"TMS directory not found: {tms_dir}")
    
    logger.info(f"Using TMS directory: {tms_dir}")
    return config

def process_pdf(pdf_path):
    """Process a single PDF file using docling"""
    try:
        logger.info(f"Processing PDF file: {pdf_path}")
        
        # Initialize converter (models should already be downloaded)
        converter = DocumentConverter()
        
        # Convert document
        logger.info("Converting document...")
        result = converter.convert(str(pdf_path))
        logger.info("Document converted successfully")
        
        # Extract text content
        text_content = []
        for i, page in enumerate(result.pages, 1):
            logger.debug(f"Processing page {i}")
            if hasattr(page, 'parsed_page') and page.parsed_page:
                text_content.append(page.parsed_page.text)
            else:
                logger.warning(f"No parsed content found for page {i}")
                text_content.append("")
        
        # Extract tables
        tables = []
        for i, page in enumerate(result.pages, 1):
            if hasattr(page, 'cells') and page.cells:
                logger.info(f"Found {len(page.cells)} cells on page {i}")
                # Convert cells to table format
                table_data = []
                for cell in page.cells:
                    if hasattr(cell, 'text'):
                        table_data.append(cell.text)
                if table_data:
                    tables.append({"data": table_data})
        
        # Create metadata
        metadata = {
            "filename": os.path.basename(pdf_path),
            "page_count": len(result.pages),
            "has_tables": bool(tables),
            "table_count": len(tables)
        }
        
        return {
            "text": text_content,
            "tables": tables,
            "metadata": metadata
        }
    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {str(e)}", exc_info=True)
        raise

def process_quarterly_reports(config):
    """Process all quarterly reports in the TMS directory"""
    tms_dir = "/media/mihiarc/RPA1TB/TimberMart_South"
    logger.info(f"Processing reports from directory: {tms_dir}")
    
    # Create output directory
    output_dir = Path("data/processed/tms_reports")
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created output directory: {output_dir}")
    
    # Process each quarterly directory
    for item in os.listdir(tms_dir):
        item_path = os.path.join(tms_dir, item)
        if os.path.isdir(item_path) and item.startswith("20"):  # Quarterly directories start with year
            logger.info(f"Processing directory: {item}")
            for file in os.listdir(item_path):
                if file.endswith(".pdf"):
                    pdf_path = os.path.join(item_path, file)
                    logger.info(f"Processing file: {file}")
                    try:
                        result = process_pdf(pdf_path)
                        
                        # Save text and metadata
                        output_file = output_dir / f"{item}_{file[:-4]}.json"
                        with open(output_file, "w") as f:
                            json.dump(result, f, indent=2)
                        logger.info(f"Saved output to {output_file}")
                        
                        # Save tables if any
                        if result["tables"]:
                            tables_dir = output_dir / "tables"
                            tables_dir.mkdir(exist_ok=True)
                            for i, table in enumerate(result["tables"]):
                                table_file = tables_dir / f"{item}_{file[:-4]}_table_{i+1}.json"
                                with open(table_file, "w") as f:
                                    json.dump(table, f, indent=2)
                                logger.info(f"Saved table to {table_file}")
                    except Exception as e:
                        logger.error(f"Failed to process {pdf_path}: {str(e)}", exc_info=True)
                        continue

def main():
    """Main function to process PDF files"""
    logger.info("Starting PDF processing")
    try:
        config = load_config()
        process_quarterly_reports(config)
        logger.info("PDF processing completed successfully")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 
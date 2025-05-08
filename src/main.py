#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main Timber Assets Processing Script

This script orchestrates the entire timber asset processing workflow,
coordinating between region-specific data processing modules and the 
reporting module. It follows the single responsibility principle by 
serving as a coordinator rather than implementing logic directly.
"""

import argparse
import os
from pathlib import Path
from src.utils.geo_crosswalks import DATA_DIR, PROCESSED_DIR, REPORTS_DIR

# Import processing modules
from src.asset.south_assets import process_south_data
from src.asset.greatlakes_assets import process_gl_data
from src.asset.table_reporting import generate_reports


def create_required_directories():
    """Create necessary directories for data processing and reporting."""
    PROCESSED_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)


def process_data(regions=None):
    """
    Process data for the specified regions.
    
    Parameters:
    -----------
    regions : list, optional
        List of region identifiers to process data for.
        If None, processes data for all regions.
        
    Returns:
    --------
    dict
        Dictionary containing processing results
    """
    results = {}
    
    if regions is None:
        regions = ['south', 'gl']
    
    for region in regions:
        try:
            print(f"Processing data for {region}...")
            
            if region.lower() == 'south':
                results['south'] = process_south_data()
                print(f"Processed {len(results['south']['table_south'])} records for the South region.")
            
            elif region.lower() in ('gl', 'great_lakes'):
                results['gl'] = process_gl_data()
                print(f"Processed {len(results['gl']['table_gl'])} records for the Great Lakes region.")
            
            else:
                print(f"Unknown region: {region}. Skipping.")
        
        except Exception as e:
            print(f"Error processing data for {region}: {e}")
    
    return results


def generate_all_reports(regions=None):
    """
    Generate reports for the specified regions.
    
    Parameters:
    -----------
    regions : list, optional
        List of region identifiers to generate reports for.
        If None, generates reports for all regions including combined 'all'.
        
    Returns:
    --------
    None
    """
    if regions is None:
        regions = ['south', 'gl', 'all']
    
    try:
        generate_reports(regions)
    except Exception as e:
        print(f"Error generating reports: {e}")


def main():
    """Main function to orchestrate the workflow."""
    parser = argparse.ArgumentParser(description='Process timber asset data and generate reports.')
    parser.add_argument('--regions', nargs='+', choices=['south', 'gl', 'all'], 
                        default=['south', 'gl', 'all'],
                        help='Regions to process and generate reports for.')
    parser.add_argument('--process-only', action='store_true',
                        help='Only process data, don\'t generate reports.')
    parser.add_argument('--report-only', action='store_true',
                        help='Only generate reports, don\'t process data.')
    
    args = parser.parse_args()
    
    # Create required directories
    create_required_directories()
    
    # Determine regions to process
    process_regions = [r for r in args.regions if r != 'all']
    report_regions = args.regions
    
    # Execute workflow
    if not args.report_only:
        process_data(process_regions)
    
    if not args.process_only:
        generate_all_reports(report_regions)
    
    print("Timber asset processing complete!")


if __name__ == "__main__":
    main() 
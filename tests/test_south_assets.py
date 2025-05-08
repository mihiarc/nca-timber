#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for south_assets module
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add the code directory to sys.path
code_dir = Path(__file__).resolve().parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from south_assets import (
    load_price_regions,
    create_mock_south_table,
    load_south_harvested_species
)
from src.utils.species_crosswalks import load_csv, speciesDict, speciesGroupDict
from src.utils.geo_crosswalks import SOUTH_STATES
from src.config import STATE_FIPS


class TestSouthAssetsFunctions(unittest.TestCase):
    """Test cases for south_assets module functions"""
    
    def test_load_price_regions(self):
        """Test loading of South price regions data"""
        # Load South price regions
        price_regions = load_price_regions()
        
        # Check basic structure
        self.assertIsInstance(price_regions, pd.DataFrame)
        self.assertGreater(len(price_regions), 0)
        
        # Check required columns
        required_columns = ['statecd', 'countycd', 'unitcd', 'priceRegion', 'fips']
        for col in required_columns:
            self.assertIn(col, price_regions.columns)
    
    def test_create_mock_south_table(self):
        """Test creation of mock South data table"""
        # Generate mock South data
        mock_south = create_mock_south_table()
        
        # Check basic structure
        self.assertIsInstance(mock_south, pd.DataFrame)
        self.assertGreater(len(mock_south), 0)
        
        # Check required columns
        required_columns = ['statecd', 'spcd', 'spgrpcd', 'product', 'volume', 'cuftPrice', 'value']
        for col in required_columns:
            self.assertIn(col, mock_south.columns)
        
        # Check for Southern states in the data
        south_fips = [STATE_FIPS[state] for state in SOUTH_STATES]
        # At least one Southern state should be in the data
        self.assertTrue(any(state in mock_south['statecd'].values for state in south_fips))
    
    def test_load_south_harvested_species(self):
        """Test loading of South harvested species data"""
        # Load South harvested species data
        species_list = load_south_harvested_species()
        
        # Check basic structure
        self.assertIsInstance(species_list, list)
        self.assertGreater(len(species_list), 0)
        
        # Check for expected default species codes
        default_species = [110, 111, 121, 131]
        for sp in default_species:
            self.assertIn(sp, species_list)


if __name__ == '__main__':
    unittest.main() 
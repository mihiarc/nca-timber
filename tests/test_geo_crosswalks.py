#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for geo_crosswalks module
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

from src.utils.geo_crosswalks import (
    get_price_regions,
    format_unit_code,
    get_state_abbr_from_fips,
    SOUTH_STATES,
    GREAT_LAKES_STATES
)
from src.utils.county import format_fips
from src.config import STATE_FIPS


class TestGeoCrosswalksFunctions(unittest.TestCase):
    """Test cases for geo_crosswalks module functions"""
    
    def test_format_fips(self):
        """Test FIPS code formatting function"""
        # Create test DataFrame
        df = pd.DataFrame({
            'statecd': [1, 5, 12],
            'countycd': [1, 20, 300],
            'other_col': ['a', 'b', 'c']
        })
        
        # Test with both state and county codes
        result = format_fips(df)
        self.assertEqual(result['fips'].tolist(), ['01001', '05020', '12300'])
        
        # Test with state code only
        df_state_only = pd.DataFrame({
            'statecd': [1, 5, 12],
            'other_col': ['a', 'b', 'c']
        })
        result_state_only = format_fips(df_state_only)
        self.assertEqual(result_state_only['fips'].tolist(), ['01', '05', '12'])
    
    def test_format_unit_code(self):
        """Test unit code formatting function"""
        # Create test DataFrame
        df = pd.DataFrame({
            'unitcd': [1, 5, 12],
            'other_col': ['a', 'b', 'c']
        })
        
        # Test formatting
        result = format_unit_code(df)
        self.assertEqual(result['unitcd'].tolist(), ['01', '05', '12'])
        
        # Test with missing unit code
        df_missing = pd.DataFrame({
            'other_col': ['a', 'b', 'c']
        })
        result_missing = format_unit_code(df_missing)
        self.assertEqual(list(result_missing.columns), ['other_col'])
    
    def test_get_state_abbr_from_fips(self):
        """Test state abbreviation lookup function"""
        # Test known FIPS codes
        self.assertEqual(get_state_abbr_from_fips('01'), 'AL')
        self.assertEqual(get_state_abbr_from_fips('26'), 'MI')
        
        # Test with full FIPS code (state + county)
        self.assertEqual(get_state_abbr_from_fips('01001'), 'AL')
        
        # Test unknown code
        self.assertIsNone(get_state_abbr_from_fips('99'))
    
    def test_get_price_regions(self):
        """Test price regions generation function"""
        # Test getting all regions
        all_regions = get_price_regions()
        self.assertGreater(len(all_regions), 0)
        self.assertIn('statecd', all_regions.columns)
        self.assertIn('priceRegion', all_regions.columns)
        
        # Test getting South regions
        south_regions = get_price_regions(region='south')
        south_state_fips = [STATE_FIPS[state] for state in SOUTH_STATES]
        self.assertTrue(all(south_regions['statecd'].isin(south_state_fips)))
        
        # Test getting Great Lakes regions
        gl_regions = get_price_regions(region='gl')
        gl_state_fips = [STATE_FIPS[state] for state in GREAT_LAKES_STATES]
        self.assertTrue(all(gl_regions['statecd'].isin(gl_state_fips)))


if __name__ == '__main__':
    unittest.main() 
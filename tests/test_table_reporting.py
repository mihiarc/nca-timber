#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for table_reporting module
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os
import shutil
from pathlib import Path

# Add the code directory to sys.path
code_dir = Path(__file__).resolve().parent.parent / 'code'
sys.path.insert(0, str(code_dir))

from table_reporting import (
    create_mock_south_table,
    create_mock_gl_table,
    add_species_info,
    generate_physical_table_by_species_class,
    generate_monetary_table_by_species_class
)


class TestTableReportingFunctions(unittest.TestCase):
    """Test cases for table_reporting module functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for test data
        from geo_crosswalks import DATA_DIR
        self.test_data_dir = DATA_DIR / 'test'
        self.test_processed_dir = self.test_data_dir / 'processed'
        self.test_processed_dir.mkdir(parents=True, exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Remove test directory if it exists
        if self.test_data_dir.exists():
            shutil.rmtree(self.test_data_dir)
    
    def test_create_mock_south_table(self):
        """Test creation of mock South data"""
        # Generate mock South data
        mock_south = create_mock_south_table()
        
        # Check basic structure
        self.assertIsInstance(mock_south, pd.DataFrame)
        self.assertGreater(len(mock_south), 0)
        
        # Check required columns
        required_columns = ['statecd', 'spcd', 'spgrpcd', 'product', 'volume', 'cuftPrice', 'value']
        for col in required_columns:
            self.assertIn(col, mock_south.columns)
    
    def test_create_mock_gl_table(self):
        """Test creation of mock Great Lakes data"""
        # Generate mock Great Lakes data
        mock_gl = create_mock_gl_table()
        
        # Check basic structure
        self.assertIsInstance(mock_gl, pd.DataFrame)
        self.assertGreater(len(mock_gl), 0)
        
        # Check required columns
        required_columns = ['statecd', 'spcd', 'spgrpcd', 'product', 'volume', 'cuftPrice', 'value']
        for col in required_columns:
            self.assertIn(col, mock_gl.columns)
    
    def test_add_species_info(self):
        """Test adding species information to table data"""
        # Create mock data
        mock_data = create_mock_south_table()
        
        # Add species info
        result = add_species_info(mock_data)
        
        # Check for new columns
        self.assertIn('speciesName', result.columns)
        self.assertIn('speciesGroup', result.columns)
        
        # Check if species class names are standardized
        self.assertIn('Coniferous', result['spclass'].unique())
    
    def test_generate_physical_table_by_species_class(self):
        """Test generation of physical table by species class"""
        # Create mock data
        mock_data = create_mock_south_table()
        mock_data = add_species_info(mock_data)
        
        # Generate table
        result = generate_physical_table_by_species_class(mock_data, 'South')
        
        # Check basic structure
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(len(result), 0)
        
        # Check if species class is in index
        self.assertIn('spclass', result.columns)
        
        # Check if product columns exist
        self.assertIn('Sawtimber', result.columns)
        self.assertIn('Pulpwood', result.columns)
    
    def test_generate_monetary_table_by_species_class(self):
        """Test generation of monetary table by species class"""
        # Create mock data
        mock_data = create_mock_south_table()
        mock_data = add_species_info(mock_data)
        
        # Generate table
        result = generate_monetary_table_by_species_class(mock_data, 'South')
        
        # Check basic structure
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreater(len(result), 0)
        
        # Check if species class is in index
        self.assertIn('spclass', result.columns)
        
        # Check if product columns exist
        self.assertIn('Sawtimber', result.columns)
        self.assertIn('Pulpwood', result.columns)


if __name__ == '__main__':
    unittest.main() 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for species_crosswalks module
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.species_crosswalks import (
    get_species_name, 
    get_species_group_name,
    convert_to_billions,
    convert_to_megatonnes,
    DOLLARS_TO_BILLIONS,
    CUBIC_FT_TO_MEGATONNE
)


class TestSpeciesCrosswalksFunctions(unittest.TestCase):
    """Test cases for species_crosswalks module functions"""
    
    def test_get_species_name(self):
        """Test species name lookup function"""
        # Test known species codes
        self.assertEqual(get_species_name(131), 'loblolly')
        self.assertEqual(get_species_name(110), 'shortleaf')
        
        # Test unknown species code
        self.assertIsNone(get_species_name(9999))
    
    def test_get_species_group_name(self):
        """Test species group name lookup function"""
        # Test known species group codes
        self.assertEqual(get_species_group_name(1), 'Longleaf and slash pines')
        self.assertEqual(get_species_group_name(2), 'Lobolly and shortleaf pines')
        
        # Test unknown species group code
        self.assertIsNone(get_species_group_name(9999))
    
    def test_convert_to_billions(self):
        """Test conversion to billions function"""
        # Create test DataFrame
        df = pd.DataFrame({
            'value': [1000000000, 2000000000, 3000000000],
            'other_col': [1, 2, 3]
        })
        
        # Test conversion
        result = convert_to_billions(df)
        self.assertEqual(result['value'].tolist(), [1.0, 2.0, 3.0])
        
        # Test with custom column name
        df = pd.DataFrame({
            'amount': [1000000000, 2000000000, 3000000000],
            'other_col': [1, 2, 3]
        })
        result = convert_to_billions(df, value_col='amount')
        self.assertEqual(result['amount'].tolist(), [1.0, 2.0, 3.0])
    
    def test_convert_to_megatonnes(self):
        """Test conversion to megatonnes function"""
        # Create test DataFrame with large values
        volume_values = [1000000000, 2000000000, 3000000000]
        df = pd.DataFrame({
            'volume': volume_values,
            'other_col': [1, 2, 3]
        })
        
        # Test conversion
        result = convert_to_megatonnes(df)
        expected = [v * CUBIC_FT_TO_MEGATONNE for v in volume_values]
        
        # Use numpy.testing.assert_almost_equal for floating point comparison
        np.testing.assert_almost_equal(result['volume'].tolist(), expected)


if __name__ == '__main__':
    unittest.main() 
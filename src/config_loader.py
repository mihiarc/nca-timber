#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration Loader Module

This module loads configuration settings from YAML files for the timber assets project.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Parameters:
    -----------
    config_path : str, optional
        Path to configuration file. If None, uses default 'config.yaml'
        
    Returns:
    --------
    dict
        Configuration settings
        
    Raises:
    -------
    FileNotFoundError
        If the configuration file does not exist
    """
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent.parent / 'config.yaml'
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


# Create config dictionaries as module-level variables for easy import
CONFIG = load_config()

# Region constants
SOUTH_STATES = CONFIG['regions']['south_states']
GREAT_LAKES_STATES = CONFIG['regions']['great_lakes_states']

# State FIPS code mapping
STATE_FIPS = CONFIG['state_fips']

# Unit conversion factors
CUBIC_FT_TO_MEGATONNE = CONFIG['conversions']['cubic_ft_to_megatonne']
DOLLARS_TO_BILLIONS = CONFIG['conversions']['dollars_to_billions']
TONS_TO_CUBIC_FEET = CONFIG['conversions']['tons_to_cubic_feet']

# Financial parameters
DISCOUNT_RATE = CONFIG['financial']['discount_rate']
MERCHANTABLE_AGE = CONFIG['financial']['merchantable_age']

# Product types
PRODUCT_TYPES = CONFIG['product_types']

# File paths
FILES = CONFIG['files']


if __name__ == "__main__":
    # Print loaded configuration for testing
    import json
    print(json.dumps(CONFIG, indent=2)) 
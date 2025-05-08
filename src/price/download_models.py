#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Model Download Script

This script downloads and caches the required docling models from Hugging Face Hub.
It can be run independently to ensure models are available before running the PDF processor.
"""

import os
import logging
import requests
from pathlib import Path
from huggingface_hub import snapshot_download
from docling.document_converter import DocumentConverter

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_cache_dir():
    """Check and create cache directory if needed"""
    cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def download_models():
    """Download required docling models"""
    try:
        logger.info("Starting model download process...")
        
        # Initialize DocumentConverter to trigger model download
        logger.info("Initializing DocumentConverter...")
        converter = DocumentConverter()
        
        # Get model info
        model_id = "ds4sd/docling-models"
        logger.info(f"Downloading models from {model_id}")
        
        # Download models with progress tracking
        cache_dir = check_cache_dir()
        logger.info(f"Using cache directory: {cache_dir}")
        
        # Download models
        snapshot_download(
            repo_id=model_id,
            local_dir=cache_dir / "models--ds4sd--docling-models",
            local_dir_use_symlinks=False,
            resume_download=True
        )
        
        logger.info("Model download completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading models: {str(e)}", exc_info=True)
        return False

def main():
    """Main function to download models"""
    logger.info("Starting model download script")
    
    if download_models():
        logger.info("All models downloaded successfully!")
    else:
        logger.error("Failed to download models. Please check the logs for details.")
        exit(1)

if __name__ == "__main__":
    main() 
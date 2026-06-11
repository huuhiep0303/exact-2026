"""
Data preprocessing script for EXACT 2026 Type 1 dataset.

This script loads the raw dataset, processes it, and splits it into
train/validation/test sets.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.utils.config_loader import load_config
from src.utils.logger import get_logger
from src.data.data_processor import DataProcessor

logger = get_logger(__name__)


def main():
    """Main preprocessing function."""
    logger.info("=" * 80)
    logger.info("EXACT 2026 - Type 1 Data Preprocessing")
    logger.info("=" * 80)
    
    # Load configuration
    config_path = "configs/config.yaml"
    logger.info(f"Loading configuration from: {config_path}")
    config = load_config(config_path)
    
    # Initialize data processor
    logger.info("Initializing data processor...")
    processor = DataProcessor(config)
    
    # Load raw data
    raw_data_path = config['data']['raw_data_path']
    if not os.path.exists(raw_data_path):
        logger.error(f"Raw data file not found: {raw_data_path}")
        logger.error("Please ensure the dataset is in the correct location.")
        sys.exit(1)
    
    # Process and save data
    logger.info("Processing data and splitting into train/val/test sets...")
    stats = processor.process_and_save()
    
    logger.info(f"Total examples created: {stats['total']}")
    logger.info(f"Train samples: {stats['train']}")
    logger.info(f"Validation samples: {stats['val']}")
    logger.info(f"Test samples: {stats['test']}")
    
    output_dir = config['data']['processed_dir']
    logger.info(f"Saved processed data to: {output_dir}")
    
    logger.info("=" * 80)
    logger.info("Data preprocessing completed successfully!")
    logger.info("=" * 80)
    logger.info(f"Train file: {config['data']['train_file']}")
    logger.info(f"Validation file: {config['data']['val_file']}")
    logger.info(f"Test file: {config['data']['test_file']}")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

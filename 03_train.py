"""
Training script for EXACT 2026 Type 1 dataset.

This script fine-tunes Qwen2.5-7B-Instruct with LoRA on the processed dataset.
"""

import os
import sys
from pathlib import Path
import torch

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.utils.config_loader import load_config
from src.utils.logger import get_logger
from src.training.trainer import train_model

logger = get_logger(__name__)


def main():
    """Main training function."""
    logger.info("=" * 80)
    logger.info("EXACT 2026 - Type 1 Model Training")
    logger.info("=" * 80)
    
    # Check CUDA availability
    if torch.cuda.is_available():
        logger.info(f"CUDA is available. Using GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        logger.warning("CUDA is not available. Training will be slow on CPU.")
    
    # Load configuration
    config_path = "configs/config.yaml"
    logger.info(f"Loading configuration from: {config_path}")
    config = load_config(config_path)
    
    # Check if processed data exists
    train_file = config['data']['train_file']
    val_file = config['data']['val_file']
    
    if not os.path.exists(train_file):
        logger.error(f"Training file not found: {train_file}")
        logger.error("Please run 02_preprocess_data.py first to process the data.")
        sys.exit(1)
    
    if not os.path.exists(val_file):
        logger.error(f"Validation file not found: {val_file}")
        logger.error("Please run 02_preprocess_data.py first to process the data.")
        sys.exit(1)
    
    # Train model
    logger.info("Starting training...")
    logger.info(f"Model: {config['model']['name']}")
    logger.info(f"Epochs: {config['training']['num_train_epochs']}")
    logger.info(f"Batch size: {config['training']['per_device_train_batch_size']}")
    logger.info(f"Learning rate: {config['training']['learning_rate']}")
    logger.info(f"LoRA rank: {config['lora']['r']}")
    logger.info("=" * 80)
    
    train_model(config)
    
    logger.info("=" * 80)
    logger.info("Training completed successfully!")
    logger.info("=" * 80)
    logger.info(f"Model saved to: {config['training']['output_dir']}/final")
    logger.info("You can now run 04_evaluate.py to evaluate the model.")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

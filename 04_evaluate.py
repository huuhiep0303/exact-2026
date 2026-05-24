"""
Evaluation script for EXACT 2026 Type 1 dataset.

This script evaluates the trained model on the test set and generates
comprehensive evaluation metrics.
"""

import os
import sys
from pathlib import Path
import argparse

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.utils.config_loader import load_config
from src.utils.logger import get_logger
from src.evaluation.evaluator import Evaluator

logger = get_logger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Evaluate trained model")
    parser.add_argument(
        "--model_path",
        type=str,
        default="outputs/checkpoints/final",
        help="Path to trained model"
    )
    parser.add_argument(
        "--test_file",
        type=str,
        default=None,
        help="Path to test file (default: from config)"
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="outputs/results/evaluation_results.json",
        help="Path to save evaluation results"
    )
    parser.add_argument(
        "--save_predictions",
        action="store_true",
        default=True,
        help="Save predictions to file"
    )
    return parser.parse_args()


def main():
    """Main evaluation function."""
    args = parse_args()
    
    logger.info("=" * 80)
    logger.info("EXACT 2026 - Type 1 Model Evaluation")
    logger.info("=" * 80)
    
    # Load configuration
    config_path = "configs/config.yaml"
    logger.info(f"Loading configuration from: {config_path}")
    config = load_config(config_path)
    
    # Get test file path
    test_file = args.test_file or config['data']['test_file']
    
    # Check if files exist
    if not os.path.exists(args.model_path):
        logger.error(f"Model not found: {args.model_path}")
        logger.error("Please run 03_train.py first to train the model.")
        sys.exit(1)
    
    if not os.path.exists(test_file):
        logger.error(f"Test file not found: {test_file}")
        logger.error("Please run 02_preprocess_data.py first to process the data.")
        sys.exit(1)
    
    # Initialize evaluator
    logger.info(f"Loading model from: {args.model_path}")
    evaluator = Evaluator(
        model_path=args.model_path,
        config=config
    )
    
    # Run evaluation
    logger.info(f"Evaluating on test file: {test_file}")
    logger.info("=" * 80)
    
    results = evaluator.evaluate(
        test_file=test_file,
        output_file=args.output_file,
        save_predictions=args.save_predictions
    )
    
    # Print results
    logger.info("=" * 80)
    logger.info("EVALUATION RESULTS")
    logger.info("=" * 80)
    logger.info(f"Number of samples: {results['num_samples']}")
    logger.info(f"Accuracy: {results['accuracy']:.4f} ({results['accuracy']*100:.2f}%)")
    logger.info(f"Premise F1: {results['premise_metrics']['f1']:.4f}")
    logger.info(f"Premise Precision: {results['premise_metrics']['precision']:.4f}")
    logger.info(f"Premise Recall: {results['premise_metrics']['recall']:.4f}")
    logger.info(f"Reasoning Quality: {results['reasoning_quality']:.4f}")
    logger.info(f"Combined Score: {results['combined_score']:.4f}")
    logger.info("=" * 80)
    logger.info(f"Results saved to: {args.output_file}")
    
    if args.save_predictions:
        predictions_file = args.output_file.replace('.json', '_predictions.json')
        logger.info(f"Predictions saved to: {predictions_file}")
    
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

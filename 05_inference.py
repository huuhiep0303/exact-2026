"""
Inference script for EXACT 2026 Type 1 dataset.

This script allows you to run inference on new data or interactive mode.
"""

import os
import sys
from pathlib import Path
import argparse
import json

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.utils.config_loader import load_config
from src.utils.logger import get_logger
from src.evaluation.evaluator import Evaluator

logger = get_logger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run inference with trained model")
    parser.add_argument(
        "--model_path",
        type=str,
        default="outputs/checkpoints/final",
        help="Path to trained model"
    )
    parser.add_argument(
        "--input_file",
        type=str,
        default=None,
        help="Path to input JSON file with premises and questions"
    )
    parser.add_argument(
        "--output_file",
        type=str,
        default="outputs/results/inference_results.json",
        help="Path to save inference results"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    return parser.parse_args()


def interactive_mode(evaluator):
    """
    Run inference in interactive mode.
    
    Args:
        evaluator: Evaluator instance
    """
    logger.info("=" * 80)
    logger.info("Interactive Inference Mode")
    logger.info("=" * 80)
    logger.info("Enter premises (one per line, empty line to finish):")
    logger.info("Then enter your question.")
    logger.info("Type 'quit' to exit.")
    logger.info("=" * 80)
    
    while True:
        # Get premises
        premises = []
        print("\nEnter premises (empty line to finish):")
        while True:
            premise = input(f"Premise {len(premises) + 1}: ").strip()
            if not premise:
                break
            if premise.lower() == 'quit':
                return
            premises.append(premise)
        
        if not premises:
            print("No premises entered. Exiting.")
            break
        
        # Get question
        question = input("\nEnter question: ").strip()
        if question.lower() == 'quit':
            break
        
        if not question:
            print("No question entered. Please try again.")
            continue
        
        # Run inference
        print("\nRunning inference...")
        result = evaluator.evaluate_single(premises, question)
        
        # Display results
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        print(f"Answer: {result['answer']}")
        print(f"\nReasoning:\n{result['reasoning']}")
        print(f"\nRelevant Premises: {result['relevant_premises']}")
        print("=" * 80)


def batch_mode(evaluator, input_file, output_file):
    """
    Run inference in batch mode.
    
    Args:
        evaluator: Evaluator instance
        input_file: Path to input file
        output_file: Path to output file
    """
    logger.info(f"Loading input data from: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} samples")
    
    results = []
    for i, sample in enumerate(data):
        logger.info(f"Processing sample {i+1}/{len(data)}")
        
        premises = sample['premises']
        question = sample['question']
        
        result = evaluator.evaluate_single(premises, question)
        
        results.append({
            'id': sample.get('id', i),
            'question': question,
            'answer': result['answer'],
            'reasoning': result['reasoning'],
            'relevant_premises': result['relevant_premises']
        })
    
    # Save results
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Results saved to: {output_file}")


def main():
    """Main inference function."""
    args = parse_args()
    
    logger.info("=" * 80)
    logger.info("EXACT 2026 - Type 1 Inference")
    logger.info("=" * 80)
    
    # Load configuration
    config_path = "configs/config.yaml"
    logger.info(f"Loading configuration from: {config_path}")
    config = load_config(config_path)
    
    # Check if model exists
    if not os.path.exists(args.model_path):
        logger.error(f"Model not found: {args.model_path}")
        logger.error("Please run 03_train.py first to train the model.")
        sys.exit(1)
    
    # Initialize evaluator
    logger.info(f"Loading model from: {args.model_path}")
    evaluator = Evaluator(
        model_path=args.model_path,
        config=config
    )
    
    # Run inference
    if args.interactive:
        interactive_mode(evaluator)
    elif args.input_file:
        if not os.path.exists(args.input_file):
            logger.error(f"Input file not found: {args.input_file}")
            sys.exit(1)
        batch_mode(evaluator, args.input_file, args.output_file)
    else:
        logger.error("Please specify either --interactive or --input_file")
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("Inference completed!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()

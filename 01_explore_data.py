"""
Data exploration script for EXACT 2026 Type 1 dataset.

This script provides basic statistics and insights about the dataset.
"""

import json
import sys
from pathlib import Path
from collections import Counter

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_data(file_path):
    """Load JSON data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_dataset(data):
    """Analyze dataset and print statistics."""
    logger.info("=" * 80)
    logger.info("DATASET STATISTICS")
    logger.info("=" * 80)
    
    # Basic stats
    num_records = len(data)
    logger.info(f"Total records: {num_records}")
    
    # Count questions
    total_questions = sum(len(record.get('questions', [])) for record in data)
    logger.info(f"Total questions: {total_questions}")
    logger.info(f"Average questions per record: {total_questions / num_records:.2f}")
    
    # Premises statistics
    premise_counts = [len(record.get('premises-NL', [])) for record in data]
    logger.info(f"\nPremises per record:")
    logger.info(f"  Min: {min(premise_counts)}")
    logger.info(f"  Max: {max(premise_counts)}")
    logger.info(f"  Average: {sum(premise_counts) / len(premise_counts):.2f}")
    
    # Question types
    question_types = []
    answer_types = []
    
    for record in data:
        questions = record.get('questions', [])
        answers = record.get('answers', [])
        for i, question_text in enumerate(questions):
            question_text = question_text.lower()
            answer = answers[i] if i < len(answers) else ''
            
            # Detect question type
            if 'yes' in question_text or 'no' in question_text:
                question_types.append('Yes/No')
            elif any(opt in question_text for opt in ['a.', 'b.', 'c.', 'd.', 'a)', 'b)', 'c)', 'd)']):
                question_types.append('Multiple Choice')
            else:
                question_types.append('Other')
            
            answer_types.append(answer)
    
    logger.info(f"\nQuestion types:")
    type_counter = Counter(question_types)
    for qtype, count in type_counter.most_common():
        logger.info(f"  {qtype}: {count} ({count/len(question_types)*100:.1f}%)")
    
    logger.info(f"\nAnswer distribution:")
    answer_counter = Counter(answer_types)
    for answer, count in answer_counter.most_common(10):
        logger.info(f"  {answer}: {count} ({count/len(answer_types)*100:.1f}%)")
    
    # Idx (relevant premises) statistics
    idx_lengths = []
    for record in data:
        for idx in record.get('idx', []):
            if idx:
                idx_lengths.append(len(idx))
    
    if idx_lengths:
        logger.info(f"\nRelevant premises (idx) per question:")
        logger.info(f"  Min: {min(idx_lengths)}")
        logger.info(f"  Max: {max(idx_lengths)}")
        logger.info(f"  Average: {sum(idx_lengths) / len(idx_lengths):.2f}")
    
    # Explanation statistics
    explanation_lengths = []
    for record in data:
        # Some records might use 'explanation' or 'explanations'
        explanations = record.get('explanation', record.get('explanations', []))
        for explanation in explanations:
            if explanation:
                explanation_lengths.append(len(explanation.split()))
    
    if explanation_lengths:
        logger.info(f"\nExplanation length (words):")
        logger.info(f"  Min: {min(explanation_lengths)}")
        logger.info(f"  Max: {max(explanation_lengths)}")
        logger.info(f"  Average: {sum(explanation_lengths) / len(explanation_lengths):.2f}")
    
    logger.info("=" * 80)


def show_samples(data, num_samples=3):
    """Show sample records."""
    logger.info("\nSAMPLE RECORDS")
    logger.info("=" * 80)
    
    for i, record in enumerate(data[:num_samples]):
        logger.info(f"\n--- Record {i+1} ---")
        premises = record.get('premises-NL', [])
        questions = record.get('questions', [])
        answers = record.get('answers', [])
        idxs = record.get('idx', [])
        explanations = record.get('explanation', record.get('explanations', []))
        
        logger.info(f"Number of premises: {len(premises)}")
        logger.info(f"Number of questions: {len(questions)}")
        
        # Show first premise
        if premises:
            logger.info(f"\nFirst premise: {premises[0][:100]}...")
        
        # Show first question
        if questions:
            logger.info(f"\nFirst question: {questions[0][:100]}...")
            if answers:
                logger.info(f"Answer: {answers[0]}")
            if idxs:
                logger.info(f"Relevant premises (idx): {idxs[0]}")
            if explanations:
                logger.info(f"Explanation: {explanations[0][:150]}...")
    
    logger.info("=" * 80)


def main():
    """Main exploration function."""
    logger.info("=" * 80)
    logger.info("EXACT 2026 - Type 1 Data Exploration")
    logger.info("=" * 80)
    
    # Load data
    data_path = "EXACT2026_dataset_2026-05-15/Logic_Based_Educational_Queries_Text_Only/Logic_Based_Educational_Queries.json"
    
    logger.info(f"Loading data from: {data_path}")
    
    try:
        data = load_data(data_path)
    except FileNotFoundError:
        logger.error(f"Data file not found: {data_path}")
        logger.error("Please ensure the dataset is in the correct location.")
        sys.exit(1)
    
    # Analyze dataset
    analyze_dataset(data)
    
    # Show samples
    show_samples(data, num_samples=2)
    
    logger.info("\nExploration completed!")


if __name__ == "__main__":
    main()

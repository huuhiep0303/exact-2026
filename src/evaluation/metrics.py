"""Evaluation metrics."""

from typing import List, Dict, Any
import numpy as np


def calculate_accuracy(predictions: List[Dict[str, Any]]) -> float:
    """
    Calculate answer accuracy.
    
    Args:
        predictions: List of prediction dictionaries
        
    Returns:
        Accuracy score
    """
    correct = 0
    total = len(predictions)
    
    for pred in predictions:
        pred_answer = pred['prediction']['answer']
        true_answer = pred['ground_truth']['answer']
        
        if pred_answer == true_answer:
            correct += 1
    
    return correct / total if total > 0 else 0.0


def calculate_premise_f1(predictions: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate premise selection F1, precision, and recall.
    
    Args:
        predictions: List of prediction dictionaries
        
    Returns:
        Dictionary with precision, recall, and F1 scores
    """
    precisions = []
    recalls = []
    f1_scores = []
    
    for pred in predictions:
        pred_premises = set(pred['prediction']['relevant_premises'])
        true_premises = set(pred['ground_truth']['relevant_premises'])
        
        if len(pred_premises) == 0:
            precision = 0.0
        else:
            precision = len(pred_premises & true_premises) / len(pred_premises)
        
        if len(true_premises) == 0:
            recall = 0.0
        else:
            recall = len(pred_premises & true_premises) / len(true_premises)
        
        if precision + recall == 0:
            f1 = 0.0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)
        
        precisions.append(precision)
        recalls.append(recall)
        f1_scores.append(f1)
    
    return {
        'precision': np.mean(precisions),
        'recall': np.mean(recalls),
        'f1': np.mean(f1_scores)
    }


def evaluate_reasoning_quality(
    reasoning: str,
    criteria: List[str] = ['clarity', 'naturalness', 'depth', 'consistency']
) -> Dict[str, float]:
    """
    Evaluate reasoning quality (simplified heuristic-based).
    
    Args:
        reasoning: Reasoning text
        criteria: List of criteria to evaluate
        
    Returns:
        Dictionary with scores for each criterion
    """
    scores = {}
    
    # Clarity: Based on sentence structure and length
    sentences = reasoning.split('.')
    avg_sentence_length = np.mean([len(s.split()) for s in sentences if s.strip()])
    clarity_score = min(5.0, max(1.0, 5.0 - abs(avg_sentence_length - 20) / 10))
    scores['clarity'] = clarity_score
    
    # Naturalness: Based on presence of natural language markers
    natural_markers = ['because', 'therefore', 'thus', 'since', 'so', 'hence', 'consequently']
    naturalness_score = min(5.0, 2.0 + sum(marker in reasoning.lower() for marker in natural_markers) * 0.5)
    scores['naturalness'] = naturalness_score
    
    # Depth: Based on reasoning length and structure
    depth_score = min(5.0, 1.0 + len(reasoning) / 200)
    scores['depth'] = depth_score
    
    # Consistency: Based on logical connectors
    logical_connectors = ['if', 'then', 'and', 'or', 'not', 'implies']
    consistency_score = min(5.0, 2.0 + sum(conn in reasoning.lower() for conn in logical_connectors) * 0.3)
    scores['consistency'] = consistency_score
    
    # Overall score
    scores['overall'] = np.mean(list(scores.values()))
    
    return scores


def calculate_combined_score(
    accuracy: float,
    premise_f1: float,
    reasoning_quality: float,
    weights: Dict[str, float] = {'accuracy': 0.4, 'premise_f1': 0.2, 'reasoning': 0.4}
) -> float:
    """
    Calculate combined score.
    
    Args:
        accuracy: Accuracy score
        premise_f1: Premise F1 score
        reasoning_quality: Reasoning quality score (1-5, normalized to 0-1)
        weights: Weights for each component
        
    Returns:
        Combined score
    """
    # Normalize reasoning quality to 0-1
    reasoning_normalized = reasoning_quality / 5.0
    
    combined = (
        weights['accuracy'] * accuracy +
        weights['premise_f1'] * premise_f1 +
        weights['reasoning'] * reasoning_normalized
    )
    
    return combined

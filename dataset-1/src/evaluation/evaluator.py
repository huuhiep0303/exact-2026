"""Main evaluator class."""

import json
import os
from typing import Dict, List, Any, Optional
from tqdm import tqdm
import torch

from .metrics import (
    calculate_accuracy,
    calculate_premise_f1,
    evaluate_reasoning_quality,
    calculate_combined_score
)
from ..models.inference import InferencePipeline
from ..models.model_loader import load_trained_model
from ..utils.logger import get_logger
from ..data.data_processor import DataProcessor

logger = get_logger(__name__)


class Evaluator:
    """Evaluator for Type 1 dataset."""
    
    def __init__(
        self,
        model_path: str,
        config: Dict[str, Any],
        device: Optional[str] = None
    ):
        """
        Initialize evaluator.
        
        Args:
            model_path: Path to trained model
            config: Configuration dictionary
            device: Device to use (cuda/cpu)
        """
        self.config = config
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        logger.info(f"Initializing evaluator with model: {model_path}")
        logger.info(f"Using device: {self.device}")
        
        # Load model and tokenizer
        model, tokenizer = load_trained_model(model_path, config)
        
        # Initialize inference pipeline
        self.inference_pipeline = InferencePipeline(
            model=model,
            tokenizer=tokenizer,
            config=config
        )
        
        self.data_processor = DataProcessor(config)
    
    def load_test_data(self, test_file: str) -> List[Dict[str, Any]]:
        """
        Load test data.
        
        Args:
            test_file: Path to test file
            
        Returns:
            List of test samples
        """
        logger.info(f"Loading test data from: {test_file}")
        
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data)} test samples")
        return data
    
    def evaluate(
        self,
        test_file: str,
        output_file: Optional[str] = None,
        save_predictions: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate model on test data.
        
        Args:
            test_file: Path to test file
            output_file: Path to save results
            save_predictions: Whether to save predictions
            
        Returns:
            Dictionary with evaluation results
        """
        # Load test data
        test_data = self.load_test_data(test_file)
        
        # Run inference
        logger.info("Running inference on test data...")
        predictions = []
        
        for sample in tqdm(test_data, desc="Evaluating"):
            # Run inference
            result = self.inference_pipeline.predict(sample)
            
            # Extract question text from input prompt
            question = ""
            for line in sample['input'].split("\n"):
                if line.startswith("Question:"):
                    question = line.replace("Question:", "").strip()
            
            # Store prediction with ground truth
            predictions.append({
                'id': sample.get('id', ''),
                'question': question,
                'prediction': {
                    'answer': result['prediction']['answer'],
                    'reasoning': result['prediction']['reasoning'],
                    'relevant_premises': result['prediction']['relevant_premises']
                },
                'ground_truth': {
                    'answer': result['ground_truth']['answer'],
                    'explanation': "",
                    'relevant_premises': result['ground_truth']['relevant_premises']
                }
            })
        
        # Calculate metrics
        logger.info("Calculating metrics...")
        results = self._calculate_metrics(predictions)
        
        # Save results
        if output_file:
            self._save_results(results, predictions, output_file, save_predictions)
        
        return results
    
    def _calculate_metrics(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate all evaluation metrics.
        
        Args:
            predictions: List of predictions
            
        Returns:
            Dictionary with all metrics
        """
        # Calculate accuracy
        accuracy = calculate_accuracy(predictions)
        logger.info(f"Accuracy: {accuracy:.4f}")
        
        # Calculate premise F1
        premise_metrics = calculate_premise_f1(predictions)
        logger.info(f"Premise F1: {premise_metrics['f1']:.4f}")
        logger.info(f"Premise Precision: {premise_metrics['precision']:.4f}")
        logger.info(f"Premise Recall: {premise_metrics['recall']:.4f}")
        
        # Calculate reasoning quality
        reasoning_sample_size = self.config.get('evaluation', {}).get('reasoning_sample_size', 200)
        reasoning_scores = []
        
        for pred in predictions[:reasoning_sample_size]:
            reasoning = pred['prediction']['reasoning']
            scores = evaluate_reasoning_quality(reasoning)
            reasoning_scores.append(scores['overall'])
        
        avg_reasoning_quality = sum(reasoning_scores) / len(reasoning_scores) if reasoning_scores else 0.0
        logger.info(f"Reasoning Quality: {avg_reasoning_quality:.4f}")
        
        # Calculate combined score
        combined_score = calculate_combined_score(
            accuracy=accuracy,
            premise_f1=premise_metrics['f1'],
            reasoning_quality=avg_reasoning_quality
        )
        logger.info(f"Combined Score: {combined_score:.4f}")
        
        return {
            'accuracy': accuracy,
            'premise_metrics': premise_metrics,
            'reasoning_quality': avg_reasoning_quality,
            'combined_score': combined_score,
            'num_samples': len(predictions)
        }
    
    def _save_results(
        self,
        results: Dict[str, Any],
        predictions: List[Dict[str, Any]],
        output_file: str,
        save_predictions: bool
    ):
        """
        Save evaluation results.
        
        Args:
            results: Evaluation results
            predictions: List of predictions
            output_file: Path to save results
            save_predictions: Whether to save predictions
        """
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_file}")
        
        # Save predictions if requested
        if save_predictions:
            predictions_file = output_file.replace('.json', '_predictions.json')
            with open(predictions_file, 'w', encoding='utf-8') as f:
                json.dump(predictions, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Predictions saved to: {predictions_file}")
    
    def evaluate_single(
        self,
        premises: List[str],
        question: str,
        ground_truth: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate single sample.
        
        Args:
            premises: List of premises
            question: Question text
            ground_truth: Ground truth (optional)
            
        Returns:
            Prediction result
        """
        prompt = self.data_processor.create_prompt(premises, question)
        example = {
            'input': prompt,
            'metadata': {
                'num_premises': len(premises),
                'question_type': 'MCQ' if any(a in question for a in ['A)', 'B)', 'C)', 'D)']) else 'YesNo',
                'answer': '',
                'relevant_premises_idx': []
            }
        }
        
        result_full = self.inference_pipeline.predict(example)
        result = result_full['prediction']
        
        if ground_truth:
            # Calculate metrics for this sample
            pred = {
                'prediction': {
                    'answer': result['answer'],
                    'reasoning': result['reasoning'],
                    'relevant_premises': result['relevant_premises']
                },
                'ground_truth': ground_truth
            }
            
            accuracy = calculate_accuracy([pred])
            premise_metrics = calculate_premise_f1([pred])
            reasoning_scores = evaluate_reasoning_quality(result['reasoning'])
            
            result['metrics'] = {
                'accuracy': accuracy,
                'premise_f1': premise_metrics['f1'],
                'reasoning_quality': reasoning_scores['overall']
            }
        
        return result

"""Inference pipeline."""

import torch
from typing import Dict, Any, List
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm

from ..utils.helpers import extract_premise_indices, extract_answer


class InferencePipeline:
    """Pipeline for model inference."""
    
    def __init__(
        self,
        model: AutoModelForCausalLM,
        tokenizer: AutoTokenizer,
        config: Dict[str, Any]
    ):
        """
        Initialize inference pipeline.
        
        Args:
            model: Model
            tokenizer: Tokenizer
            config: Configuration dictionary
        """
        self.model = model
        self.tokenizer = tokenizer
        self.config = config
        self.device = next(model.parameters()).device
    
    def generate(self, prompt: str) -> str:
        """
        Generate response for a prompt.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated text
        """
        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors='pt',
            max_length=self.config['model']['max_length'],
            truncation=True
        ).to(self.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.config['inference']['max_new_tokens'],
                num_beams=self.config['inference']['num_beams'],
                temperature=self.config['inference']['temperature'],
                top_p=self.config['inference']['top_p'],
                do_sample=self.config['model']['do_sample'],
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode
        generated_text = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )
        
        # Extract only the response part (after the prompt)
        response = generated_text[len(prompt):].strip()
        
        return response
    
    def parse_response(
        self,
        response: str,
        num_premises: int,
        question_type: str
    ) -> Dict[str, Any]:
        """
        Parse model response.
        
        Args:
            response: Model response
            num_premises: Total number of premises
            question_type: "MCQ" or "YesNo"
            
        Returns:
            Parsed response dictionary
        """
        # Extract relevant premises
        relevant_premises = extract_premise_indices(response, num_premises)
        
        # Extract answer
        answer = extract_answer(response, question_type)
        
        # Extract reasoning (text between "Reasoning:" and "Answer:")
        reasoning = ""
        if "**Reasoning:**" in response and "**Answer:**" in response:
            start = response.find("**Reasoning:**") + len("**Reasoning:**")
            end = response.find("**Answer:**")
            reasoning = response[start:end].strip()
        elif "Reasoning:" in response and "Answer:" in response:
            start = response.find("Reasoning:") + len("Reasoning:")
            end = response.find("Answer:")
            reasoning = response[start:end].strip()
        else:
            reasoning = response
        
        return {
            'relevant_premises': relevant_premises,
            'reasoning': reasoning,
            'answer': answer,
            'raw_response': response
        }
    
    def predict(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make prediction for a single example.
        
        Args:
            example: Example dictionary
            
        Returns:
            Prediction dictionary
        """
        prompt = example['input']
        metadata = example['metadata']
        
        # Generate response
        response = self.generate(prompt)
        
        # Parse response
        parsed = self.parse_response(
            response,
            metadata['num_premises'],
            metadata['question_type']
        )
        
        return {
            'prediction': parsed,
            'ground_truth': {
                'relevant_premises': metadata['relevant_premises_idx'],
                'answer': metadata['answer']
            },
            'metadata': metadata
        }
    
    def predict_batch(
        self,
        examples: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Make predictions for a batch of examples.
        
        Args:
            examples: List of examples
            show_progress: Whether to show progress bar
            
        Returns:
            List of predictions
        """
        predictions = []
        
        iterator = tqdm(examples, desc="Predicting") if show_progress else examples
        
        for example in iterator:
            pred = self.predict(example)
            predictions.append(pred)
        
        return predictions

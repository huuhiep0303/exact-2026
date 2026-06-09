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
    
    def generate(self, messages: list) -> str:
        """
        Generate response for a prompt.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Generated text (response only, not including the prompt)
        """
        # Tokenize using chat template
        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors='pt',
            return_dict=True
        ).to(self.device)
        
        input_length = inputs['input_ids'].shape[1]
        
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
        
        # Extract only the generated tokens (after the input)
        response_ids = outputs[0][input_length:]
        response = self.tokenizer.decode(
            response_ids,
            skip_special_tokens=True
        ).strip()
        
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
        # Extract relevant premises — only from the "Relevant Premises" section
        # to avoid picking up premise references from reasoning text
        premises_section = ""
        if "**Relevant Premises:**" in response:
            start = response.find("**Relevant Premises:**")
            # Find next section
            end = response.find("**Reasoning:**", start)
            if end == -1:
                end = response.find("**Answer:**", start)
            if end == -1:
                end = len(response)
            premises_section = response[start:end]
        else:
            premises_section = response
        
        relevant_premises = extract_premise_indices(premises_section, num_premises)
        
        # Extract answer — prioritize the "Answer:" section
        answer_section = ""
        if "**Answer:**" in response:
            start = response.find("**Answer:**") + len("**Answer:**")
            answer_section = response[start:].strip()
        else:
            answer_section = response
        
        answer = extract_answer(answer_section, question_type)
        
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
        
        # Apply Qwen chat template to match training
        messages = [
            {"role": "system", "content": "You are a logical reasoning expert."},
            {"role": "user", "content": prompt}
        ]
        
        # Generate response
        response = self.generate(messages)
        
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

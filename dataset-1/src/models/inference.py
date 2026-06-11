"""Inference pipeline."""

import torch
from typing import Dict, Any, List
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm

from ..utils.helpers import extract_premise_indices, extract_answer
from ..data.data_processor import SYSTEM_PROMPT


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
        # Tokenize using chat template with thinking enabled for Qwen3
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True  # Qwen3: enable thinking mode
        )
        
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            add_special_tokens=False
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
        import re
        think_match = re.search(r'<think>\n?(.*?)\n?</think>', response, re.DOTALL)
        think_block = think_match.group(1) if think_match else response

        # Extract relevant premises — only from the "Relevant Premises" section
        # to avoid picking up premise references from reasoning text
        premises_section = ""
        if "**Relevant Premises:**" in think_block:
            start = think_block.find("**Relevant Premises:**")
            # Find next section
            end = think_block.find("**Reasoning:**", start)
            if end == -1:
                end = len(think_block)
            premises_section = think_block[start:end]
        else:
            premises_section = think_block
        
        relevant_premises = extract_premise_indices(premises_section, num_premises)
        
        # Extract answer — prioritize the "Answer:" section
        answer_section = ""
        if "**Answer:**" in response:
            start = response.find("**Answer:**") + len("**Answer:**")
            answer_section = response[start:].strip()
        else:
            # If Answer section is not explicitly marked, try to get anything after </think>
            after_think_match = re.search(r'</think>\s*(.*)', response, re.DOTALL)
            if after_think_match:
                answer_section = after_think_match.group(1).strip()
            else:
                answer_section = response
        
        answer = extract_answer(answer_section, question_type)
        
        # Extract reasoning
        reasoning = ""
        if "**Reasoning:**" in think_block:
            start = think_block.find("**Reasoning:**") + len("**Reasoning:**")
            reasoning = think_block[start:].strip()
        else:
            reasoning = think_block.strip()
        
        return {
            'relevant_premises': relevant_premises,
            'reasoning': reasoning,
            'answer': answer,
            'raw_response': response
        }
    
    def predict(self, example: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make prediction for a single example.
        
        CRITICAL FIX: The example['input'] now contains only the user message
        content (no chat template tokens). We build the chat messages properly
        using the shared SYSTEM_PROMPT so the format EXACTLY matches training.
        
        Args:
            example: Example dictionary with 'input' (user content) and 'metadata'
            
        Returns:
            Prediction dictionary
        """
        user_content = example['input']
        metadata = example['metadata']
        
        # Build chat messages using the SAME system prompt as training
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
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

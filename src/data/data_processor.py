"""Data preprocessing."""

import random
from typing import List, Dict, Any, Tuple
from pathlib import Path

from .data_loader import load_raw_data, save_processed_data
from ..utils.helpers import format_premises


# System prompt used consistently across training AND inference.
# Import this from anywhere to ensure consistency.
SYSTEM_PROMPT = """You are an expert in formal logical reasoning. Your task is to analyze premises and answer questions using rigorous logical deduction.

Rules:
1. Select ONLY the MINIMUM premises needed to answer the question.
2. Provide clear, step-by-step reasoning based strictly on the selected premises.
3. For Yes/No questions: Answer "Yes" ONLY if the conclusion can be logically DERIVED from the premises. Answer "No" if the premises CONTRADICT the conclusion. Answer "Unknown" if the premises are INSUFFICIENT to determine the truth of the conclusion.
4. For multiple choice questions: Select the option that is BEST supported by the premises.
5. Your answer MUST be consistent with your reasoning. Do NOT contradict your own analysis."""


class DataProcessor:
    """Process raw data into training format."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize data processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.random_seed = config['split']['random_seed']
        random.seed(self.random_seed)
    
    def create_prompt(
        self,
        premises: List[str],
        question: str
    ) -> str:
        """
        Create input prompt — returns ONLY the user message content.
        
        The chat template (system message, role tokens) will be applied
        by the tokenizer during training/inference. This function should
        NOT include any special tokens like <|im_start|> or <|im_end|>.
        
        Args:
            premises: List of premises
            question: Question text
            
        Returns:
            User message content string (no chat template tokens)
        """
        premises_text = format_premises(premises)
        
        user_message = f"""Given the following premises, answer the question below.

Premises:
{premises_text}

Question: {question}

Provide your response in EXACTLY this format:
<think>
**Relevant Premises:** [List only the premise numbers you used, e.g., P1, P3, P5]
**Reasoning:** [Step-by-step logical deduction using only the selected premises]
</think>
**Answer:** [Your final answer: A/B/C/D or Yes/No/Unknown]"""
        
        return user_message
    
    def create_response(
        self,
        idx: List[int],
        explanation: str,
        answer: str
    ) -> str:
        """
        Create expected response — returns ONLY the assistant message content.
        
        NO special tokens (<|im_end|>) should be included here.
        The tokenizer's chat template will handle adding them.
        
        Args:
            idx: List of relevant premise indices
            explanation: Explanation text
            answer: Answer
            
        Returns:
            Assistant response content (no chat template tokens)
        """
        relevant_premises_str = ", ".join([f"P{i}" for i in idx])
        
        response = f"""<think>
**Relevant Premises:** {relevant_premises_str}
**Reasoning:** {explanation}
</think>
**Answer:** {answer}"""
        
        return response
    
    def process_record(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process a single record into training examples.
        
        Args:
            record: Raw record
            
        Returns:
            List of training examples
        """
        premises_nl = record['premises-NL']
        questions = record['questions']
        answers = record['answers']
        explanations = record.get('explanation', record.get('explanations', [''] * len(questions)))
        idx_lists = record['idx']
        
        examples = []
        
        for q_id, (question, answer, explanation, idx) in enumerate(
            zip(questions, answers, explanations, idx_lists)
        ):
            # Determine question type
            if answer in ['A', 'B', 'C', 'D']:
                question_type = 'MCQ'
            else:
                question_type = 'YesNo'
            
            # Create prompt (user content only) and response (assistant content only)
            prompt = self.create_prompt(premises_nl, question)
            response = self.create_response(idx, explanation, answer)
            
            example = {
                'input': prompt,
                'output': response,
                'metadata': {
                    'num_premises': len(premises_nl),
                    'num_premises_used': len(idx),
                    'question_type': question_type,
                    'answer': answer,
                    'relevant_premises_idx': idx
                }
            }
            
            examples.append(example)
        
        return examples
    
    def split_data(
        self,
        data: List[Dict[str, Any]]
    ) -> Tuple[List, List, List]:
        """
        Split data into train/val/test sets.
        
        Args:
            data: List of examples
            
        Returns:
            Tuple of (train, val, test) lists
        """
        data_copy = data.copy()
        random.shuffle(data_copy)
        
        n = len(data_copy)
        train_ratio = self.config['split']['train']
        val_ratio = self.config['split']['val']
        
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        
        train_data = data_copy[:train_end]
        val_data = data_copy[train_end:val_end]
        test_data = data_copy[val_end:]
        
        return train_data, val_data, test_data
    
    def process_and_save(self):
        """Process raw data and save train/val/test splits."""
        # Load raw data
        raw_data = load_raw_data(self.config['data']['raw_data_path'])
        
        # Process all records
        all_examples = []
        for record in raw_data:
            examples = self.process_record(record)
            all_examples.extend(examples)
        
        # Split data
        train_data, val_data, test_data = self.split_data(all_examples)
        
        # Save splits
        processed_dir = Path(self.config['data']['processed_dir'])
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        save_processed_data(train_data, processed_dir / 'train.json')
        save_processed_data(val_data, processed_dir / 'val.json')
        save_processed_data(test_data, processed_dir / 'test.json')
        
        return {
            'train': len(train_data),
            'val': len(val_data),
            'test': len(test_data),
            'total': len(all_examples)
        }

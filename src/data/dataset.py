"""PyTorch Dataset for logic reasoning."""

import torch
from torch.utils.data import Dataset
from typing import List, Dict, Any
from transformers import PreTrainedTokenizer

from .data_processor import SYSTEM_PROMPT


class LogicReasoningDataset(Dataset):
    """Dataset for logic reasoning tasks."""
    
    def __init__(
        self,
        data: List[Dict[str, Any]],
        tokenizer: PreTrainedTokenizer,
        max_length: int = 3072
    ):
        """
        Initialize dataset.
        
        Args:
            data: List of examples (each with 'input' and 'output' keys)
            tokenizer: Tokenizer
            max_length: Maximum sequence length
        """
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self) -> int:
        """Return dataset size."""
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get a single example.
        
        Uses the tokenizer's chat template to format messages consistently.
        The SYSTEM_PROMPT is imported from data_processor to ensure the
        same system message is used everywhere (training, inference).
        
        Label masking: Only the assistant's response tokens contribute to
        the loss. The prompt portion (system + user + generation prompt)
        is masked with -100.
        
        Args:
            idx: Example index
            
        Returns:
            Dictionary with tokenized inputs
        """
        example = self.data[idx]
        
        # Build chat messages using the shared SYSTEM_PROMPT
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": example['input']}
        ]
        
        # Tokenize prompt only (system + user + generation prompt) to find boundary
        prompt_str = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
            enable_thinking=True  # Qwen3: enable thinking for SFT
        )
        prompt_encoding = self.tokenizer(prompt_str, add_special_tokens=False)
        input_length = len(prompt_encoding['input_ids'])
        
        # Build full messages including assistant response
        messages.append({"role": "assistant", "content": example['output']})
        full_str = self.tokenizer.apply_chat_template(
            messages, tokenize=False,
            enable_thinking=True  # Qwen3: enable thinking for SFT
        )
        
        # Tokenize full text
        encoding = self.tokenizer(
            full_str,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt',
            add_special_tokens=False
        )
        
        # Create labels — only compute loss on the response part
        labels = encoding['input_ids'].clone()
        
        # Mask the prompt portion (set to -100 so loss is not computed)
        labels[0, :input_length] = -100
        
        # Mask padding tokens in labels
        labels[labels == self.tokenizer.pad_token_id] = -100
        
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': labels.squeeze(0)
        }

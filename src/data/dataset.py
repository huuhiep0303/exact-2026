"""PyTorch Dataset for logic reasoning."""

import torch
from torch.utils.data import Dataset
from typing import List, Dict, Any
from transformers import PreTrainedTokenizer


class LogicReasoningDataset(Dataset):
    """Dataset for logic reasoning tasks."""
    
    def __init__(
        self,
        data: List[Dict[str, Any]],
        tokenizer: PreTrainedTokenizer,
        max_length: int = 4096
    ):
        """
        Initialize dataset.
        
        Args:
            data: List of examples
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
        
        Args:
            idx: Example index
            
        Returns:
            Dictionary with tokenized inputs
        """
        example = self.data[idx]
        
        # Combine input and output for training
        full_text = example['input'] + example['output']
        
        # Tokenize
        encoding = self.tokenizer(
            full_text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        # Create labels (same as input_ids for causal LM)
        labels = encoding['input_ids'].clone()
        
        # Mask padding tokens in labels
        labels[labels == self.tokenizer.pad_token_id] = -100
        
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'labels': labels.squeeze(0)
        }

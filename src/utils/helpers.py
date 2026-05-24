"""Helper functions."""

import random
import numpy as np
import torch
from pathlib import Path
from typing import List


def set_seed(seed: int = 42):
    """
    Set random seed for reproducibility.
    
    Args:
        seed: Random seed
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def create_directories(dirs: List[str]):
    """
    Create directories if they don't exist.
    
    Args:
        dirs: List of directory paths
    """
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)


def format_premises(premises: List[str]) -> str:
    """
    Format premises with numbering.
    
    Args:
        premises: List of premise strings
        
    Returns:
        Formatted premises string
    """
    formatted = []
    for i, premise in enumerate(premises, 1):
        formatted.append(f"P{i}: {premise}")
    return "\n".join(formatted)


def extract_premise_indices(text: str, num_premises: int) -> List[int]:
    """
    Extract premise indices from text.
    
    Args:
        text: Text containing premise references (e.g., "P1, P5, P7")
        num_premises: Total number of premises
        
    Returns:
        List of premise indices (1-based)
    """
    import re
    
    pattern = r'P(\d+)'
    matches = re.findall(pattern, text)
    indices = [int(m) for m in matches]
    
    # Validate indices
    indices = [i for i in indices if 1 <= i <= num_premises]
    
    return sorted(set(indices))


def extract_answer(text: str, question_type: str) -> str:
    """
    Extract answer from model output.
    
    Args:
        text: Model output text
        question_type: "MCQ" or "YesNo"
        
    Returns:
        Extracted answer
    """
    import re
    
    if question_type == "MCQ":
        # Look for A, B, C, D
        pattern = r'\b([ABCD])\b'
        matches = re.findall(pattern, text, re.IGNORECASE)
        return matches[-1].upper() if matches else "Unknown"
    else:
        # Look for Yes, No, Unknown
        pattern = r'\b(Yes|No|Unknown)\b'
        matches = re.findall(pattern, text, re.IGNORECASE)
        return matches[-1].capitalize() if matches else "Unknown"

"""Data loading functions."""

import json
from pathlib import Path
from typing import List, Dict, Any


def load_raw_data(data_path: str) -> List[Dict[str, Any]]:
    """
    Load raw dataset from JSON file.
    
    Args:
        data_path: Path to JSON file
        
    Returns:
        List of records
    """
    data_path = Path(data_path)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def load_processed_data(data_path: str) -> List[Dict[str, Any]]:
    """
    Load processed dataset from JSON file.
    
    Args:
        data_path: Path to processed JSON file
        
    Returns:
        List of processed examples
    """
    return load_raw_data(data_path)


def save_processed_data(data: List[Dict[str, Any]], save_path: str):
    """
    Save processed data to JSON file.
    
    Args:
        data: List of processed examples
        save_path: Path to save file
    """
    save_path = Path(save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

"""Model loading utilities."""

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig
)
from peft import PeftModel, LoraConfig, get_peft_model
from typing import Dict, Any, Tuple


def load_model_and_tokenizer(
    config: Dict[str, Any],
    for_training: bool = True
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load model and tokenizer.
    
    Supports both Qwen2.5 and Qwen3 models. Both use ChatML format
    with <|im_start|>/<|im_end|> special tokens.
    
    Args:
        config: Configuration dictionary
        for_training: Whether loading for training
        
    Returns:
        Tuple of (model, tokenizer)
    """
    model_name = config['model']['name']
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side='right'
    )
    
    # Set pad token — for Qwen models, use <|endoftext|> as pad token
    # to avoid conflicts with <|im_end|> (the eos_token used in chat template)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = '<|endoftext|>'
        tokenizer.pad_token_id = tokenizer.convert_tokens_to_ids('<|endoftext|>')
    
    # Quantization config
    if config['quantization']['load_in_4bit']:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type=config['quantization']['bnb_4bit_quant_type'],
            bnb_4bit_use_double_quant=config['quantization']['bnb_4bit_use_double_quant']
        )
    else:
        bnb_config = None
    
    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16
    )
    
    # Prepare for training with LoRA
    if for_training:
        # Enable gradient checkpointing
        model.gradient_checkpointing_enable()
        
        # Prepare model for k-bit training
        from peft import prepare_model_for_kbit_training
        model = prepare_model_for_kbit_training(model)
        
        # Add LoRA adapters
        lora_config = LoraConfig(
            r=config['lora']['r'],
            lora_alpha=config['lora']['lora_alpha'],
            target_modules=config['lora']['target_modules'],
            lora_dropout=config['lora']['lora_dropout'],
            bias=config['lora']['bias'],
            task_type=config['lora']['task_type']
        )
        
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
    
    return model, tokenizer


def load_trained_model(
    checkpoint_path: str,
    config: Dict[str, Any]
) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
    """
    Load trained model from checkpoint.
    
    Args:
        checkpoint_path: Path to checkpoint
        config: Configuration dictionary
        
    Returns:
        Tuple of (model, tokenizer)
    """
    model_name = config['model']['name']
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        padding_side='right'
    )
    
    if tokenizer.pad_token is None:
        tokenizer.pad_token = '<|endoftext|>'
        tokenizer.pad_token_id = tokenizer.convert_tokens_to_ids('<|endoftext|>')
    
    # Quantization config
    if config['quantization']['load_in_4bit']:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type=config['quantization']['bnb_4bit_quant_type'],
            bnb_4bit_use_double_quant=config['quantization']['bnb_4bit_use_double_quant']
        )
    else:
        bnb_config = None
    
    # Load base model
    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.float16
    )
    
    # Load LoRA weights
    model = PeftModel.from_pretrained(base_model, checkpoint_path)
    
    return model, tokenizer

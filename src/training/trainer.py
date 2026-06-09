"""Training functions."""

import torch
from transformers import (
    Trainer,
    TrainingArguments,
    default_data_collator
)
from typing import Dict, Any
from pathlib import Path

from ..data import load_processed_data, LogicReasoningDataset
from ..models import load_model_and_tokenizer
from ..utils import get_logger


def train_model(config: Dict[str, Any]):
    """
    Train model with LoRA.
    
    Args:
        config: Configuration dictionary
    """
    logger = get_logger(
        name="trainer",
        log_file=f"{config['logging']['log_dir']}/training.log"
    )
    
    logger.info("=" * 80)
    logger.info("Starting training")
    logger.info("=" * 80)
    
    # Load model and tokenizer
    logger.info(f"Loading model: {config['model']['name']}")
    model, tokenizer = load_model_and_tokenizer(config, for_training=True)
    
    # Load data
    logger.info("Loading training data...")
    train_data = load_processed_data(config['data']['train_file'])
    val_data = load_processed_data(config['data']['val_file'])
    
    logger.info(f"Train examples: {len(train_data)}")
    logger.info(f"Val examples: {len(val_data)}")
    
    # Create datasets
    train_dataset = LogicReasoningDataset(
        train_data,
        tokenizer,
        max_length=config['model']['max_length']
    )
    
    val_dataset = LogicReasoningDataset(
        val_data,
        tokenizer,
        max_length=config['model']['max_length']
    )
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=config['training']['output_dir'],
        num_train_epochs=config['training']['num_train_epochs'],
        per_device_train_batch_size=config['training']['per_device_train_batch_size'],
        per_device_eval_batch_size=config['training']['per_device_eval_batch_size'],
        gradient_accumulation_steps=config['training']['gradient_accumulation_steps'],
        learning_rate=config['training']['learning_rate'],
        weight_decay=config['training']['weight_decay'],
        warmup_steps=config['training']['warmup_steps'],
        warmup_ratio=config.get('training', {}).get('warmup_ratio', 0.0),
        logging_steps=config['training']['logging_steps'],
        eval_steps=config['training']['eval_steps'],
        save_steps=config['training']['save_steps'],
        save_total_limit=config['training']['save_total_limit'],
        fp16=config['training']['fp16'],
        optim=config['training']['optim'],
        lr_scheduler_type=config['training']['lr_scheduler_type'],
        max_grad_norm=config['training']['max_grad_norm'],
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={'use_reentrant': False},
        eval_strategy="steps",
        save_strategy="steps",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="tensorboard" if not config['logging']['use_wandb'] else "wandb",
        logging_dir=config['logging']['log_dir'],
        remove_unused_columns=False
    )
    
    # Initialize trainer — use default_data_collator to preserve our custom labels
    # (DataCollatorForLanguageModeling would override our label masking)
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=default_data_collator
    )
    
    # Train
    logger.info("Starting training...")
    train_result = trainer.train()
    
    # Save final model
    logger.info("Saving final model...")
    trainer.save_model(f"{config['training']['output_dir']}/final")
    
    # Save training metrics
    metrics = train_result.metrics
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)
    
    logger.info("=" * 80)
    logger.info("Training completed!")
    logger.info("=" * 80)
    
    return trainer

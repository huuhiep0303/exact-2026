"""
Train a QLoRA adapter for the Physics AI reasoner.

This script intentionally uses a fixed config file instead of an automatic
hyperparameter search. Use the Modal A100 Qwen3 config for the current
Phase 5 run, or pass an older config explicitly when comparing baselines.
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "finetuning" / "configs" / "qwen3_8b_modal_a100.yaml"


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.lower() in {"null", "none", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        if "." in value or "e" in value.lower():
            return float(value)
        return int(value)
    except ValueError:
        return value.strip("\"'")


def load_simple_yaml(path: Path) -> dict[str, Any]:
    """Load the flat YAML files used by this project without extra deps."""
    config: dict[str, Any] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        config[key.strip()] = parse_scalar(value)
    return config


def resolve_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def apply_overrides(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    overrides = {
        "train_file": args.train_file,
        "val_file": args.val_file,
        "test_file": args.test_file,
        "output_dir": args.output_dir,
        "max_steps": args.max_steps,
    }
    for key, value in overrides.items():
        if value is not None:
            config[key] = str(value) if isinstance(value, Path) else value
    if args.model_name:
        config["model_name"] = args.model_name
    return config


def load_jsonl_dataset(path: Path):
    from datasets import load_dataset

    dataset = load_dataset("json", data_files=str(path), split="train")
    if "trainable" in dataset.column_names:
        dataset = dataset.filter(lambda row: bool(row.get("trainable", True)))
    return dataset


def tokenize_dataset(dataset, tokenizer, max_seq_length: int, split_name: str = "dataset"):
    def tokenize(batch):
        encoded = tokenizer(
            batch["text"],
            truncation=True,
            max_length=max_seq_length,
            padding=False,
        )
        prompt_texts = batch.get("prompt_text") or batch.get("prompt") or [""] * len(batch["text"])
        labels = []
        for input_ids, prompt_text in zip(encoded["input_ids"], prompt_texts):
            prompt_ids = tokenizer(
                prompt_text,
                add_special_tokens=False,
                truncation=True,
                max_length=max_seq_length,
                padding=False,
            )["input_ids"]
            label_ids = list(input_ids)
            cutoff = min(len(prompt_ids), len(label_ids))
            label_ids[:cutoff] = [-100] * cutoff
            labels.append(label_ids)
        encoded["labels"] = labels
        return encoded

    keep_columns = dataset.column_names
    tokenized = dataset.map(tokenize, batched=True, remove_columns=keep_columns)

    supervised_counts = [
        sum(1 for token_id in labels if token_id != -100)
        for labels in tokenized["labels"]
    ]
    zero_supervised = sum(count == 0 for count in supervised_counts)
    median_supervised = statistics.median(supervised_counts) if supervised_counts else 0
    min_supervised = min(supervised_counts, default=0)
    max_supervised = max(supervised_counts, default=0)
    print(
        f"[SFT] {split_name}: {len(supervised_counts)} examples, "
        f"zero-supervised={zero_supervised}, "
        f"supervised_tokens min/median/max="
        f"{min_supervised}/{median_supervised}/{max_supervised}"
    )
    if supervised_counts and zero_supervised == len(supervised_counts):
        raise ValueError(
            f"All {split_name} examples have zero supervised completion tokens. "
            "Increase max_seq_length or shorten the prompt before training."
        )
    if supervised_counts and zero_supervised / len(supervised_counts) > 0.05:
        raise ValueError(
            f"{zero_supervised}/{len(supervised_counts)} {split_name} examples have "
            "zero supervised completion tokens. Increase max_seq_length or shorten prompts."
        )
    return tokenized


class PromptCompletionCollator:
    """Pad prompt-masked Causal LM batches without recreating labels."""

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, Any]:
        labels = [feature.pop("labels") for feature in features]
        batch = self.tokenizer.pad(features, padding=True, return_tensors="pt")

        import torch

        max_len = batch["input_ids"].shape[1]
        padded_labels = []
        for label in labels:
            pad_len = max_len - len(label)
            padded_labels.append(label + [-100] * pad_len)
        batch["labels"] = torch.tensor(padded_labels, dtype=torch.long)
        return batch


def training_args_kwargs(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    from transformers import TrainingArguments

    kwargs: dict[str, Any] = {
        "output_dir": str(output_dir),
        "per_device_train_batch_size": int(config["per_device_train_batch_size"]),
        "gradient_accumulation_steps": int(config["gradient_accumulation_steps"]),
        "num_train_epochs": float(config["num_train_epochs"]),
        "learning_rate": float(config["learning_rate"]),
        "warmup_steps": int(config.get("warmup_steps", 0)),
        "logging_steps": int(config.get("logging_steps", 10)),
        "save_strategy": str(config.get("save_strategy", "epoch")),
        "seed": int(config.get("seed", 42)),
        "optim": "adamw_8bit",
        "weight_decay": 0.01,
        "lr_scheduler_type": "linear",
        "report_to": "none",
        "save_total_limit": 2,
    }

    eval_strategy_key = (
        "eval_strategy"
        if "eval_strategy" in inspect.signature(TrainingArguments.__init__).parameters
        else "evaluation_strategy"
    )
    kwargs[eval_strategy_key] = str(config.get("eval_strategy", "epoch"))

    max_steps = config.get("max_steps")
    if max_steps not in {None, "", 0, "0"}:
        kwargs["max_steps"] = int(max_steps)

    if bool(config.get("load_best_model_at_end", False)) and str(config.get("eval_strategy")) != "no":
        kwargs["load_best_model_at_end"] = True
        kwargs["metric_for_best_model"] = "eval_loss"
        kwargs["greater_is_better"] = False

    return kwargs


def train(config: dict[str, Any]) -> Path:
    import torch
    from unsloth import FastLanguageModel, is_bfloat16_supported
    from transformers import Trainer, TrainingArguments

    train_file = resolve_path(config["train_file"])
    val_file = resolve_path(config.get("val_file"))
    output_dir = resolve_path(config["output_dir"])
    assert train_file is not None
    assert output_dir is not None
    output_dir.mkdir(parents=True, exist_ok=True)

    model_name = str(config["model_name"])
    max_seq_length = int(config["max_seq_length"])
    target_modules = str(config["target_modules"]).split(",")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=max_seq_length,
        dtype=None,
        load_in_4bit=bool(config.get("load_in_4bit", True)),
        token=os.getenv("HF_TOKEN") or None,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    if hasattr(model, "config"):
        model.config.use_cache = False
    model = FastLanguageModel.get_peft_model(
        model,
        r=int(config["lora_r"]),
        target_modules=[m.strip() for m in target_modules if m.strip()],
        lora_alpha=int(config["lora_alpha"]),
        lora_dropout=float(config.get("lora_dropout", 0.0)),
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=int(config.get("seed", 42)),
    )

    train_dataset = tokenize_dataset(load_jsonl_dataset(train_file), tokenizer, max_seq_length, split_name="train")
    eval_dataset = None
    if val_file and val_file.exists() and str(config.get("eval_strategy", "epoch")) != "no":
        eval_dataset = tokenize_dataset(load_jsonl_dataset(val_file), tokenizer, max_seq_length, split_name="val")

    args_kwargs = training_args_kwargs(config, output_dir)
    args_kwargs["bf16"] = is_bfloat16_supported()
    args_kwargs["fp16"] = not args_kwargs["bf16"]
    training_args = TrainingArguments(**args_kwargs)

    collator = PromptCompletionCollator(tokenizer=tokenizer)
    trainer = Trainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=collator,
    )
    train_result = trainer.train()
    trainer.save_model(str(output_dir / "adapter"))
    tokenizer.save_pretrained(str(output_dir / "adapter"))

    metrics = train_result.metrics
    metrics["train_samples"] = len(train_dataset)
    if eval_dataset is not None:
        metrics["eval_samples"] = len(eval_dataset)
    metrics["cuda_available"] = torch.cuda.is_available()
    (output_dir / "train_metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "resolved_config.json").write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a LoRA adapter with Unsloth.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--model-name", type=str, default=None)
    parser.add_argument("--train-file", type=Path, default=None)
    parser.add_argument("--val-file", type=Path, default=None)
    parser.add_argument("--test-file", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = apply_overrides(load_simple_yaml(args.config), args)
    output_dir = train(config)
    print(f"Saved LoRA adapter and metrics to: {output_dir}")


if __name__ == "__main__":
    main()

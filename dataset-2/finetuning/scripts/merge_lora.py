"""Merge a trained LoRA adapter into the base model before GGUF export."""
from __future__ import annotations

import argparse
import os
from pathlib import Path


def merge_lora(base_model: str, adapter_dir: Path, output_dir: Path) -> None:
    import torch
    from dotenv import load_dotenv
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    load_dotenv()
    output_dir.mkdir(parents=True, exist_ok=True)
    token = os.getenv("HF_TOKEN") or None
    print("Merging LoRA adapter into base model.")
    print("This can download ~15GB and may need 30GB+ free disk during export.")
    print(f"Base model: {base_model}")
    print(f"Adapter: {adapter_dir}")
    print(f"Output: {output_dir}")

    tokenizer = AutoTokenizer.from_pretrained(adapter_dir, trust_remote_code=True, token=token)
    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True,
        trust_remote_code=True,
        token=token,
    )
    model = PeftModel.from_pretrained(base, adapter_dir)
    merged = model.merge_and_unload()
    merged.save_pretrained(output_dir, safe_serialization=True)
    tokenizer.save_pretrained(output_dir)
    print(f"Merged model saved to: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge LoRA adapter into base weights.")
    parser.add_argument("--base-model", default="Qwen/Qwen3-8B")
    parser.add_argument("--adapter-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    merge_lora(args.base_model, args.adapter_dir, args.output_dir)


if __name__ == "__main__":
    main()

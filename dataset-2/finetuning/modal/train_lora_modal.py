"""Run Phase 5 LoRA training on Modal."""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime
import os
from pathlib import PurePosixPath

import modal

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - Modal CLI env may not have python-dotenv
    load_dotenv = None


APP_NAME = "physics-ai-phase5-lora"
REMOTE_REPO = PurePosixPath("/root/project")
REMOTE_DATA = PurePosixPath("/data/processed")
REMOTE_RUNS = PurePosixPath("/runs")
IGNORED_UPLOAD_PARTS = {
    ".git",
    ".venv",
    ".venv-wsl",
    "__pycache__",
    ".pytest_cache",
    "external",
    "qdrant_storage",
    "runs",
    "adapters",
    "processed",
    "wandb",
}
IGNORED_UPLOAD_NAMES = {
    ".env",
}

if load_dotenv:
    load_dotenv()

modal_secrets = []
if os.getenv("HF_TOKEN"):
    modal_secrets.append(modal.Secret.from_dict({"HF_TOKEN": os.environ["HF_TOKEN"]}))


def ignore_upload(path) -> bool:
    """Keep Modal snapshots stable and avoid uploading local/generated files."""
    parts = set(path.parts)
    if any(part.startswith(".venv") for part in path.parts):
        return True
    if parts & IGNORED_UPLOAD_PARTS:
        return True
    if path.name in IGNORED_UPLOAD_NAMES:
        return True
    if path.suffix in {".pyc", ".safetensors", ".gguf"}:
        return True
    return False


image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git", "build-essential")
    .pip_install(
        "torch",
        "transformers>=4.45.0",
        "datasets>=2.20.0",
        "accelerate>=0.34.0",
        "peft>=0.12.0",
        "bitsandbytes>=0.43.0",
        "sentencepiece>=0.2.0",
        "protobuf>=5.0.0",
        "unsloth",
        "trl>=0.9.0",
        "python-dotenv>=1.0.0",
    )
    .add_local_dir(".", remote_path=str(REMOTE_REPO), ignore=ignore_upload)
)

app = modal.App(APP_NAME, image=image)

hf_cache = modal.Volume.from_name("physics-lora-hf-cache", create_if_missing=True)
data_volume = modal.Volume.from_name("physics-lora-data", create_if_missing=True)
runs_volume = modal.Volume.from_name("physics-lora-runs", create_if_missing=True)


def run(cmd: list[str], cwd: PurePosixPath = REMOTE_REPO) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, stdout=sys.stdout, stderr=sys.stderr, check=True)


def train_impl(
    config_path: str = "finetuning/configs/qwen3_8b_modal_a100.yaml",
    dataset_path: str = "dataset_2/physic_version_2.csv",
    run_id: str | None = None,
    max_steps: int | None = None,
) -> str:
    import os

    os.environ["HF_HOME"] = "/cache/huggingface"
    os.environ["HF_HUB_CACHE"] = "/cache/huggingface/hub"

    run_id = run_id or datetime.utcnow().strftime("qwen3_8b_lora_%Y%m%d_%H%M%S")
    output_dir = REMOTE_RUNS / run_id
    train_file = REMOTE_DATA / "train.jsonl"
    val_file = REMOTE_DATA / "val.jsonl"
    test_file = REMOTE_DATA / "test.jsonl"

    run(
        [
            sys.executable,
            "finetuning/scripts/prepare_sft_dataset.py",
            "--dataset",
            dataset_path,
            "--output-dir",
            str(REMOTE_DATA),
            "--seed",
            "42",
        ]
    )

    train_cmd = [
        sys.executable,
        "finetuning/scripts/train_lora_unsloth.py",
        "--config",
        config_path,
        "--train-file",
        str(train_file),
        "--val-file",
        str(val_file),
        "--test-file",
        str(test_file),
        "--output-dir",
        str(output_dir),
    ]
    if max_steps is not None:
        train_cmd += ["--max-steps", str(max_steps)]
    run(train_cmd)

    runs_volume.commit()
    data_volume.commit()
    print(f"Remote run saved in Modal volume physics-lora-runs:{output_dir}")
    return str(output_dir)


_TRAIN_VOLUMES = {
    "/cache": hf_cache,
    "/data": data_volume,
    "/runs": runs_volume,
}


@app.function(
    gpu="A10",
    timeout=60 * 60 * 6,
    volumes=_TRAIN_VOLUMES,
    secrets=modal_secrets,
)
def train_remote_a10(
    config_path: str = "finetuning/configs/qwen3_8b_modal_a100.yaml",
    dataset_path: str = "dataset_2/physic_version_2.csv",
    run_id: str | None = None,
    max_steps: int | None = None,
) -> str:
    return train_impl(config_path=config_path, dataset_path=dataset_path, run_id=run_id, max_steps=max_steps)


@app.function(
    gpu="L4",
    timeout=60 * 60 * 8,
    volumes=_TRAIN_VOLUMES,
    secrets=modal_secrets,
)
def train_remote_l4(
    config_path: str = "finetuning/configs/qwen3_8b_modal_a100.yaml",
    dataset_path: str = "dataset_2/physic_version_2.csv",
    run_id: str | None = None,
    max_steps: int | None = None,
) -> str:
    return train_impl(config_path=config_path, dataset_path=dataset_path, run_id=run_id, max_steps=max_steps)


@app.function(
    gpu="L40S",
    timeout=60 * 60 * 6,
    volumes=_TRAIN_VOLUMES,
    secrets=modal_secrets,
)
def train_remote_l40s(
    config_path: str = "finetuning/configs/qwen3_8b_modal_a100.yaml",
    dataset_path: str = "dataset_2/physic_version_2.csv",
    run_id: str | None = None,
    max_steps: int | None = None,
) -> str:
    return train_impl(config_path=config_path, dataset_path=dataset_path, run_id=run_id, max_steps=max_steps)


@app.function(
    gpu="A100",
    timeout=60 * 60 * 6,
    volumes=_TRAIN_VOLUMES,
    secrets=modal_secrets,
)
def train_remote_a100(
    config_path: str = "finetuning/configs/qwen3_8b_modal_a100.yaml",
    dataset_path: str = "dataset_2/physic_version_2.csv",
    run_id: str | None = None,
    max_steps: int | None = None,
) -> str:
    return train_impl(config_path=config_path, dataset_path=dataset_path, run_id=run_id, max_steps=max_steps)


@app.local_entrypoint()
def main(
    config_path: str = "finetuning/configs/qwen3_8b_modal_a100.yaml",
    dataset_path: str = "dataset_2/physic_version_2.csv",
    run_id: str | None = None,
    max_steps: int | None = None,
    gpu: str = "A100",
) -> None:
    gpu = gpu.upper()
    if gpu == "A100":
        train_fn = train_remote_a100
    elif gpu == "L40S":
        train_fn = train_remote_l40s
    elif gpu == "L4":
        train_fn = train_remote_l4
    elif gpu == "A10":
        train_fn = train_remote_a10
    else:
        raise ValueError("Supported training GPUs are A10, L4, L40S, and A100.")

    remote_output = train_fn.remote(
        config_path=config_path,
        dataset_path=dataset_path,
        run_id=run_id,
        max_steps=max_steps,
    )
    print(f"Done. Output directory on Modal volume: {remote_output}")
    print("Download example:")
    print("modal volume get physics-lora-runs <run_id> ./finetuning/runs/<run_id>")

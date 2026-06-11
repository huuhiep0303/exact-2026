"""Merge a trained LoRA adapter on Modal instead of local Windows/CPU."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import PurePosixPath

import modal

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


APP_NAME = "physics-ai-phase5-merge-lora"
REMOTE_REPO = PurePosixPath("/root/project")
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
IGNORED_UPLOAD_NAMES = {".env"}

if load_dotenv:
    load_dotenv()

modal_secrets = []
if os.getenv("HF_TOKEN"):
    modal_secrets.append(modal.Secret.from_dict({"HF_TOKEN": os.environ["HF_TOKEN"]}))


def ignore_upload(path) -> bool:
    """Keep Modal snapshots stable and avoid uploading generated artifacts."""
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
        "accelerate>=0.34.0",
        "peft>=0.12.0",
        "sentencepiece>=0.2.0",
        "protobuf>=5.0.0",
        "safetensors>=0.4.0",
        "python-dotenv>=1.0.0",
    )
    .add_local_dir(".", remote_path=str(REMOTE_REPO), ignore=ignore_upload)
)

app = modal.App(APP_NAME, image=image)
hf_cache = modal.Volume.from_name("physics-lora-hf-cache", create_if_missing=True)
runs_volume = modal.Volume.from_name("physics-lora-runs", create_if_missing=True)


def run(cmd: list[str], cwd: PurePosixPath = REMOTE_REPO) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, stdout=sys.stdout, stderr=sys.stderr, check=True)


def merge_impl(run_id: str, base_model: str, output_name: str) -> str:
    os.environ["HF_HOME"] = "/cache/huggingface"
    os.environ["HF_HUB_CACHE"] = "/cache/huggingface/hub"

    adapter_dir = REMOTE_RUNS / run_id / "adapter"
    output_dir = REMOTE_RUNS / run_id / output_name
    if not os.path.exists(str(adapter_dir)):
        raise FileNotFoundError(f"Adapter not found in Modal volume: {adapter_dir}")

    run(
        [
            sys.executable,
            "finetuning/scripts/merge_lora.py",
            "--base-model",
            base_model,
            "--adapter-dir",
            str(adapter_dir),
            "--output-dir",
            str(output_dir),
        ]
    )

    runs_volume.commit()
    print(f"Merged model saved in Modal volume: {output_dir}")
    return str(output_dir)


@app.function(
    gpu="A10",
    timeout=60 * 60 * 3,
    volumes={"/cache": hf_cache, "/runs": runs_volume},
    secrets=modal_secrets,
)
def merge_remote_a10(
    run_id: str,
    base_model: str = "Qwen/Qwen3-8B",
    output_name: str = "merged",
) -> str:
    return merge_impl(run_id=run_id, base_model=base_model, output_name=output_name)


@app.function(
    gpu="L40S",
    timeout=60 * 60 * 3,
    volumes={"/cache": hf_cache, "/runs": runs_volume},
    secrets=modal_secrets,
)
def merge_remote_l40s(
    run_id: str,
    base_model: str = "Qwen/Qwen3-8B",
    output_name: str = "merged",
) -> str:
    return merge_impl(run_id=run_id, base_model=base_model, output_name=output_name)


@app.function(
    gpu="A100",
    timeout=60 * 60 * 3,
    volumes={"/cache": hf_cache, "/runs": runs_volume},
    secrets=modal_secrets,
)
def merge_remote_a100(
    run_id: str,
    base_model: str = "Qwen/Qwen3-8B",
    output_name: str = "merged",
) -> str:
    return merge_impl(run_id=run_id, base_model=base_model, output_name=output_name)


@app.local_entrypoint()
def main(
    run_id: str,
    base_model: str = "Qwen/Qwen3-8B",
    output_name: str = "merged",
    gpu: str = "A100",
) -> None:
    gpu = gpu.upper()
    if gpu == "A100":
        remote_output = merge_remote_a100.remote(
            run_id=run_id,
            base_model=base_model,
            output_name=output_name,
        )
    elif gpu == "L40S":
        remote_output = merge_remote_l40s.remote(
            run_id=run_id,
            base_model=base_model,
            output_name=output_name,
        )
    elif gpu == "A10":
        remote_output = merge_remote_a10.remote(
            run_id=run_id,
            base_model=base_model,
            output_name=output_name,
        )
    else:
        raise ValueError("Supported merge GPUs are A10, L40S, and A100.")

    print(f"Done. Merged model directory on Modal volume: {remote_output}")
    print("Download example:")
    print(f"modal volume get physics-lora-runs {run_id}/{output_name} ./finetuning/runs/{run_id}")

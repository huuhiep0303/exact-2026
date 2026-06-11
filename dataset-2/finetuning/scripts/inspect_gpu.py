"""Print a small GPU/CUDA report for local fine-tuning smoke tests."""
from __future__ import annotations

import shutil
import subprocess


def run_nvidia_smi() -> None:
    if not shutil.which("nvidia-smi"):
        print("nvidia-smi: not found")
        return
    cmd = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.free,driver_version",
        "--format=csv,noheader",
    ]
    try:
        output = subprocess.check_output(cmd, text=True).strip()
        print("nvidia-smi:")
        print(output or "(no GPUs reported)")
    except Exception as exc:
        print(f"nvidia-smi failed: {exc}")


def run_torch_report() -> None:
    try:
        import torch
    except Exception as exc:
        print(f"torch: not importable ({exc})")
        return

    print(f"torch: {torch.__version__}")
    print(f"cuda available: {torch.cuda.is_available()}")
    if not torch.cuda.is_available():
        return
    for idx in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(idx)
        total_gb = props.total_memory / (1024**3)
        print(f"cuda:{idx}: {props.name}, {total_gb:.2f} GiB")


def main() -> None:
    run_nvidia_smi()
    run_torch_report()


if __name__ == "__main__":
    main()


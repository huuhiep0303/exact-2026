import subprocess

import modal


APP_NAME = "exact-2026-vllm"
MODEL_NAME = "Qwen/Qwen3-8B"
VLLM_PORT = 8000

app = modal.App(APP_NAME)

# This volume must contain the two LoRA adapter directories referenced below.
volume = modal.Volume.from_name("exact-2026-volume", create_if_missing=True)
hf_cache_volume = modal.Volume.from_name("exact-2026-hf-cache", create_if_missing=True)
vllm_cache_volume = modal.Volume.from_name("exact-2026-vllm-cache", create_if_missing=True)

vllm_image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install("vllm>=0.7.0", "huggingface_hub", "hf-transfer")
    .env({
        "HF_HUB_ENABLE_HF_TRANSFER": "1",
        "HF_XET_HIGH_PERFORMANCE": "1",
        "VLLM_LOG_STATS_INTERVAL": "5",
        "VLLM_USE_FLASHINFER": "0",
        "VLLM_USE_FLASHINFER_SAMPLER": "0",
        "VLLM_DISABLE_FLASHINFER": "1",
        "VLLM_ATTENTION_BACKEND": "FLASH_ATTN",
    })
)


@app.function(
    image=vllm_image,
    gpu="A100",
    volumes={
        "/workspace": volume,
        "/root/.cache/huggingface": hf_cache_volume,
        "/root/.cache/vllm": vllm_cache_volume,
    },
    secrets=[modal.Secret.from_name("exact-2026-config")],
    min_containers=1,
    max_containers=1,
    scaledown_window=600,
    timeout=900,
)
@modal.concurrent(max_inputs=8)
@modal.web_server(VLLM_PORT, startup_timeout=600)
def serve():
    cmd = [
        "python",
        "-u",
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        MODEL_NAME,
        "--host",
        "0.0.0.0",
        "--port",
        str(VLLM_PORT),
        "--enable-lora",
        "--lora-modules",
        "exact-lora=/workspace/checkpoints/final",
        "exact-lora-type2=/workspace/checkpoints/type2-final",
        "--max-loras",
        "1",
        "--max-cpu-loras",
        "2",
        "--max-lora-rank",
        "64",
        "--max-model-len",
        "4096",
        "--gpu-memory-utilization",
        "0.9",
        "--enforce-eager",
        "--enable-prefix-caching",
        "--safetensors-load-strategy",
        "prefetch",
    ]

    import socket
    import time

    print("Starting vLLM server...")
    import sys
    proc = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)

    # Monitor startup and fail fast if the subprocess exits prematurely
    start_time = time.time()
    port_open = False
    while time.time() - start_time < 580:  # slightly less than the 600s startup_timeout
        if proc.poll() is not None:
            raise RuntimeError(
                f"vLLM server exited prematurely with code {proc.returncode}. "
                "Check Modal logs for CUDA OOM, missing checkpoint volume, or other errors."
            )
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                s.connect(("127.0.0.1", VLLM_PORT))
                port_open = True
                break
        except Exception:
            time.sleep(2)

    if not port_open:
        proc.terminate()
        raise TimeoutError("vLLM server did not bind to port in time.")

    print("vLLM server is ready and listening on port!")

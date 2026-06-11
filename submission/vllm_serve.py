import modal

app = modal.App("exact-2026-vllm")

# Khởi tạo Volume chứa LoRA weights
volume = modal.Volume.from_name("exact-2026-volume", create_if_missing=True)

# Image chứa vLLM và các thư viện cần thiết
vllm_image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install("vllm>=0.4.0", "huggingface_hub", "hf-transfer")
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

# Chạy vLLM server như một web_server trên port 8000
@app.function(
    image=vllm_image,
    gpu="A100", # Cần A100 để chạy 8B + LoRA mượt mà
    volumes={"/workspace": volume},
    secrets=[modal.Secret.from_name("huggingface-secret")],
    timeout=3600, # Giữ container sống lâu để tránh cold start liên tục
)
@modal.web_server(8000, startup_timeout=600)
def serve():
    import subprocess
    
    # Khởi chạy vLLM OpenAI-compatible server với LoRA
    # Base model: Qwen/Qwen3-8B
    # LoRA module sẽ được gắn tên là 'exact-lora' và trỏ tới volume
    cmd = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", "Qwen/Qwen3-8B",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--enable-lora",
        "--lora-modules", "exact-lora=/workspace/checkpoints/final", "exact-lora-type2=/workspace/checkpoints/type2-final",
        "--max-lora-rank", "64",
        "--max-model-len", "4096",
        "--gpu-memory-utilization", "0.9"
    ]
    # Use subprocess.Popen().wait() so the function blocks indefinitely.
    # If the function returns, Modal kills the container.
    process = subprocess.Popen(cmd)
    process.wait()

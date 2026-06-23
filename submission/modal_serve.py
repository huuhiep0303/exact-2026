import modal
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the Modal App
app = modal.App("exact-2026-submission")
hf_cache_volume = modal.Volume.from_name("exact-2026-hf-cache", create_if_missing=True)

# Define the image with required dependencies
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi", "uvicorn", "pydantic", "httpx", "openai",
        "python-dotenv", "qdrant-client", "sentence-transformers"
    )
    .env({
        "HF_XET_HIGH_PERFORMANCE": "1",
        "USE_QDRANT": "true",
        "QDRANT_HOST": "https://4e048dd7-7f79-4151-b176-38a386c6298e.sa-east-1-0.aws.cloud.qdrant.io",
        "QDRANT_API_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6ZWJmODI1ZWMtZmNlOC00ZjAwLTlkYzItMjRhZWI3MmFhZWFhIn0._NCEdi3t_d8bR_c9YLIQu45nZ_nDi-_0_B5EGonq3bc",
        "QDRANT_COLLECTION": "physics_kb"
    })
    .add_local_dir(os.path.join(BASE_DIR, "submission"), remote_path="/root/Project/submission", ignore=["__pycache__", ".git", "dist"])
    .add_local_dir(os.path.join(BASE_DIR, "dataset-1"), remote_path="/root/Project/dataset-1", ignore=["venv", "outputs", "__pycache__", ".git", "EXACT2026_dataset_2026-05-15"])
    .add_local_dir(
        os.path.join(BASE_DIR, "dataset-2"),
        remote_path="/root/Project/dataset-2",
        ignore=[
            "venv",
            "eval_results",
            "__pycache__",
            ".git",
            "checkpoints",
            "wandb",
            ".env",
            "external",
            "finetuning",
            "outputs",
            "qdrant_storage",
        ],
    )
)

# Expose the FastAPI app
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("exact-2026-config")],
    volumes={"/root/.cache/huggingface": hf_cache_volume},
    min_containers=0,
    max_containers=1,
    scaledown_window=600,
    # timeout=600, #có hoặc không
)
@modal.concurrent(max_inputs=8)
@modal.asgi_app()
def fastapi_app():
    import sys
    # IMPORTANT: Insert dataset-2 at position 0 BEFORE importing submission.app.
    # This ensures 'from app.pipeline import run_pipeline' resolves to
    # /root/Project/dataset-2/app/pipeline.py, NOT submission/app.py (name collision).
    sys.path.insert(0, "/root/Project/dataset-2")
    sys.path.append("/root/Project")
    # Change working directory so dataset-2 can find its KB files relative to itself
    os.chdir("/root/Project")

    # Keep one-time Qdrant and embedding initialization out of the first
    # competition request's 60-second response budget.
    os.environ["PIPELINE_MODE"] = "api"
    vllm_url = os.getenv("VLLM_API_URL", "https://ngocthaodn0109--exact-2026-vllm-serve.modal.run/v1")
    os.environ["VLLM_API_URL"] = vllm_url
    os.environ["OPENAI_BASE_URL"] = vllm_url
    os.environ["REASONER_API_MODEL"] = os.getenv(
        "TYPE2_MODEL", "exact-lora-type2"
    )
    from app.modules.knowledge_base import get_knowledge_base
    get_knowledge_base()

    try:
        import httpx

        model_name = os.environ["REASONER_API_MODEL"]
        with httpx.Client(timeout=httpx.Timeout(20.0, connect=5.0)) as client:
            client.post(
                f"{vllm_url}/chat/completions",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": "Return 1."}],
                    "max_tokens": 1,
                    "temperature": 0,
                },
            )
        print(f"[Warmup] Requested vLLM LoRA adapter: {model_name}")
    except Exception as exc:
        print(f"[Warmup] vLLM LoRA adapter warmup skipped: {exc}")
    
    from submission.app import app as web_app
    return web_app

# Note: To run vLLM on Modal, you should use the official Modal vLLM template 
# (https://modal.com/docs/examples/vllm_inference) to spin up the OpenAI-compatible server.
# Ensure that the vLLM app exposes the `/v1/models` endpoint as required by the competition!

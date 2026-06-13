import modal
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the Modal App
app = modal.App("exact-2026-submission")

# Define the image with required dependencies
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install(
        "fastapi", "uvicorn", "pydantic", "httpx", "openai",
        "python-dotenv", "qdrant-client", "sentence-transformers"
    )
    .add_local_dir(os.path.join(BASE_DIR, "submission"), remote_path="/root/Project/submission", ignore=["__pycache__", ".git", "dist"])
    .add_local_dir(os.path.join(BASE_DIR, "dataset-1"), remote_path="/root/Project/dataset-1", ignore=["venv", "outputs", "__pycache__", ".git", "EXACT2026_dataset_2026-05-15"])
    .add_local_dir(os.path.join(BASE_DIR, "dataset-2"), remote_path="/root/Project/dataset-2", ignore=["venv", "eval_results", "__pycache__", ".git", "checkpoints", "wandb", ".env"])
)

# Expose the FastAPI app
@app.function(
    image=image,
    secrets=[modal.Secret.from_name("exact-2026-config")],
    min_containers=0,
    max_containers=1,
    scaledown_window=60,
    # timeout=600, #có hoặc không
)
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
    
    from submission.app import app as web_app
    return web_app

# Note: To run vLLM on Modal, you should use the official Modal vLLM template 
# (https://modal.com/docs/examples/vllm_inference) to spin up the OpenAI-compatible server.
# Ensure that the vLLM app exposes the `/v1/models` endpoint as required by the competition!

import modal
import os

# Define the Modal App
app = modal.App("exact-2026-submission")

# Define the image with required dependencies
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("fastapi", "uvicorn", "pydantic", "httpx")
)

# Mount the local submission directory into the Modal container
# This assumes you run `modal deploy submission/modal_serve.py` from the Project root
submission_dir = modal.Mount.from_local_dir(
    local_path="./submission", 
    remote_path="/root/submission"
)

# Expose the FastAPI app
@app.function(
    image=image, 
    mounts=[submission_dir], 
    allow_concurrent_inputs=100,
    secrets=[modal.Secret.from_dict({
        # Replace this URL with your actual vLLM endpoint URL deployed on Modal or elsewhere
        "VLLM_API_URL": "http://your-vllm-endpoint-url.modal.run/v1",
        "MODEL_NAME": "Qwen/Qwen3-8B"
    })]
)
@modal.asgi_app()
def fastapi_app():
    import sys
    sys.path.append("/root/submission")
    from app import app as web_app
    return web_app

# Note: To run vLLM on Modal, you should use the official Modal vLLM template 
# (https://modal.com/docs/examples/vllm_inference) to spin up the OpenAI-compatible server.
# Ensure that the vLLM app exposes the `/v1/models` endpoint as required by the competition!

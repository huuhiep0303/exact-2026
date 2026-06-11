"""Run pipeline evaluation on Modal with a vLLM OpenAI-compatible server."""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path, PurePosixPath

import modal

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


APP_NAME = "physics-ai-phase5-eval"
REMOTE_REPO = PurePosixPath("/root/project")
REMOTE_RUNS = PurePosixPath("/runs")
REMOTE_EVAL = PurePosixPath("/eval_results")
VLLM_PORT = 8001

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
secret_values = {}
for secret_name in ("HF_TOKEN", "QDRANT_HOST", "QDRANT_API_KEY", "QDRANT_COLLECTION"):
    if os.getenv(secret_name):
        secret_values[secret_name] = os.environ[secret_name]
if secret_values:
    modal_secrets.append(modal.Secret.from_dict(secret_values))


def ignore_upload(path) -> bool:
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
        "vllm>=0.6.0",
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "qdrant-client>=1.9.0",
        "sentence-transformers>=3.0.0",
    )
    .add_local_dir(".", remote_path=str(REMOTE_REPO), ignore=ignore_upload)
)

app = modal.App(APP_NAME, image=image)
hf_cache = modal.Volume.from_name("physics-lora-hf-cache", create_if_missing=True)
runs_volume = modal.Volume.from_name("physics-lora-runs", create_if_missing=True)
eval_volume = modal.Volume.from_name("physics-lora-eval", create_if_missing=True)


def run(cmd: list[str], cwd: PurePosixPath = REMOTE_REPO, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, env=env, stdout=sys.stdout, stderr=sys.stderr, check=True)


def wait_for_vllm(server: subprocess.Popen, timeout_sec: int = 900) -> None:
    url = f"http://127.0.0.1:{VLLM_PORT}/v1/models"
    deadline = time.time() + timeout_sec
    last_error: Exception | None = None
    while time.time() < deadline:
        if server.poll() is not None:
            raise RuntimeError(f"vLLM server exited before becoming ready with code {server.returncode}.")
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if 200 <= response.status < 300:
                    print("vLLM server is ready.")
                    return
        except Exception as exc:  # noqa: BLE001 - readiness probe
            last_error = exc
        time.sleep(5)
    raise TimeoutError(f"Timed out waiting for vLLM server at {url}: {last_error}")


def qdrant_preflight(output_root: PurePosixPath) -> None:
    """Fail fast when Modal eval is requested with Qdrant but credentials/collection are not usable."""
    host = os.getenv("QDRANT_HOST", "")
    api_key = os.getenv("QDRANT_API_KEY", "")
    collection = os.getenv("QDRANT_COLLECTION", "physics_kb")
    status_path = output_root / "qdrant_preflight.txt"
    if not host:
        raise RuntimeError("USE_QDRANT=true but QDRANT_HOST was not provided to Modal.")
    try:
        from qdrant_client import QdrantClient

        client = QdrantClient(url=host, api_key=api_key or None)
        info = client.get_collection(collection)
        message = (
            "qdrant_connected=true\n"
            f"host={host[:32]}...\n"
            f"collection={collection}\n"
            f"points_count={getattr(info, 'points_count', 'unknown')}\n"
        )
        print(message)
        Path(str(status_path)).write_text(message, encoding="utf-8")
        os.environ["QDRANT_CONNECTED"] = "true"
    except Exception as exc:  # noqa: BLE001 - preflight should surface the real remote error
        Path(str(status_path)).write_text(
            f"qdrant_connected=false\nerror={type(exc).__name__}: {exc}\n",
            encoding="utf-8",
        )
        os.environ["QDRANT_CONNECTED"] = "false"
        raise RuntimeError(f"Qdrant preflight failed for collection {collection}: {exc}") from exc


def start_vllm(
    model_path: str,
    served_model_name: str,
    max_model_len: int,
    gpu_memory_utilization: float,
) -> subprocess.Popen:
    cmd = [
        sys.executable,
        "-m",
        "vllm.entrypoints.openai.api_server",
        "--model",
        model_path,
        "--served-model-name",
        served_model_name,
        "--host",
        "127.0.0.1",
        "--port",
        str(VLLM_PORT),
        "--max-model-len",
        str(max_model_len),
        "--gpu-memory-utilization",
        str(gpu_memory_utilization),
    ]
    print("+", " ".join(cmd))
    env = os.environ.copy()
    # Modal's slim image does not include nvcc. vLLM may auto-select the
    # FlashInfer sampler, whose JIT path needs nvcc; force the native sampler.
    env["VLLM_USE_FLASHINFER_SAMPLER"] = "0"
    return subprocess.Popen(cmd, cwd=REMOTE_REPO, env=env, stdout=sys.stdout, stderr=sys.stderr)


def eval_impl(
    dataset_path: str,
    id_prefix: str,
    start: int,
    limit: int,
    run_id: str | None,
    model_subdir: str,
    base_model: str,
    served_model_name: str,
    max_model_len: int,
    gpu_memory_utilization: float,
    reasoner_max_tokens: int,
    structurer_max_tokens: int,
    report_misses_only: bool,
    use_qdrant: bool,
) -> str:
    os.environ["HF_HOME"] = "/cache/huggingface"
    os.environ["HF_HUB_CACHE"] = "/cache/huggingface/hub"

    if run_id:
        model_path = str(REMOTE_RUNS / run_id / model_subdir)
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Merged model not found: {model_path}. Run merge_lora_modal.py first."
            )
        output_root = REMOTE_EVAL / run_id
    else:
        model_path = base_model
        output_root = REMOTE_EVAL / "base"

    id_prefix = "" if id_prefix.upper() == "ALL" else id_prefix
    prefix = id_prefix.upper() if id_prefix else "ALL"
    os.makedirs(str(output_root), exist_ok=True)
    if use_qdrant:
        os.environ["USE_QDRANT"] = "true"
        qdrant_preflight(output_root)
    else:
        os.environ["USE_QDRANT"] = "false"
        os.environ["QDRANT_CONNECTED"] = "false"
    output_jsonl = output_root / f"{prefix}_{start}_{limit}.jsonl"
    report_md = output_root / f"{prefix}_{start}_{limit}.md"

    server = start_vllm(
        model_path=model_path,
        served_model_name=served_model_name,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
    )
    try:
        wait_for_vllm(server)
        env = os.environ.copy()
        env.update(
            {
                "PIPELINE_MODE": "api",
                "OPENAI_BASE_URL": f"http://127.0.0.1:{VLLM_PORT}/v1",
                "OPENAI_API_KEY": "not-needed",
                "REASONER_API_MODEL": served_model_name,
                "REASONER_MAX_TOKENS": str(reasoner_max_tokens),
                "STRUCTURER_MAX_TOKENS": str(structurer_max_tokens),
                "USE_QDRANT": "true" if use_qdrant else "false",
                "QDRANT_CONNECTED": os.getenv("QDRANT_CONNECTED", "false"),
                "DEBUG": "false",
            }
        )

        cmd = [
            sys.executable,
            "evaluate_pipeline.py",
            "--dataset",
            dataset_path,
            "--mode",
            "api",
            "--start",
            str(start),
            "--limit",
            str(limit),
            "--output",
            str(output_jsonl),
            "--report",
            str(report_md),
        ]
        if id_prefix:
            cmd += ["--id-prefix", id_prefix]
        if report_misses_only:
            cmd.append("--report-misses-only")
        run(cmd, env=env)
    finally:
        server.terminate()
        try:
            server.wait(timeout=30)
        except subprocess.TimeoutExpired:
            server.kill()

    eval_volume.commit()
    print(f"Evaluation saved in Modal volume: {output_root}")
    return str(output_root)


def eval_many_impl(
    dataset_path: str,
    id_prefixes: str,
    start: int,
    limit: int,
    run_id: str | None,
    model_subdir: str,
    base_model: str,
    served_model_name: str,
    max_model_len: int,
    gpu_memory_utilization: float,
    reasoner_max_tokens: int,
    structurer_max_tokens: int,
    report_misses_only: bool,
    use_qdrant: bool,
) -> str:
    os.environ["HF_HOME"] = "/cache/huggingface"
    os.environ["HF_HUB_CACHE"] = "/cache/huggingface/hub"

    if run_id:
        model_path = str(REMOTE_RUNS / run_id / model_subdir)
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Merged model not found: {model_path}. Run merge_lora_modal.py first."
            )
        output_root = REMOTE_EVAL / run_id
    else:
        model_path = base_model
        output_root = REMOTE_EVAL / "base"

    prefixes = [p.strip().upper() for p in id_prefixes.split(",") if p.strip()]
    if not prefixes:
        raise ValueError("id_prefixes must contain at least one prefix.")
    os.makedirs(str(output_root), exist_ok=True)
    if use_qdrant:
        os.environ["USE_QDRANT"] = "true"
        qdrant_preflight(output_root)
    else:
        os.environ["USE_QDRANT"] = "false"
        os.environ["QDRANT_CONNECTED"] = "false"

    server = start_vllm(
        model_path=model_path,
        served_model_name=served_model_name,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
    )
    try:
        wait_for_vllm(server)
        env = os.environ.copy()
        env.update(
            {
                "PIPELINE_MODE": "api",
                "OPENAI_BASE_URL": f"http://127.0.0.1:{VLLM_PORT}/v1",
                "OPENAI_API_KEY": "not-needed",
                "REASONER_API_MODEL": served_model_name,
                "REASONER_MAX_TOKENS": str(reasoner_max_tokens),
                "STRUCTURER_MAX_TOKENS": str(structurer_max_tokens),
                "USE_QDRANT": "true" if use_qdrant else "false",
                "QDRANT_CONNECTED": os.getenv("QDRANT_CONNECTED", "false"),
                "DEBUG": "false",
            }
        )
        failed_prefixes: list[str] = []
        for prefix in prefixes:
            id_prefix = "" if prefix == "ALL" else prefix
            file_prefix = id_prefix or "ALL"
            output_jsonl = output_root / f"{file_prefix}_{start}_{limit}.jsonl"
            report_md = output_root / f"{file_prefix}_{start}_{limit}.md"
            cmd = [
                sys.executable,
                "evaluate_pipeline.py",
                "--dataset",
                dataset_path,
                "--mode",
                "api",
                "--start",
                str(start),
                "--limit",
                str(limit),
                "--output",
                str(output_jsonl),
                "--report",
                str(report_md),
            ]
            if id_prefix:
                cmd += ["--id-prefix", id_prefix]
            if report_misses_only:
                cmd.append("--report-misses-only")
            try:
                run(cmd, env=env)
            except subprocess.CalledProcessError as exc:
                failed_prefixes.append(prefix)
                print(f"Evaluation failed for prefix {prefix}: {exc}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=30)
        except subprocess.TimeoutExpired:
            server.kill()

    eval_volume.commit()
    if failed_prefixes:
        print(f"Completed with failed prefixes: {', '.join(failed_prefixes)}")
    print(f"Evaluation saved in Modal volume: {output_root}")
    return str(output_root)


@app.function(
    gpu="A100",
    timeout=60 * 60 * 3,
    volumes={"/cache": hf_cache, "/runs": runs_volume, "/eval_results": eval_volume},
    secrets=modal_secrets,
)
def eval_remote_a100(
    dataset_path: str = "dataset_2/Physics_Problems_Text_Only.csv",
    id_prefix: str = "DDT",
    start: int = 0,
    limit: int = 20,
    run_id: str | None = None,
    model_subdir: str = "merged",
    base_model: str = "Qwen/Qwen3-8B",
    served_model_name: str = "physics-qwen3-8b-lora",
    max_model_len: int = 4096,
    gpu_memory_utilization: float = 0.85,
    reasoner_max_tokens: int = 1024,
    structurer_max_tokens: int = 256,
    report_misses_only: bool = True,
    use_qdrant: bool = False,
) -> str:
    return eval_impl(
        dataset_path=dataset_path,
        id_prefix=id_prefix,
        start=start,
        limit=limit,
        run_id=run_id,
        model_subdir=model_subdir,
        base_model=base_model,
        served_model_name=served_model_name,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
        reasoner_max_tokens=reasoner_max_tokens,
        structurer_max_tokens=structurer_max_tokens,
        report_misses_only=report_misses_only,
        use_qdrant=use_qdrant,
    )


@app.function(
    gpu="A100",
    timeout=60 * 60 * 8,
    volumes={"/cache": hf_cache, "/runs": runs_volume, "/eval_results": eval_volume},
    secrets=modal_secrets,
)
def eval_many_remote_a100(
    dataset_path: str = "dataset_2/Physics_Problems_Text_Only.csv",
    id_prefixes: str = "CH,CHLT,DDT,DT,LD,NL,TD,THCB",
    start: int = 0,
    limit: int = 20,
    run_id: str | None = None,
    model_subdir: str = "merged",
    base_model: str = "Qwen/Qwen3-8B",
    served_model_name: str = "physics-qwen3-8b-lora",
    max_model_len: int = 4096,
    gpu_memory_utilization: float = 0.85,
    reasoner_max_tokens: int = 1024,
    structurer_max_tokens: int = 256,
    report_misses_only: bool = True,
    use_qdrant: bool = False,
) -> str:
    return eval_many_impl(
        dataset_path=dataset_path,
        id_prefixes=id_prefixes,
        start=start,
        limit=limit,
        run_id=run_id,
        model_subdir=model_subdir,
        base_model=base_model,
        served_model_name=served_model_name,
        max_model_len=max_model_len,
        gpu_memory_utilization=gpu_memory_utilization,
        reasoner_max_tokens=reasoner_max_tokens,
        structurer_max_tokens=structurer_max_tokens,
        report_misses_only=report_misses_only,
        use_qdrant=use_qdrant,
    )


@app.local_entrypoint()
def main(
    dataset_path: str = "dataset_2/Physics_Problems_Text_Only.csv",
    id_prefix: str = "DDT",
    start: int = 0,
    limit: int = 20,
    run_id: str | None = None,
    model_subdir: str = "merged",
    base_model: str = "Qwen/Qwen3-8B",
    served_model_name: str = "physics-qwen3-8b-lora",
    max_model_len: int = 4096,
    gpu_memory_utilization: float = 0.85,
    reasoner_max_tokens: int = 1024,
    structurer_max_tokens: int = 256,
    report_misses_only: bool = True,
    id_prefixes: str = "",
    use_qdrant: bool = False,
) -> None:
    if id_prefixes:
        remote_output = eval_many_remote_a100.remote(
            dataset_path=dataset_path,
            id_prefixes=id_prefixes,
            start=start,
            limit=limit,
            run_id=run_id,
            model_subdir=model_subdir,
            base_model=base_model,
            served_model_name=served_model_name,
            max_model_len=max_model_len,
            gpu_memory_utilization=gpu_memory_utilization,
            reasoner_max_tokens=reasoner_max_tokens,
            structurer_max_tokens=structurer_max_tokens,
            report_misses_only=report_misses_only,
            use_qdrant=use_qdrant,
        )
    else:
        remote_output = eval_remote_a100.remote(
            dataset_path=dataset_path,
            id_prefix=id_prefix,
            start=start,
            limit=limit,
            run_id=run_id,
            model_subdir=model_subdir,
            base_model=base_model,
            served_model_name=served_model_name,
            max_model_len=max_model_len,
            gpu_memory_utilization=gpu_memory_utilization,
            reasoner_max_tokens=reasoner_max_tokens,
            structurer_max_tokens=structurer_max_tokens,
            report_misses_only=report_misses_only,
            use_qdrant=use_qdrant,
        )
    print(f"Done. Evaluation directory on Modal volume: {remote_output}")
    print("Download example:")
    print("modal volume get physics-lora-eval <run_id-or-base> ./eval_results/modal/<run_id-or-base>")

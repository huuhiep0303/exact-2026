# EXACT 2026 Reasoning API 🚀

An advanced, high-performance API for the **EXACT 2026 Competition**, designed to solve complex logical deduction and physics reasoning problems. This project leverages **Fine-tuned Large Language Models (Qwen3-8B)** with multiple LoRA adapters, orchestrated by **FastAPI** and served efficiently via **vLLM** on **Modal Serverless Cloud**.

---

## 🏗️ Architecture Overview

The system is designed for high throughput, low latency, and accurate logical reasoning. It is divided into two decoupled layers deployed on Modal:

1. **vLLM Inference Engine (`vllm_serve.py`)**: 
   - Runs the base model `Qwen/Qwen3-8B` on an NVIDIA A100 GPU.
   - **Multi-LoRA Enabled**: Loads and serves multiple task-specific LoRA adapters simultaneously without consuming extra VRAM for base weights.
   - Adapters loaded: 
     - `exact-lora` (Type 1 Logic)
     - `exact-lora-type2` (Type 2 Physics)

2. **FastAPI Gateway (`modal_serve.py` & `app.py`)**:
   - Handles HTTP routing, input validation, and data formatting.
   - Acts as a smart router:
     - **Type 1 Requests** are routed directly to vLLM using the `exact-lora` adapter.
     - **Type 2 Requests** are delegated to the complex `dataset-2` Physics Reasoner, which extracts First-Order Logic (FOL), Chain of Thought (CoT), and queries vLLM using the `exact-lora-type2` adapter.

---

## ⚙️ Features

### Type 1: Logic Deduction (FOL)
- Processes multiple premises and a core query.
- Identifies the *minimal* required premises.
- Provides step-by-step rigorous logical deduction.
- Outputs exact answers (A/B/C/D or Yes/No/Unknown).

### Type 2: Physics Solver
- Solves physics word problems and formulas.
- Extracts mathematical entities and units.
- Generates detailed CoT and formal logic steps.

---

## 📂 Repository Structure

```text
├── dataset-1/                 # Training scripts and LoRA weights for Type 1 (Logic)
│   ├── configs/               # Unsloth fine-tuning configuration
│   └── outputs/               # Contains upload_to_modal.py and final checkpoints
├── dataset-2/                 # Training scripts, pipeline, and LoRA weights for Type 2 (Physics)
│   ├── app/                   # Physics Reasoning Pipeline (FOL & CoT extraction)
│   └── outputs/               # Contains upload_to_modal.py and final checkpoints
├── submission/                # Core API Server & Deployment Scripts
│   ├── app.py                 # FastAPI Application (Smart Router)
│   ├── modal_serve.py         # Modal Deployment config for FastAPI
│   └── vllm_serve.py          # Modal Deployment config for vLLM Engine
├── demo.html                  # Beautiful Local Web Demo to interact with the API
├── test_submission.py         # Automated integration testing script
└── README.md                  # This file
```

---

## 🚀 Deployment Instructions

This project is built to run entirely on [Modal](https://modal.com/).

### 1. Upload LoRA Checkpoints to Modal
Before deploying the servers, you must upload your locally fine-tuned LoRA weights to Modal Volumes.
```bash
# Upload Type 1 LoRA
python dataset-1/outputs/upload_to_modal.py

# Upload Type 2 LoRA
python dataset-2/outputs/upload_to_modal.py
```

### 2. Deploy vLLM Engine
Deploy the heavy inference server. This step returns a URL endpoint for vLLM.
```bash
modal deploy submission/vllm_serve.py
```

### 3. Deploy FastAPI Server
Update the `VLLM_API_URL` inside `submission/modal_serve.py` with the URL generated from Step 2, then deploy the API gateway:
```bash
modal deploy submission/modal_serve.py
```
This will give you the final Production Endpoint (e.g., `https://<workspace>--exact-2026-submission-fastapi-app.modal.run/predict`).

---

## 🧪 Testing

### Web UI Demo
Simply double-click the `demo.html` file to open it in any modern browser. It connects directly to your Modal FastAPI server, providing a beautiful, glassmorphism-themed UI to test both Type 1 and Type 2 reasoning.

### Automated Testing
Run the Python test script to validate the payload structure and response latencies:
```bash
python test_submission.py
```

---

*Built with ❤️ for EXACT 2026.*

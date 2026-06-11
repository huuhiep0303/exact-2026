# Export LoRA Model To Ollama

After Phase 5 training, the output is a LoRA adapter. Ollama should run a
merged and quantized model, not the raw training checkpoint.

## 1. Merge LoRA Into Base Model

Recommended: merge on Modal so the local RTX 3050/4050 machine does not need to
download and hold the full 7B base model.

```powershell
modal run finetuning/modal/merge_lora_modal.py `
  --run-id qwen2_5_7b_lora_20260605_185537
```

If A10 runs out of memory during merge, retry on L40S:

```powershell
modal run finetuning/modal/merge_lora_modal.py `
  --run-id qwen2_5_7b_lora_20260605_185537 `
  --gpu L40S
```

Then download the merged model directory:

```powershell
modal volume get physics-lora-runs qwen2_5_7b_lora_20260605_185537/merged .\finetuning\runs\qwen2_5_7b_lora_20260605_185537
```

Local merge is also possible, but it downloads ~15GB and may need 30GB+ free
disk during the merge/export workflow:

```powershell
python finetuning/scripts/merge_lora.py `
  --base-model Qwen/Qwen2.5-7B-Instruct `
  --adapter-dir finetuning/runs/qwen2_5_7b_lora_20260605_185537/adapter `
  --output-dir finetuning/runs/qwen2_5_7b_lora_20260605_185537/merged
```

## 2. Convert Merged Model To GGUF

Use `llama.cpp` from a Linux/WSL shell:

```bash
git clone https://github.com/ggml-org/llama.cpp external/llama.cpp
python external/llama.cpp/convert_hf_to_gguf.py \
  finetuning/runs/qwen2_5_7b_lora_20260605_185537/merged \
  --outfile finetuning/runs/qwen2_5_7b_lora_20260605_185537/physics-qwen-f16.gguf \
  --outtype f16
```

Quantize for local Ollama:

```bash
cmake -S external/llama.cpp -B external/llama.cpp/build
cmake --build external/llama.cpp/build --config Release
external/llama.cpp/build/bin/llama-quantize \
  finetuning/runs/qwen2_5_7b_lora_20260605_185537/physics-qwen-f16.gguf \
  finetuning/runs/qwen2_5_7b_lora_20260605_185537/physics-qwen-q4_k_m.gguf \
  Q4_K_M
```

## 3. Create An Ollama Modelfile

Create `finetuning/runs/qwen2_5_7b_lora_20260605_185537/Modelfile`:

```text
FROM ./physics-qwen-q4_k_m.gguf
PARAMETER temperature 0.1
PARAMETER num_ctx 4096
SYSTEM """You are an expert physics problem solver. Always return [FOL], [CODE], and [ANSWER] when solving."""
```

Then register it:

```powershell
ollama create physics-qwen-lora -f finetuning/runs/qwen2_5_7b_lora_20260605_185537/Modelfile
ollama run physics-qwen-lora
```

Finally set `reasoner_model` in `app/config.py` or `.env` to:

```ini
REASONER_MODEL=physics-qwen-lora
```

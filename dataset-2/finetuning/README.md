# Phase 5 LoRA Fine-Tuning

This folder contains the Phase 5 training scaffold for the Physics AI reasoner.
The first version uses fixed hyperparameters; it does not run automatic
hyperparameter search.

## Folder Layout

```text
finetuning/
  configs/          Fixed local and Modal training configs
  scripts/          Dataset prep, GPU inspection, train, merge, export notes
  modal/            Modal remote training entrypoint
  data/processed/   Generated JSONL splits, ignored by git
  runs/             Generated checkpoints/metrics, ignored by git
  adapters/         Optional adapter storage, ignored by git
```

## 1. Modal-First Path

You can skip local training entirely. On your local machine, install only Modal:

```powershell
pip install modal
modal setup
```

Then run a remote smoke test:

```powershell
modal run finetuning/modal/train_lora_modal.py --max-steps 20
```

If that succeeds, run the full A10 job:

```powershell
modal run finetuning/modal/train_lora_modal.py
```

The Modal runner prepares the SFT data remotely before training, so local
`torch`, `unsloth`, and `bitsandbytes` are not required for this path.

## 2. Prepare Stratified SFT Data Locally

```powershell
python finetuning/scripts/prepare_sft_dataset.py
```

This writes:

```text
finetuning/data/processed/train.jsonl
finetuning/data/processed/val.jsonl
finetuning/data/processed/test.jsonl
finetuning/data/processed/manifest.json
```

The split is done independently inside each topic prefix (`LD`, `CH`, `NL`,
`TD`, `DDT`, `THCB`, `DT`, `CHLT`) so every topic is represented in all splits.

The generated records now mirror inference-time context:

```text
question + detected topic + unit hints + topic hints + retrieved premises
  -> [FOL] + executable [CODE] + [ANSWER]
```

Records that do not yet have a reliable executable formula target are kept for
audit metadata with `trainable=false`. The training script filters those out by
default, so LoRA is not trained to memorize `answer = gold_answer`. Prompt
tokens are masked during training; only the assistant completion contributes to
loss.

## 3. Local Smoke Test

Use local only as a smoke test on RTX 3050/4050-class GPUs:

```powershell
python finetuning/scripts/inspect_gpu.py
python finetuning/scripts/train_lora_unsloth.py --config finetuning/configs/qwen2_5_7b_local_smoke.yaml
```

The smoke config uses `max_steps: 20`, `max_seq_length: 512`, and LoRA rank 8.

## 4. Modal Full Training

Install and authenticate Modal:

```powershell
pip install modal
modal setup
```

If your local `.env` contains `HF_TOKEN=...`, the Modal runner forwards it as a
temporary Modal secret. For public models such as `Qwen/Qwen2.5-7B-Instruct`,
`HF_TOKEN` is usually optional.

Run a remote smoke test:

```powershell
modal run finetuning/modal/train_lora_modal.py --max-steps 20
```

Run the full A10 training job:

```powershell
modal run finetuning/modal/train_lora_modal.py
```

The Modal runner stores model cache, processed data, and runs in Modal Volumes.
After a run, download the output:

```powershell
modal volume get physics-lora-runs <run_id> .\finetuning\runs\<run_id>
```

## 5. Ollama Export

The training job saves a LoRA adapter, not a ready-to-run Ollama model. Follow:

```text
finetuning/scripts/export_ollama_gguf.md
```

The intended flow is:

```text
LoRA adapter -> merge into Qwen2.5-7B -> GGUF -> ollama create
```

Merge on Modal first:

```powershell
modal run finetuning/modal/merge_lora_modal.py --run-id qwen2_5_7b_lora_20260605_185537
```

If A10 is too tight for merge, use:

```powershell
modal run finetuning/modal/merge_lora_modal.py --run-id qwen2_5_7b_lora_20260605_185537 --gpu L40S
```

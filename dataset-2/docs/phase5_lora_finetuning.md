# Phase 5: LoRA Fine-Tuning Plan

## Muc tieu

Phase 5 fine-tunes the reasoner model so it better follows the project output
contract:

```text
[FOL]
[CODE]
[ANSWER]
```

It is not intended to replace RAG, hints, sandbox execution, or the evaluator.
The first implementation uses fixed defaults, then later runs can compare a
small number of configs if needed.

## Data Strategy

Source file:

```text
dataset_2/Physics_Problems_Text_Only.csv
```

The dataset is split by topic, not by file order:

```text
LD    -> shuffle -> 80/10/10
CH    -> shuffle -> 80/10/10
NL    -> shuffle -> 80/10/10
TD    -> shuffle -> 80/10/10
DDT   -> shuffle -> 80/10/10
THCB  -> shuffle -> 80/10/10
DT    -> shuffle -> 80/10/10
CHLT  -> shuffle -> 80/10/10
```

`CHLT` has only 20 rows, so the expected split is about 16 train, 2 val, 2
test. This prevents small topics from disappearing from validation/test.

## Default Training Config

```yaml
model_name: Qwen/Qwen2.5-7B-Instruct
num_train_epochs: 3
learning_rate: 2e-4
lora_r: 16
lora_alpha: 32
max_seq_length: 1024
per_device_train_batch_size: 1
gradient_accumulation_steps: 8
eval_strategy: epoch
save_strategy: epoch
load_best_model_at_end: true
```

These values are intentionally fixed for v1. Hyperparameter search is deferred
until after a baseline train/eval cycle exists.

## GPU Strategy

Local RTX 3050 and RTX 4050 machines are suitable for:

- verifying CUDA/PyTorch installation;
- preparing data;
- running `max_steps=20` smoke tests;
- testing export steps.

They are not the default full-training target because 7B QLoRA can fit only
tightly on 6GB-class GPUs and often fails once sequence length, cache, or other
desktop GPU usage is included.

The default full-training target is Modal `A10`. Alternatives:

- `L4`: cheaper but slower;
- `L40S`: faster with more VRAM, higher cost.

## Modal Workflow

```powershell
pip install modal
modal setup
modal run finetuning/modal/train_lora_modal.py --max-steps 20
modal run finetuning/modal/train_lora_modal.py
```

The runner uses:

```text
physics-lora-hf-cache
physics-lora-data
physics-lora-runs
```

as Modal Volumes.

## Ollama Workflow

Training produces a LoRA adapter. Ollama should run the merged/quantized model:

```text
adapter -> merged HF model -> GGUF -> ollama create physics-qwen-lora
```

Detailed commands live in:

```text
finetuning/scripts/export_ollama_gguf.md
```

Do not assume the raw LoRA adapter directory can be used directly as the final
Ollama model.

## Evaluation

After training, evaluate in this order:

```powershell
python evaluate_pipeline.py --mode local --id-prefix CHLT --start 0 --limit 20 --output eval_results/CHLT/lora_20.jsonl --report eval_results/CHLT/lora_20.md --report-misses-only
```

Repeat for `LD`, `DT`, `TD`, `THCB`, `CH`, `DDT`, and `NL`. If the 20-row/topic
check is better than baseline, run the full dataset.

Acceptance targets:

- output parse rate for `[FOL]`, `[CODE]`, `[ANSWER]` is high;
- hard topics `THCB`, `DT`, `DDT`, `CHLT` improve;
- strong topics `CH` and `NL` do not regress heavily.


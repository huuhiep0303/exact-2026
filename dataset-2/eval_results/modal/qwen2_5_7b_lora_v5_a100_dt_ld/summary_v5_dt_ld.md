# Qwen2.5-7B LoRA V5: DT/LD Evaluation

## Run status

- Modal account: `duonghoangminh15112005`
- Run: `qwen2_5_7b_lora_v5_a100`
- Base model: `Qwen/Qwen2.5-7B-Instruct`
- Training: 4 epochs, 1072 steps, final train loss `0.13466`
- Inference: merged model served by vLLM on Modal A100
- Qdrant: connected to `physics_kb`, 334 points
- Runtime errors: 0
- Blank predictions: 0

## Accuracy

| Topic | Qwen3 V4 baseline | Qwen2.5 V5 | Change | Target |
| --- | ---: | ---: | ---: | ---: |
| DT | 43/68 (63.24%) | 44/68 (64.71%) | +1 | 55/68 (80.88%) |
| LD | 246/397 (61.96%) | 285/397 (71.79%) | +39 | 318/397 (80.10%) |
| Combined | 289/465 (62.15%) | 329/465 (70.75%) | +40 | 373/465 (80.22%) |

## Remaining misses

| Miss type | DT | LD | Total |
| --- | ---: | ---: | ---: |
| Geometry/vector | 8 | 78 | 86 |
| Wrong target or formula | 7 | 26 | 33 |
| Unit/scale | 9 | 6 | 15 |
| Evaluator format | 0 | 1 | 1 |
| Qualitative | 0 | 1 | 1 |
| Total | 24 | 112 | 136 |

The main bottleneck is still geometry and vector composition, especially in the later LD electric-field blocks. Fine-tuning improved repeated numeric templates substantially, but it did not provide a reliable general geometry procedure.

Two clear router errors were found among misses:

- `LD041` was routed to `ac_circuit` because the symbolic force notation triggered an AC pattern.
- `LD137` was routed to `general` instead of `coulomb_force`.

DT symbolic answers also remain weak. Examples include perpendicular-bisector expressions, square-center vector sums, and requests where the answer must preserve a symbolic variable or radical rather than become an unsupported numeric value.

## Artifacts

- `qwen2_5_7b_lora_v5_a100/DT_0_1000.md`
- `qwen2_5_7b_lora_v5_a100/DT_0_1000.jsonl`
- `qwen2_5_7b_lora_v5_a100/LD_0_1000.md`
- `qwen2_5_7b_lora_v5_a100/LD_0_1000.jsonl`
- `qwen2_5_7b_lora_v5_a100/miss_audit_v5.jsonl`
- `qwen2_5_7b_lora_v5_a100/qdrant_preflight.txt`

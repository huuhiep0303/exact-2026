# Qwen3-8B LoRA V3 Post-Fix 8 Topic Benchmark

| Topic | Accuracy | Numeric | Unit | Physical unit | Runtime errors | Blank | Top miss reasons |
|---|---:|---:|---:|---:|---:|---:|---|
| CH | 20/20 (100%) | 20/20 | 20/20 | 20/20 | 0/20 | 0/20 | - |
| CHLT | 19/20 (95%) | 0/20 | 20/20 | 0/20 | 0/20 | 0/20 | numeric_wrong:1 |
| DDT | 12/20 (60%) | 10/20 | 16/20 | 10/20 | 0/20 | 0/20 | numeric_wrong:5, value_or_formula_mismatch:2, unit_mismatch:1 |
| DT | 19/20 (95%) | 17/20 | 20/20 | 17/20 | 0/20 | 0/20 | numeric_wrong:1 |
| LD | 10/20 (50%) | 10/20 | 19/20 | 10/20 | 0/20 | 0/20 | numeric_wrong:10 |
| NL | 18/20 (90%) | 18/20 | 20/20 | 18/20 | 0/20 | 0/20 | numeric_wrong:2 |
| TD | 6/20 (30%) | 9/20 | 15/20 | 6/20 | 0/20 | 0/20 | numeric_wrong:9, unit_mismatch:3, value_or_formula_mismatch:2 |
| THCB | 10/20 (50%) | 6/20 | 19/20 | 6/20 | 0/20 | 0/20 | numeric_wrong:9, value_or_formula_mismatch:1 |

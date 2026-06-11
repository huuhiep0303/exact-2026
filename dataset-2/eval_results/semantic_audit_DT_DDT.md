# Semantic Audit: DT and DDT

This audit separates model quality from evaluator quality. A row can be marked
MISS in the normal report even when the answer is physically/semantically
correct. Conversely, a newer run can pass more unit checks while regressing in
reasoning.

Compared files:

- `eval_results/DDT/1.md`
- `eval_results/DDT/qdrant_upgrade_20.md`
- `eval_results/DDT/base_rag_after_upgrade_20.md`
- `eval_results/DDT/lora_20.md`
- `eval_results/DT/1.md`
- `eval_results/DT/qdrant_upgrade_20.md`
- `eval_results/DT/base_rag_after_upgrade_20.md`
- `eval_results/DT/lora_20.md`

## DDT: Semantic Correct But Marked MISS

| ID | Run | Gold | Prediction | Audit | Needed fix |
| --- | --- | --- | --- | --- | --- |
| DDT131 | `1`, `qdrant_upgrade_20`, `base_rag_after_upgrade_20` | `0.005 T` | `0.00502655 T` | Correct within physics rounding. Model used `mu0 = 4*pi*1e-7`; gold is rounded. | Loosen numeric tolerance for rounded textbook constants, or normalize common constants. |
| DDT136 | `qdrant_upgrade_20`, `base_rag_after_upgrade_20` | `Number of turns density and current intensity` | `Number of turns density and current intensity`, `Number of turns and current intensity` | Semantically correct. `turn density` and `number of turns per unit length` are equivalent in this context. | Qualitative synonym normalization. |
| DDT137 | `1`, `qdrant_upgrade_20`, `base_rag_after_upgrade_20` | `Doubled` | `2`, `Doubled` | Correct. `2` means doubled when question asks "how does it change?" | Qualitative ratio normalization: `2`, `2x`, `factor of two`, `doubled`. |
| DDT138 | `1`, `qdrant_upgrade_20` | `5.654 mT` | `0.00565487 T` | Correct physical equivalence. Later evaluator handles this better. | Keep physical unit equivalence for magnetic field. |
| DDT140 | `qdrant_upgrade_20`, `base_rag_after_upgrade_20`, `lora_20` | `Approximately zero` | `0`, `external field is negligible`, `nearly zero` | Correct qualitative answer. | Qualitative zero synonyms: `0`, `negligible`, `nearly zero`, `approximately zero`. |
| DDT142 | `qdrant_upgrade_20` | `60 V` | `-60 V` | Correct magnitude if the task asks induced EMF magnitude; negative sign encodes Lenz direction. | Sign-insensitive comparison for EMF magnitude questions. |
| DDT144 | `qdrant_upgrade_20` | `75 V` | `-75 V` | Same as DDT142. | Sign-insensitive comparison for EMF magnitude questions. |
| DDT148 | `qdrant_upgrade_20` | `10 V` | `-10 V` | Same as DDT142. | Sign-insensitive comparison for EMF magnitude questions. |
| DDT149 | `base_rag_after_upgrade_20` | `Increase and opposite current direction` | `EMF opposes the rapid increase in current` | Semantically close and includes the Lenz-direction idea. | Qualitative induction synonym matching. |

## DDT: True Reasoning Or Calculation Regressions

| ID | Better earlier behavior | Worse later behavior | Audit | Needed fix |
| --- | --- | --- | --- | --- |
| DDT139 | `1.md`: `2.51327 J/m^3`, close to `2.51 J/m^3` | `qdrant_upgrade_20`: `25132.7 J/m^3`; `base_rag_after_upgrade_20`: `1.5915e+12 J/m^3`; `lora_20`: `1.05 nJ/m^3` | Real regression. The model confuses given turn density `n = 1000 turns/m` with total turns/length and invents bad conversions. | Add DDT energy-density guard: if `turn density` is given, use it directly in `B = mu0*n*I`; area is irrelevant for energy density `u = B^2/(2*mu0)`. |
| DDT141 | `base_rag_after_upgrade_20`: `0.003 Wb`, correct | `qdrant_upgrade_20`: `3e-06 Wb`; `lora_20`: `0.3 Wb` | Real calculation/unit regression in some runs. Correct flux linkage through entire solenoid is `N*B*A_turn`. | Hint must distinguish single-turn flux `Phi = B*A` from total flux linkage `N*Phi`. |
| DDT145 | `lora_20`: `Current - I`, semantically close | `base_rag_after_upgrade_20`: numeric inductance in `H` | Retrieval/prompt chooses quantitative formula when question is qualitative. | Route "does not depend on" as qualitative; force answer from formula variables, not calculation. |
| DDT146 | None fully correct | Numeric inductance or `Solenoid` | Application question incorrectly solved as formula task. | Add DDT application hint: solenoid applications include electromagnet, relay, electric bell/actuator. |

## DT: Semantic Correct But Marked MISS

| ID | Run | Gold | Prediction | Audit | Needed fix |
| --- | --- | --- | --- | --- | --- |
| DT033 | `qdrant_upgrade_20` | `6300000 V/m` | `6.3e+06 N/C` | Correct. `N/C` is physically equivalent to `V/m`. Earlier model reasoned this case better. | Keep electric-field unit equivalence and ensure reports show physical equivalence clearly. |
| DT035 | `qdrant_upgrade_20`, `base_rag_after_upgrade_20` | `45.10^{5} V/m` | `4.5e+06 N/C` | Correct if gold means `45 * 10^5 = 4.5e6`. MISS indicates gold-expression parsing is fragile. | Parse textbook notation like `45.10^{5}` as `45*10^5`, not decimal `45.10`. |
| DT036 | `qdrant_upgrade_20` | `12 cm` | `0.12 m` | Correct physical equivalence. If marked MISS, unit conversion/equivalence was insufficient in that run. | Keep length unit equivalence. |
| DT027 | `lora_20` | `8 cm` | `8 cm` | Correct. This is a case where LoRA did better than base+RAG after upgrade. | Preserve zero-field same-sign ratio rule. |
| DT028 | `base_rag_after_upgrade_20` | `4 cm` | `0.04 m` | Correct. | Keep length unit equivalence. |

## DT: True Reasoning Or Geometry Regressions

| ID | Better earlier behavior | Worse later behavior | Audit | Needed fix |
| --- | --- | --- | --- | --- |
| DT033 | `qdrant_upgrade_20`: `6.3e+06 N/C`, correct | `base_rag_after_upgrade_20`: `1.17e+07 N/C`; `lora_20`: `1.02e+06 V/m` | Real regression. Geometry is collinear: `AC=20 cm`, `AB=15 cm`, `BC=5 cm`; fields oppose, so `9e6 - 2.7e6 = 6.3e6`. | Add deterministic collinear electric-field solver/checker. |
| DT001 | None correct in inspected runs | `115200`, `814587`, `806394` | True geometry error. Since `MA=MB=5 cm` and `AB=10 cm`, M is midpoint; equal same-sign fields cancel. | Solver must detect midpoint and equal charges. |
| DT003 | Some runs closer but still wrong | `225000`, `450000`, `5196.15` | True vector-component error. For equal charges on perpendicular bisector, horizontal components cancel and vertical components add. | Add perpendicular-bisector vector formula. |
| DT004 | Earlier/base gives `0.9 N`, closer than LoRA `450 N` | LoRA gives `450 N` | True calculation/geometry error. This should follow DT003's field then multiply by `q3`. | Use field-first solver when force on test charge is asked. |
| DT005 | `1.md`: `0.225 N`, closer but still wrong | later runs `0` or tiny negative | True direction error. Opposite charges at equal distances produce field components in same direction, not cancellation. | Add sign-aware vector direction rule. |
| DT006 | `1.md`: `-0.16817 N`, magnitude correct | later runs `0.0125 N`, `-4.68e-05 N`, `120 V/m` | Earlier model solved magnitude well but kept sign. Later models regress. | For force magnitude questions, compare absolute value; solver should output magnitude unless direction requested. |
| DT025 | None fully correct in inspected runs | `0.12 m`, `0.25 m`, `0.0615385 m`, `3 cm` | True zero-field location error. Opposite signs: zero point is outside segment on side of smaller magnitude charge. | Deterministic zero-field solver. |
| DT029/DT030 | None fully correct in inspected runs | in-segment distances or complex values | True zero-field region error for opposite signs. | Solver must first determine valid region, then solve distance. |
| DT034 | None fully correct in inspected runs | V=0 rule used instead of E=0 | Retrieval/rerank error plus solver absence. | If question says electric field zero, forbid V=0 premise. |
| DT037 | None correct in inspected runs | `12.6491 m`, `0.15 m`, `16 cm` | True same-sign zero-field reference-point error. | Solver must return requested distance from A or B. |

## Immediate Supplements To Implement

1. Evaluator supplements:
   - sign-insensitive match for induced EMF magnitude questions;
   - parse `45.10^{5}` as `45*10^5`;
   - qualitative synonyms for `doubled`, `factor of two`, `2`, `negligible`, `approximately zero`;
   - mark semantic-correct separately from final numeric score in future reports.

2. DT solver supplements:
   - collinear two-charge electric field;
   - equal-distance midpoint cancellation;
   - perpendicular-bisector formula;
   - force on test charge as `F = |q3| * |E_net|`;
   - same-sign and opposite-sign `E=0` point solver with requested distance from A/B.

3. DDT solver/hint supplements:
   - energy density `u = B^2/(2*mu0)` should ignore cross-sectional area when `n` is given;
   - flux linkage through entire solenoid: `N*B*A_turn`;
   - qualitative router for "does not depend on", "applications", "external magnetic field", and induction direction.


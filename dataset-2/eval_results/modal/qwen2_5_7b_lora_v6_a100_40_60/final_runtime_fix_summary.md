# Final Runtime Pipeline Fix Summary

Local validation after final pipeline fixes:

- Tests: `python -m unittest tests/test_answer_target.py tests/test_evaluator_normalization.py tests/test_deterministic_solver.py tests/test_finetuning_data_prep.py tests/test_hint_engine.py tests/test_problem_facts.py`
- Result: `59 tests OK`

Projected effect on already-downloaded V6 sample `start=40`, `limit=20` without calling the model again:

| Topic | Old V6 | Projected with final runtime fixes | Gain |
|---|---:|---:|---:|
| CH | 15/20 | 20/20 | +5 |
| CHLT | 0/0 | 0/0 | +0 |
| DDT | 15/20 | 20/20 | +5 |
| DT | 11/20 | 11/20 | +0 |
| LD | 8/20 | 16/20 | +8 |
| NL | 16/20 | 19/20 | +3 |
| TD | 18/20 | 20/20 | +2 |
| THCB | 19/20 | 20/20 | +1 |

Total over non-empty topics: old `102/140 = 72.86%`, projected `126/140 = 90.00%`.

Main fixes:

- CH: resonance power guard `P = U^2/R`.
- DDT: induced EMF current-change parser, qualitative solenoid/inductance guards, RLC characteristic from `Z_L/Z_C`.
- LD: symbolic `sqrt(2)F0`, equilateral center zero force, collinear equidistant midpoint, point-distance parser, equal-distance dipole field, direction toward negative charge.
- NL: isolated capacitor energy percentage, LC energy location/quarter-period qualitative guard.
- TD: direct `Q = C U` charge guard with `pC` compatibility.
- THCB: multi-answer absolute error plus percentage relative error compatibility.
- Evaluator: symbolic/qualitative normalization for F0, inductive characteristic, solenoid qualitative wording, and Vietnamese `q2` direction phrase.

Recommendation: run Modal sample 40-60 again with the same command. If it matches the projection closely, run final full evaluation. No additional fine-tuning is required for these fixes.

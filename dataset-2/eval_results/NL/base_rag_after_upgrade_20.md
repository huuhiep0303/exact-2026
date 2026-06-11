# Pipeline Evaluation Report

## Summary

| Metric | Value |
| --- | ---: |
| Total | 20 |
| Final accuracy | 19/20 (95.00%) |
| Exact full-string match | 8/20 (40.00%) |
| Numeric value match | 19/20 (95.00%) |
| Strict unit match | 20/20 (100.00%) |
| Physical equivalent match | 19/20 (95.00%) |
| Runtime errors | 0/20 (0.00%) |
| Average time per row | 38.25s |

## Results Table

| # | ID | Status | Gold | Prediction | Confidence | Time |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | NL001 | OK | 100.00 mJ | 100 mJ | 0.98 | 74.65s |
| 2 | NL002 | OK | 90.00 mJ | 90 mJ | 0.98 | 29.64s |
| 3 | NL003 | OK | 900.00 mJ | 900 mJ | 0.98 | 35.23s |
| 4 | NL004 | OK | 1000.00 mJ | 1000 mJ | 0.98 | 21.08s |
| 5 | NL005 | OK | 9.49 V | 9.48683 V | 0.98 | 34.39s |
| 6 | NL006 | OK | 10.00 V | 10 V | 0.98 | 31.10s |
| 7 | NL007 | OK | 0.11 A | 0.11 A | 0.98 | 34.45s |
| 8 | NL008 | OK | 0.01 H | 0.01 H | 0.98 | 58.06s |
| 9 | NL009 | OK | 0.10 μF | 0.1 μF | 0.98 | 69.36s |
| 10 | NL010 | OK | 0.0004 H | 0.0004 H | 0.98 | 34.86s |
| 11 | NL011 | OK | 216.00 mJ | 216 mJ | 0.98 | 38.81s |
| 12 | NL012 | OK | 0.40 μF | 0.4 μF | 0.98 | 34.38s |
| 13 | NL013 | OK | 14.83 V | 14.83 V | 0.98 | 33.13s |
| 14 | NL014 | OK | 1250.00 mJ | 1250 mJ | 0.98 | 36.78s |
| 15 | NL015 | OK | 0.09 A | 0.09 A | 0.98 | 31.34s |
| 16 | NL016 | OK | 0.002 H | 0.002 H | 0.98 | 33.25s |
| 17 | NL017 | OK | 17.32 V | 17.32 V | 0.98 | 31.72s |
| 18 | NL018 | MISS | 0.07 μF | 0 μF | 0.98 | 28.59s |
| 19 | NL019 | OK | 0.25 mH | 0.25 mH | 0.98 | 38.15s |
| 20 | NL020 | OK | 675.00 mJ | 675 mJ | 0.98 | 35.95s |

## Miss Details

### 1. MISS NL018

**Question:** A capacitor stores 0.75 mJ of energy when the voltage across it is 150 V. Calculate its capacitance (unit: μF, round the result to two decimal places).

**Gold:** `0.07 μF`

**Prediction:** `0 μF`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Energy stored in inductor, the computation yields a result of 0, in units of μF.

**Retrieved Premises:**

- Energy stored in inductor: W_L = 0.5 * L * I^2 | Answer type: quantitative
- Excerpt from NL_lc_energy_oscillation (part 12): | Use: NL if capacitor energy is known at a moment, inductor energy is W_total - W_C. | Note: Source: reference_docs/NL_lc_energy_oscillation.md | Answer type: reference
- Excerpt from NL_lc_energy_oscillation (part 13): | Use: NL if inductor energy is known at a moment, capacitor energy is W_total - W_L. | Note: Source: reference_docs/NL_lc_energy_oscillation.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: [FOL]: W_C > 0.5 * C * U^2 [CODE]: ```python import math # Given values (converted to SI) W_C = 0.75e-3 # Convert mJ to J U = 150 # V # Apply formula to find capacitance C C = 2 * W_C / U**2 answer = C unit = "μF" # Round the result to two decimal places answer = round(answer, 2) ``` [ANSWER]: 0.03 μF


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
| Average time per row | 31.69s |

## Results Table

| # | ID | Status | Gold | Prediction | Confidence | Time |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | NL001 | OK | 100.00 mJ | 100 mJ | 0.98 | 76.73s |
| 2 | NL002 | OK | 90.00 mJ | 90 mJ | 0.98 | 25.98s |
| 3 | NL003 | OK | 900.00 mJ | 900 mJ | 0.98 | 36.83s |
| 4 | NL004 | OK | 1000.00 mJ | 1000 mJ | 0.98 | 22.16s |
| 5 | NL005 | OK | 9.49 V | 9.49 V | 0.98 | 31.45s |
| 6 | NL006 | OK | 10.00 V | 10 V | 0.98 | 24.94s |
| 7 | NL007 | OK | 0.11 A | 0.11 A | 0.98 | 29.86s |
| 8 | NL008 | OK | 0.01 H | 0.01 H | 0.97 | 32.20s |
| 9 | NL009 | OK | 0.10 μF | 0.1 μF | 0.98 | 34.93s |
| 10 | NL010 | OK | 0.0004 H | 0.0004 H | 0.97 | 18.77s |
| 11 | NL011 | OK | 216.00 mJ | 216 mJ | 0.98 | 30.96s |
| 12 | NL012 | OK | 0.40 μF | 0.4 μF | 0.98 | 33.15s |
| 13 | NL013 | OK | 14.83 V | 14.8324 V | 0.98 | 26.63s |
| 14 | NL014 | OK | 1250.00 mJ | 1250 mJ | 0.98 | 31.68s |
| 15 | NL015 | OK | 0.09 A | 0.09 A | 0.98 | 29.70s |
| 16 | NL016 | OK | 0.002 H | 0.002 H | 0.98 | 29.48s |
| 17 | NL017 | OK | 17.32 V | 17.32 V | 0.98 | 27.03s |
| 18 | NL018 | MISS | 0.07 μF | 0 μF | 0.98 | 22.32s |
| 19 | NL019 | OK | 0.25 mH | 0.25 mH | 0.97 | 36.54s |
| 20 | NL020 | OK | 675.00 mJ | 675 mJ | 0.97 | 32.37s |

## Miss Details

### 1. MISS NL018

**Question:** A capacitor stores 0.75 mJ of energy when the voltage across it is 150 V. Calculate its capacitance (unit: μF, round the result to two decimal places).

**Gold:** `0.07 μF`

**Prediction:** `0 μF`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Energy stored in capacitor, the computation yields a result of 0, in units of μF.

**Retrieved Premises:**

- Energy stored in capacitor: W = 0.5 * C * U^2 = Q^2/(2*C) = Q*U/2 | Answer type: quantitative
- Capacitance of parallel-plate capacitor: C = epsilon_0 * epsilon * A / d | Answer type: quantitative
- Excerpt from TD_capacitor_rules (part 2): | Use: TD capacitance. For a parallel-plate capacitor C = epsilon0*epsilon_r*A/d. Convert area to m^2 and distance to m before computing. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: [FOL]: C > 0.75e-3 = 0.5 * C * 150^2 [CODE]: ```python import math # Given values (converted to SI) W = 0.75e-3 # energy in J U = 150 # voltage in V # Apply formula W = 0.5 * C * U**2 and solve for C C = 2 * W / U**2 answer = round(C, 2) unit = "μF" ``` [ANSWER]: 0.01 μF


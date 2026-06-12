# Pipeline Evaluation Report

## Summary

| Metric | Value |
| --- | ---: |
| Total | 20 |
| Final accuracy | 18/20 (90.00%) |
| Exact full-string match | 8/20 (40.00%) |
| Numeric value match | 16/20 (80.00%) |
| Strict unit match | 19/20 (95.00%) |
| Physical equivalent match | 15/20 (75.00%) |
| Runtime errors | 0/20 (0.00%) |
| Average time per row | 6.85s |
| Qdrant enabled | true |
| Qdrant connected | true |

## Results Table

| # | ID | Status | Gold | Prediction | Source | Strategy | Route | Target | Confidence | Time |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| 1 | THCB001 | OK | 0.1 A | 0.1 A | sandbox |  | dc_circuit | unknown | 0.97 | 54.40s |
| 2 | THCB002 | OK | 3.57 % | 3.57 % | sandbox |  | measurement_error | unknown | 0.98 | 6.78s |
| 3 | THCB003 | OK | 1.0 Ω | 1 Ω | deterministic_solver | thcb_resistance_absolute_error | measurement_error | unknown | 1.0 | 6.23s |
| 4 | THCB004 | OK | 0.26 A | 0.26 A | sandbox |  | measurement_error | unknown | 0.97 | 4.36s |
| 5 | THCB005 | MISS | 4.21 % | 0.24 % | sandbox |  | measurement_error | power | 0.98 | 3.97s |
| 6 | THCB006 | OK | 0.4 Ω | 0.4 Ω | sandbox |  | measurement_error | angular_frequency | 0.98 | 5.41s |
| 7 | THCB007 | OK | 0.2 A | 0.2 A | sandbox |  | measurement_error | unknown | 0.97 | 3.53s |
| 8 | THCB008 | OK | 0.19 W | 0.19 W | deterministic_solver | thcb_power_absolute_error | measurement_error | power | 1.0 | 4.90s |
| 9 | THCB009 | OK | 1.5 Ω | 1.5 Ω | sandbox |  | dc_circuit | angular_frequency | 0.98 | 5.03s |
| 10 | THCB010 | MISS | 3.92 % | 4 % | sandbox |  | measurement_error | angular_frequency | 0.98 | 3.45s |
| 11 | THCB066 | OK | I_D₁ = 1.0; I_D₂ = 1.0; I_total = 2.0 A; A; A | I_D1 = 1; I_D2 = 1; I_total = 2 A; A; A | deterministic_solver | thcb_parallel_identical_lamps | dc_circuit | unknown | 1.0 | 4.41s |
| 12 | THCB067 | OK | I_D₂ = 0.6 A | 0.6 A | sandbox |  | dc_circuit | unknown | 0.98 | 3.51s |
| 13 | THCB068 | OK | I_total = 1.5 A | 1.5 A | deterministic_solver | thcb_parallel_total_current | dc_circuit | unknown | 1.0 | 3.31s |
| 14 | THCB069 | OK | I_D = 1.0 A | I_1 = I_2 = 1.0 A | sandbox |  | dc_circuit | unknown | 0.98 | 3.51s |
| 15 | THCB070 | OK | I_total_new = 0.5 A | 0.5 A | deterministic_solver | thcb_removed_branch_current | dc_circuit | unknown | 1.0 | 3.17s |
| 16 | THCB071 | OK | Resistance decreases → current increases. — | Increase | sandbox |  | dc_circuit | unknown | 0.48 | 3.58s |
| 17 | THCB072 | OK | I_total = 3.0 A | I_total = 3.0 A | sandbox |  | dc_circuit | power | 0.98 | 3.33s |
| 18 | THCB073 | OK | The lamp shines brighter because the current through it increases. — | Brighter | sandbox |  | dc_circuit | qualitative | 0.48 | 3.44s |
| 19 | THCB074 | OK | Rtd = 7.5 Ω | 7.5 Ω | sandbox |  | dc_circuit | unknown | 0.98 | 3.64s |
| 20 | THCB075 | OK | P = 48.0 W | 48 W | deterministic_solver | thcb_power | dc_circuit | power | 1.0 | 7.00s |

## Miss Details

### 1. MISS THCB005

**Question:** In an experiment, the measured voltage was 9.5 ± 0.2 V, and the measured current was 0.95 ± 0.02 A. What is the relative error in the power?

**Gold:** `4.21 %`

**Prediction:** `0.24 %`

**Confidence:** `0.98`

**Pipeline Metadata:** source=`sandbox`, strategy=`none`, route=`measurement_error`, target=`power`, expected_dimension=`power`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Excerpt from THCB_measurement_error (part 24), the computation yields a result of 0.24, in units of %.

**Retrieved Premises:**

- Excerpt from THCB_measurement_error (part 24): | Use: THCB if measured value is zero, relative error is undefined; answer qualitatively or use absolute error only. | Note: Source: reference_docs/THCB_measurement_error.md | Answer type: reference
- Error propagation — power: Z = X^n => delta_Z = n * delta_X | Use: Multiply relative error by the exponent | Answer type: quantitative
- Total measurement error: Delta_total = max(Delta_random, Delta_instrument) | Use: The total error is the larger of random error and instrument error | Answer type: quantitative

**Predicted CoT / Reasoning Trace:**

1. Step 1: Read the requested quantity and the useful givens from the problem: 9.5; 0.2; 0.95; 0.02.
2. Step 2: Keep the given quantities in consistent SI units and preserve the requested output unit for the final report.
3. Step 3: Choose the governing relation: use Delta x equal to the instrument least count when no other uncertainty is given; relative error = Delta x / measured value; percentage error = relative error * 100%.
4. Step 4: Substitute the converted values from the earlier steps, simplify the intermediate SI result, and round only after the arithmetic is complete.
5. Step 5: The computed result in the requested format is 0.24 %.

### 2. MISS THCB010

**Question:** If the actual resistance is 10.2 Ω but the measured value is 9.8 Ω, what is the relative error?

**Gold:** `3.92 %`

**Prediction:** `4 %`

**Confidence:** `0.98`

**Pipeline Metadata:** source=`sandbox`, strategy=`none`, route=`measurement_error`, target=`angular_frequency`, expected_dimension=`angular_frequency`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Excerpt from THCB_measurement_error (part 24), the computation yields a result of 4, in units of %.

**Retrieved Premises:**

- Excerpt from THCB_measurement_error (part 24): | Use: THCB if measured value is zero, relative error is undefined; answer qualitatively or use absolute error only. | Note: Source: reference_docs/THCB_measurement_error.md | Answer type: reference
- Excerpt from THCB_measurement_error (part 26): | Use: THCB precision comparison. Smaller relative error means more precise measurement, even if absolute error is larger. | Note: Source: reference_docs/THCB_measurement_error.md | Answer type: reference
- Relative error (percentage error): delta_X = Delta_X / X * 100% | Use: Ratio of absolute error to value, expressed as % | Answer type: symbolic

**Predicted CoT / Reasoning Trace:**

1. Step 1: Read the requested quantity and the useful givens from the problem: 10.2 ohm; 9.8 ohm.
2. Step 2: Keep the given quantities in consistent SI units and preserve the requested output unit for the final report.
3. Step 3: Choose the governing relation: relative error = Delta x / measured value.
4. Step 4: Substitute the converted values from the earlier steps, simplify the intermediate SI result, and round only after the arithmetic is complete.
5. Step 5: The computed result in the requested format is 4.0 %.


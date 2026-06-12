# Pipeline Evaluation Report

## Summary

| Metric | Value |
| --- | ---: |
| Total | 20 |
| Final accuracy | 20/20 (100.00%) |
| Exact full-string match | 7/20 (35.00%) |
| Numeric value match | 18/20 (90.00%) |
| Strict unit match | 19/20 (95.00%) |
| Physical equivalent match | 17/20 (85.00%) |
| Runtime errors | 0/20 (0.00%) |
| Average time per row | 5.03s |
| Qdrant enabled | true |
| Qdrant connected | true |

## Results Table

| # | ID | Status | Gold | Prediction | Source | Strategy | Route | Target | Confidence | Time |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| 1 | THCB001 | OK | 0.1 A | 0.1 A | sandbox |  | dc_circuit | unknown | 0.97 | 34.37s |
| 2 | THCB002 | OK | 3.57 % | 3.57 % | sandbox |  | measurement_error | percentage | 0.98 | 3.13s |
| 3 | THCB003 | OK | 1.0 Ω | 1 Ω | deterministic_solver | thcb_resistance_absolute_error | measurement_error | unknown | 1.0 | 5.17s |
| 4 | THCB004 | OK | 0.26 A | 0.26 A | sandbox |  | measurement_error | unknown | 0.97 | 3.56s |
| 5 | THCB005 | OK | 4.21 % | 4.21053 % | deterministic_solver | thcb_power_relative_error | measurement_error | percentage | 1.0 | 3.57s |
| 6 | THCB006 | OK | 0.4 Ω | 0.4 Ω | sandbox |  | measurement_error | unknown | 0.98 | 3.20s |
| 7 | THCB007 | OK | 0.2 A | 0.2 A | sandbox |  | measurement_error | unknown | 0.97 | 3.51s |
| 8 | THCB008 | OK | 0.19 W | 0.19 W | deterministic_solver | thcb_power_absolute_error | measurement_error | power | 1.0 | 4.72s |
| 9 | THCB009 | OK | 1.5 Ω | 1.5 Ω | sandbox |  | dc_circuit | unknown | 0.98 | 3.35s |
| 10 | THCB010 | OK | 3.92 % | 3.92157 % | deterministic_solver | thcb_relative_error | measurement_error | percentage | 1.0 | 3.24s |
| 11 | THCB066 | OK | I_D₁ = 1.0; I_D₂ = 1.0; I_total = 2.0 A; A; A | I_D1 = 1; I_D2 = 1; I_total = 2 A; A; A | deterministic_solver | thcb_parallel_identical_lamps | dc_circuit | unknown | 1.0 | 4.13s |
| 12 | THCB067 | OK | I_D₂ = 0.6 A | 0.6 A | sandbox |  | dc_circuit | unknown | 0.98 | 3.28s |
| 13 | THCB068 | OK | I_total = 1.5 A | 1.5 A | deterministic_solver | thcb_parallel_total_current | dc_circuit | unknown | 1.0 | 3.07s |
| 14 | THCB069 | OK | I_D = 1.0 A | I_1 = I_2 = 1.0 A | sandbox |  | dc_circuit | unknown | 0.98 | 3.47s |
| 15 | THCB070 | OK | I_total_new = 0.5 A | 0.5 A | deterministic_solver | thcb_removed_branch_current | dc_circuit | unknown | 1.0 | 3.04s |
| 16 | THCB071 | OK | Resistance decreases → current increases. — | Increase | sandbox |  | dc_circuit | unknown | 0.48 | 3.28s |
| 17 | THCB072 | OK | I_total = 3.0 A | 3 A | deterministic_solver | thcb_parallel_total_current | dc_circuit | unknown | 1.0 | 3.23s |
| 18 | THCB073 | OK | The lamp shines brighter because the current through it increases. — | Brighter | sandbox |  | dc_circuit | qualitative | 0.48 | 3.16s |
| 19 | THCB074 | OK | Rtd = 7.5 Ω | 7.5 Ω | sandbox |  | dc_circuit | unknown | 0.98 | 3.07s |
| 20 | THCB075 | OK | P = 48.0 W | 48 W | deterministic_solver | thcb_power | dc_circuit | power | 1.0 | 2.97s |

## Miss Details

No rows to show.

# Qwen2.5-7B LoRA V6 Sample 40-60 Comparison

Window: per-topic rows `start=40`, `limit=20` from `dataset_2/physic_version_2.csv`. CHLT has only 20 rows, so this window is empty for CHLT.

| Topic | V4 Qwen3-8B v4 | V5 Qwen2.5-7B v5 | V6 runtime fixes | Delta V6-V4 | Delta V6-V5 |
|---|---:|---:|---:|---:|---:|
| CH | 20/20 (100.00%) | 20/20 (100.00%) | 15/20 (75.00%) | -5 | -5 |
| CHLT | NA | NA | NA | NA | NA |
| DDT | 18/20 (90.00%) | 17/20 (85.00%) | 15/20 (75.00%) | -3 | -2 |
| DT | 8/20 (40.00%) | 9/20 (45.00%) | 11/20 (55.00%) | +3 | +2 |
| LD | 14/20 (70.00%) | 12/20 (60.00%) | 8/20 (40.00%) | -6 | -4 |
| NL | 17/20 (85.00%) | 16/20 (80.00%) | 16/20 (80.00%) | -1 | +0 |
| TD | 20/20 (100.00%) | 20/20 (100.00%) | 18/20 (90.00%) | -2 | -2 |
| THCB | 20/20 (100.00%) | 18/20 (90.00%) | 19/20 (95.00%) | -1 | +1 |

## V6 Misses

### CH
| ID | Gold | Prediction | Source | Strategy | Route | Target |
|---|---|---|---|---|---|---|
| CH050 | 110 W | 121 W | sandbox |  | ac_circuit | power |
| CH056 | 240 W | 480 W | sandbox |  | ac_circuit | power |
| CH057 | 500 W | 50 W | sandbox |  | ac_circuit | power |
| CH058 | 800 W | 3200 W | sandbox |  | ac_circuit | power |
| CH060 | 80 W | 160 W | sandbox |  | ac_circuit | power |

### DDT
| ID | Gold | Prediction | Source | Strategy | Route | Target |
|---|---|---|---|---|---|---|
| DDT214 | 20.00 V | 0 Wb | sandbox |  | magnetism_induction | emf |
| DDT216 | Increases in proportion to the square of the number of turns — | Increases by the square of the ratio | sandbox |  | general | inductance |
| DDT219 | the magnetic field energy increases proportionally to B² — | increases proportionally to the square of the increase | sandbox |  | magnetism_induction | energy |
| DDT220 | the current changes with time — | only when the magnetic flux through the coil changes | sandbox |  | magnetism_induction | emf |
| DDT330 | the circuit exhibits an inductive characteristic — | 20 Ω | sandbox |  | ac_circuit | unknown |

### DT
| ID | Gold | Prediction | Source | Strategy | Route | Target |
|---|---|---|---|---|---|---|
| DT061 | 16 V/m | 12 V/m | sandbox |  | coulomb_force | electric_field |
| DT072 | 3863925.47 N/C | 338665 V/m | sandbox |  | coulomb_force | electric_field |
| DT083 | 156154.35 V/m | 3.92e+06 V/m | sandbox |  | coulomb_force | electric_field |
| DT084 | 245.91 N/C | 2153.23 V/m | sandbox |  | coulomb_force | electric_field |
| DT087 | 2000 V/m | 8000 V/m | deterministic_solver | electric_field_point_charge | coulomb_force | electric_field |
| DT088 | 10^{-11} C | 10^{-6} C | sandbox |  | coulomb_force | charge |
| DT089 | 2.26.10^4 V/m | 100000 V/m | sandbox |  | coulomb_force | electric_field |
| DT091 | 100 V/m | 1000 V/m | sandbox |  | electric_field | electric_field |
| DT092 | 1.23 . 10^6 V/m | 8.55e+06 V/m | sandbox |  | coulomb_force | electric_field |

### LD
| ID | Gold | Prediction | Source | Strategy | Route | Target |
|---|---|---|---|---|---|---|
| LD041 | \sqrt{2} × F₀ N | 1.414 × F₀ N | sandbox |  | coulomb_force | force |
| LD043 | 0 N | 7.7957k\|ε×\|q\|²/a² N | sandbox |  | coulomb_force | force |
| LD044 | 9.45 N | 9 N | sandbox |  | coulomb_force | force |
| LD045 | 45 N | 0.033 N | llm |  | coulomb_force | force |
| LD047 | Hướng về phía q₂ - | Up | sandbox |  | coulomb_force | direction |
| LD049 | 14.34 N | 14 N | sandbox |  | coulomb_force | force |
| LD050 | 14.4 N | 1.8 N | deterministic_solver | ld_equidistant_two_source_force | coulomb_force | force |
| LD053 | 3.125 × 10^6 V/m | 6.81795e+06 V/m | deterministic_solver | dt_two_charge_field_vector | coulomb_force | electric_field |
| LD054 | 0.094 N | 1.4625 N | sandbox |  | coulomb_force | force |
| LD056 | 33.6 × 10^5 V/m | 0.16817 N | deterministic_solver | ld_two_source_force_vector | coulomb_force | force |
| LD057 | 0.17 N | 0.032 N | llm |  | coulomb_force | force |
| LD059 | 0 V/m | \frac{4 \sqrt{2} k \|q\|}{a^2} | sandbox |  | coulomb_force | electric_field |

### NL
| ID | Gold | Prediction | Source | Strategy | Route | Target |
|---|---|---|---|---|---|---|
| NL086 | 2.83 A | 0.0894427 A | deterministic_solver | nl_current_from_inductor_energy | energy_oscillation | unknown |
| NL091 | 25 % | 0.2 J | deterministic_solver | td_capacitor_energy | capacitor | energy |
| NL095 | all the energy is stored in the electric field of the capacitor. — | Capacitor; electric field energy; maximum capacitance energy | llm |  | energy_oscillation | energy |
| NL100 | maximum (WC = ½LI₀²) — | 0.5 ×W | sandbox |  | energy_oscillation | unknown |

### TD
| ID | Gold | Prediction | Source | Strategy | Route | Target |
|---|---|---|---|---|---|---|
| TD039 | 0.6 nC | 14.9973 nC | sandbox |  | capacitor | charge |
| TD051 | 0.93 nC | 93.226 nC | sandbox |  | capacitor | charge |

### THCB
| ID | Gold | Prediction | Source | Strategy | Route | Target |
|---|---|---|---|---|---|---|
| THCB100 | 0.8; 1.07 kg; % | 0.8 % | sandbox |  | measurement_error | percentage |

## Quick Read
- V6 improves DT in this slice versus V4/V5, but DT is still only 11/20.
- LD regresses badly in this slice: 8/20 versus V4 14/20 and V5 12/20. Most misses are geometry/vector or symbolic-equivalent evaluator cases.
- CH drops to 15/20 because RLC power cases are still being solved by sandbox with wrong RMS/peak or power formula choices.
- TD and THCB are near target; TD 18/20 and THCB 19/20. These are acceptable for a sample, but the two TD misses are charge scale/capacitance geometry cases.
- Qdrant preflight was connected in this run; runtime errors and blank predictions were zero.

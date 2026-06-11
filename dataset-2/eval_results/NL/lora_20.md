# Pipeline Evaluation Report

## Summary

| Metric | Value |
| --- | ---: |
| Total | 20 |
| Final accuracy | 6/20 (30.00%) |
| Exact full-string match | 2/20 (10.00%) |
| Numeric value match | 5/20 (25.00%) |
| Strict unit match | 18/20 (90.00%) |
| Physical equivalent match | 6/20 (30.00%) |
| Runtime errors | 0/20 (0.00%) |
| Average time per row | 49.14s |

## Results Table

| # | ID | Status | Gold | Prediction | Confidence | Time |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | NL001 | OK | 100.00 mJ | 100 mJ | 0.98 | 92.82s |
| 2 | NL002 | MISS | 90.00 mJ | 0.09 mJ | 0.98 | 46.98s |
| 3 | NL003 | MISS | 900.00 mJ | 0.9 mJ | 0.98 | 53.90s |
| 4 | NL004 | OK | 1000.00 mJ | 1 J | 0.98 | 38.38s |
| 5 | NL005 | MISS | 9.49 V | 9 V | 0.98 | 45.90s |
| 6 | NL006 | OK | 10.00 V | 10 V | 0.98 | 44.39s |
| 7 | NL007 | MISS | 0.11 A | 2 A | 0.98 | 39.47s |
| 8 | NL008 | MISS | 0.01 H | 0.1 H | 0.97 | 41.23s |
| 9 | NL009 | MISS | 0.10 μF | 1 μF | 0.98 | 61.14s |
| 10 | NL010 | OK | 0.0004 H | 0.0004 H | 0.97 | 45.42s |
| 11 | NL011 | MISS | 216.00 mJ | 180 mJ | 0.98 | 39.47s |
| 12 | NL012 | MISS | 0.40 μF | 10 μF | 0.98 | 42.25s |
| 13 | NL013 | MISS | 14.83 V | 6.32 V | 0.98 | 46.00s |
| 14 | NL014 | MISS | 1250.00 mJ | 0.5 J | 0.98 | 42.62s |
| 15 | NL015 | MISS | 0.09 A | 0.03 A | 0.98 | 48.58s |
| 16 | NL016 | MISS | 0.002 H | 0.01 H | 0.98 | 47.82s |
| 17 | NL017 | MISS | 17.32 V | 73.49 V | 0.98 | 46.98s |
| 18 | NL018 | MISS | 0.07 μF | 1 μF | 0.98 | 32.16s |
| 19 | NL019 | OK | 0.25 mH | 0.25 mH | 0.97 | 62.74s |
| 20 | NL020 | OK | 675.00 mJ | 675 mJ | 0.97 | 64.57s |

## Miss Details

### 1. MISS NL002

**Question:** A capacitor has a capacitance C = 50 μF, and the voltage across its plates is 60 V. Calculate the energy (mJ) stored in the electric field.

**Gold:** `90.00 mJ`

**Prediction:** `0.09 mJ`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Energy stored in capacitor, the computation yields a result of 0.09, in units of mJ.

**Retrieved Premises:**

- Energy stored in capacitor: W = 0.5 * C * U^2 = Q^2/(2*C) = Q*U/2 | Answer type: quantitative
- Capacitance of parallel-plate capacitor: C = epsilon_0 * epsilon * A / d | Answer type: quantitative
- Excerpt from TD_capacitor_rules (part 2): | Use: TD capacitance. For a parallel-plate capacitor C = epsilon0*epsilon_r*A/d. Convert area to m^2 and distance to m before computing. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify the given values from the question.
2. Step 2: Convert the capacitance C = 50 μF to SI units of Farads, which is 50 × 10⁻⁶ F.
3. Step 3: Recall the formula for energy stored in a capacitor: W = ½CU².
4. Step 4: Substitute the given values into the formula: W = ½(50 × 10⁻⁶ F)(60 V)².
5. Step 5: Calculate the square of the voltage (U²): (60 V)² = 3600 V².
6. Step 6: Perform the calculation step by step: W = 25 × 10⁻⁶ F × 3600 V² = 90000 × 10⁻⁶ J = 0.09 J.

### 2. MISS NL003

**Question:** An inductor has an inductance L = 0.2 H, and the current flowing through it is 3 A. Calculate the magnetic field energy (mJ) stored in the inductor.

**Gold:** `900.00 mJ`

**Prediction:** `0.9 mJ`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Inductance of solenoid, the computation yields a result of 0.9, in units of mJ.

**Retrieved Premises:**

- Inductance of solenoid: L = mu_0 * N^2 * A / l | Answer type: quantitative
- Excerpt from DDT_magnetism_induction (part 17): | Use: DDT unit traps. T for magnetic field, Wb for flux, H for inductance, V for induced EMF. Area in cm^2 must become m^2. | Note: Source: reference_docs/DDT_magnetism_induction.md | Answer type: reference
- Energy stored in inductor: W_L = 0.5 * L * I^2 | Answer type: quantitative

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify the given values from the question.
2. Step 2: The inductance of the inductor is L = 0.2 H and the current flowing through it is I = 3 A.
3. Step 3: Recall the formula for the energy stored in an inductor, which is W_L = 1/2 × L × I^2.
4. Step 4: Substitute the given values into the formula to calculate the magnetic field energy. The final calculated value of the magnetic field energy is approximately 0.9 J.

### 3. MISS NL005

**Question:** A capacitor has an electric field energy of 0.9 mJ, and its capacitance is C = 20 μF. Calculate the potential difference (unit: V) between its two plates (round the result to two decimal places).

**Gold:** `9.49 V`

**Prediction:** `9 V`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Capacitance of parallel-plate capacitor, the computation yields a result of 9, in units of V.

**Retrieved Premises:**

- Capacitance of parallel-plate capacitor: C = epsilon_0 * epsilon * A / d | Answer type: quantitative
- Excerpt from TD_capacitor_rules (part 2): | Use: TD capacitance. For a parallel-plate capacitor C = epsilon0*epsilon_r*A/d. Convert area to m^2 and distance to m before computing. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference
- Merging capacitors (unlike-sign plates together): U_final = |Q1 - Q2| / (C1 + C2) | Use: Charge difference divided by total capacitance | Answer type: quantitative

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify the given electric field energy W = 0.9 mJ and capacitance C = 20 μF.
2. Step 2: Convert the values to SI units: W = 0.9 × 10⁻³ J, C = 20 × 10⁻⁶ F.
3. Step 3: Recall the formula for energy stored in a capacitor: W = Q² / (2C).
4. Step 4: Rearrange the formula to solve for potential difference U: U = √(2WC) = 9 V

### 4. MISS NL007

**Question:** An inductor has a magnetic field energy of 1.8 mJ and an inductance (L) of 0.3 H. Calculate the current (unit: A, round the result to two decimal places).

**Gold:** `0.11 A`

**Prediction:** `2 A`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Inductance of solenoid, the computation yields a result of 2, in units of A.

**Retrieved Premises:**

- Inductance of solenoid: L = mu_0 * N^2 * A / l | Answer type: quantitative
- Excerpt from DDT_magnetism_induction (part 17): | Use: DDT unit traps. T for magnetic field, Wb for flux, H for inductance, V for induced EMF. Area in cm^2 must become m^2. | Note: Source: reference_docs/DDT_magnetism_induction.md | Answer type: reference
- Excerpt from NL_lc_energy_oscillation (part 4): | Use: NL maximum current. At maximum inductor current, all energy is magnetic: W_total = 0.5*L*I_max^2. | Note: Source: reference_docs/NL_lc_energy_oscillation.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify the given values from the question.
2. Step 2: Convert the total energy stored in the magnetic field from millijoules (mJ) to joules (J).
3. Step 3: Recall the formula for the maximum current (I_max) in an ideal inductor when all its energy is stored in the magnetic field.
4. Step 4: Substitute the converted values into the formula and calculate the square of the current.
5. Step 5: Take the positive square root to find the magnitude of the current.

### 5. MISS NL008

**Question:** An inductor has a magnetic field energy of 0.45 mJ, and the current through it is 0.3 A. Calculate the inductance (H).

**Gold:** `0.01 H`

**Prediction:** `0.1 H`

**Confidence:** `0.97`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Inductance of solenoid, the computation yields a result of 0.1, in units of H.

**Retrieved Premises:**

- Inductance of solenoid: L = mu_0 * N^2 * A / l | Answer type: quantitative
- Excerpt from DDT_magnetism_induction (part 17): | Use: DDT unit traps. T for magnetic field, Wb for flux, H for inductance, V for induced EMF. Area in cm^2 must become m^2. | Note: Source: reference_docs/DDT_magnetism_induction.md | Answer type: reference
- Excerpt from NL_lc_energy_oscillation (part 4): | Use: NL maximum current. At maximum inductor current, all energy is magnetic: W_total = 0.5*L*I_max^2. | Note: Source: reference_docs/NL_lc_energy_oscillation.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify the given values from the question.
2. Step 2: Convert the magnetic field energy to Joules.
3. Step 3: Recall the formula for the energy stored in an inductor, W = 0.5*L*I^2.
4. Step 4: Rearrange the formula to solve for inductance L: L = (2W) / I^2.
5. Step 5: Substitute the converted values into the rearranged formula and calculate the result.

### 6. MISS NL009

**Question:** A capacitor has a voltage of U = 200 V, and the stored electric field energy is 2 mJ. Calculate the capacitance (μF) of the capacitor.

**Gold:** `0.10 μF`

**Prediction:** `1 μF`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Energy stored in capacitor, the computation yields a result of 1, in units of μF.

**Retrieved Premises:**

- Energy stored in capacitor: W = 0.5 * C * U^2 = Q^2/(2*C) = Q*U/2 | Answer type: quantitative
- Capacitance of parallel-plate capacitor: C = epsilon_0 * epsilon * A / d | Answer type: quantitative
- Excerpt from TD_capacitor_rules (part 2): | Use: TD capacitance. For a parallel-plate capacitor C = epsilon0*epsilon_r*A/d. Convert area to m^2 and distance to m before computing. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify the given values from the question.
2. Step 2: The voltage U = 200 V and the stored electric field energy W = 2 mJ are provided.
3. Step 3: Convert the stored energy to SI units (Joules): W = 2 x 10^-3 J.
4. Step 4: Recall the formula for the energy stored in a capacitor, which is W = 0.5 × C × U^2.
5. Step 5: Rearrange the formula to solve for capacitance C: C = 2W / (U^2).
6. Step 6: Substitute the given values into the rearranged formula: C = 2 x (2 x 10^-3) / (200)^2.
7. Step 7: Calculate the denominator first: (200)^2 = 40000.
8. Step 8: Perform the division and multiplication: C = 4 x 10^-3 / 40000 = 1 x 10^-6 F.

### 7. MISS NL011

**Question:** A capacitor has a capacitance C = 30 μF and a voltage U = 120 V. Calculate the energy (mJ) stored in the electric field.

**Gold:** `216.00 mJ`

**Prediction:** `180 mJ`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Energy stored in capacitor, the computation yields a result of 180, in units of mJ.

**Retrieved Premises:**

- Energy stored in capacitor: W = 0.5 * C * U^2 = Q^2/(2*C) = Q*U/2 | Answer type: quantitative
- Capacitance of parallel-plate capacitor: C = epsilon_0 * epsilon * A / d | Answer type: quantitative
- Excerpt from TD_capacitor_rules (part 2): | Use: TD capacitance. For a parallel-plate capacitor C = epsilon0*epsilon_r*A/d. Convert area to m^2 and distance to m before computing. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify the given values from the question.
2. Step 2: Convert the capacitance to SI units so that it can be used directly in the formula.
3. Step 3: Recall the formula for energy stored in a capacitor, W = 0.5 × C × U^2.
4. Step 4: Substitute the converted capacitance and given voltage into the formula.

### 8. MISS NL012

**Question:** A capacitor is charged to U = 80 V, and the stored electrical energy is 1.28 mJ. Calculate the capacitance (μF) of the capacitor.

**Gold:** `0.40 μF`

**Prediction:** `10 μF`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Energy stored in capacitor, the computation yields a result of 10, in units of μF.

**Retrieved Premises:**

- Energy stored in capacitor: W = 0.5 * C * U^2 = Q^2/(2*C) = Q*U/2 | Answer type: quantitative
- Capacitance of parallel-plate capacitor: C = epsilon_0 * epsilon * A / d | Answer type: quantitative
- Excerpt from TD_capacitor_rules (part 2): | Use: TD capacitance. For a parallel-plate capacitor C = epsilon0*epsilon_r*A/d. Convert area to m^2 and distance to m before computing. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify given values from the question.
2. Step 2: Convert the total stored energy to SI units (Joules).
3. Step 3: Recall the formula for electrical energy stored in a capacitor, W = 0.5 × C × U^2.
4. Step 4: Rearrange the formula to solve for capacitance C: C = 2W / U^2.
5. Step 5: Substitute the given values into the rearranged formula and calculate the result.

### 9. MISS NL013

**Question:** A capacitor with a capacitance of 22 μF stores 2.42 mJ of energy. Calculate the potential difference U (V) between its plates (round the result to two decimal places).

**Gold:** `14.83 V`

**Prediction:** `6.32 V`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Capacitance of parallel-plate capacitor, the computation yields a result of 6.32, in units of V.

**Retrieved Premises:**

- Capacitance of parallel-plate capacitor: C = epsilon_0 * epsilon * A / d | Answer type: quantitative
- Energy stored in capacitor: W = 0.5 * C * U^2 = Q^2/(2*C) = Q*U/2 | Answer type: quantitative
- Excerpt from TD_capacitor_rules (part 2): | Use: TD capacitance. For a parallel-plate capacitor C = epsilon0*epsilon_r*A/d. Convert area to m^2 and distance to m before computing. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify C = 22 μF and W = 2.42 mJ.
2. Step 2: Convert units to SI: C = 22 × 10⁻⁶ F, W = 2.42 × 10⁻³ J.
3. Step 3: Recall the energy formula for a capacitor: W = ½CU².
4. Step 4: Rearrange the formula to solve for U: U = √(2W/C).
5. Step 5: Substitute the values into the formula: U = √((2 × (2.42 × 10⁻³)) / (22 × 10⁻⁶)).

### 10. MISS NL014

**Question:** An inductor has an inductance L = 0.4 H, and the current flowing through it is 2.5 A. Calculate the magnetic field energy (mJ).

**Gold:** `1250.00 mJ`

**Prediction:** `0.5 J`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=False, physical_equiv=False

**Explanation:**

Using Inductance of solenoid, the computation yields a result of 0.5, in units of J.

**Retrieved Premises:**

- Inductance of solenoid: L = mu_0 * N^2 * A / l | Answer type: quantitative
- Excerpt from DDT_magnetism_induction (part 17): | Use: DDT unit traps. T for magnetic field, Wb for flux, H for inductance, V for induced EMF. Area in cm^2 must become m^2. | Note: Source: reference_docs/DDT_magnetism_induction.md | Answer type: reference
- Excerpt from NL_lc_energy_oscillation (part 4): | Use: NL maximum current. At maximum inductor current, all energy is magnetic: W_total = 0.5*L*I_max^2. | Note: Source: reference_docs/NL_lc_energy_oscillation.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify the given values from the question.
2. Step 2: The inductance of the inductor is L = 0.4 H and the current flowing through it is I = 2.5 A.
3. Step 3: Recall the formula for magnetic field energy stored in an inductor, which is W = 1/2 × L × I^2.
4. Step 4: Substitute the given values into the formula to calculate the total magnetic field energy of the inductor.

### 11. MISS NL015

**Question:** An inductor has an inductance L = 0.12 H and stores 0.54 mJ of magnetic energy. Calculate the current (unit: A, round the result to two decimal places).

**Gold:** `0.09 A`

**Prediction:** `0.03 A`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Inductance of solenoid, the computation yields a result of 0.03, in units of A.

**Retrieved Premises:**

- Inductance of solenoid: L = mu_0 * N^2 * A / l | Answer type: quantitative
- Energy stored in inductor: W_L = 0.5 * L * I^2 | Answer type: quantitative
- Energy stored in inductor: W_L = 0.5 * L * I^2 | Answer type: quantitative

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify the given values from the question: Inductance L = 0.12 H and Magnetic Energy W_L = 0.54 mJ.
2. Step 2: Convert the magnetic energy to Joules (J): W_L = 0.54 × 10^-3 J.
3. Step 3: Recall the formula for the current in an inductor given its inductance L and stored magnetic energy W_L: I = √(2W_L / L).
4. Step 4: Substitute the values into the formula: I = √(2 × 0.54 × 10^-3 J) / 0.12 H.
5. Step 5: Calculate the square root and simplify: I = √(1.08 × 10^-3 A^2) / 0.12 A.
6. Step 6: Perform the division to find the current: I ≈ 0.0297 A.

### 12. MISS NL016

**Question:** An inductor has a current of 1.8 A and a magnetic field energy of 3.24 mJ. Calculate the inductance L (H).

**Gold:** `0.002 H`

**Prediction:** `0.01 H`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Inductance of solenoid, the computation yields a result of 0.01, in units of H.

**Retrieved Premises:**

- Inductance of solenoid: L = mu_0 * N^2 * A / l | Answer type: quantitative
- Excerpt from DDT_magnetism_induction (part 17): | Use: DDT unit traps. T for magnetic field, Wb for flux, H for inductance, V for induced EMF. Area in cm^2 must become m^2. | Note: Source: reference_docs/DDT_magnetism_induction.md | Answer type: reference
- Excerpt from NL_lc_energy_oscillation (part 4): | Use: NL maximum current. At maximum inductor current, all energy is magnetic: W_total = 0.5*L*I_max^2. | Note: Source: reference_docs/NL_lc_energy_oscillation.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify the given values from the question.
2. Step 2: The current I = 1.8 A and the magnetic field energy W = 3.24 mJ.
3. Step 3: Convert the magnetic field energy to Joules (W) using the conversion factor 1 J = 1000 mJ, so W = 3.24 × 10^-3 J.
4. Step 4: Recall the formula for the magnetic field energy stored in an inductor: W = ½ L I^2.
5. Step 5: Rearrange the formula to solve for the inductance L: L = (2W) / I^2 = 0.01 H.

### 13. MISS NL017

**Question:** A capacitor has a capacitance C = 12 μF and stores 1.8 mJ of energy. Calculate the voltage U (V) across it (round the result to two decimal places).

**Gold:** `17.32 V`

**Prediction:** `73.49 V`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Energy stored in capacitor, the computation yields a result of 73.49, in units of V.

**Retrieved Premises:**

- Energy stored in capacitor: W = 0.5 * C * U^2 = Q^2/(2*C) = Q*U/2 | Answer type: quantitative
- Capacitance of parallel-plate capacitor: C = epsilon_0 * epsilon * A / d | Answer type: quantitative
- Excerpt from TD_capacitor_rules (part 2): | Use: TD capacitance. For a parallel-plate capacitor C = epsilon0*epsilon_r*A/d. Convert area to m^2 and distance to m before computing. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify the given values from the question.
2. Step 2: Convert the capacitance and stored energy into SI units. C = 12 μF = 12 × 10⁻⁶ F, W = 1.8 mJ = 1.8 × 10⁻³ J
3. Step 3: Recall the formula for the energy stored in a capacitor: W = ½ C U².
4. Step 4: Rearrange the formula to solve for voltage (U): U = √(2W / C).
5. Step 5: Substitute the converted values into the rearranged formula and calculate the result. U = √(2 × 1.8 × 10⁻³ J) / (12 × 10⁻⁶ F) ≈ 73.49 V

### 14. MISS NL018

**Question:** A capacitor stores 0.75 mJ of energy when the voltage across it is 150 V. Calculate its capacitance (unit: μF, round the result to two decimal places).

**Gold:** `0.07 μF`

**Prediction:** `1 μF`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=True, physical_equiv=False

**Explanation:**

Using Energy stored in capacitor, the computation yields a result of 1, in units of μF.

**Retrieved Premises:**

- Energy stored in capacitor: W = 0.5 * C * U^2 = Q^2/(2*C) = Q*U/2 | Answer type: quantitative
- Capacitance of parallel-plate capacitor: C = epsilon_0 * epsilon * A / d | Answer type: quantitative
- Excerpt from TD_capacitor_rules (part 2): | Use: TD capacitance. For a parallel-plate capacitor C = epsilon0*epsilon_r*A/d. Convert area to m^2 and distance to m before computing. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: Identify the given values from the question.
2. Step 2: Convert the stored energy from millijoules (mJ) to joules (J).
3. Step 3: Recall the formula for the capacitance of a capacitor using its stored energy and voltage.
4. Step 4: Substitute the converted values into the formula.
5. Step 5: Calculate the capacitance C = 1.00 μF


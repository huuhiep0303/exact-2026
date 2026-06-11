# Pipeline Evaluation Report

## Summary

| Metric | Value |
| --- | ---: |
| Total | 5 |
| Final accuracy | 4/5 (80.00%) |
| Exact full-string match | 3/5 (60.00%) |
| Numeric value match | 3/5 (60.00%) |
| Strict unit match | 3/5 (60.00%) |
| Physical equivalent match | 4/5 (80.00%) |
| Runtime errors | 0/5 (0.00%) |
| Average time per row | 36.57s |

## Results Table

| # | ID | Status | Gold | Prediction | Confidence | Time |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | TD401 | OK | 0.045 J | 0.045 J | 0.98 | 48.91s |
| 2 | TD402 | OK | 100 μF | 0.0001 F | 0.98 | 30.30s |
| 3 | TD001 | OK | 150 V | 150 V | 0.99 | 40.99s |
| 4 | TD002 | OK | 300 V | 300 V | 0.99 | 26.85s |
| 5 | TD003 | MISS | 11.25 μJ | 2.25e-05 J | 0.99 | 35.80s |

## Details

### 1. OK TD401

**Question:** Calculate the energy stored in capacitor C when C = 100 μF and U = 30 V.

**Gold:** `0.045 J`

**Prediction:** `0.045 J`

**Confidence:** `0.98`

**Match Flags:** exact=True, numeric=True, unit=True, physical_equiv=True

**Explanation:**

Using Energy stored in inductor, the computation yields a result of 0.045, in units of J.

**Retrieved Premises:**

- Energy stored in inductor: W_L = 0.5 * L * I^2 | Answer type: quantitative
- Energy stored in capacitor: W_C = 0.5 * C * U^2 = Q^2 / (2*C) | Answer type: quantitative
- Energy stored in capacitor: W = 0.5 * C * U^2 = Q^2/(2*C) = Q*U/2 | Answer type: quantitative

**Predicted CoT / Reasoning Trace:**

1. Step 1: [FOL]: W_C = 0.5 * C * U^2 [CODE]: ```python import math # Given values (converted to SI) C = 100e-06 # Capacitance in Farads U = 30 # Voltage in Volts # Calculate energy stored in the capacitor W_C = 0.5 * C * U**2 answer = W_C unit = "J" ``` [ANSWER]: 1.5 J

### 2. OK TD402

**Question:** Calculate the capacitance C of the capacitor, given that it stores Q = 3 mC when fully charged under U = 30 V.

**Gold:** `100 μF`

**Prediction:** `0.0001 F`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=False, unit=False, physical_equiv=True

**Explanation:**

Using Capacitance of parallel-plate capacitor, the computation yields a result of 0.0001, in units of F.

**Retrieved Premises:**

- Capacitance of parallel-plate capacitor: C = epsilon_0 * epsilon * A / d | Answer type: quantitative
- Excerpt from DT_electric_potential_voltage (part 25): | Use: DT when a plate capacitor appears in a voltage question, decide whether it is uniform-field U=E*d or capacitance Q=C*U. | Note: Source: reference_docs/DT_electric_potential_voltage.md | Answer type: reference
- Excerpt from TD_capacitor_rules (part 2): | Use: TD capacitance. For a parallel-plate capacitor C = epsilon0*epsilon_r*A/d. Convert area to m^2 and distance to m before computing. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: [FOL]: C = Q / U [CODE]: ```python import math # Given values (converted to SI) Q = 3e-3 # mC converted to C U = 30 # V # Apply formula C = Q / U answer = C unit = "F" ``` [ANSWER]: 0.0001 F

### 3. OK TD001

**Question:** An air-filled parallel-plate capacitor has a capacitance C = 500 pF and is charged to a potential difference U = 300 V. It is then disconnected from the source and immersed in a liquid dielectric with dielectric constant ε = 2. What is the potential difference between the plates of the capacitor?

**Gold:** `150 V`

**Prediction:** `150 V`

**Confidence:** `0.99`

**Match Flags:** exact=True, numeric=True, unit=True, physical_equiv=True

**Explanation:**

Using Excerpt from TD_capacitor_rules (part 2), the computation yields a result of 150, in units of V.

**Retrieved Premises:**

- Excerpt from TD_capacitor_rules (part 2): | Use: TD capacitance. For a parallel-plate capacitor C = epsilon0*epsilon_r*A/d. Convert area to m^2 and distance to m before computing. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference
- Effect of dielectric (disconnected from source): Q = const, C_new = epsilon * C0, U_new = Q / C_new = U0 / epsilon, W_new = W0 / epsilon | Use: Disconnected: Q unchanged, U and W decrease | Answer type: quantitative
- Capacitance of parallel-plate capacitor: C = epsilon_0 * epsilon * A / d | Answer type: quantitative

**Predicted CoT / Reasoning Trace:**

1. Step 1: [FOL]: C_initial * U_initial = Q; C_new = epsilon * C_initial; U_new = Q / C_new; W_initial = 0.5 * C_initial * U_initial**2; W_final = W_initial / epsilon [CODE]: ```python import math # Given values (converted to SI) C_initial = 500e-12 # initial capacitance in F U_initial = 300 # initial potential difference in V epsilon = 2 # dielectric constant of the liquid # Since the capacitor is disconnected from the source, Q remains constant
2. Step 2: Q = C_initial * U_initial # New capacitance after inserting the dielectric C_new = epsilon * C_initial # New potential difference U_new = Q / C_new answer = U_new unit = "V" ``` [ANSWER]: 150.0 V

### 4. OK TD002

**Question:** An air-filled parallel plate capacitor has a capacitance C = 500 pF and is charged to a voltage U = 300 V. While still connected to the source, it is immersed in a liquid dielectric with a dielectric constant ε = 2. What will be the potential difference between the capacitor plates?

**Gold:** `300 V`

**Prediction:** `300 V`

**Confidence:** `0.99`

**Match Flags:** exact=True, numeric=True, unit=True, physical_equiv=True

**Explanation:**

Using Excerpt from TD_capacitor_rules (part 6), the computation yields a result of 300, in units of V.

**Retrieved Premises:**

- Excerpt from TD_capacitor_rules (part 6): | Use: TD connected capacitor. While connected to the voltage source, U remains constant. If C changes, Q = C*U and W = 0.5*C*U^2 change with C. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference
- Excerpt from TD_capacitor_rules (part 22): | Use: TD if the question says still connected, connected to source, or voltage maintained, treat it as U constant. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference
- Effect of dielectric (connected to source): U = const, C_new = epsilon * C0, Q_new = C_new * U, W_new = epsilon * W0 | Use: Connected: U unchanged, Q and W increase | Answer type: quantitative

**Predicted CoT / Reasoning Trace:**

1. Step 1: [FOL]: U_new = U_initial [CODE]: ```python import math # Given values (converted to SI) C_original = 500e-12 # F U_initial = 300 # V epsilon = 2 # Since the capacitor is still connected to the source, the voltage U remains constant
2. Step 2: U_new = U_initial answer = U_new unit = "V" ``` [ANSWER]: 300 V

### 5. MISS TD003

**Question:** An air-filled parallel plate capacitor with capacitance C = 500 pF is charged to a voltage U = 300 V. The capacitor is then disconnected from the source and immersed in a liquid dielectric with a relative permittivity (dielectric constant) of ε_r = 2. What is the electric field energy stored between the plates of the capacitor?

**Gold:** `11.25 μJ`

**Prediction:** `2.25e-05 J`

**Confidence:** `0.99`

**Match Flags:** exact=False, numeric=False, unit=False, physical_equiv=False

**Explanation:**

Using Excerpt from DT_electric_potential_voltage (part 9), the computation yields a result of 2.25e-05, in units of J.

**Retrieved Premises:**

- Excerpt from DT_electric_potential_voltage (part 9): | Use: DT uniform field. Between parallel plates, E = U/d. Convert d to m. Potential decreases in the direction of the electric field. | Note: Source: reference_docs/DT_electric_potential_voltage.md | Answer type: reference
- Excerpt from TD_capacitor_rules (part 17): | Use: TD electric field between plates. E = U/d. If U changes because the capacitor is disconnected, update U before computing E. | Note: Source: reference_docs/TD_capacitor_rules.md | Answer type: reference
- Excerpt from DT_electric_field_vector (part 4): | Use: DT field direction. A positive source charge creates an electric field pointing away from the charge. A negative source charge creates an electric field pointing toward the charge. | Note: Source: reference_docs/DT_electric_field_vector.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: [FOL]: E_field_energy = 0.5 * C * U^2 [CODE]: ```python import math # Given values (converted to SI) C = 500e-12 # Capacitance in Farads U = 300 # Voltage in Volts # Calculate the electric field energy stored between the plates of the capacitor E_field_energy = 0.5 * C * U**2 answer = E_field_energy unit = "J" ``` [ANSWER]: 7.5 J


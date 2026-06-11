# Pipeline Evaluation Report

## Summary

| Metric | Value |
| --- | ---: |
| Total | 5 |
| Final accuracy | 5/5 (100.00%) |
| Exact full-string match | 1/5 (20.00%) |
| Numeric value match | 5/5 (100.00%) |
| Strict unit match | 5/5 (100.00%) |
| Physical equivalent match | 5/5 (100.00%) |
| Runtime errors | 0/5 (0.00%) |
| Average time per row | 36.70s |

## Results Table

| # | ID | Status | Gold | Prediction | Confidence | Time |
| ---: | --- | --- | --- | --- | ---: | ---: |
| 1 | NL001 | OK | 100.00 mJ | 100 mJ | 0.98 | 47.74s |
| 2 | NL002 | OK | 90.00 mJ | 90 mJ | 0.98 | 39.61s |
| 3 | NL003 | OK | 900.00 mJ | 900 mJ | 0.99 | 35.05s |
| 4 | NL004 | OK | 1000.00 mJ | 1000 mJ | 0.98 | 24.20s |
| 5 | NL005 | OK | 9.49 V | 9.49 V | 0.98 | 36.92s |

## Details

### 1. OK NL001

**Question:** A capacitor with a capacitance of C = 20 μF is charged to 100 V. Calculate the energy (mJ) stored in the capacitor.

**Gold:** `100.00 mJ`

**Prediction:** `100 mJ`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=True, unit=True, physical_equiv=True

**Explanation:**

Using Energy stored in capacitor, the computation yields a result of 100, in units of mJ.

**Retrieved Premises:**

- Energy stored in capacitor: W_C = 0.5 * C * U^2 = Q^2 / (2*C) | Answer type: quantitative
- Excerpt from NL_lc_energy_oscillation (part 12): | Use: NL if capacitor energy is known at a moment, inductor energy is W_total - W_C. | Note: Source: reference_docs/NL_lc_energy_oscillation.md | Answer type: reference
- Excerpt from NL_lc_energy_oscillation (part 13): | Use: NL if inductor energy is known at a moment, capacitor energy is W_total - W_L. | Note: Source: reference_docs/NL_lc_energy_oscillation.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: [FOL]: W_C = 0.5 * C * U^2 [CODE]: ```python import math # Given values (converted to SI) C = 20e-6 # Capacitance in Farads U = 100 # Voltage in Volts # Calculate the energy stored in the capacitor W_C = 0.5 * C * U**2 # Convert the final answer to mJ answer = W_C / 1e-3 unit = "mJ" ``` [ANSWER]: 1000 mJ

### 2. OK NL002

**Question:** A capacitor has a capacitance C = 50 μF, and the voltage across its plates is 60 V. Calculate the energy (mJ) stored in the electric field.

**Gold:** `90.00 mJ`

**Prediction:** `90 mJ`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=True, unit=True, physical_equiv=True

**Explanation:**

Using Excerpt from DT_electric_field_vector (part 3), the computation yields a result of 90, in units of mJ.

**Retrieved Premises:**

- Excerpt from DT_electric_field_vector (part 3): | Use: DT electric field is a vector. Compute each source field magnitude, determine its direction, resolve into signed components, then sum components. Do not add scalar magnitudes unless the directions are proven to be the same. | Note: Source: reference_docs/DT_electric_field_vector.md | Answer type: reference
- Excerpt from DT_electric_field_vector (part 4): | Use: DT field direction. A positive source charge creates an electric field pointing away from the charge. A negative source charge creates an electric field pointing toward the charge. | Note: Source: reference_docs/DT_electric_field_vector.md | Answer type: reference
- Excerpt from LD_coulomb_force_field (part 7): | Use: LD force from electric field. After computing net field at a point, use F = q0*E for a charge placed there. If q0 is negative, the force direction is opposite the electric field direction. | Note: Source: reference_docs/LD_coulomb_force_field.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: [FOL]: The energy stored in an electric field can be calculated using the formula E = 1/2 * C * U^2, where C is capacitance and U is voltage
2. Step 2: [CODE]: ```python import math # Given values (converted to SI) C = 50e-06 # Capacitance in Farads U = 60 # Voltage in Volts # Apply formula E = 1/2 * C * U**2 # Energy stored in Joules answer = E / 1e-03 # Convert to mJ unit = "mJ" ``` [ANSWER]: 9.0 mJ

### 3. OK NL003

**Question:** An inductor has an inductance L = 0.2 H, and the current flowing through it is 3 A. Calculate the magnetic field energy (mJ) stored in the inductor.

**Gold:** `900.00 mJ`

**Prediction:** `900 mJ`

**Confidence:** `0.99`

**Match Flags:** exact=False, numeric=True, unit=True, physical_equiv=True

**Explanation:**

Using Energy stored in inductor, the computation yields a result of 900, in units of mJ.

**Retrieved Premises:**

- Energy stored in inductor: W_L = 0.5 * L * I^2 | Answer type: quantitative
- Excerpt from NL_lc_energy_oscillation (part 4): | Use: NL maximum current. At maximum inductor current, all energy is magnetic: W_total = 0.5*L*I_max^2. | Note: Source: reference_docs/NL_lc_energy_oscillation.md | Answer type: reference
- Energy stored in inductor: W_L = 0.5 * L * I^2 | Answer type: quantitative

**Predicted CoT / Reasoning Trace:**

1. Step 1: [FOL]: W_L = 0.5 * L * I^2 [CODE]: ```python import math # Given values (converted to SI) L = 0.2 # Henry I = 3 # Ampere # Apply formula for magnetic field energy stored in the inductor W_L = 0.5 * L * I**2 # Convert the final answer to mJ as required by the question answer = W_L / 1e-03 unit = "mJ" ``` [ANSWER]: 900.0 mJ

### 4. OK NL004

**Question:** An inductor has an inductance L = 0.5 H and carries a current of 2 A. Calculate the magnetic field energy (mJ).

**Gold:** `1000.00 mJ`

**Prediction:** `1000 mJ`

**Confidence:** `0.98`

**Match Flags:** exact=False, numeric=True, unit=True, physical_equiv=True

**Explanation:**

Using Excerpt from NL_lc_energy_oscillation (part 4), the computation yields a result of 1000, in units of mJ.

**Retrieved Premises:**

- Excerpt from NL_lc_energy_oscillation (part 4): | Use: NL maximum current. At maximum inductor current, all energy is magnetic: W_total = 0.5*L*I_max^2. | Note: Source: reference_docs/NL_lc_energy_oscillation.md | Answer type: reference
- Energy stored in inductor: W_L = 0.5 * L * I^2 | Answer type: quantitative
- Excerpt from NL_lc_energy_oscillation (part 12): | Use: NL if capacitor energy is known at a moment, inductor energy is W_total - W_C. | Note: Source: reference_docs/NL_lc_energy_oscillation.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: [FOL]: W_L = 0.5 * L * I^2 [CODE]: ```python import math # Given values (converted to SI) L = 0.5 # H I = 2 # A # Apply formula for magnetic field energy W_L = 0.5 * L * I**2 answer = W_L / 1e-03 # Convert from J to mJ unit = "mJ" ``` [ANSWER]: 400.0 mJ

### 5. OK NL005

**Question:** A capacitor has an electric field energy of 0.9 mJ, and its capacitance is C = 20 μF. Calculate the potential difference (unit: V) between its two plates (round the result to two decimal places).

**Gold:** `9.49 V`

**Prediction:** `9.49 V`

**Confidence:** `0.98`

**Match Flags:** exact=True, numeric=True, unit=True, physical_equiv=True

**Explanation:**

Using Excerpt from DT_electric_field_vector (part 3), the computation yields a result of 9.49, in units of V.

**Retrieved Premises:**

- Excerpt from DT_electric_field_vector (part 3): | Use: DT electric field is a vector. Compute each source field magnitude, determine its direction, resolve into signed components, then sum components. Do not add scalar magnitudes unless the directions are proven to be the same. | Note: Source: reference_docs/DT_electric_field_vector.md | Answer type: reference
- Excerpt from DT_electric_potential_voltage (part 9): | Use: DT uniform field. Between parallel plates, E = U/d. Convert d to m. Potential decreases in the direction of the electric field. | Note: Source: reference_docs/DT_electric_potential_voltage.md | Answer type: reference
- Excerpt from DT_electric_field_vector (part 4): | Use: DT field direction. A positive source charge creates an electric field pointing away from the charge. A negative source charge creates an electric field pointing toward the charge. | Note: Source: reference_docs/DT_electric_field_vector.md | Answer type: reference

**Predicted CoT / Reasoning Trace:**

1. Step 1: [FOL]: E_field_energy > 0.9 * mJ; capacitance > 20 * μF; find potential_difference in V [CODE]: ```python import math # Given values (converted to SI) E_field_energy = 0.9 * 1e-3 # Convert mJ to J C = 20 * 1e-6 # Convert μF to F # Apply formula: E_field_energy = 0.5 * C * U^2, solve for U (potential difference) U = math.sqrt(2 * E_field_energy / C) answer = round(U, 2) unit = "V" ``` [ANSWER]: 21.21 V


# Qwen3 8B LoRA v4 Full Official Evaluation

## Overall

| Metric | Value |
| --- | ---: |
| Total | 1352 |
| Final accuracy | 1062/1352 (78.55%) |
| Numeric match | 940/1352 (69.53%) |
| Unit match | 1171/1352 (86.61%) |
| Physical equivalent | 971/1352 (71.82%) |
| Runtime errors | 0/1352 |
| Blank predictions | 1/1352 |
| Router acceptable | 1153/1352 (85.28%) |

## By Topic

| Topic | Accuracy | Numeric | Unit | Physical | Errors | Router OK |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CH | 254/290 (87.59%) | 251/290 | 280/290 | 254/290 | 0 | 234/290 (80.69%) |
| CHLT | 20/20 (100.00%) | 0/20 | 20/20 | 0/20 | 0 | 17/20 (85.00%) |
| DDT | 116/130 (89.23%) | 83/130 | 95/130 | 91/130 | 0 | 110/130 (84.62%) |
| DT | 43/68 (63.24%) | 40/68 | 51/68 | 40/68 | 0 | 68/68 (100.00%) |
| LD | 246/397 (61.96%) | 244/397 | 385/397 | 244/397 | 0 | 396/397 (99.75%) |
| NL | 157/190 (82.63%) | 102/190 | 129/190 | 141/190 | 0 | 115/190 (60.53%) |
| TD | 149/177 (84.18%) | 145/177 | 154/177 | 149/177 | 0 | 134/177 (75.71%) |
| THCB | 77/80 (96.25%) | 75/80 | 57/80 | 52/80 | 0 | 79/80 (98.75%) |

## Router Distribution

- CH: ac_circuit: 217, electric_potential: 20, magnetism_induction: 18, general: 18, dc_circuit: 17
- CHLT: ac_circuit: 17, dc_circuit: 3
- DDT: magnetism_induction: 63, energy_oscillation: 25, ac_circuit: 22, dc_circuit: 7, electric_field: 7, capacitor: 3, general: 2, electric_potential: 1
- DT: coulomb_force: 53, electric_field_zero: 11, electric_field: 4
- LD: coulomb_force: 395, electric_field_zero: 1, general: 1
- NL: energy_oscillation: 113, electric_field: 74, capacitor: 1, electric_potential: 1, magnetism_induction: 1
- TD: capacitor: 113, electric_field: 41, energy_oscillation: 21, coulomb_force: 2
- THCB: measurement_error: 58, dc_circuit: 21, electric_potential: 1

## Miss Reason Buckets

- wrong_numeric: 202
- wrong_numeric_or_formula: 36
- router_mismatch: 35
- unit_only_or_unit_parse: 8
- qualitative_or_text_mismatch: 8
- blank_prediction: 1

## First Miss IDs By Topic

- CH (36): CH033, CH068, CH070, CH093, CH101, CH105, CH106, CH107, CH108, CH109, CH110, CH141, CH142, CH143, CH144, CH147, CH154, CH169, CH194, CH197, CH209, CH212, CH214, CH236, CH241, CH244, CH245, CH345, CH352, CH355, CH356, CH366, CH367, CH368, CH369, CH370
- CHLT (0): 
- DDT (14): DDT156, DDT214, DDT220, DDT338, DDT352, DDT353, DDT355, DDT356, DDT358, DDT359, DDT360, DDT376, DDT379, DDT394
- DT (25): DT049, DT052, DT053, DT054, DT055, DT056, DT058, DT059, DT060, DT073, DT074, DT075, DT081, DT082, DT083, DT084, DT085, DT090, DT091, DT092, DT093, DT095, DT097, DT098, DT100
- LD (151): LD016, LD021, LD039, LD047, LD050, LD053, LD054, LD056, LD057, LD061, LD062, LD063, LD065, LD066, LD067, LD068, LD069, LD071, LD074, LD076, LD080, LD081, LD082, LD083, LD085, LD086, LD087, LD090, LD091, LD096, LD098, LD099, LD100, LD103, LD119, LD122, LD123, LD124, LD129, LD133
- NL (33): NL021, NL086, NL091, NL100, NL127, NL303, NL307, NL308, NL310, NL315, NL316, NL324, NL327, NL329, NL335, NL346, NL348, NL350, NL358, NL361, NL366, NL373, NL376, NL378, NL379, NL380, NL383, NL384, NL386, NL387, NL393, NL397, NL399
- TD (28): TD092, TD095, TD096, TD099, TD364, TD367, TD369, TD371, TD373, TD374, TD376, TD377, TD380, TD381, TD385, TD386, TD387, TD388, TD389, TD390, TD391, TD392, TD393, TD395, TD396, TD397, TD398, TD400
- THCB (3): THCB083, THCB092, THCB128

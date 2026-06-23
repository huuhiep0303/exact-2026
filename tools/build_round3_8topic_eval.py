"""Build a compact Round 3 Type 2 evaluation set across all 8 physics topics.

The output intentionally mirrors the judge JSON shape used by
judge_topic2_modal.py, so it can be dry-run or sent to a deployed endpoint
without changing the judge.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "dataset-2" / "dataset_2" / "physic_version_2.csv"
DEFAULT_OUT_JSON = ROOT / "eval_cases" / "round3_8topic_representative_type2.json"
DEFAULT_OUT_MD = ROOT / "eval_cases" / "round3_8topic_representative_summary.md"

TOPIC_PREFIXES = ["CHLT", "THCB", "DDT", "LD", "CH", "NL", "TD", "DT"]
TOPIC_NAMES = {
    "LD": "coulomb_force",
    "CH": "ac_circuit",
    "NL": "energy_oscillation",
    "TD": "capacitor",
    "DDT": "magnetism_induction",
    "THCB": "measurement_error",
    "DT": "electric_potential",
    "CHLT": "ac_resonance",
}
MIN_CSV_CASES_PER_TOPIC = 20


@dataclass(frozen=True)
class Rule:
    label: str
    any_terms: tuple[str, ...]
    all_terms: tuple[str, ...] = ()
    limit: int = 2


def detect_prefix(sample_id: str) -> str:
    sample_id = (sample_id or "").upper()
    for prefix in TOPIC_PREFIXES:
        if sample_id.startswith(prefix):
            return prefix
    return "".join(ch for ch in sample_id if ch.isalpha()) or "UNK"


def normalize_text(text: str) -> str:
    return (
        (text or "")
        .replace("µ", "u")
        .replace("μ", "u")
        .replace("Î¼", "u")
        .replace("Ω", "ohm")
        .replace("Î©", "ohm")
        .replace("×", "x")
        .replace("Ã—", "x")
        .replace("−", "-")
        .replace("âˆ’", "-")
        .replace("–", "-")
        .replace("â€“", "-")
        .replace("—", "-")
        .replace("â€”", "-")
        .lower()
    )


def normalize_unit(unit: str) -> str:
    value = (unit or "").strip()
    value = (
        value.replace("µ", "u")
        .replace("μ", "u")
        .replace("Î¼", "u")
        .replace("Ω", "ohm")
        .replace("Î©", "ohm")
        .replace("—", "-")
        .replace("â€”", "-")
    )
    return value


REPRESENTATIVE_RULES: dict[str, list[Rule]] = {
    "TD": [
        Rule("charge_from_capacitance_voltage", ("calculate the charge", "what charge", "stored charge", "charge stored", "q ="), ("capacitance",)),
        Rule("capacitance_from_charge_voltage", ("calculate the capacitance", "what capacitance", "find the capacitance"), ("charge",)),
        Rule("capacitor_energy", ("energy", "stored"), ("capacitor",)),
        Rule("equivalent_capacitance_parallel", ("connected in parallel", "parallel combination", "equivalent capacitance"), ("parallel",)),
        Rule("equivalent_capacitance_series", ("connected in series", "series combination", "equivalent capacitance"), ("series",)),
        Rule("parallel_plate_capacitance", ("parallel plate", "parallel-plate"), ("area",)),
        Rule("dielectric_disconnected", ("disconnected",), ("dielectric",)),
        Rule("dielectric_connected", ("connected",), ("dielectric",)),
        Rule("voltage_from_charge_capacitance", ("potential difference", "voltage"), ("charge", "capacitance")),
        Rule("plate_distance_change", ("distance", "separation"), ("plate",)),
    ],
    "THCB": [
        Rule("absolute_error", ("absolute error",), ("error",)),
        Rule("relative_error", ("relative error",), ("error",)),
        Rule("least_count", ("least count",), ()),
        Rule("uncertainty", ("uncertainty", "+/-", "±"), ()),
        Rule("resistance_error", ("resistance", "r = u/i"), ("error",)),
        Rule("power_error", ("power", "p = ui"), ("error",)),
        Rule("maximum_value", ("maximum",), ()),
        Rule("minimum_value", ("minimum",), ()),
        Rule("voltage_measurement", ("voltage", "voltmeter"), ("error",)),
        Rule("current_measurement", ("current", "ammeter"), ("error",)),
    ],
    "DT": [
        Rule("single_charge_electric_field", ("point charge",), ("electric field",)),
        Rule("two_charge_electric_field", ("q1", "q2"), ("electric field",)),
        Rule("midpoint_field", ("midpoint",), ("electric field",)),
        Rule("zero_field", ("zero", "e = 0"), ("field",)),
        Rule("electric_potential", ("potential",), ("charge",)),
        Rule("ring_field", ("ring",), ("field",)),
        Rule("symbolic_field", ("sqrt", "frac", "abs"), ("field",)),
        Rule("force_from_field", ("force",), ("electric field",)),
        Rule("distance_on_field_line", ("distance",), ("field",)),
        Rule("voltage_difference", ("potential difference", "voltage"), ()),
    ],
    "LD": [
        Rule("direct_coulomb_force", ("coulomb", "force"), ("q1", "q2")),
        Rule("third_charge_force", ("q3", "third charge", "test charge"), ("force",)),
        Rule("resultant_force", ("resultant", "net force"), ("force",)),
        Rule("midpoint_force", ("midpoint",), ("force",)),
        Rule("equilateral_geometry", ("equilateral",), ("force",)),
        Rule("right_triangle_geometry", ("right-angled", "right triangle"), ("force",)),
        Rule("perpendicular_bisector", ("perpendicular bisector",), ("force",)),
        Rule("symbolic_force", ("sqrt", "frac"), ("force",)),
        Rule("inverse_charge", ("determine the charge", "find the charge"), ("force",)),
        Rule("field_strength", ("electric field", "field strength"), ()),
    ],
    "DDT": [
        Rule("solenoid_magnetic_field", ("solenoid",), ("magnetic field",)),
        Rule("solenoid_inductance", ("inductance",), ("solenoid",)),
        Rule("inductor_energy", ("energy",), ("inductance",)),
        Rule("turns_per_meter", ("turns per meter", "number of turns per meter"), ()),
        Rule("magnetic_flux", ("magnetic flux", "flux"), ()),
        Rule("faraday_emf", ("emf", "induced"), ()),
        Rule("transformer_voltage", ("transformer",), ("voltage",)),
        Rule("transformer_turns", ("transformer",), ("turns",)),
        Rule("power_factor", ("power factor", "cos"), ()),
        Rule("reactance", ("reactance",), ()),
    ],
    "CH": [
        Rule("resonant_frequency", ("resonant frequency",), ("capacitance", "inductance")),
        Rule("resonance_resistance", ("resonance",), ("impedance", "resistance")),
        Rule("impedance", ("impedance",), ("rlc",)),
        Rule("inductive_reactance", ("inductive reactance", "xl"), ()),
        Rule("capacitive_reactance", ("capacitive reactance", "xc"), ()),
        Rule("power_factor", ("power factor", "cos"), ()),
        Rule("power", ("power",), ("rlc",)),
        Rule("find_inductance", ("inductance", "determine l", "calculate l"), ("resonance",)),
        Rule("find_capacitance", ("capacitance", "determine c", "calculate c"), ("resonance",)),
        Rule("circuit_characteristic", ("inductive", "capacitive", "characteristic"), ()),
    ],
    "CHLT": [
        Rule("resonance_yes_no", ("resonance", "resonate"), ()),
        Rule("frequency_compare", ("frequency",), ("resonance",)),
    ],
    "NL": [
        Rule("capacitor_energy", ("capacitor",), ("energy",)),
        Rule("inductor_energy", ("inductor",), ("energy",)),
        Rule("lc_total_energy", ("lc",), ("energy",)),
        Rule("charge_amplitude", ("maximum charge", "charge amplitude", "qmax"), ()),
        Rule("current_amplitude", ("maximum current", "current amplitude", "imax"), ()),
        Rule("voltage_from_energy", ("voltage",), ("energy",)),
        Rule("frequency", ("frequency",), ("lc",)),
        Rule("period", ("period",), ("lc",)),
        Rule("oscillation", ("oscillation", "oscillating"), ()),
        Rule("energy_exchange", ("electric field", "magnetic field"), ("energy",)),
    ],
}


UNSEEN_VARIANTS: dict[str, list[dict[str, str]]] = {
    "TD": [
        {"label": "energy_reworded", "query": "A capacitor of 80 uF is charged to 25 V. How much energy is stored in it?", "answer": "0.025", "unit": "J"},
        {"label": "charge_reworded", "query": "A 47 nF capacitor has 12 V across its plates. Find the stored charge.", "answer": "564", "unit": "nC"},
        {"label": "capacitance_inverse", "query": "A capacitor stores 3 mC of charge when connected to a 60 V source. What is its capacitance?", "answer": "50", "unit": "uF"},
        {"label": "parallel_equivalent", "query": "Three capacitors of 4 uF, 6 uF, and 10 uF are connected in parallel. Find the equivalent capacitance.", "answer": "20", "unit": "uF"},
        {"label": "series_equivalent", "query": "Two capacitors of 6 uF and 12 uF are connected in series. What is the equivalent capacitance?", "answer": "4", "unit": "uF"},
        {"label": "parallel_plate", "query": "A parallel-plate capacitor has plate area 0.02 m^2 and separation 1 mm in air. Use epsilon0 = 8.85e-12 F/m. Find its capacitance.", "answer": "177", "unit": "pF"},
    ],
    "THCB": [
        {"label": "least_count_absolute", "query": "An ammeter has least count 0.02 A and reads 1.36 A. What absolute error should be assigned?", "answer": "0.02", "unit": "A"},
        {"label": "relative_voltage_error", "query": "A voltmeter reads 12.0 V with uncertainty 0.3 V. Calculate the relative error in percent.", "answer": "2.5", "unit": "%"},
        {"label": "resistance_error", "query": "Resistance is found from R = U/I. Given U = 10.0 +/- 0.2 V and I = 2.0 +/- 0.1 A, find the absolute error of R.", "answer": "0.35", "unit": "ohm"},
        {"label": "power_relative_error", "query": "Power is calculated by P = UI. If U = 120 +/- 3 V and I = 0.50 +/- 0.02 A, what is the relative error of P?", "answer": "6.5", "unit": "%"},
        {"label": "maximum_current", "query": "A measured current is 1.25 +/- 0.05 A. What is the maximum possible current?", "answer": "1.30", "unit": "A"},
    ],
    "DT": [
        {"label": "single_charge_field", "query": "A point charge q = +5 nC is in air. What is the electric field magnitude at a point 10 cm away? Use k = 9.0 x 10^9 N*m^2/C^2.", "answer": "4500", "unit": "N/C"},
        {"label": "two_charge_potential", "query": "Point P is 20 cm from q1 = +4 nC and 10 cm from q2 = -1 nC. Find the electric potential at P. Use k = 9.0 x 10^9.", "answer": "90", "unit": "V"},
        {"label": "opposite_charge_midpoint_field", "query": "Two charges +3 nC and -3 nC are 30 cm apart. Find the electric field magnitude at the midpoint. Use k = 9.0 x 10^9.", "answer": "2400", "unit": "N/C"},
        {"label": "zero_field_between_like_charges", "query": "Charges q1 = +4 nC and q2 = +9 nC are 10 cm apart. Where between them is the electric field zero, measured from q1?", "answer": "4", "unit": "cm"},
        {"label": "single_charge_potential", "query": "Find the electric potential 30 cm from a +6 nC point charge in air. Use k = 9.0 x 10^9.", "answer": "180", "unit": "V"},
    ],
    "LD": [
        {"label": "direct_coulomb_force", "query": "Two point charges q1 = 2 uC and q2 = 3 uC are separated by 30 cm in air. Find the magnitude of their Coulomb force. Use k = 9.0 x 10^9.", "answer": "0.6", "unit": "N"},
        {"label": "force_from_field", "query": "A test charge q0 = 2 nC is placed in a uniform electric field of 5000 N/C. What electric force acts on it?", "answer": "1e-5", "unit": "N"},
        {"label": "inverse_charge", "query": "Two charges are 20 cm apart and attract with force 0.09 N. If one charge is 1 uC, find the magnitude of the other charge. Use k = 9.0 x 10^9.", "answer": "0.4", "unit": "uC"},
        {"label": "equal_perpendicular_forces", "query": "Two perpendicular electric forces of 3 N and 4 N act on a charge. Find the magnitude of the resultant force.", "answer": "5", "unit": "N"},
        {"label": "midpoint_equal_like_field", "query": "Two equal positive point charges are placed symmetrically around a midpoint. What is the net electric field at the midpoint?", "answer": "0", "unit": "N/C"},
    ],
    "DDT": [
        {"label": "solenoid_field", "query": "A 0.5 m solenoid has 1000 turns and carries 2 A. Use mu0 = 4*pi*10^-7 T*m/A. Find the magnetic field inside.", "answer": "0.00503", "unit": "T"},
        {"label": "inductor_energy", "query": "An inductor of 0.4 H carries a current of 3 A. Find the magnetic energy stored.", "answer": "1.8", "unit": "J"},
        {"label": "transformer_voltage", "query": "An ideal transformer has 1100 primary turns and 100 secondary turns. If the primary voltage is 220 V, find the secondary voltage.", "answer": "20", "unit": "V"},
        {"label": "magnetic_flux", "query": "A uniform 0.2 T magnetic field passes normally through an area of 0.05 m^2. Find the magnetic flux.", "answer": "0.01", "unit": "Wb"},
        {"label": "solenoid_inductance", "query": "A solenoid has 500 turns, length 0.25 m, and cross-sectional area 4 cm^2. Use mu0 = 4*pi*10^-7. Find its inductance.", "answer": "0.503", "unit": "mH"},
    ],
    "CH": [
        {"label": "lc_natural_frequency", "query": "A series LC circuit contains a 200 mH inductor and a 50 uF capacitor. What is its natural oscillation frequency?", "answer": "50.3", "unit": "Hz"},
        {"label": "inductive_reactance", "query": "Find the inductive reactance of a 0.2 H inductor at frequency 50 Hz.", "answer": "62.8", "unit": "ohm"},
        {"label": "capacitive_reactance", "query": "Find the capacitive reactance of a 100 uF capacitor at frequency 50 Hz.", "answer": "31.8", "unit": "ohm"},
        {"label": "rlc_impedance", "query": "In a series RLC circuit, R = 30 ohm, XL = 80 ohm, and XC = 40 ohm. Find the impedance.", "answer": "50", "unit": "ohm"},
        {"label": "power_factor", "query": "An AC circuit has resistance 24 ohm and impedance 30 ohm. Calculate the power factor.", "answer": "0.8", "unit": "-"},
        {"label": "power_from_current", "query": "A series AC circuit has resistance 10 ohm and rms current 2 A. Find the average power dissipated in the resistor.", "answer": "40", "unit": "W"},
    ],
    "CHLT": [
        {"label": "resonance_yes", "query": "An RLC series circuit has L = 0.5 H and C = 20 uF. Does it resonate at 50.3 Hz?", "answer": "Yes", "unit": "-"},
        {"label": "resonance_no", "query": "An RLC series circuit has L = 0.5 H and C = 20 uF. Will resonance occur at 60 Hz?", "answer": "No", "unit": "-"},
        {"label": "resonance_yes_reworded", "query": "For an LC branch with L = 0.2 H and C = 50 uF, determine if the applied frequency 50.3 Hz is the resonant frequency.", "answer": "Yes", "unit": "-"},
        {"label": "resonance_no_low_frequency", "query": "A series circuit has L = 0.1 H and C = 10 uF. Is the circuit at resonance when f = 100 Hz?", "answer": "No", "unit": "-"},
        {"label": "resonance_no_high_frequency", "query": "Given R = 20 ohm, L = 0.4 H, and C = 25 uF, decide whether a 90 Hz source makes the series circuit resonant.", "answer": "No", "unit": "-"},
    ],
    "NL": [
        {"label": "capacitor_energy", "query": "A 100 uF capacitor is charged to 20 V. Find the electric field energy stored in the capacitor.", "answer": "0.02", "unit": "J"},
        {"label": "inductor_energy", "query": "An inductor with L = 0.2 H carries current 3 A. Calculate the magnetic energy stored.", "answer": "0.9", "unit": "J"},
        {"label": "lc_energy_from_qmax", "query": "In an LC circuit, the maximum charge on a 20 uF capacitor is 60 uC. Find the total electromagnetic energy.", "answer": "9e-5", "unit": "J"},
        {"label": "imax_from_energy", "query": "An LC oscillator has total energy 0.05 J and inductance 0.4 H. Find the maximum current.", "answer": "0.5", "unit": "A"},
        {"label": "lc_frequency", "query": "An LC oscillator has L = 0.1 H and C = 10 uF. Calculate its oscillation frequency.", "answer": "159", "unit": "Hz"},
    ],
}


def row_matches(row: dict[str, str], rule: Rule) -> bool:
    text = normalize_text(f"{row.get('question', '')} {row.get('answer', '')} {row.get('unit', '')}")
    return all(term in text for term in rule.all_terms) and any(term in text for term in rule.any_terms)


def is_judge_friendly(row: dict[str, str]) -> bool:
    """Prefer rows whose expected answer can be scored by the mini judge."""
    answer = normalize_text(row.get("answer", "")).strip()
    unit = normalize_unit(row.get("unit", "")).strip()
    question = normalize_text(row.get("question", ""))
    if not answer:
        return False
    if ";" in answer:
        return False
    if any(term in question for term in ["what happens", "how does", "where is the energy stored", "unit of"]):
        return False
    if answer in {"yes", "no"}:
        return True
    if unit and any(ch.isdigit() for ch in answer):
        return True
    if unit == "-" and any(ch.isdigit() for ch in answer):
        return True
    return False


def choose_representatives(rows: list[dict[str, str]], prefix: str) -> list[tuple[dict[str, str], str]]:
    if prefix == "CHLT":
        return [(row, "all_chlt_csv") for row in rows]

    preferred_rows = [row for row in rows if is_judge_friendly(row)]
    fallback_rows = rows if len(preferred_rows) < MIN_CSV_CASES_PER_TOPIC else preferred_rows
    selected: list[tuple[dict[str, str], str]] = []
    selected_ids: set[str] = set()

    for rule in REPRESENTATIVE_RULES[prefix]:
        added = 0
        for row in fallback_rows:
            sample_id = row.get("id", "")
            if sample_id in selected_ids:
                continue
            if row_matches(row, rule):
                selected.append((row, rule.label))
                selected_ids.add(sample_id)
                added += 1
                if added >= rule.limit:
                    break

    remaining = [row for row in fallback_rows if row.get("id", "") not in selected_ids]
    needed = max(0, MIN_CSV_CASES_PER_TOPIC - len(selected))
    if needed:
        # Fill from evenly spaced rows to avoid simply taking the first N samples.
        step = max(1, len(remaining) // needed)
        cursor = step // 2
        while len(selected) < MIN_CSV_CASES_PER_TOPIC and remaining:
            row = remaining[cursor % len(remaining)]
            sample_id = row.get("id", "")
            if sample_id not in selected_ids:
                selected.append((row, "coverage_fill"))
                selected_ids.add(sample_id)
            cursor += step
            if cursor > len(remaining) * 3:
                break
        for row in remaining:
            if len(selected) >= MIN_CSV_CASES_PER_TOPIC:
                break
            sample_id = row.get("id", "")
            if sample_id not in selected_ids:
                selected.append((row, "coverage_fill"))
                selected_ids.add(sample_id)

    return selected


def make_case(
    *,
    query_id: str,
    topic_prefix: str,
    case_group: str,
    query: str,
    answer: str,
    unit: str,
    source_id: str = "",
    selection_label: str = "",
) -> dict[str, Any]:
    unit = normalize_unit(unit)
    return {
        "query_id": query_id,
        "type": "type2",
        "topic_prefix": topic_prefix,
        "dataset_topic": TOPIC_NAMES[topic_prefix],
        "case_group": case_group,
        "source_id": source_id,
        "selection_label": selection_label,
        "request_payload": {
            "query_id": query_id,
            "type": "type2",
            "query": query,
            "premises": [],
            "options": [],
        },
        "expected": {
            "answer": str(answer).strip(),
            "unit": unit,
            "aliases": [],
        },
    }


def build_cases(dataset_path: Path) -> list[dict[str, Any]]:
    with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    by_prefix: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        prefix = detect_prefix(row.get("id", ""))
        if prefix in TOPIC_NAMES:
            by_prefix[prefix].append(row)

    cases: list[dict[str, Any]] = []
    for prefix in ["TD", "THCB", "DT", "LD", "DDT", "CH", "CHLT", "NL"]:
        representatives = choose_representatives(by_prefix[prefix], prefix)
        for index, (row, label) in enumerate(representatives, start=1):
            query_id = f"R3_{prefix}_{index:03d}"
            cases.append(
                make_case(
                    query_id=query_id,
                    topic_prefix=prefix,
                    case_group="csv_representative",
                    query=row.get("question", "").strip(),
                    answer=row.get("answer", "").strip(),
                    unit=row.get("unit", "").strip(),
                    source_id=row.get("id", "").strip(),
                    selection_label=label,
                )
            )

        for index, variant in enumerate(UNSEEN_VARIANTS[prefix], start=1):
            query_id = f"R3_{prefix}_UNSEEN_{index:03d}"
            cases.append(
                make_case(
                    query_id=query_id,
                    topic_prefix=prefix,
                    case_group="unseen_variant",
                    query=variant["query"],
                    answer=variant["answer"],
                    unit=variant["unit"],
                    selection_label=variant["label"],
                )
            )

    return cases


def write_summary(cases: list[dict[str, Any]], md_path: Path) -> None:
    by_topic = Counter(case["topic_prefix"] for case in cases)
    by_group = Counter(case["case_group"] for case in cases)
    label_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for case in cases:
        label_counts[case["topic_prefix"]][case.get("selection_label", "")] += 1

    lines = [
        "# Round 3 8-Topic Representative Type 2 Eval",
        "",
        f"- Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"- Total cases: {len(cases)}",
        f"- Case groups: {dict(sorted(by_group.items()))}",
        "",
        "## Counts by topic",
        "",
        "| Topic | Dataset topic | Total | CSV representative | Unseen variant |",
        "|---|---|---:|---:|---:|",
    ]
    for prefix in ["TD", "THCB", "DT", "LD", "DDT", "CH", "CHLT", "NL"]:
        csv_count = sum(1 for case in cases if case["topic_prefix"] == prefix and case["case_group"] == "csv_representative")
        unseen_count = sum(1 for case in cases if case["topic_prefix"] == prefix and case["case_group"] == "unseen_variant")
        lines.append(f"| {prefix} | {TOPIC_NAMES[prefix]} | {by_topic[prefix]} | {csv_count} | {unseen_count} |")

    lines.extend(["", "## Selection labels", ""])
    for prefix in ["TD", "THCB", "DT", "LD", "DDT", "CH", "CHLT", "NL"]:
        labels = ", ".join(f"{label}: {count}" for label, count in sorted(label_counts[prefix].items()))
        lines.append(f"- {prefix}: {labels}")

    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    cases = build_cases(DEFAULT_DATASET)
    payload = {
        "success": True,
        "sample_version": "round3_8topic_representative_type2_v1",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "total": len(cases),
            "topics": dict(Counter(case["topic_prefix"] for case in cases)),
            "case_groups": dict(Counter(case["case_group"] for case in cases)),
            "source_dataset": str(DEFAULT_DATASET.relative_to(ROOT)),
        },
        "logs": cases,
    }

    DEFAULT_OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_summary(cases, DEFAULT_OUT_MD)

    print(f"Wrote {len(cases)} cases to {DEFAULT_OUT_JSON}")
    print(f"Wrote summary to {DEFAULT_OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

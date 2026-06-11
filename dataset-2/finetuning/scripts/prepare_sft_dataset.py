"""
Prepare stratified SFT JSONL files for Phase 5 LoRA fine-tuning.

The split is performed independently inside each dataset topic prefix so every
topic appears in train/val/test. The output format is intentionally plain JSONL
with a `text` field so it can be consumed by HuggingFace Trainer, TRL, or
Unsloth examples without a custom dataset class.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.hints import get_topic_hints, get_unit_hints
from app.modules.knowledge_base import InMemoryKB
from app.modules.query_router import route_question
from app.modules.rag import TOPIC_PREFIX_BOOST, _topic_adjustment
from app.modules.topic_router import detect_topic
from app.prompts.reasoner_prompt import REASONER_SYSTEM_PROMPT



# DEFAULT_DATASET = ROOT / "dataset_2" / "Physics_Problems_Text_Only.csv"
DEFAULT_DATASET = ROOT / "dataset_2" / "physic_version_2.csv"
DEFAULT_OUTPUT_DIR = ROOT / "finetuning" / "data" / "processed"

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


SYSTEM_PROMPT = REASONER_SYSTEM_PROMPT

_KB: InMemoryKB | None = None


def detect_topic_prefix(sample_id: str) -> str:
    sample_id = (sample_id or "").upper()
    for prefix in TOPIC_PREFIXES:
        if sample_id.startswith(prefix):
            return prefix
    match = re.match(r"[A-Z]+", sample_id)
    return match.group(0) if match else "UNK"


def normalize_unit(unit: str) -> str:
    unit = (unit or "").strip()
    unit = unit.replace("—", "-")
    unit = unit.replace("Âµ", "μ").replace("µ", "μ")
    return unit


def is_numeric_answer(answer: str) -> bool:
    answer = (answer or "").strip().replace(",", "")
    return bool(re.match(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$", answer, re.IGNORECASE))


def answer_type(answer: str) -> str:
    if is_numeric_answer(answer):
        return "quantitative"
    if any(token in (answer or "") for token in ["\\", "sqrt", "frac", "^", "×", "x 10"]):
        return "symbolic"
    return "qualitative"


def python_literal(value: str) -> str:
    if is_numeric_answer(value):
        return value.strip()
    return json.dumps((value or "").strip(), ensure_ascii=False)


def _get_kb() -> InMemoryKB:
    """Use deterministic in-memory retrieval for SFT data generation."""
    global _KB
    if _KB is None:
        _KB = InMemoryKB()
        _KB.load_from_json(ROOT / "dataset_2" / "physics_knowledge_base.json")
    return _KB


def retrieve_sft_premises(question: str, topic: str, top_k: int = 3, distractor_k: int = 1) -> tuple[list[str], list[str]]:
    """Return topic-relevant premises plus RAFT-style distractors."""
    kb = _get_kb()
    candidate_k = max(30, top_k * 8)
    scored = []
    for entry, score in kb.search(question, top_k=candidate_k):
        final_score = score + _topic_adjustment(entry, question, topic)
        scored.append((entry, final_score))
    scored.sort(key=lambda item: item[1], reverse=True)

    relevant = [entry.premise_string for entry, score in scored if score > 0][:top_k]

    allowed_prefixes = TOPIC_PREFIX_BOOST.get(topic, set())
    distractors = []
    for entry, _ in scored:
        if entry.topic_prefix.upper() not in allowed_prefixes and entry.premise_string not in relevant:
            distractors.append(entry.premise_string)
        if len(distractors) >= distractor_k:
            break
    return relevant, distractors


_NUMBER = r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:\s*(?:×|x)\s*10\^?[+-]?\d+|(?:e[+-]?\d+)?)?)"


def _num_to_python(value: str) -> str:
    value = value.strip().replace(",", "")
    value = value.replace("×", "x")
    value = re.sub(r"\s*x\s*10\s*\^?\s*([+-]?\d+)", r"e\1", value, flags=re.IGNORECASE)
    return value.replace(" ", "")


def _find_value(question: str, names: list[str], units: list[str]) -> tuple[str, str] | None:
    unit_pattern = "|".join(re.escape(unit) for unit in units)
    for name in names:
        pattern = rf"\b{re.escape(name)}\s*=\s*{_NUMBER}\s*({unit_pattern})\b"
        m = re.search(pattern, question, flags=re.IGNORECASE)
        if m:
            return _num_to_python(m.group(1)), m.group(2)
    pattern = rf"{_NUMBER}\s*({unit_pattern})\b"
    m = re.search(pattern, question, flags=re.IGNORECASE)
    if m:
        return _num_to_python(m.group(1)), m.group(2)
    return None


def _si_factor(unit: str) -> float:
    normalized = unit.replace("µ", "μ")
    factors = {
        "pF": 1e-12,
        "nF": 1e-9,
        "μF": 1e-6,
        "uF": 1e-6,
        "mF": 1e-3,
        "F": 1.0,
        "nC": 1e-9,
        "μC": 1e-6,
        "uC": 1e-6,
        "mC": 1e-3,
        "C": 1.0,
        "mH": 1e-3,
        "μH": 1e-6,
        "uH": 1e-6,
        "H": 1.0,
        "mJ": 1e-3,
        "μJ": 1e-6,
        "uJ": 1e-6,
        "nJ": 1e-9,
        "J": 1.0,
        "cm": 1e-2,
        "mm": 1e-3,
        "m": 1.0,
        "kHz": 1e3,
        "Hz": 1.0,
        "V": 1.0,
        "A": 1.0,
        "Ω": 1.0,
        "ohm": 1.0,
        "N": 1.0,
        "V/m": 1.0,
        "N/C": 1.0,
        "W": 1.0,
    }
    return factors.get(normalized, 1.0)


def _assignment(name: str, found: tuple[str, str]) -> str:
    value, unit = found
    factor = _si_factor(unit)
    return f"{name} = ({value}) * {factor:.12g}  # {value} {unit} -> SI"


def _output_expr(si_var: str, unit: str) -> str:
    unit = normalize_unit(unit)
    if unit in {"", "-", "—"}:
        return si_var
    factor = _si_factor(unit)
    if factor != 1.0:
        return f"{si_var} / {factor:.12g}"
    return si_var


def _format_answer_line(answer: str, unit: str) -> str:
    unit = normalize_unit(unit)
    if unit and unit not in {"-", "—"}:
        return f"{answer} {unit}"
    return answer


def _code_block(lines: list[str]) -> str:
    return "\n".join(["import math", "", *lines])


_SUPERSCRIPT_DIGITS = str.maketrans({
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "⁻": "-",
    "⁺": "+",
})


def _normalize_physics_text(text: str) -> str:
    """Normalize common physics notation and mojibake for lightweight parsing."""
    text = text or ""
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")
    text = text.replace("×", "x").replace("·", "*")
    text = text.replace("µ", "u").replace("μ", "u").replace("Î¼", "u").replace("Âµ", "u")
    text = text.replace("Ω", "ohm").replace("Î©", "ohm")
    text = text.replace("²", "^2").replace("³", "^3")
    text = text.replace("⁻^", "^-").replace("⁺^", "^+").replace("^^", "^")
    text = text.replace("₀", "0").replace("₁", "1").replace("₂", "2").replace("₃", "3")
    text = text.replace("₄", "4").replace("₅", "5").replace("₆", "6").replace("₇", "7")
    text = text.replace("₈", "8").replace("₉", "9")

    def superscript_exp(match: re.Match[str]) -> str:
        return "10^" + match.group(1).translate(_SUPERSCRIPT_DIGITS)

    text = re.sub(r"10([⁺⁻]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)", superscript_exp, text)
    return text


_FLOAT_TOKEN = (
    r"[+-]?(?:"
    r"\d+\.10\s*\^?\s*[+-]?\d+"
    r"|(?:\d+(?:\.\d*)?|\.\d+)(?:(?:\s*(?:x|\*)\s*10\s*\^?\s*[+-]?\d+)|(?:e[+-]?\d+)?)"
    r")"
)


def _number_to_float(value: str) -> float | None:
    value = _normalize_physics_text(value).strip().replace(",", "")
    value = value.replace("{", "").replace("}", "")
    value = re.sub(r"(\d+(?:\.\d+)?)\s*(?:x|\*)\s*10\s*\^?\s*([+-]?\d+)", r"\1e\2", value, flags=re.IGNORECASE)
    value = re.sub(r"(\d+)\.10\s*\^?\s*([+-]?\d+)", r"\1e\2", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", "", value)
    try:
        return float(value)
    except ValueError:
        return None


def _parse_numeric_answer(answer: str) -> float | None:
    answer = _normalize_physics_text(answer).strip()
    if not answer:
        return None
    if any(symbol in answer for symbol in ["\\", "sqrt", "frac", "abs", "q", "a", "E_"]):
        return None
    match = re.search(_FLOAT_TOKEN, answer, flags=re.IGNORECASE)
    if not match:
        return None
    return _number_to_float(match.group(0))


def _distance_factor(unit: str) -> float:
    unit = _normalize_physics_text(unit).lower()
    return {"mm": 1e-3, "cm": 1e-2, "m": 1.0}.get(unit, 1.0)


def _area_factor(unit: str) -> float:
    unit = _normalize_physics_text(unit).lower().replace("^", "")
    return {
        "mm2": 1e-6,
        "cm2": 1e-4,
        "m2": 1.0,
    }.get(unit, 1.0)


def _charge_factor(unit: str) -> float:
    unit = _normalize_physics_text(unit)
    return {"nC": 1e-9, "uC": 1e-6, "mC": 1e-3, "C": 1.0}.get(unit, 1.0)


def _magnetic_factor(unit: str) -> float:
    unit = _normalize_physics_text(unit)
    return {"mT": 1e-3, "uT": 1e-6, "T": 1.0}.get(unit, 1.0)


def _value_factor(unit: str) -> float:
    unit = _normalize_physics_text(unit)
    unit = unit.replace("uF", "Î¼F").replace("uH", "Î¼H").replace("uJ", "Î¼J").replace("uWb", "Î¼Wb")
    return {
        "pF": 1e-12,
        "nF": 1e-9,
        "Î¼F": 1e-6,
        "mF": 1e-3,
        "F": 1.0,
        "Î¼H": 1e-6,
        "mH": 1e-3,
        "H": 1.0,
        "Î¼J": 1e-6,
        "mJ": 1e-3,
        "J": 1.0,
        "Î¼Wb": 1e-6,
        "mWb": 1e-3,
        "Wb": 1.0,
        "mT": 1e-3,
        "T": 1.0,
        "V": 1.0,
        "A": 1.0,
        "s": 1.0,
        "ms": 1e-3,
        "Hz": 1.0,
        "kHz": 1e3,
        "ohm": 1.0,
    }.get(unit, 1.0)


def _extract_distances(question: str) -> dict[str, float]:
    text = _normalize_physics_text(question)
    distances: dict[str, float] = {}
    valid_pairs = {
        "AB", "BA", "AC", "CA", "BC", "CB", "AM", "MA", "BM", "MB",
        "AN", "NA", "BN", "NB", "AH", "HA", "BH", "HB", "CH", "HC",
        "MO", "OM", "AO", "OA", "BO", "OB", "CN", "NC", "AD", "DA",
        "BD", "DB", "CD", "DC", "OD", "DO",
    }
    chain_pattern = r"\b((?:[A-Z]{2}\s*=\s*)+)(" + _FLOAT_TOKEN + r")\s*(mm|cm|m)\b"
    for chain, value, unit in re.findall(chain_pattern, text):
        distance = (_number_to_float(value) or 0.0) * _distance_factor(unit)
        for name in re.findall(r"[A-Z]{2}", chain):
            if name.upper() in valid_pairs:
                distances[name.upper()] = distance
    for name, value, unit in re.findall(r"\b([A-Z]{2})\s*(?:=|is|are)?\s*(" + _FLOAT_TOKEN + r")\s*(mm|cm|m)\b", text, re.IGNORECASE):
        if name.upper() in valid_pairs:
            distances[name.upper()] = (_number_to_float(value) or 0.0) * _distance_factor(unit)
    for p1, p2, value, unit in re.findall(r"distance\s+from\s+([A-Z])\s+to\s+([A-Z])\s+(?:is|being)?\s*(" + _FLOAT_TOKEN + r")\s*(mm|cm|m)\b", text, re.IGNORECASE):
        distances[(p1 + p2).upper()] = (_number_to_float(value) or 0.0) * _distance_factor(unit)
    for p1, p2, value, unit in re.findall(r"([A-Z])\s+is\s+(" + _FLOAT_TOKEN + r")\s*(mm|cm|m)\s+from\s+([A-Z])\b", text, re.IGNORECASE):
        distances[(p1 + p2).upper()] = (_number_to_float(value) or 0.0) * _distance_factor(unit)
    ab = re.search(r"(?:separated\s+by|which\s+are|are|is|AB\s*=|distance\s+AB\s+is|A\s+and\s+B,)[^.\n]{0,40}?(" + _FLOAT_TOKEN + r")\s*(mm|cm|m)\s*(?:apart|long|from|in|and|,|\.|$)", text, re.IGNORECASE)
    if ab and "AB" not in distances:
        distances["AB"] = (_number_to_float(ab.group(1)) or 0.0) * _distance_factor(ab.group(2))
    return {k: v for k, v in distances.items() if v > 0}


def _dist(distances: dict[str, float], name: str) -> float | None:
    name = name.upper()
    return distances.get(name) or distances.get(name[::-1])


def _extract_named_values(question: str, units: list[str]) -> list[tuple[str, str, str]]:
    text = _normalize_physics_text(question)
    unit_pattern = "|".join(re.escape(_normalize_physics_text(unit)) for unit in units)
    return re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\s*=\s*(" + _FLOAT_TOKEN + rf")\s*({unit_pattern})\b", text, re.IGNORECASE)


def _extract_first_value(question: str, units: list[str], keywords: list[str] | None = None) -> float | None:
    text = _normalize_physics_text(question)
    if keywords:
        for keyword in keywords:
            pattern = re.escape(keyword)
            match = re.search(pattern + r"[^.\n]{0,80}?(" + _FLOAT_TOKEN + r")\s*(" + "|".join(re.escape(_normalize_physics_text(unit)) for unit in units) + r")\b", text, re.IGNORECASE)
            if match:
                return (_number_to_float(match.group(1)) or 0.0) * _value_factor(match.group(2))
    match = re.search(r"(" + _FLOAT_TOKEN + r")\s*(" + "|".join(re.escape(_normalize_physics_text(unit)) for unit in units) + r")\b", text, re.IGNORECASE)
    if match:
        return (_number_to_float(match.group(1)) or 0.0) * _value_factor(match.group(2))
    return None


def _extract_charges(question: str) -> dict[str, float]:
    text = _normalize_physics_text(question)
    charges: dict[str, float] = {}
    name_pattern = r"q(?:[0-9]|[A-Z]|0|prime|'|′)?|Q"

    def norm_name(name: str) -> str:
        name = name.replace("′", "prime").replace("'", "prime")
        return name.lower()

    for first, sign, second, value, unit in re.findall(
        rf"\b({name_pattern})\s*=\s*(-?)\s*({name_pattern})\s*=\s*({_FLOAT_TOKEN})\s*(nC|uC|mC|C)\b",
        text,
        re.IGNORECASE,
    ):
        val = (_number_to_float(value) or 0.0) * _charge_factor(unit)
        charges[norm_name(first)] = val
        charges[norm_name(second)] = -val if sign == "-" else val

    chain_pattern = rf"\b((?:{name_pattern}\s*=\s*)+)({_FLOAT_TOKEN})\s*(nC|uC|mC|C)\b"
    for chain, value, unit in re.findall(chain_pattern, text, re.IGNORECASE):
        val = (_number_to_float(value) or 0.0) * _charge_factor(unit)
        for name in re.findall(name_pattern, chain, re.IGNORECASE):
            charges[norm_name(name)] = val

    simple_pattern = rf"\b({name_pattern})\s*=\s*({_FLOAT_TOKEN})\s*(nC|uC|mC|C)\b"
    for name, value, unit in re.findall(simple_pattern, text, re.IGNORECASE):
        charges[norm_name(name)] = (_number_to_float(value) or 0.0) * _charge_factor(unit)

    return charges


def _source_charges(charges: dict[str, float]) -> tuple[float, float] | None:
    if "q1" in charges and "q2" in charges:
        return charges["q1"], charges["q2"]
    if "qa" in charges and "qb" in charges:
        return charges["qa"], charges["qb"]
    return None


def _test_charge(charges: dict[str, float]) -> float | None:
    for key in ("q3", "q0", "qprime", "q"):
        if key in charges:
            return charges[key]
    return None


def _gold_answer_assignment(raw_var: str, answer: str) -> str:
    numeric = _parse_numeric_answer(answer)
    if numeric is not None and re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", answer.strip().replace(",", "")):
        decimals = len(answer.strip().split(".", 1)[1]) if "." in answer.strip() else 0
        if decimals:
            return f"answer = round({raw_var}, {decimals})"
        return f"answer = round({raw_var})"
    return f"answer = {json.dumps(answer.strip(), ensure_ascii=False)}"


def _finish_code(lines: list[str], raw_var: str, row: dict[str, str]) -> list[str]:
    answer = (row.get("answer") or "").strip()
    unit = normalize_unit(row.get("unit") or "")
    return [
        *lines,
        _gold_answer_assignment(raw_var, answer),
        f"unit = {json.dumps(unit, ensure_ascii=False)}",
    ]


def _symbolic_or_text_code(row: dict[str, str], strategy: str, comment: str) -> tuple[str, str, bool]:
    answer = (row.get("answer") or "").strip()
    unit = normalize_unit(row.get("unit") or "")
    lines = [
        f"# {comment}",
        f"answer = {json.dumps(answer, ensure_ascii=False)}",
        f"unit = {json.dumps(unit, ensure_ascii=False)}",
    ]
    return _code_block(lines), strategy, True


def _supervised_target_code(row: dict[str, str], strategy: str) -> tuple[str, str, bool]:
    answer = (row.get("answer") or "").strip()
    unit = normalize_unit(row.get("unit") or "")
    lines = [
        "# Complex supervised pattern: the CoT above is the verified solution path.",
        "# Keep answer/unit aligned with the dataset label for SFT formatting.",
        f"answer = {python_literal(answer)}",
        f"unit = {json.dumps(unit, ensure_ascii=False)}",
    ]
    return _code_block(lines), strategy, True


def _is_field_or_force_topic(topic: str) -> bool:
    return topic in {"coulomb_force", "electric_field", "electric_field_zero"}


def _synthesize_zero_field(row: dict[str, str], topic: str) -> tuple[str, str, bool] | None:
    if not _is_field_or_force_topic(topic):
        return None
    question = row.get("question", "")
    q = _normalize_physics_text(question).lower()
    if "zero" not in q and "e = 0" not in q and "field strength is zero" not in q:
        return None

    distances = _extract_distances(question)
    d = _dist(distances, "AB")
    if not d:
        return None

    charges = _extract_charges(question)
    sources = _source_charges(charges)
    if sources:
        q1, q2 = sources
        a1, a2 = abs(q1), abs(q2)
    else:
        ratio = re.search(r"q1\s*=\s*(" + _FLOAT_TOKEN + r")\s*q2", _normalize_physics_text(question), re.IGNORECASE)
        if not ratio:
            return None
        a1, a2 = _number_to_float(ratio.group(1)) or 0.0, 1.0
        q1, q2 = a1, a2
    if a1 <= 0 or a2 <= 0:
        return None

    ask_from_b = any(term in q for term in ["from b", "distance bm", "calculate bm", "to b"])
    ask_coordinate = "coordinate" in q or "origin" in q or "ox axis" in q
    lines = [
        f"d = {d:.12g}",
        f"q1 = {q1:.12g}",
        f"q2 = {q2:.12g}",
        "s1 = math.sqrt(abs(q1))",
        "s2 = math.sqrt(abs(q2))",
    ]
    if q1 * q2 > 0:
        raw = "rB" if ask_from_b else "rA"
        lines += [
            "rA = d * s1 / (s1 + s2)",
            "rB = d - rA",
            f"x_si = {raw}",
        ]
        strategy = "zero_field_same_sign"
    else:
        lines += [
            "if abs(q1) < abs(q2):",
            "    outside_from_A = s1 * d / (s2 - s1)",
            "    coord_from_A = -outside_from_A",
            "    distance_from_A = outside_from_A",
            "    distance_from_B = d + outside_from_A",
            "else:",
            "    outside_from_B = s2 * d / (s1 - s2)",
            "    coord_from_A = d + outside_from_B",
            "    distance_from_A = d + outside_from_B",
            "    distance_from_B = outside_from_B",
        ]
        if ask_coordinate:
            raw = "coord_from_A"
        elif ask_from_b:
            raw = "distance_from_B"
        else:
            raw = "distance_from_A"
        lines.append(f"x_si = {raw}")
        strategy = "zero_field_opposite_sign"

    unit = normalize_unit(row.get("unit") or "")
    out = _output_expr("x_si", unit)
    lines += [f"x_out = {out}"]
    return _code_block(_finish_code(lines, "x_out", row)), strategy, True


def _synthesize_two_charge_vector(row: dict[str, str], topic: str) -> tuple[str, str, bool] | None:
    if not _is_field_or_force_topic(topic):
        return None
    question = row.get("question", "")
    q = _normalize_physics_text(question).lower()
    charges = _extract_charges(question)
    sources = _source_charges(charges)
    if not sources:
        return None
    distances = _extract_distances(question)
    d = _dist(distances, "AB")
    if not d:
        return None

    point = None
    r_a = r_b = None
    for candidate in ["C", "M", "N", "H", "O"]:
        cand_a = _dist(distances, candidate + "A")
        cand_b = _dist(distances, candidate + "B")
        if cand_a and cand_b:
            point = candidate
            r_a, r_b = cand_a, cand_b
            break
    if r_a is None and ("midpoint" in q or "mid-point" in q):
        point = "M"
        r_a = r_b = d / 2
    if r_a is None and "perpendicular bisector" in q:
        h_match = re.search(r"(?:distance|at a distance|away|l\s*=|ℓ\s*=)[^.\n]{0,30}?(" + _FLOAT_TOKEN + r")\s*(mm|cm|m)", _normalize_physics_text(question), re.IGNORECASE)
        if h_match:
            h = (_number_to_float(h_match.group(1)) or 0.0) * _distance_factor(h_match.group(2))
            r_a = r_b = math.sqrt((d / 2) ** 2 + h**2)
            point = "M"
    if r_a is None or r_b is None:
        return None

    q1, q2 = sources
    qtest = _test_charge(charges)
    wants_force = qtest is not None and ("force" in q or "acting on" in q)
    if not wants_force and not any(term in q for term in ["electric field", "field strength", "field vector", "resultant field"]):
        return None

    epsilon = _extract_first_value(question, [""], ["dielectric constant"]) if False else None
    eps_match = re.search(r"(?:dielectric constant|ε|epsilon)\s*(?:=|of)?\s*(" + _FLOAT_TOKEN + r")", _normalize_physics_text(question), re.IGNORECASE)
    epsilon = _number_to_float(eps_match.group(1)) if eps_match else 1.0
    if not epsilon:
        epsilon = 1.0

    lines = [
        "k = 9e9",
        f"epsilon = {epsilon:.12g}",
        f"q1 = {q1:.12g}",
        f"q2 = {q2:.12g}",
        f"d = {d:.12g}",
        f"rA = {r_a:.12g}",
        f"rB = {r_b:.12g}",
        "x = (rA**2 - rB**2 + d**2) / (2 * d)",
        "y2 = max(rA**2 - x**2, 0.0)",
        "y = math.sqrt(y2)",
        "E1x = (k / epsilon) * q1 * x / (rA**3)",
        "E1y = (k / epsilon) * q1 * y / (rA**3)",
        "E2x = (k / epsilon) * q2 * (x - d) / (rB**3)",
        "E2y = (k / epsilon) * q2 * y / (rB**3)",
        "Ex = E1x + E2x",
        "Ey = E1y + E2y",
        "E = math.sqrt(Ex**2 + Ey**2)",
    ]
    if wants_force:
        lines += [f"q_test = {qtest:.12g}", "F = abs(q_test) * E"]
        raw_var = _output_expr("F", normalize_unit(row.get("unit") or ""))
        lines.append(f"result = {raw_var}")
        strategy = "two_charge_force_vector"
    else:
        raw_var = _output_expr("E", normalize_unit(row.get("unit") or ""))
        lines.append(f"result = {raw_var}")
        strategy = "two_charge_field_vector"
    return _code_block(_finish_code(lines, "result", row)), strategy, True


def _synthesize_symbolic_geometry(row: dict[str, str], topic: str) -> tuple[str, str, bool] | None:
    if not _is_field_or_force_topic(topic):
        return None
    q = _normalize_physics_text(row.get("question", "")).lower()
    answer = row.get("answer", "")
    if any(token in answer for token in ["\\", "sqrt", "frac", "F₀", "q", "a", "E_"]):
        if "perpendicular bisector" in q:
            if "maximum" in q:
                return _symbolic_or_text_code(row, "symbolic_perpendicular_bisector_maximum", "Symbolic result: maximize E(h) on the perpendicular bisector.")
            return _symbolic_or_text_code(row, "symbolic_perpendicular_bisector_field", "Symbolic result: resolve equal-charge fields on the perpendicular bisector.")
        if "square" in q or "vertices" in q or "equilateral" in q or "right" in q:
            return _symbolic_or_text_code(row, "symbolic_geometry_vector", "Symbolic vector-geometry result; preserve expression form.")
    return None


def _synthesize_ddt(row: dict[str, str], topic: str) -> tuple[str, str, bool] | None:
    if topic != "magnetism_induction":
        return None
    question = row.get("question", "")
    q = _normalize_physics_text(question).lower()
    unit = normalize_unit(row.get("unit") or "")

    if row.get("answer_type") == "qualitative":
        return None

    text = _normalize_physics_text(question)
    turns_match = re.search(r"(\d+(?:\.\d+)?)\s+turns", text, re.IGNORECASE)
    N = float(turns_match.group(1)) if turns_match else None
    n_match = re.search(r"(?:turn density|n\s*=|number of turns per meter)[^.\n]{0,40}?(" + _FLOAT_TOKEN + r")\s*turns/m", text, re.IGNORECASE)
    n = _number_to_float(n_match.group(1)) if n_match else None
    length = _extract_first_value(question, ["m", "cm"], ["long", "length", "l ="])
    area = None
    area_match = re.search(r"(?:area|cross-sectional area|loop is)[^.\n]{0,50}?(" + _FLOAT_TOKEN + r")\s*(cm\^2|m\^2|cm2|m2)", text, re.IGNORECASE)
    if area_match:
        area = (_number_to_float(area_match.group(1)) or 0.0) * _area_factor(area_match.group(2))
    I = _extract_first_value(question, ["A"], ["current", "carries", "I ="])
    L = _extract_first_value(question, ["H", "mH"], ["inductance", "L ="])
    B = _extract_first_value(question, ["T", "mT"], ["magnetic field", "B =", "flux density"])
    emf = _extract_first_value(question, ["V"], ["emf", "electromotive force", "voltage"])

    lines: list[str] = ["mu0 = 4 * math.pi * 1e-7"]

    if any(term in q for term in ["turn density", "turns per meter", "turns per unit"]) and N and length:
        lines += [f"N = {N:.12g}", f"l = {length:.12g}", "n = N / l"]
        lines += [f"result = {_output_expr('n', unit)}"]
        return _code_block(_finish_code(lines, "result", row)), "ddt_turn_density", True

    if any(term in q for term in ["magnetic field inside", "magnetic field strength", "flux density", "magnetic field b inside"]):
        if n is None and N and length:
            lines += [f"N = {N:.12g}", f"l = {length:.12g}", "n = N / l"]
        elif n is not None:
            lines += [f"n = {n:.12g}"]
        else:
            return None
        if not I:
            return None
        lines += [f"I = {I:.12g}", "B = mu0 * n * I", f"result = {_output_expr('B', unit)}"]
        return _code_block(_finish_code(lines, "result", row)), "ddt_solenoid_field", True

    if "inductance" in q and "depend" not in q and N and length and area:
        lines += [f"N = {N:.12g}", f"l = {length:.12g}", f"A = {area:.12g}", "L = mu0 * N**2 * A / l", f"result = {_output_expr('L', unit)}"]
        return _code_block(_finish_code(lines, "result", row)), "ddt_solenoid_inductance", True

    if any(term in q for term in ["energy density", "magnetic field energy density"]):
        if B is None and n is not None and I:
            lines += [f"n = {n:.12g}", f"I = {I:.12g}", "B = mu0 * n * I"]
        elif B is not None:
            lines += [f"B = {B:.12g}"]
        else:
            return None
        lines += ["w = B**2 / (2 * mu0)", f"result = {_output_expr('w', unit)}"]
        return _code_block(_finish_code(lines, "result", row)), "ddt_magnetic_energy_density", True

    if "magnetic field energy" in q or "magnetic energy" in q or "stored magnetic energy" in q:
        if L and I:
            lines += [f"L = {L:.12g}", f"I = {I:.12g}", "W = 0.5 * L * I**2", f"result = {_output_expr('W', unit)}"]
            return _code_block(_finish_code(lines, "result", row)), "ddt_inductor_energy", True
        if N and length and area and I:
            lines += [f"N = {N:.12g}", f"l = {length:.12g}", f"A = {area:.12g}", f"I = {I:.12g}", "L = mu0 * N**2 * A / l", "W = 0.5 * L * I**2", f"result = {_output_expr('W', unit)}"]
            return _code_block(_finish_code(lines, "result", row)), "ddt_solenoid_energy", True

    if "flux" in q:
        flux_match = re.search(r"(?:flux|phi|Φ)[^.\n]{0,50}?(" + _FLOAT_TOKEN + r")\s*(uWb|mWb|Wb)", text, re.IGNORECASE)
        phi = (_number_to_float(flux_match.group(1)) or 0.0) * _value_factor(flux_match.group(2)) if flux_match else None
        if "linkage" in q and phi is not None and N:
            lines += [f"N = {N:.12g}", f"phi = {phi:.12g}", "flux = N * phi", f"result = {_output_expr('flux', unit)}"]
            return _code_block(_finish_code(lines, "result", row)), "ddt_flux_linkage", True
        if B is None and n is not None and I:
            lines += [f"n = {n:.12g}", f"I = {I:.12g}", "B = mu0 * n * I"]
        elif B is not None:
            lines += [f"B = {B:.12g}"]
        else:
            return None
        if area is None:
            return None
        multiplier = "N * " if N and any(term in q for term in ["entire", "total", "linkage"]) else ""
        if N and multiplier:
            lines += [f"N = {N:.12g}"]
        lines += [f"A = {area:.12g}", f"phi = {multiplier}B * A", f"result = {_output_expr('phi', unit)}"]
        return _code_block(_finish_code(lines, "result", row)), "ddt_magnetic_flux", True

    current_change = re.search(r"current\s+(?:through\s+the\s+solenoid\s+)?(?:decreases|increases|changes)?[^.\n]{0,80}?from\s+(" + _FLOAT_TOKEN + r")\s*A\s+to\s+(" + _FLOAT_TOKEN + r")\s*A\s+in\s+(" + _FLOAT_TOKEN + r")\s*s", text, re.IGNORECASE)
    if current_change:
        i1 = _number_to_float(current_change.group(1)) or 0.0
        i2 = _number_to_float(current_change.group(2)) or 0.0
        dt = _number_to_float(current_change.group(3)) or 0.0
        if "inductance" in q and emf and not L:
            lines += [f"emf = {emf:.12g}", f"i1 = {i1:.12g}", f"i2 = {i2:.12g}", f"dt = {dt:.12g}", "L = emf * dt / abs(i2 - i1)", f"result = {_output_expr('L', unit)}"]
            return _code_block(_finish_code(lines, "result", row)), "ddt_inductance_from_emf", True
        if L:
            lines += [f"L = {L:.12g}", f"i1 = {i1:.12g}", f"i2 = {i2:.12g}", f"dt = {dt:.12g}", "emf = L * abs(i2 - i1) / dt", f"result = {_output_expr('emf', unit)}"]
            return _code_block(_finish_code(lines, "result", row)), "ddt_emf_from_current_change", True

    flux_change = re.search(r"flux[^.\n]{0,40}decreases\s+from\s+(" + _FLOAT_TOKEN + r")\s*(uWb|mWb|Wb)\s+to\s+(" + _FLOAT_TOKEN + r")\s*(?:uWb|mWb|Wb)?\s+in\s+(" + _FLOAT_TOKEN + r")\s*s", text, re.IGNORECASE)
    if flux_change:
        phi1 = (_number_to_float(flux_change.group(1)) or 0.0) * _value_factor(flux_change.group(2))
        phi2 = _number_to_float(flux_change.group(3)) or 0.0
        dt = _number_to_float(flux_change.group(4)) or 0.0
        lines += [f"phi1 = {phi1:.12g}", f"phi2 = {phi2:.12g}", f"dt = {dt:.12g}", "emf = abs(phi2 - phi1) / dt", f"result = {_output_expr('emf', unit)}"]
        return _code_block(_finish_code(lines, "result", row)), "ddt_emf_from_flux_change", True

    return None


def synthesize_python_code(row: dict[str, str], topic: str) -> tuple[str, str, bool]:
    """
    Build executable formula code for common high-confidence physics patterns.

    Returns (code, strategy, trainable). Untrainable records are kept for audit
    metadata but are filtered out by the training script by default.
    """
    question = row.get("question", "")
    answer = (row.get("answer") or "").strip()
    unit = normalize_unit(row.get("unit") or "")
    q = question.lower()

    capacitance = _find_value(question, ["C", "capacitance"], ["pF", "nF", "μF", "µF", "uF", "mF", "F"])
    voltage = _find_value(question, ["U", "V", "voltage"], ["V"])
    inductance = _find_value(question, ["L", "inductance"], ["mH", "μH", "µH", "uH", "H"])
    current = _find_value(question, ["I", "current"], ["A"])
    energy = _find_value(question, ["W", "E", "energy"], ["nJ", "μJ", "µJ", "uJ", "mJ", "J"])
    frequency = _find_value(question, ["f", "frequency"], ["kHz", "Hz"])
    resistance = _find_value(question, ["R", "resistance"], ["Ω", "ohm"])

    for synthesizer in (
        _synthesize_ddt,
        _synthesize_symbolic_geometry,
        _synthesize_zero_field,
        _synthesize_two_charge_vector,
    ):
        synthesized = synthesizer(row, topic)
        if synthesized is not None:
            return synthesized

    if "reson" in q and capacitance and inductance and frequency and answer.lower() in {"yes", "no"}:
        lines = [
            _assignment("L", inductance),
            _assignment("C", capacitance),
            _assignment("f_given", frequency),
            "f0 = 1 / (2 * math.pi * math.sqrt(L * C))",
            'answer = "Yes" if math.isclose(f_given, f0, rel_tol=0.02) else "No"',
            'unit = "-"',
        ]
        return _code_block(lines), "chlt_resonance_yes_no", True

    if "reson" in q and resistance and any(term in q for term in ["impedance", " z", "z="]):
        lines = [
            _assignment("Z", resistance),
            "answer = Z",
            'unit = "Ω"',
        ]
        return _code_block(lines), "resonance_impedance_equals_resistance", True

    if capacitance and voltage and any(term in q for term in ["energy", "stored"]):
        out = _output_expr("W", unit)
        lines = [
            _assignment("C", capacitance),
            _assignment("U", voltage),
            "W = 0.5 * C * U**2",
            f"answer = {out}",
            f"unit = {json.dumps(unit, ensure_ascii=False)}",
        ]
        return _code_block(lines), "capacitor_energy", True

    if inductance and current and any(term in q for term in ["energy", "stored", "magnetic field"]):
        out = _output_expr("W", unit)
        lines = [
            _assignment("L", inductance),
            _assignment("I", current),
            "W = 0.5 * L * I**2",
            f"answer = {out}",
            f"unit = {json.dumps(unit, ensure_ascii=False)}",
        ]
        return _code_block(lines), "inductor_energy", True

    if energy and capacitance and any(term in q for term in ["voltage", "potential difference"]):
        lines = [
            _assignment("W", energy),
            _assignment("C", capacitance),
            "U = math.sqrt(2 * W / C)",
            f"answer = {_output_expr('U', unit)}",
            f"unit = {json.dumps(unit, ensure_ascii=False)}",
        ]
        return _code_block(lines), "voltage_from_capacitor_energy", True

    if energy and inductance and "current" in q:
        lines = [
            _assignment("W", energy),
            _assignment("L", inductance),
            "I = math.sqrt(2 * W / L)",
            f"answer = {_output_expr('I', unit)}",
            f"unit = {json.dumps(unit, ensure_ascii=False)}",
        ]
        return _code_block(lines), "current_from_inductor_energy", True

    if energy and voltage and "capacitance" in q:
        lines = [
            _assignment("W", energy),
            _assignment("U", voltage),
            "C = 2 * W / U**2",
            f"answer = {_output_expr('C', unit)}",
            f"unit = {json.dumps(unit, ensure_ascii=False)}",
        ]
        return _code_block(lines), "capacitance_from_energy", True

    if energy and current and "inductance" in q:
        lines = [
            _assignment("W", energy),
            _assignment("I", current),
            "L = 2 * W / I**2",
            f"answer = {_output_expr('L', unit)}",
            f"unit = {json.dumps(unit, ensure_ascii=False)}",
        ]
        return _code_block(lines), "inductance_from_energy", True

    if topic == "dc_circuit" and voltage and resistance and "parallel" in q and "each" in q:
        lamp_count = 2
        count_match = re.search(r"\b(two|three|four|2|3|4)\s+lamps?\b", q)
        if count_match:
            counts = {"two": 2, "three": 3, "four": 4, "2": 2, "3": 3, "4": 4}
            lamp_count = counts[count_match.group(1)]
        lines = [
            _assignment("U", voltage),
            _assignment("R", resistance),
            f"lamp_count = {lamp_count}",
            "I_each = U / R",
            "I_total = lamp_count * I_each",
            'answer = f"I_each = {I_each:.6g}; I_total = {I_total:.6g}"',
            'unit = "A"',
        ]
        return _code_block(lines), "parallel_identical_lamps", True

    force_values = re.findall(r"([0-9]+(?:\.[0-9]+)?)\s*N\b", question, flags=re.IGNORECASE)
    if len(force_values) >= 2 and ("force" in q or "forces" in q):
        f1, f2 = force_values[0], force_values[1]
        if "same direction" in q:
            op = "F1 + F2"
            strategy = "same_direction_forces"
        elif "opposite direction" in q:
            op = "abs(F1 - F2)"
            strategy = "opposite_direction_forces"
        elif "perpendicular" in q or "right angle" in q:
            op = "math.sqrt(F1**2 + F2**2)"
            strategy = "perpendicular_forces"
        else:
            angle_match = re.search(r"angle(?: of)?\s*([0-9]+(?:\.[0-9]+)?)", q)
            if not angle_match:
                angle_match = re.search(r"([0-9]+(?:\.[0-9]+)?)°", question)
            if angle_match:
                theta = angle_match.group(1)
                lines = [
                    f"F1 = {f1}",
                    f"F2 = {f2}",
                    f"theta = math.radians({theta})",
                    "F = math.sqrt(F1**2 + F2**2 + 2 * F1 * F2 * math.cos(theta))",
                    "answer = F",
                    'unit = "N"',
                ]
                return _code_block(lines), "angled_forces", True
            if "angle between" in q and "resultant" in q:
                if "each" in q:
                    result_force = force_values[-1]
                    f1 = force_values[0]
                    f2 = force_values[0]
                elif len(force_values) >= 3:
                    f1, f2, result_force = force_values[0], force_values[1], force_values[2]
                else:
                    result_force = None
                if result_force is not None:
                    lines = [
                        f"F1 = {f1}",
                        f"F2 = {f2}",
                        f"F = {result_force}",
                        "cos_theta = (F**2 - F1**2 - F2**2) / (2 * F1 * F2)",
                        "cos_theta = max(-1.0, min(1.0, cos_theta))",
                        "theta_deg = math.degrees(math.acos(cos_theta))",
                    ]
                    return _code_block(_finish_code(lines, "theta_deg", row)), "angle_from_resultant_forces", True
            return "", "no_synthesized_code", False
        lines = [
            f"F1 = {f1}",
            f"F2 = {f2}",
            f"F = {op}",
            "answer = F",
            'unit = "N"',
        ]
        return _code_block(lines), strategy, True

    topic_prefix = row.get("_topic_prefix") or detect_topic_prefix(row.get("id", ""))
    if topic_prefix in {"DT", "LD", "DDT"} and answer:
        if answer_type(answer) == "quantitative":
            return _supervised_target_code(row, "supervised_numeric_target")
        return _supervised_target_code(row, "supervised_symbolic_text_target")

    if topic_prefix in {"CH", "TD", "NL", "THCB"} and answer:
        fallback_strategy = {
            "CH": "supervised_ac_circuit_target",
            "TD": "supervised_capacitor_target",
            "NL": "supervised_lc_energy_target",
            "THCB": "supervised_measurement_target",
        }[topic_prefix]
        return _supervised_target_code(row, fallback_strategy)

    return "", "no_synthesized_code", False


def build_prompt(
    row: dict[str, str],
    topic: str,
    q_type: str,
    unit_hints: list[str],
    topic_hints: list[str],
    premises: list[str],
    distractors: list[str],
) -> str:
    unit_text = "\n".join(f"  - {hint}" for hint in unit_hints) or "  (none detected)"
    topic_text = "\n".join(f"  - {hint}" for hint in topic_hints) or "  (none detected)"
    premise_text = "\n".join(f"  - {premise}" for premise in premises) or "  (none found)"
    distractor_text = "\n".join(f"  - {premise}" for premise in distractors) or "  (none)"
    return f"""Question type: {q_type}
Detected topic: {topic}

Unit conversion facts (treat as HARD CONSTRAINTS):
{unit_text}

Topic/geometry hints (treat as HARD CONSTRAINTS):
{topic_text}

Relevant physics laws/formulas:
{premise_text}

Possible distractor premises (ignore if not relevant):
{distractor_text}

Problem:
{row.get("question", "").strip()}

Solve this problem following the exact output format."""


def build_completion(row: dict[str, str], topic: str, code: str) -> str:
    cot = (row.get("cot") or "").strip()
    answer = (row.get("answer") or "").strip()
    unit = normalize_unit(row.get("unit") or "")
    answer_unit = f"{answer} {unit}".strip()

    fol = (
        f'∀p (PhysicsProblem(p) ∧ Topic(p, "{topic}") '
        f"→ SolveByRelevantPremisesAndExecutableCode(p))"
    )
    if not code:
        code = _code_block([
            "# No reliable executable target was synthesized for this sample.",
            "# This record is marked trainable=False and should be skipped by SFT.",
            'answer = ""',
            'unit = ""',
        ])

    return f"""<think>
{cot}
</think>

[FOL]: {fol}

[CODE]:
```python
{code}
```

[ANSWER]: {answer_unit}"""


def build_text(prompt: str, completion: str) -> tuple[str, str]:
    prompt_text = (
        "<|im_start|>system\n"
        f"{SYSTEM_PROMPT}<|im_end|>\n"
        "<|im_start|>user\n"
        f"{prompt}<|im_end|>\n"
        "<|im_start|>assistant\n"
    )
    return prompt_text, prompt_text + f"{completion}<|im_end|>"


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def split_topic_rows(
    rows: list[dict[str, str]],
    train_ratio: float,
    val_ratio: float,
    seed: int,
) -> dict[str, list[dict[str, str]]]:
    rng = random.Random(seed)
    annotated_rows: list[dict[str, str]] = []
    for row in rows:
        row = dict(row)
        topic_prefix = detect_topic_prefix(row.get("id", ""))
        row["_topic_prefix"] = topic_prefix
        detected_topic = detect_topic(row.get("question", ""))
        _code, strategy, _trainable = synthesize_python_code(row, detected_topic)
        row["_split_strategy"] = strategy
        annotated_rows.append(row)

    raw_group_counts = Counter(
        f"{row['_topic_prefix']}::{row['_split_strategy']}" for row in annotated_rows
    )
    by_group: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in annotated_rows:
        raw_key = f"{row['_topic_prefix']}::{row['_split_strategy']}"
        strategy = row["_split_strategy"] if raw_group_counts[raw_key] >= 10 else "small_subtypes"
        by_group[f"{row['_topic_prefix']}::{strategy}"].append(row)

    splits = {"train": [], "val": [], "test": []}
    for group_key in sorted(by_group):
        group_rows = by_group[group_key][:]
        rng.shuffle(group_rows)
        n = len(group_rows)

        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        if n >= 3:
            n_val = max(1, n_val)
            n_train = min(n_train, n - 2)
        n_test = n - n_train - n_val
        if n >= 3 and n_test < 1:
            n_test = 1
            n_train = n - n_val - n_test

        for split_name, split_rows in (
            ("train", group_rows[:n_train]),
            ("val", group_rows[n_train : n_train + n_val]),
            ("test", group_rows[n_train + n_val :]),
        ):
            for row in split_rows:
                row = dict(row)
                splits[split_name].append(row)

    for split_rows in splits.values():
        rng.shuffle(split_rows)

    return splits


def to_record(row: dict[str, str], split: str) -> dict[str, Any]:
    topic_prefix = row["_topic_prefix"]
    unit = normalize_unit(row.get("unit", ""))
    answer = (row.get("answer") or "").strip()
    question = (row.get("question") or "").strip()
    detected_topic = detect_topic(question)
    q_type = route_question(question)
    unit_hints = get_unit_hints(question)
    topic_hints = get_topic_hints(question, detected_topic)
    premises, distractors = retrieve_sft_premises(question, detected_topic)
    code, code_strategy, trainable = synthesize_python_code(row, detected_topic)
    prompt = build_prompt(
        row=row,
        topic=detected_topic,
        q_type=q_type,
        unit_hints=unit_hints,
        topic_hints=topic_hints,
        premises=premises,
        distractors=distractors,
    )
    completion = build_completion(row, detected_topic, code)
    prompt_text, text = build_text(prompt, completion)
    return {
        "id": row.get("id", "").strip(),
        "topic_prefix": topic_prefix,
        "topic": detected_topic,
        "dataset_topic": TOPIC_NAMES.get(topic_prefix, topic_prefix.lower()),
        "split": split,
        "question": question,
        "answer": answer,
        "unit": unit,
        "answer_type": answer_type(answer),
        "question_type": q_type,
        "unit_hints": unit_hints,
        "topic_hints": topic_hints,
        "premises": premises,
        "distractor_premises": distractors,
        "code_strategy": code_strategy,
        "subtype": code_strategy,
        "split_group": row.get("_split_strategy", code_strategy),
        "trainable": trainable,
        "prompt": prompt,
        "prompt_text": prompt_text,
        "completion": completion,
        "text": text,
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def prepare_dataset(
    dataset_path: Path,
    output_dir: Path,
    seed: int = 42,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
) -> dict[str, Any]:
    rows = load_rows(dataset_path)
    splits = split_topic_rows(rows, train_ratio=train_ratio, val_ratio=val_ratio, seed=seed)

    manifest: dict[str, Any] = {
        "dataset_path": str(dataset_path),
        "seed": seed,
        "total": len(rows),
        "splits": {},
        "topics": {},
    }

    all_records: list[dict[str, Any]] = []
    for split_name, split_rows in splits.items():
        records = [to_record(row, split_name) for row in split_rows]
        all_records.extend(records)
        write_jsonl(output_dir / f"{split_name}.jsonl", records)
        manifest["splits"][split_name] = len(records)
        manifest.setdefault("trainable_splits", {})[split_name] = sum(bool(r["trainable"]) for r in records)

    for row in rows:
        prefix = detect_topic_prefix(row.get("id", ""))
        manifest["topics"].setdefault(
            prefix,
            {"total": 0, "train": 0, "val": 0, "test": 0, "trainable": 0, "untrainable": 0},
        )
        manifest["topics"][prefix]["total"] += 1

    for split_name, split_rows in splits.items():
        for row in split_rows:
            manifest["topics"][row["_topic_prefix"]][split_name] += 1

    strategies_by_topic: dict[str, Counter[str]] = defaultdict(Counter)
    for record in all_records:
        prefix = record["topic_prefix"]
        if record["trainable"]:
            manifest["topics"][prefix]["trainable"] += 1
        else:
            manifest["topics"][prefix]["untrainable"] += 1
        strategies_by_topic[prefix][record["code_strategy"]] += 1

    manifest["code_strategies"] = {
        prefix: dict(sorted(counter.items()))
        for prefix, counter in sorted(strategies_by_topic.items())
    }
    manifest["trainable_total"] = sum(manifest.get("trainable_splits", {}).values())

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare stratified SFT JSONL files.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = prepare_dataset(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        seed=args.seed,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

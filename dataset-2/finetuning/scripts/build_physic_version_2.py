"""Build a cleaned CoT-only version of the physics CSV dataset.

The script writes dataset_2/physic_version_2.csv without changing question,
answer, unit, row order, or schema. It rewrites only selected weak CoT fields.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "dataset_2" / "Physics_Problems_Text_Only.csv"
DEFAULT_OUTPUT = ROOT / "dataset_2" / "physic_version_2.csv"

TOPIC_TARGETS = {
    "THCB": 78,
    "CH": 129,
    "LD": 119,
    "TD": 53,
    "DT": 41,
    "NL": 29,
    "DDT": 25,
    "CHLT": 4,
}

TOPIC_ORDER = ["CHLT", "THCB", "DDT", "LD", "CH", "NL", "TD", "DT"]

FORCED_IDS = {
    "THCB001",
    "LD001",
    "LD002",
    "DT004",
    "DT025",
    "DDT139",
    "DDT141",
    "TD401",
    "CH007",
    "NL001",
    "CHLT009",
}

DO_NOT_REWRITE = {"DDT131"}


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def topic_prefix(sample_id: str) -> str:
    sample_id = (sample_id or "").upper()
    for prefix in TOPIC_ORDER:
        if sample_id.startswith(prefix):
            return prefix
    match = re.match(r"[A-Z]+", sample_id)
    return match.group(0) if match else "UNK"


def normalize_text(text: str) -> str:
    out = text or ""
    # Preserve squared units before flattening superscript digits.
    for src, dst in [
        ("cm²", "cm^2"),
        ("mm²", "mm^2"),
        ("m²", "m^2"),
        ("cm³", "cm^3"),
        ("mm³", "mm^3"),
        ("m³", "m^3"),
    ]:
        out = out.replace(src, dst)

    replacements = {
        "×": "x",
        "μ": "u",
        "µ": "u",
        "Ω": "ohm",
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
        "−": "-",
        "π": "pi",
        "φ": "phi",
        "Φ": "Phi",
        "Δ": "Delta",
    }
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    return out


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9_]+", text or ""))


def step_count(text: str) -> int:
    return len(re.findall(r"(?i)\bstep\s*\d+", text or ""))


def op_count(text: str) -> int:
    return sum((text or "").count(ch) for ch in ["=", "x", "×", "*", "/", "^", "+"])


def numeric_count(text: str) -> int:
    return len(re.findall(r"[-+]?\d+(?:[.,]\d+)?", normalize_text(text or "")))


def is_numericish(answer: str) -> bool:
    value = normalize_text((answer or "").strip()).replace(",", "")
    value = re.sub(r"\s*x\s*10\s*\^?\s*([+-]?\d+)", r"e\1", value, flags=re.IGNORECASE)
    return bool(re.match(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$", value, re.IGNORECASE))


def answer_unit(row: dict[str, str]) -> str:
    answer = (row.get("answer") or "").strip()
    unit = (row.get("unit") or "").strip()
    if not unit or unit in {"-", "—", "â€”"}:
        return answer
    return f"{answer} {unit}"


def final_answer_text(row: dict[str, str]) -> str:
    final = answer_unit(row)
    return final if final else "(no unit)"


NUMBER = r"[+-]?\d+(?:\.\d+)?(?:\s*(?:x|X)\s*10\s*\^?\s*[+-]?\d+)?"
UNIT_PATTERN = (
    r"turns/m|N/C|V/m|cm\^2|mm\^2|m\^2|uF|mF|nF|pF|uC|mC|nC|"
    r"mH|uH|mJ|uJ|nJ|kHz|ohm|Wb|cm|mm|Hz|F|C|H|J|m|V|A|T|W|N|turns"
)


def parse_number(raw: str) -> float | None:
    text = normalize_text(raw).strip().replace(",", "")
    text = re.sub(r"\s*x\s*10\s*\^?\s*([+-]?\d+)", r"e\1", text, flags=re.IGNORECASE)
    text = text.replace(" ", "")
    try:
        return float(text)
    except ValueError:
        return None


def fmt_number(value: float) -> str:
    if value == 0:
        return "0"
    if abs(value) >= 1e4 or abs(value) < 1e-3:
        return f"{value:.6g}"
    return f"{value:.6g}".rstrip("0").rstrip(".")


def compact_unique(items: Iterable[str], limit: int = 6) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        item = " ".join(item.split())
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
        if len(out) >= limit:
            break
    return out


def extract_assignments(question: str, limit: int = 7) -> list[str]:
    q = normalize_text(question)
    pattern = re.compile(
        rf"\b([A-Za-z][A-Za-z0-9_]*)\s*=\s*({NUMBER})\s*([A-Za-z/%^0-9.-]+)?",
        re.IGNORECASE,
    )
    items = []
    for name, value, unit in pattern.findall(q):
        unit = unit.strip(".,;) ") if unit else ""
        items.append(f"{name} = {value.strip()} {unit}".strip())

    generic = re.compile(rf"({NUMBER})\s*({UNIT_PATTERN})(?![A-Za-z0-9/^])", re.IGNORECASE)
    for value, unit in generic.findall(q):
        items.append(f"{value.strip()} {unit.strip()}")
    return compact_unique(items, limit=limit)


def givens_text(row: dict[str, str]) -> str:
    givens = extract_assignments(row.get("question", ""))
    if givens:
        return "; ".join(givens)
    question = " ".join((row.get("question") or "").split())
    return question[:180] + ("..." if len(question) > 180 else "")


def convert_unit(value: float, unit: str) -> tuple[float, str] | None:
    unit = unit.lower()
    factors = {
        "pf": (1e-12, "F"),
        "nf": (1e-9, "F"),
        "uf": (1e-6, "F"),
        "mf": (1e-3, "F"),
        "uc": (1e-6, "C"),
        "mc": (1e-3, "C"),
        "nc": (1e-9, "C"),
        "uh": (1e-6, "H"),
        "mh": (1e-3, "H"),
        "uj": (1e-6, "J"),
        "mj": (1e-3, "J"),
        "nj": (1e-9, "J"),
        "khz": (1e3, "Hz"),
        "cm": (1e-2, "m"),
        "mm": (1e-3, "m"),
        "cm^2": (1e-4, "m^2"),
        "mm^2": (1e-6, "m^2"),
    }
    if unit not in factors:
        return None
    factor, target = factors[unit]
    return value * factor, target


def conversion_notes(question: str) -> list[str]:
    q = normalize_text(question)
    pattern = re.compile(
        rf"({NUMBER})\s*(cm\^2|mm\^2|uF|mF|nF|pF|uC|mC|nC|mH|uH|mJ|uJ|nJ|kHz|cm|mm)(?![A-Za-z0-9/^])",
        re.IGNORECASE,
    )
    notes = []
    for value_raw, unit in pattern.findall(q):
        value = parse_number(value_raw)
        if value is None:
            continue
        converted = convert_unit(value, unit)
        if converted is None:
            continue
        si_value, si_unit = converted
        notes.append(f"{value_raw.strip()} {unit} = {fmt_number(si_value)} {si_unit}")
    return compact_unique(notes, limit=5)


def extract_distances(question: str) -> dict[str, float]:
    q = normalize_text(question)
    distances: dict[str, float] = {}
    for name, value_raw, unit in re.findall(
        rf"\b([A-Z]{{2}})\s*=\s*({NUMBER})\s*(cm|mm|m)\b",
        q,
        flags=re.IGNORECASE,
    ):
        value = parse_number(value_raw)
        if value is None:
            continue
        factor = {"cm": 1e-2, "mm": 1e-3, "m": 1.0}[unit.lower()]
        key = "".join(sorted(name.upper()))
        distances[key] = value * factor

    apart = re.search(
        rf"\b([A-Z])\s+and\s+([A-Z])\b[^.]*?({NUMBER})\s*(cm|mm|m)\s+apart",
        q,
        flags=re.IGNORECASE,
    )
    if apart:
        a, b, value_raw, unit = apart.groups()
        value = parse_number(value_raw)
        if value is not None:
            factor = {"cm": 1e-2, "mm": 1e-3, "m": 1.0}[unit.lower()]
            distances["".join(sorted(a.upper() + b.upper()))] = value * factor
    return distances


def close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-3, abs_tol=1e-9)


def geometry_notes(question: str, topic: str) -> list[str]:
    q = normalize_text(question)
    ql = q.lower()
    notes: list[str] = []
    distances = extract_distances(question)

    explicit_right = re.search(
        r"right[- ]angled\s+(?:triangle\s+)?([A-Z]{3})\s*\(right[- ]angled\s+at\s+([A-Z])\)",
        q,
        flags=re.IGNORECASE,
    )
    if explicit_right:
        vertices, vertex = explicit_right.groups()
        notes.append(f"triangle {vertices.upper()} is right-angled at {vertex.upper()}, so the two sides through that vertex are perpendicular")

    if "equilateral" in ql:
        notes.append("equilateral geometry gives equal sides and 60 degree angles")
    if "perpendicular bisector" in ql:
        notes.append("a point on the perpendicular bisector is equidistant from the two endpoints")
    if "midpoint" in ql or "mid-point" in ql:
        notes.append("midpoint geometry gives equal distances to the two endpoints")

    for a, b, c in [("AB", "AC", "BC"), ("AB", "AM", "BM"), ("AB", "CA", "CB"), ("AB", "MA", "MB")]:
        vals = []
        for side in [a, b, c]:
            vals.append((side, distances.get("".join(sorted(side)))))
        if any(value is None for _, value in vals):
            continue
        ordered = sorted(((name, value) for name, value in vals if value is not None), key=lambda item: item[1])
        (s1_name, s1), (s2_name, s2), (s3_name, s3) = ordered
        if close(s1 + s2, s3):
            notes.append(f"{s1_name} + {s2_name} = {s3_name}, so the three points are collinear")
        elif close(s1 * s1 + s2 * s2, s3 * s3):
            notes.append(f"{s1_name}^2 + {s2_name}^2 = {s3_name}^2, so the triangle is right-angled")

    if topic in {"LD", "DT"} and any(term in ql for term in ["force", "field", "electric field", "q3"]):
        notes.append("treat force/electric-field quantities as vectors and add signed components")
    if topic == "DT" and "potential" in ql:
        notes.append("electric potential is scalar, so add algebraic potentials rather than vector components")

    return compact_unique(notes, limit=4)


def formula_hints(topic: str, question: str) -> list[str]:
    q = normalize_text(question).lower()
    hints: list[str] = []

    if topic == "THCB":
        if "absolute error" in q:
            hints.append("use Delta x equal to the instrument least count when no other uncertainty is given")
        if "relative error" in q:
            hints.append("relative error = Delta x / measured value")
        if "percentage" in q or "percent" in q:
            hints.append("percentage error = relative error * 100%")
        if "average" in q or "mean" in q or "random" in q:
            hints.append("average repeated measurements first, then compare deviations from the average")
        if not hints:
            hints.append("apply the measurement-error rule before rounding the reported value")
    elif topic == "LD":
        if "electric field" in q:
            hints.append("use E = k*|q|/r^2 for each source charge")
        if "force" in q or "acting on" in q:
            hints.append("use Coulomb force F = k*|q_i*q_j|/r^2 for each pair")
        hints.append("combine directions by charge signs: like charges repel and unlike charges attract")
    elif topic == "DT":
        if "potential" in q or "voltage" in q:
            hints.append("use V = k*q/r and U_AB = V_A - V_B for potential/voltage questions")
        if "electric field" in q or "field strength" in q:
            hints.append("use E = k*|q|/r^2 and add field vectors with signs")
        if "force" in q and "q3" in q:
            hints.append("after finding E_net, use F = |q3|*|E_net| for force magnitude")
        if "zero" in q:
            hints.append("solve the zero condition in the physically valid region before reporting the coordinate")
    elif topic == "TD":
        if "energy" in q or "stored" in q:
            hints.append("use capacitor energy W = 0.5*C*U^2 or W = Q^2/(2*C), choosing the form matching the givens")
        if "capacitance" in q:
            hints.append("use C = Q/U or the parallel-plate relation C = epsilon*A/d")
        if "electric field" in q:
            hints.append("use E = U/d for a uniform field between plates")
        if "disconnected" in q or "connected" in q:
            hints.append("check source state: disconnected keeps Q constant; connected keeps U constant")
    elif topic in {"CH", "CHLT"}:
        if "reson" in q:
            hints.append("at resonance X_L = X_C, Z = R, and f0 = 1/(2*pi*sqrt(L*C))")
        if "impedance" in q:
            hints.append("use X_L = 2*pi*f*L, X_C = 1/(2*pi*f*C), and Z = sqrt(R^2 + (X_L - X_C)^2)")
        if "power factor" in q or "cos" in q:
            hints.append("use cos(phi) = R/Z")
        if "power" in q:
            hints.append("use P = U*I*cos(phi) or P = I^2*R for the resistive power")
    elif topic == "NL":
        if "energy" in q:
            hints.append("use LC energy conservation: W_total = W_C + W_L")
            hints.append("use W_C = 0.5*C*U^2 and W_L = 0.5*L*I^2")
        if "frequency" in q or "period" in q or "oscillation" in q:
            hints.append("use omega = 1/sqrt(L*C), T = 2*pi*sqrt(L*C), and f = 1/T")
    elif topic == "DDT":
        if "turn density" in q or "magnetic field inside" in q:
            hints.append("use B = mu0*n*I, with n = N/l only when turn density is not already given")
        if "flux" in q:
            hints.append("use Phi = B*A for one turn and N*Phi for the entire solenoid/flux linkage")
        if "inductance" in q:
            hints.append("use solenoid inductance L = mu0*N^2*A/l with area in m^2")
        if "energy density" in q:
            hints.append("use magnetic energy density u = B^2/(2*mu0); area is not needed")
        if "electromotive" in q or "emf" in q:
            hints.append("use |e| = L*|Delta I|/Delta t or N*|Delta Phi|/Delta t as appropriate")

    if not hints:
        hints.append("select the relation that contains the requested quantity and the given variables")
    return compact_unique(hints, limit=3)


def has_geometry_question(question: str) -> bool:
    q = normalize_text(question)
    ql = q.lower()
    return bool(re.search(r"\b[A-Z]{2}\s*=", q)) or any(
        term in ql
        for term in [
            "triangle",
            "right-angled",
            "right angled",
            "equilateral",
            "perpendicular",
            "bisector",
            "midpoint",
            "mid-point",
            "collinear",
            "apart",
            "coordinate",
            "axis",
            "vector",
            "square",
        ]
    )


def has_concrete_geometry_cot(cot: str) -> bool:
    c = normalize_text(cot).lower()
    phrase_terms = [
        "pythag",
        "right-angled at",
        "right angle at",
        "right triangle",
        "perpendicular bisector",
        "collinear",
        "equilateral",
        "midpoint",
        "component",
        "components",
        "resolve",
        "decompose",
        "resultant",
        "angle between",
        "vectors form",
        "cancel",
        "symmetry",
        "horizontal",
        "vertical",
        "scalar",
    ]
    if any(term in c for term in phrase_terms):
        return True
    tokens = set(re.findall(r"[a-z]+", c))
    return bool(tokens.intersection({"cos", "sin", "tan", "sqrt"}))


def row_score(row: dict[str, str]) -> tuple[int, list[str]]:
    cot = row.get("cot") or ""
    q = row.get("question") or ""
    topic = topic_prefix(row.get("id", ""))
    words = word_count(cot)
    steps = step_count(cot)
    nums = numeric_count(cot)
    ops = op_count(normalize_text(cot))
    score = 0
    reasons: list[str] = []

    if (row.get("id") or "") in FORCED_IDS:
        score += 100
        reasons.append("forced_spot_check")
    if cot.count("Step 1") > 1 or "for aStep" in cot or "Step 7:  the" in cot:
        score += 12
        reasons.append("broken_or_duplicated_steps")
    if words < 55 or steps < 3:
        score += 10
        reasons.append("too_short")
    elif words < 85:
        score += 5
        reasons.append("short")
    if steps <= 4:
        score += 4
        reasons.append("few_steps")
    if is_numericish(row.get("answer", "")) and (nums < 6 or ops < 4 or answer_unit(row) not in cot):
        score += 8
        reasons.append("no_calculations")
    generic = len(
        re.findall(
            r"(?i)\b(identify|recall|substitute|calculate|determine|use the formula|given values)\b",
            cot,
        )
    )
    if generic >= 3 and words < 110:
        score += 5
        reasons.append("vague_steps")
    if has_geometry_question(q) and not has_concrete_geometry_cot(cot):
        score += 8
        reasons.append("missing_geo_step")
    if topic == "THCB":
        score += 2
    return score, reasons


def select_rows(rows: list[dict[str, str]]) -> dict[str, list[str]]:
    by_topic: dict[str, list[tuple[int, str, list[str]]]] = defaultdict(list)
    for row in rows:
        sample_id = row.get("id", "")
        if sample_id in DO_NOT_REWRITE:
            continue
        score, reasons = row_score(row)
        topic = topic_prefix(sample_id)
        by_topic[topic].append((score, sample_id, reasons))

    selected: dict[str, list[str]] = {}
    for topic, target in TOPIC_TARGETS.items():
        candidates = sorted(by_topic.get(topic, []), key=lambda item: (-item[0], item[1]))
        forced = [item for item in candidates if item[1] in FORCED_IDS]
        regular = [item for item in candidates if item[1] not in FORCED_IDS]
        chosen = (forced + regular)[:target]
        selected[topic] = [sample_id for _, sample_id, _ in chosen]
    return selected


def special_cot(row: dict[str, str]) -> str | None:
    final = final_answer_text(row)
    sample_id = row.get("id", "")
    templates = {
        "THCB001": [
            "Step 1: Read the instrument data: the ammeter least count is 0.1 A and the measured current is 1.2 A.",
            "Step 2: For a single reading when no other uncertainty is specified, the absolute error is taken as the least count of the instrument.",
            "Step 3: Therefore Delta I = 0.1 A; the measuring range only tells us the meter can measure up to 2 A and does not change this error.",
            f"Step 4: Report the absolute error as {final}.",
        ],
        "LD001": [
            "Step 1: Convert the distances: CA = 5 cm = 0.05 m, CB = 3 cm = 0.03 m, and AB = 8 cm = 0.08 m.",
            "Step 2: Since CA + CB = AB, point C lies between A and B, so both forces on positive q3 point toward B: q1 repels q3 and q2 attracts q3.",
            "Step 3: Compute F13 = k*|q1*q3|/CA^2 = 9e9*(6e-8*6e-8)/(0.05^2) = 0.01296 N.",
            "Step 4: Compute F23 = k*|q2*q3|/CB^2 = 9e9*(6e-8*6e-8)/(0.03^2) = 0.036 N.",
            f"Step 5: The forces have the same direction, so F_net = 0.01296 + 0.036 = 0.04896 N, which rounds to {final}.",
        ],
        "LD002": [
            "Step 1: The triangle is right-angled at A, with AB = 4 m and BC = 5 m, so AC = sqrt(BC^2 - AB^2) = 3 m.",
            "Step 2: Force from B on A is attractive along AB: F_BA = 9e9*(5.0e-6*5.0e-6)/(4^2) = 0.01406 N.",
            "Step 3: Force from C on A is repulsive along the line AC: F_CA = 9e9*(5.0e-6*4.0e-6)/(3^2) = 0.0200 N.",
            "Step 4: The two force directions are perpendicular, so F_net = sqrt(F_BA^2 + F_CA^2).",
            f"Step 5: F_net = sqrt(0.01406^2 + 0.0200^2) = 0.02445 N = {final}.",
        ],
        "DT004": [
            "Step 1: Convert distances and charges: AB = 0.10 m, AC = BC = 0.08 m, q1 = q2 = 16e-8 C, and q3 = 2e-6 C.",
            "Step 2: The geometry is an isosceles triangle. The altitude from C to AB is h = sqrt(0.08^2 - 0.05^2) = 0.06245 m.",
            "Step 3: Each source charge repels q3 with F = k*q*q3/r^2 = 9e9*(16e-8*2e-6)/(0.08^2) = 0.45 N.",
            "Step 4: Horizontal components cancel by symmetry, while vertical components add: F_net = 2*F*(h/0.08).",
            f"Step 5: F_net = 2*0.45*(0.06245/0.08) = 0.702 N, which rounds to {final}.",
        ],
        "DT025": [
            "Step 1: Place q1 = -9e-6 C at x = 0 and q2 = 4e-6 C at x = 0.20 m on the Ox axis.",
            "Step 2: Because the charges have opposite signs, the zero-field point is outside the segment, on the side of the smaller charge q2.",
            "Step 3: For x > 0.20 m, set magnitudes equal: k*9e-6/x^2 = k*4e-6/(x - 0.20)^2.",
            "Step 4: Taking square roots gives 3/x = 2/(x - 0.20), so 3(x - 0.20) = 2x and x = 0.60 m.",
            f"Step 5: Express the coordinate in the requested unit: {final}.",
        ],
        "DDT139": [
            "Step 1: Use the given turn density directly: n = 1000 turns/m and I = 2 A. The area is not needed for energy density.",
            "Step 2: Compute the solenoid field B = mu0*n*I = (4*pi*1e-7)*1000*2 = 0.002513 T.",
            "Step 3: Magnetic energy density is u = B^2/(2*mu0).",
            "Step 4: Substitute B = 0.002513 T: u = (0.002513^2)/(2*4*pi*1e-7) = 2.51 J/m^3.",
            f"Step 5: Therefore the magnetic field energy density is {final}.",
        ],
        "DDT141": [
            "Step 1: Convert the area of each turn: A = 6 cm^2 = 6e-4 m^2.",
            "Step 2: Flux through one turn is Phi = B*A = 0.005*6e-4 = 3e-6 Wb.",
            "Step 3: The question asks for flux through the entire solenoid, so multiply by N = 1000 turns.",
            "Step 4: Phi_total = N*Phi = 1000*3e-6 = 0.003 Wb.",
            f"Step 5: Therefore the magnetic flux through the entire solenoid is {final}.",
        ],
        "TD401": [
            "Step 1: Identify C = 100 uF and U = 30 V.",
            "Step 2: Convert the capacitance to SI units: C = 100 uF = 100e-6 F = 1e-4 F.",
            "Step 3: Use capacitor energy W = 0.5*C*U^2.",
            "Step 4: Substitute the values: W = 0.5*(1e-4)*(30^2) = 0.5*1e-4*900 = 0.045 J.",
            f"Step 5: Therefore the stored energy is {final}.",
        ],
        "CH007": [
            "Step 1: At resonance in a series RLC circuit, the inductive and capacitive reactances cancel: X_L = X_C.",
            "Step 2: Therefore the total impedance is purely resistive, so Z = R.",
            "Step 3: The measured resonance impedance is Z = 75 ohm.",
            f"Step 4: Hence R = Z = {final}.",
        ],
        "NL001": [
            "Step 1: Identify C = 20 uF and U = 100 V.",
            "Step 2: Convert C to farads: C = 20 uF = 20e-6 F = 2e-5 F.",
            "Step 3: Use capacitor energy W = 0.5*C*U^2.",
            "Step 4: Substitute the values: W = 0.5*(2e-5)*(100^2) = 0.1 J = 100 mJ.",
            f"Step 5: Therefore the stored energy is {final}.",
        ],
        "CHLT009": [
            "Step 1: Identify C = 100 uF, L = 0.01 H, R = 8 ohm, and the test frequency f = 100 Hz.",
            "Step 2: Convert C to SI units: C = 100 uF = 1e-4 F.",
            "Step 3: For resonance, f0 = 1/(2*pi*sqrt(L*C)).",
            "Step 4: Substitute L = 0.01 H and C = 1e-4 F: f0 = 1/(2*pi*sqrt(1e-6)) = about 159 Hz.",
            f"Step 5: Since 100 Hz is not equal to the resonance frequency, the answer is {final}.",
        ],
    }
    steps = templates.get(sample_id)
    return "\n".join(steps) if steps else None


def build_generic_cot(row: dict[str, str], reasons: list[str]) -> str:
    topic = topic_prefix(row.get("id", ""))
    question = row.get("question") or ""
    final = final_answer_text(row)
    givens = givens_text(row)
    conversions = conversion_notes(question)
    geometry = geometry_notes(question, topic)
    formulas = formula_hints(topic, question)
    numeric = is_numericish(row.get("answer", ""))

    steps = [f"Step 1: Read the requested quantity and the useful givens from the problem: {givens}."]

    if conversions:
        steps.append(f"Step 2: Convert all non-SI quantities before substituting: {'; '.join(conversions)}.")
    else:
        steps.append("Step 2: Keep the given quantities in consistent SI units and preserve the requested output unit for the final report.")

    if geometry:
        steps.append(f"Step 3: Handle the geometry or sign convention explicitly: {'; '.join(geometry)}.")
        formula_step = 4
    else:
        formula_step = 3

    steps.append(f"Step {formula_step}: Choose the governing relation: {'; '.join(formulas)}.")
    if numeric:
        steps.append(
            f"Step {formula_step + 1}: Substitute the converted values from the earlier steps, simplify the intermediate SI result, and round only after the arithmetic is complete."
        )
        steps.append(f"Step {formula_step + 2}: The computed result in the requested format is {final}.")
    else:
        steps.append(
            f"Step {formula_step + 1}: Apply the relation qualitatively to the specific condition in the question instead of inventing an unrelated numerical calculation."
        )
        steps.append(f"Step {formula_step + 2}: Therefore the answer is {final}.")
    return "\n".join(steps)


def build_rewrite(row: dict[str, str], reasons: list[str]) -> str:
    special = special_cot(row)
    if special:
        return special
    return build_generic_cot(row, reasons)


def validate(
    original: list[dict[str, str]],
    rewritten: list[dict[str, str]],
    fieldnames: list[str],
    changed_ids: set[str],
) -> None:
    assert len(original) == len(rewritten) == 1352, "row count changed"
    assert fieldnames == ["id", "question", "cot", "answer", "unit"], "schema changed"

    original_topics = Counter(topic_prefix(row["id"]) for row in original)
    rewritten_topics = Counter(topic_prefix(row["id"]) for row in rewritten)
    assert original_topics == rewritten_topics, "topic counts changed"

    actual_changed: set[str] = set()
    for before, after in zip(original, rewritten):
        assert before["id"] == after["id"], f"row order changed near {before['id']}"
        for key in ["id", "question", "answer", "unit"]:
            assert before[key] == after[key], f"non-cot field changed for {before['id']}: {key}"
        if before["cot"] != after["cot"]:
            actual_changed.add(before["id"])
            assert after["cot"].strip(), f"empty rewritten cot for {before['id']}"
            assert "Step 1:" in after["cot"], f"missing Step 1 for {before['id']}"
            final = final_answer_text(after)
            assert final in after["cot"], f"final answer not present in cot for {before['id']}"
            assert "for aStep" not in after["cot"], f"broken concatenation remains for {before['id']}"

    assert actual_changed == changed_ids, "changed IDs do not match selection"
    missing_forced = FORCED_IDS - actual_changed
    assert not missing_forced, f"forced spot-check IDs were not rewritten: {sorted(missing_forced)}"
    assert "DDT131" not in actual_changed, "DDT131 should remain unchanged"


def build(source: Path, output: Path) -> dict[str, object]:
    rows = load_rows(source)
    if not rows:
        raise RuntimeError(f"No rows loaded from {source}")
    fieldnames = list(rows[0].keys())
    selected_by_topic = select_rows(rows)
    selected_ids = {sample_id for ids in selected_by_topic.values() for sample_id in ids}

    reason_map: dict[str, list[str]] = {}
    for row in rows:
        _, reasons = row_score(row)
        reason_map[row["id"]] = reasons

    rewritten: list[dict[str, str]] = []
    for row in rows:
        new_row = dict(row)
        if row["id"] in selected_ids:
            new_row["cot"] = build_rewrite(row, reason_map.get(row["id"], []))
        rewritten.append(new_row)

    validate(rows, rewritten, fieldnames, selected_ids)
    write_rows(output, rewritten, fieldnames)

    changed_counts = Counter(topic_prefix(sample_id) for sample_id in selected_ids)
    return {
        "source": str(source),
        "output": str(output),
        "total_rows": len(rows),
        "changed_total": len(selected_ids),
        "changed_by_topic": dict(sorted(changed_counts.items())),
        "topic_counts": dict(sorted(Counter(topic_prefix(row["id"]) for row in rows).items())),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build dataset_2/physic_version_2.csv with CoT-only rewrites.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build(args.source, args.output)
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

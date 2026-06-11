"""
Shared lightweight fact extraction for physics routing, hints, and RAG rerank.

This module intentionally stays deterministic and conservative. It extracts
facts that are explicit in the problem text or follow from simple distance
relations, then lets downstream modules use those facts as hard constraints.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field


def _to_meters(value: float, unit: str) -> float:
    unit = unit.lower()
    if unit == "cm":
        return value / 100.0
    if unit == "mm":
        return value / 1000.0
    return value


def _close(a: float, b: float, rel_tol: float = 1e-3, abs_tol: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


@dataclass
class ProblemFacts:
    question: str
    requested_quantity: str = ""
    distances_m: dict[str, float] = field(default_factory=dict)
    symbolic_distances: dict[str, str] = field(default_factory=dict)
    charge_signs: dict[str, int] = field(default_factory=dict)
    charge_magnitudes: dict[str, float] = field(default_factory=dict)
    same_sign_sources: bool | None = None
    opposite_sign_sources: bool | None = None
    has_test_charge: bool = False
    asks_force: bool = False
    asks_field: bool = False
    asks_zero_field: bool = False
    asks_symbolic: bool = False
    mentions_perpendicular_bisector: bool = False
    midpoint_points: list[str] = field(default_factory=list)
    collinear_facts: list[str] = field(default_factory=list)
    right_triangle_facts: list[str] = field(default_factory=list)
    isosceles_triangle_facts: list[str] = field(default_factory=list)
    equilateral_triangle_facts: list[str] = field(default_factory=list)
    perpendicular_bisector_h: float | None = None
    square_center: bool = False
    square_mixed_sign: bool = False
    zero_field_region: str = ""
    requested_distance_from: str = ""

    @property
    def has_midpoint(self) -> bool:
        return bool(self.midpoint_points)

    @property
    def has_collinear(self) -> bool:
        return bool(self.collinear_facts)

    @property
    def has_right_triangle(self) -> bool:
        return bool(self.right_triangle_facts)


def _store_distance(distances: dict[str, float], name: str, value_m: float) -> None:
    name = name.upper()
    distances[name] = value_m
    distances[name[::-1]] = value_m


def _distance(distances: dict[str, float], name: str) -> float | None:
    name = name.upper()
    return distances.get(name, distances.get(name[::-1]))


def _extract_distances(question: str) -> tuple[dict[str, float], dict[str, str]]:
    distances: dict[str, float] = {}
    symbolic: dict[str, str] = {}

    # Chained equality: "MA = MB = 5 cm", "AC = BC = 8 cm".
    chain = re.compile(
        r"\b([A-Z]{2})\s*=\s*([A-Z]{2})\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\b",
        re.IGNORECASE,
    )
    for first, second, value, unit in chain.findall(question):
        value_m = _to_meters(float(value), unit)
        _store_distance(distances, first, value_m)
        _store_distance(distances, second, value_m)

    # Standard numeric equality: "AB = 5 cm".
    for name, value, unit in re.findall(
        r"\b([A-Z]{2})\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\b",
        question,
        re.IGNORECASE,
    ):
        _store_distance(distances, name, _to_meters(float(value), unit))

    # Symbolic equality: "AB = 2a", "AB = 2a (m)".
    for name, expr in re.findall(
        r"\b([A-Z]{2})\s*=\s*([0-9]*\.?[0-9]*\s*[a-z])\b",
        question,
        re.IGNORECASE,
    ):
        symbolic[name.upper()] = re.sub(r"\s+", "", expr.lower())

    patterns = [
        r"\b([A-Z])\s+and\s+([A-Z])\b[^.]{0,100}?(?:separated by|are|,)\s*([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\s*apart",
        r"points\s+([A-Z])\s+and\s+([A-Z])[^.]{0,100}?([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\s*apart",
        r"\b([A-Z])\s+and\s+([A-Z])\s+are\s+separated\s+by\s+([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, question, re.IGNORECASE)
        if match:
            a, b, value, unit = match.groups()
            _store_distance(distances, f"{a}{b}", _to_meters(float(value), unit))

    generic = re.search(
        r"(?:separated by|located)\s+([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)",
        question,
        re.IGNORECASE,
    )
    if generic and "AB" not in distances:
        _store_distance(distances, "AB", _to_meters(float(generic.group(1)), generic.group(2)))

    generic_apart = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\s*apart", question, re.IGNORECASE)
    if generic_apart and "AB" not in distances:
        _store_distance(distances, "AB", _to_meters(float(generic_apart.group(1)), generic_apart.group(2)))

    return distances, symbolic


def _extract_charges(question: str) -> tuple[dict[str, int], dict[str, float], bool]:
    signs: dict[str, int] = {}
    magnitudes: dict[str, float] = {}

    for name, raw in re.findall(
        r"\b(q[123])\s*=\s*([+-]?\s*[0-9]+(?:\.[0-9]+)?(?:\s*(?:x|×)\s*10\^?[-+]?\d+)?)",
        question,
        re.IGNORECASE,
    ):
        cleaned = raw.replace("×", "x").replace(" ", "")
        sign = -1 if cleaned.startswith("-") else 1
        signs[name.lower()] = sign
        try:
            value = re.sub(r"x10\^?([-+]?\d+)", r"e\1", cleaned, flags=re.IGNORECASE)
            magnitudes[name.lower()] = abs(float(value))
        except ValueError:
            pass

    for name, _factor, _base in re.findall(r"\b(q[12])\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*q([12])\b", question, re.IGNORECASE):
        signs.setdefault(name.lower(), 1)

    compact = question.replace(" ", "").lower()
    if "q1=q2" in compact:
        if "q1" not in signs:
            signs["q1"] = 1
        if "q2" not in signs:
            signs["q2"] = signs.get("q1", 1)
    if "q1=-q2" in compact or "q2=-q1" in compact:
        signs["q1"] = 1
        signs["q2"] = -1

    has_test_charge = "q3" in question.lower() or "test charge" in question.lower() or "third charge" in question.lower()
    return signs, magnitudes, has_test_charge


def _requested_quantity(question: str) -> str:
    q = question.lower()
    if any(term in q for term in ["field strength is zero", "net electric field is zero", "where the net electric field", "find point m where", "point where"]):
        return "zero_field_location"
    if "electric field is zero" in q or "field is zero" in q:
        return "zero_field_location"
    if "force" in q or "acting on" in q:
        return "force"
    if any(term in q for term in ["electric field", "field strength", "resultant field", "net field"]):
        return "field"
    if "potential" in q or "voltage" in q:
        return "potential"
    return ""


def _requested_distance_from(question: str) -> str:
    q = question.lower()
    for point in ["a", "b", "o"]:
        if f"distance {point}m" in q or f"distance from {point.upper()}" in question or f"calculate {point.upper()}M" in question:
            return point.upper()
    match = re.search(r"\b(calculate|find)(?:\s+the)?(?:\s+distance)?\s+([ABOM])M\b", question, re.IGNORECASE)
    if match:
        return match.group(2).upper()
    if "coordinate" in q or "ox axis" in q:
        return "O"
    return ""


def _derive_geometry(facts: ProblemFacts) -> None:
    distances = facts.distances_m

    for base, first, second in [
        ("AB", "AM", "MB"),
        ("AB", "MA", "MB"),
        ("AB", "AN", "NB"),
        ("AB", "NA", "NB"),
        ("AC", "AB", "BC"),
        ("AC", "AB", "CB"),
        ("CA", "AB", "BC"),
    ]:
        d_base = _distance(distances, base)
        d_first = _distance(distances, first)
        d_second = _distance(distances, second)
        if d_base is None or d_first is None or d_second is None:
            continue
        if _close(d_first + d_second, d_base):
            shared = set(first) & set(second)
            middle = next(iter(shared), "")
            facts.collinear_facts.append(
                f"{first} + {second} = {base}; points are collinear"
                + (f" and {middle} lies between {base[0]} and {base[1]}" if middle else "")
            )
        if _close(d_first, d_second) and _close(d_base, 2 * d_first):
            shared = set(first) & set(second)
            midpoint = next(iter(shared), "")
            if midpoint:
                facts.midpoint_points.append(midpoint)

    for triple in [("AB", "AC", "BC"), ("AB", "CA", "CB"), ("AB", "AM", "BM"), ("AB", "MA", "MB"), ("AB", "AN", "NB"), ("AB", "NA", "NB")]:
        values = [(name, _distance(distances, name)) for name in triple]
        if any(value is None for _, value in values):
            continue
        sorted_sides = sorted([(name, float(value)) for name, value in values], key=lambda item: item[1])
        (s1n, s1), (s2n, s2), (s3n, s3) = sorted_sides
        if _close(s1 + s2, s3):
            shared = set(s1n) & set(s2n)
            endpoints = set(s3n)
            middle = next(iter(shared - endpoints), next(iter(shared), ""))
            fact = (
                f"{s1n} + {s2n} = {s3n}; points are collinear"
                + (f" and {middle} lies between {s3n[0]} and {s3n[1]}" if middle else "")
            )
            facts.collinear_facts.append(fact)

    for sides in [("AB", "AC", "BC"), ("AB", "CA", "CB"), ("AB", "AC", "CB")]:
        values = [(name, _distance(distances, name)) for name in sides]
        if any(value is None for _, value in values):
            continue
        sorted_sides = sorted([(name, float(value)) for name, value in values], key=lambda item: item[1])
        (s1n, s1), (s2n, s2), (s3n, s3) = sorted_sides
        if _close(s1**2 + s2**2, s3**2):
            all_points = set(s1n + s2n + s3n)
            right_vertex = next(iter(all_points - set(s3n)), "")
            facts.right_triangle_facts.append(
                f"{s1n}^2 + {s2n}^2 = {s3n}^2; triangle is right-angled at {right_vertex}"
            )

    for base, p1, p2 in [("AB", "AC", "BC"), ("AB", "AM", "BM"), ("AB", "AN", "BN")]:
        d_base = _distance(distances, base)
        d_1 = _distance(distances, p1)
        d_2 = _distance(distances, p2)
        if d_base is None or d_1 is None or d_2 is None:
            continue
            
        if _close(d_1, d_2) and _close(d_1, d_base):
            facts.equilateral_triangle_facts.append(f"{p1} = {p2} = {base} = {d_base}; triangle is equilateral")
            facts.perpendicular_bisector_h = d_1 * math.sqrt(3) / 2
            facts.mentions_perpendicular_bisector = True
        elif _close(d_1, d_2):
            is_right = _close(d_1**2 + d_2**2, d_base**2)
            if not is_right and not _close(d_1 + d_2, d_base):
                facts.isosceles_triangle_facts.append(f"{p1} = {p2} = {d_1}; triangle is isosceles")
                h_sq = d_1**2 - (d_base/2)**2
                if h_sq > 0:
                    facts.perpendicular_bisector_h = math.sqrt(h_sq)
                    facts.mentions_perpendicular_bisector = True

    q = facts.question.lower()
    facts.midpoint_points = list(dict.fromkeys(facts.midpoint_points))
    facts.collinear_facts = list(dict.fromkeys(facts.collinear_facts))
    facts.right_triangle_facts = list(dict.fromkeys(facts.right_triangle_facts))
    facts.isosceles_triangle_facts = list(dict.fromkeys(facts.isosceles_triangle_facts))
    facts.equilateral_triangle_facts = list(dict.fromkeys(facts.equilateral_triangle_facts))
    facts.mentions_perpendicular_bisector = facts.mentions_perpendicular_bisector or "perpendicular bisector" in q
    facts.square_center = "square" in q and any(term in q for term in ["intersection", "center", "centre", "diagonals"])
    if facts.square_center:
        facts.square_mixed_sign = (
            ("positive" in q and "negative" in q)
            or ("+q" in q and "-q" in q)
        )


def analyze_problem(question: str) -> ProblemFacts:
    facts = ProblemFacts(question=question)
    facts.distances_m, facts.symbolic_distances = _extract_distances(question)
    facts.charge_signs, facts.charge_magnitudes, facts.has_test_charge = _extract_charges(question)
    facts.requested_quantity = _requested_quantity(question)
    facts.asks_force = facts.requested_quantity == "force"
    facts.asks_field = facts.requested_quantity == "field"
    facts.asks_zero_field = facts.requested_quantity == "zero_field_location"
    facts.requested_distance_from = _requested_distance_from(question)

    q = question.lower()
    facts.asks_symbolic = bool(facts.symbolic_distances) or any(
        re.search(pattern, q)
        for pattern in [
            r"\bq1\s*=\s*q2\s*=\s*q\b",
            r"\bmagnitude\s+q\b",
            r"\bside\s+length\s+a\b",
            r"\bdistance\s+h\b",
            r"\bab\s*=\s*2a\b",
        ]
    )

    source_signs = [facts.charge_signs.get("q1"), facts.charge_signs.get("q2")]
    if all(sign is not None for sign in source_signs):
        facts.same_sign_sources = source_signs[0] == source_signs[1]
        facts.opposite_sign_sources = source_signs[0] != source_signs[1]
    elif "same sign" in q or "q1 = q2" in q.replace(" ", ""):
        facts.same_sign_sources = True
        facts.opposite_sign_sources = False
    elif "opposite sign" in q:
        facts.same_sign_sources = False
        facts.opposite_sign_sources = True

    if facts.asks_zero_field:
        if facts.same_sign_sources:
            facts.zero_field_region = "between"
        elif facts.opposite_sign_sources:
            facts.zero_field_region = "outside"

    _derive_geometry(facts)
    return facts

"""
Topic hints for Coulomb Force & Electric Field — prefix LD.

Covers ALL 397 LD questions:
  LD001-LD050  : Coulomb force on charges (collinear, triangle, special configs)
  LD051-LD100  : Electric field strength at a point (midpoint, perpendicular bisector, etc.)

The hints are deterministic geometry/direction facts extracted from the question
text so the LLM does not have to infer them.
"""
import math
import re
from typing import List

from app.modules.problem_facts import ProblemFacts, analyze_problem


def _to_meters(value: float, unit: str) -> float:
    unit = unit.lower()
    if unit == "cm":
        return value / 100.0
    if unit == "mm":
        return value / 1000.0
    return value


def _close(a: float, b: float, rel_tol: float = 1e-3, abs_tol: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)


def _extract_distances(question: str) -> dict[str, float]:
    """Extract named distances like AB = 5 cm, CA = 3 cm."""
    distances: dict[str, float] = {}
    # Standard: AB = 5 cm
    for name, value, unit in re.findall(
        r"\b([A-Z]{2})\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\b", question, re.IGNORECASE
    ):
        distances[name.upper()] = _to_meters(float(value), unit)

    # "A and B ... 8 cm apart"
    m = re.search(
        r"\b([A-Z])\s+and\s+([A-Z])\b[^.]{0,80}?"
        r"(?:separated by|are|,)\s*([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\s*apart",
        question, re.IGNORECASE,
    )
    if m:
        a, b, val, unit = m.groups()
        distances[f"{a.upper()}{b.upper()}"] = _to_meters(float(val), unit)

    m = re.search(
        r"points\s+([A-Z])\s+and\s+([A-Z])[^.]{0,80}?"
        r"([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\s*apart",
        question, re.IGNORECASE,
    )
    if m:
        a, b, val, unit = m.groups()
        distances[f"{a.upper()}{b.upper()}"] = _to_meters(float(val), unit)

    m = re.search(
        r"\b([A-Z])\s+and\s+([A-Z])\s+are\s+separated\s+by\s+"
        r"([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\b",
        question, re.IGNORECASE,
    )
    if m:
        a, b, val, unit = m.groups()
        distances[f"{a.upper()}{b.upper()}"] = _to_meters(float(val), unit)

    # "separated by 10 cm" (generic two-charge)
    m = re.search(
        r"separated\s+by\s+([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)",
        question, re.IGNORECASE,
    )
    if m and "AB" not in distances:
        distances["AB"] = _to_meters(float(m.group(1)), m.group(2))

    # "X cm apart" (generic)
    m = re.search(
        r"([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\s*apart",
        question, re.IGNORECASE,
    )
    if m and "AB" not in distances:
        distances["AB"] = _to_meters(float(m.group(1)), m.group(2))

    return distances


def _dist(distances: dict[str, float], name: str) -> float | None:
    name = name.upper()
    return distances.get(name, distances.get(name[::-1]))


# ─── Geometry detection ─────────────────────────────────────────────

def _detect_right_triangle(question: str, distances: dict) -> List[str]:
    """Detect right-angled triangle from explicit text or Pythagoras check."""
    hints = []

    # Explicit "right-angled at X"
    m = re.search(
        r"right[- ]angled\s+(?:triangle\s+)?([A-Z]{3})\s*"
        r"\(right[- ]angled\s+at\s+([A-Z])\)",
        question, re.IGNORECASE,
    )
    if not m:
        m = re.search(
            r"triangle\s+([A-Z]{3})\s+is\s+right[- ]angled\s+at\s+([A-Z])",
            question, re.IGNORECASE,
        )
    if m:
        vertices, vertex = m.groups()
        vertices = vertices.upper()
        vertex = vertex.upper()
        others = [v for v in vertices if v != vertex]
        if len(others) == 2:
            side1 = vertex + others[0]
            side2 = vertex + others[1]
            hyp = others[0] + others[1]
            d1 = _dist(distances, side1)
            d2 = _dist(distances, side2)
            d_hyp = _dist(distances, hyp)
            hints.append(
                f"Geometry: triangle {vertices} is right-angled at {vertex}; "
                f"{hyp} is the hypotenuse."
            )
            if d_hyp and d1 and not d2:
                missing = math.sqrt(max(d_hyp**2 - d1**2, 0.0))
                hints.append(f"Geometry: {side2} = sqrt({hyp}² - {side1}²) = {missing:.6g} m.")
            elif d_hyp and d2 and not d1:
                missing = math.sqrt(max(d_hyp**2 - d2**2, 0.0))
                hints.append(f"Geometry: {side1} = sqrt({hyp}² - {side2}²) = {missing:.6g} m.")
            hints.append(
                f"Geometry: force/field vectors along {side1} and {side2} are "
                f"perpendicular (90°) at {vertex}."
            )
            return hints

    # Implicit: check Pythagoras for any triple of distances
    triples = [("AB", "AC", "BC"), ("AB", "AM", "BM"), ("CA", "CB", "AB"),
               ("MA", "MB", "AB"), ("AB", "AH", "BH"), ("AC", "AH", "CH"),
               ("NA", "NB", "AB")]
    for a, b, c in triples:
        d1 = _dist(distances, a)
        d2 = _dist(distances, b)
        d3 = _dist(distances, c)
        if d1 is None or d2 is None or d3 is None:
            continue
        sides = sorted([(a, d1), (b, d2), (c, d3)], key=lambda x: x[1])
        (s1n, s1), (s2n, s2), (s3n, s3) = sides
        if _close(s1**2 + s2**2, s3**2):
            all_pts = set(s1n + s2n + s3n)
            opp_pts = set(s3n)
            right_v = next(iter(all_pts - opp_pts), "?")
            hints.append(
                f"Geometry: {s1n}² + {s2n}² = {s3n}², so the triangle is "
                f"right-angled at {right_v}; vectors through {right_v} are "
                f"perpendicular (use Pythagoras for resultant)."
            )
        elif _close(s1 + s2, s3):
            shared = set(s1n) & set(s2n)
            endpoints = set(s3n)
            if shared and not shared & endpoints:
                mid = next(iter(shared))
                hints.append(
                    f"Geometry: {s1n} + {s2n} = {s3n}, so the points are "
                    f"COLLINEAR and {mid} lies between {s3n[0]} and {s3n[1]}."
                )
            else:
                hints.append(
                    f"Geometry: {s1n} + {s2n} = {s3n}, so the three points "
                    f"are COLLINEAR."
                )
    return hints


def _detect_equilateral(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if "equilateral triangle" in q or "equilateral" in q:
        hints.append(
            "Geometry: equilateral triangle — all sides equal, "
            "each angle = 60°."
        )
        hints.append(
            "Geometry: for two EQUAL-magnitude forces at one vertex of an "
            "equilateral triangle with angle 60° between them: "
            "F_net = sqrt(F1² + F2² + 2·F1·F2·cos(60°)). "
            "If F1 = F2 = F, then F_net = F·sqrt(3)."
        )
        hints.append(
            "Geometry: distance from each vertex to the CENTER of an "
            "equilateral triangle with side a is r = a / sqrt(3)."
        )
    return hints


def _detect_isosceles_right(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if "isosceles right" in q or ("isosceles" in q and "right" in q):
        hints.append(
            "Geometry: isosceles right triangle — two equal legs at 90°, "
            "hypotenuse = leg × sqrt(2). "
            "Two forces along the legs combine as F_net = sqrt(F1² + F2²)."
        )
    return hints


def _detect_square(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if "square" in q:
        hints.append(
            "Geometry: square ABCD with side a — diagonal = a·sqrt(2), "
            "distance from vertex to centre = a·sqrt(2)/2."
        )
        if "center" in q or "centre" in q or "intersection" in q:
            hints.append(
                "Geometry: if identical charges are at all 4 vertices, "
                "the field/force at the centre is ZERO by symmetry."
            )
    return hints


def _detect_perpendicular_bisector(question: str, distances: dict) -> List[str]:
    hints = []
    q = question.lower()
    if "perpendicular bisector" not in q:
        return hints

    base_m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\s+apart", question, re.IGNORECASE)
    height_m = re.search(
        r"perpendicular bisector[^.]{0,120}?([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)"
        r"\s+(?:away|from)",
        question, re.IGNORECASE,
    )
    if base_m and height_m:
        base = _to_meters(float(base_m.group(1)), base_m.group(2))
        height = _to_meters(float(height_m.group(1)), height_m.group(2))
        half = base / 2.0
        r = math.sqrt(half**2 + height**2)
        hints.append(
            f"Geometry: point on perpendicular bisector — distance to each "
            f"charge r = sqrt((AB/2)² + h²) = sqrt({half:.6g}² + {height:.6g}²) "
            f"= {r:.6g} m."
        )
        hints.append(
            "Geometry: decompose each force/field into components along AB "
            "and along the bisector; by symmetry some components cancel "
            "and others add."
        )
    return hints


def _detect_midpoint(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if "midpoint" in q or "mid-point" in q or "middle" in q:
        hints.append(
            "Geometry: test charge/point at the MIDPOINT — distances to "
            "both source charges are equal (= AB/2)."
        )
        hints.append(
            "Geometry: at midpoint between two EQUAL same-sign charges, "
            "fields/forces cancel → net = 0. "
            "Between two EQUAL opposite-sign charges, fields/forces ADD."
        )
    return hints


# ─── Force / Field direction ────────────────────────────────────────

def _detect_force_direction(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if "force" in q or "acting on" in q:
        hints.append(
            "HARD VECTOR LOGIC: Same-sign charges REPEL (force pushes away); "
            "opposite-sign charges ATTRACT (force pulls toward source)."
        )
        hints.append(
            "HARD FORCE COMPUTATION: first compute the net electric field from source charges by vector components, "
            "then compute force on the target charge with F_vector = q_target * E_net. "
            "If q_target is negative, the force direction is opposite to E_net; the requested magnitude is |q_target|*|E_net|."
        )
        hints.append(
            "HARD SUPERPOSITION (COLLINEAR): if both vectors point in the SAME direction "
            "→ F_net = F1 + F2. If OPPOSITE directions → F_net = |F1 − F2|."
        )
    if "electric field" in q or "field strength" in q or "cường độ" in q:
        hints.append(
            "HARD VECTOR LOGIC: Electric field from a POSITIVE charge points AWAY from it; "
            "Electric field from a NEGATIVE charge points TOWARD it."
        )
        hints.append(
            "HARD SUPERPOSITION: If two vectors point in SAME direction, ADD them (E_net = E1 + E2). "
            "If OPPOSITE direction, SUBTRACT them (E_net = |E1 - E2|). "
            "If at an angle, use VECTOR ADDITION."
        )
        hints.append(
            "HARD FIELD COMPUTATION: assign coordinates and compute Ex,Ey in Python with "
            "E_i = k*q_i*(target-source)/r_i^3; do not decide signs from prose alone."
        )
    return hints


def _detect_symmetry_zero(question: str) -> List[str]:
    """Detect problems where symmetry gives F=0 or E=0."""
    hints = []
    q = question.lower()
    # Identical charges at all vertices of equilateral triangle + center
    if ("center" in q or "centre" in q) and "equilateral" in q:
        hints.append(
            "Symmetry: three IDENTICAL charges at equilateral triangle vertices "
            "→ net field/force at centre = 0 (120° symmetry cancellation)."
        )
    # Identical charges at midpoint
    if ("midpoint" in q or "mid-point" in q) and "q1 = q2" in q.replace(" ", ""):
        hints.append(
            "Symmetry: two identical charges with test at midpoint → "
            "equal and opposite forces/fields → net = 0."
        )
    return hints


# ─── Main entry point ───────────────────────────────────────────────

def _detect_shared_facts(facts: ProblemFacts) -> List[str]:
    """Convert shared deterministic facts into hard prompt constraints."""
    hints: List[str] = []

    for point in facts.midpoint_points:
        hints.append(
            f"HARD GEOMETRY: point {point} is the midpoint between the two source charges because its distances to both endpoints are equal and each equals half the source separation."
        )
        if facts.same_sign_sources and (facts.asks_field or facts.asks_zero_field):
            hints.append(
                "HARD SYMMETRY: at the midpoint between two equal same-sign source charges, the net electric field is 0 because equal field vectors point in opposite directions."
            )

    for fact in facts.collinear_facts:
        hints.append(f"HARD GEOMETRY: {fact}. Use signed one-dimensional components, not perpendicular-bisector formulas.")

    for fact in facts.right_triangle_facts:
        hints.append(
            f"HARD GEOMETRY: {fact}. Combine perpendicular field/force components with sqrt(component1^2 + component2^2)."
        )

    for fact in facts.isosceles_triangle_facts:
        hints.append(
            f"HARD GEOMETRY: {fact}. The point lies on the perpendicular bisector. Combine vectors using projection (cosine)."
        )

    for fact in facts.equilateral_triangle_facts:
        hints.append(
            f"HARD GEOMETRY: {fact}. The angle is 60 degrees. Combine equal vectors using E_net = E1 * sqrt(3) if angle is 60 (repulsion) or E_net = E1 if angle is 120 (attraction)."
        )

    if facts.perpendicular_bisector_h is not None:
        hints.append(
            f"HARD GEOMETRY: The calculated distance from the point to the midpoint of the base is h = {facts.perpendicular_bisector_h:.6g} m. Use this to find the projection cosine."
        )

    if facts.mentions_perpendicular_bisector:
        hints.append(
            "HARD GEOMETRY: the problem explicitly states perpendicular bisector; use r = sqrt((AB/2)^2 + h^2) and decompose components."
        )

    if facts.asks_zero_field:
        hints.append("HARD INTENT: the question asks where electric field E is zero; do not use electric potential V=0 formulas.")
        if facts.zero_field_region == "between":
            hints.append(
                "HARD ZERO-FIELD REGION: for same-sign source charges, the E=0 point lies between the charges. "
                "Solve the equation: sqrt(|q1|)/x = sqrt(|q2|)/(d - x) where d is the distance between charges and x is the distance from q1."
            )
        elif facts.zero_field_region == "outside":
            hints.append(
                "HARD ZERO-FIELD REGION: for opposite-sign source charges, the E=0 point lies outside the segment, closer to the charge with smaller absolute magnitude. "
                "Solve the equation: sqrt(|q1|)/x = sqrt(|q2|)/(x + d) where x is the distance from q1, assuming |q1| < |q2|."
            )
        if facts.requested_distance_from:
            hints.append(f"HARD OUTPUT TARGET: return the distance/coordinate measured from {facts.requested_distance_from}, not from the other source charge.")

    if facts.square_center:
        hints.append(
            "HARD GEOMETRY: at a square center, distance to each vertex is a*sqrt(2)/2 and all four field vectors must be summed by components."
        )
        if facts.square_mixed_sign:
            hints.append(
                "HARD SQUARE SIGN CHECK: mixed positive and negative charges at square vertices do not automatically cancel; identical opposite vertices can cancel only when their vector directions are opposite."
            )

    if facts.asks_symbolic:
        hints.append(
            "HARD SYMBOLIC: the problem contains symbolic quantities. Do not substitute a=1, q=1, h=1, or any placeholder number; return a string expression in the given symbols."
        )

    return hints


def analyze(question: str, facts: ProblemFacts | None = None) -> List[str]:
    """Return all applicable Coulomb/E-field hints for the question."""
    facts = facts or analyze_problem(question)
    distances = _extract_distances(question)
    hints: List[str] = []

    hints.extend(_detect_shared_facts(facts))
    hints.extend(_detect_right_triangle(question, distances))
    hints.extend(_detect_equilateral(question))
    hints.extend(_detect_isosceles_right(question))
    hints.extend(_detect_square(question))
    hints.extend(_detect_perpendicular_bisector(question, distances))
    hints.extend(_detect_midpoint(question))
    hints.extend(_detect_force_direction(question))
    hints.extend(_detect_symmetry_zero(question))

    return list(dict.fromkeys(hints))

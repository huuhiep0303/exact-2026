"""
DEPRECATED: deterministic geometry hints for electrostatics vector problems.

This module is retained for reference only. The active pipeline uses
`app.hints.hint_coulomb_force_LD` through `app.hints.get_topic_hints`.
"""
import math
import re


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
    """Extract named distances such as AB = 5 cm, CA = 3 cm, MA = 4 cm."""
    distances: dict[str, float] = {}
    pattern = re.compile(r"\b([A-Z]{2})\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\b", re.IGNORECASE)
    for name, value, unit in pattern.findall(question):
        distances[name.upper()] = _to_meters(float(value), unit)

    separated = re.search(
        r"\b([A-Z])\s+and\s+([A-Z])\b[^.]{0,80}?(?:separated by|are|which are|,)\s*([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\s+apart",
        question,
        re.IGNORECASE,
    )
    if separated:
        a, b, value, unit = separated.groups()
        distances[f"{a.upper()}{b.upper()}"] = _to_meters(float(value), unit)

    placed_at = re.search(
        r"points\s+([A-Z])\s+and\s+([A-Z])[^.]{0,80}?([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\s+apart",
        question,
        re.IGNORECASE,
    )
    if placed_at:
        a, b, value, unit = placed_at.groups()
        distances[f"{a.upper()}{b.upper()}"] = _to_meters(float(value), unit)

    separated_by = re.search(
        r"\b([A-Z])\s+and\s+([A-Z])\s+are\s+separated\s+by\s+([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\b",
        question,
        re.IGNORECASE,
    )
    if separated_by:
        a, b, value, unit = separated_by.groups()
        distances[f"{a.upper()}{b.upper()}"] = _to_meters(float(value), unit)

    return distances


def _distance(distances: dict[str, float], name: str) -> float | None:
    name = name.upper()
    reverse = name[::-1]
    return distances.get(name, distances.get(reverse))


def analyze_geometry(question: str, topic: str = "general") -> list[str]:
    """Return geometry hints that should be treated as hard constraints."""
    if topic != "coulomb_force":
        return []

    q = question.lower()
    distances = _extract_distances(question)
    hints: list[str] = []

    # Right triangle: "right-angled at A" means the two sides meeting at A are
    # perpendicular and the side opposite A is the hypotenuse.
    right_match = re.search(r"right[- ]angled\s+(?:triangle\s+)?([A-Z]{3})\s*\(right[- ]angled\s+at\s+([A-Z])\)", question, re.IGNORECASE)
    if right_match:
        vertices, vertex = right_match.groups()
        vertices = vertices.upper()
        vertex = vertex.upper()
        others = [v for v in vertices if v != vertex]
        if len(others) == 2:
            side1 = "".join(sorted(vertex + others[0]))
            side2 = "".join(sorted(vertex + others[1]))
            hyp = "".join(sorted(others[0] + others[1]))
            d_side1 = _distance(distances, side1)
            d_side2 = _distance(distances, side2)
            d_hyp = _distance(distances, hyp)
            hints.append(
                f"Geometry: triangle {vertices} is right-angled at {vertex}; the sides through {vertex} are perpendicular and {hyp} is the hypotenuse."
            )
            if d_hyp is not None and d_side1 is not None and d_side2 is None:
                missing = math.sqrt(max(d_hyp**2 - d_side1**2, 0.0))
                hints.append(f"Geometry: {side2} = sqrt({hyp}^2 - {side1}^2) = {missing:.6g} m.")
            elif d_hyp is not None and d_side2 is not None and d_side1 is None:
                missing = math.sqrt(max(d_hyp**2 - d_side2**2, 0.0))
                hints.append(f"Geometry: {side1} = sqrt({hyp}^2 - {side2}^2) = {missing:.6g} m.")
            hints.append(f"Geometry: force vectors along {side1} and {side2} form a 90 degree angle when acting at {vertex}.")

    # Generic triangle side check: AB, AC/CA, BC/CB can reveal collinear or
    # right-angle geometry even when the text does not explicitly say so.
    for a, b, c in [("AB", "AC", "BC"), ("AB", "AM", "BM")]:
        d1 = _distance(distances, a)
        d2 = _distance(distances, b)
        d3 = _distance(distances, c)
        if d1 is None or d2 is None or d3 is None:
            continue
        sides = sorted([(a, d1), (b, d2), (c, d3)], key=lambda item: item[1])
        (s1_name, s1), (s2_name, s2), (s3_name, s3) = sides
        if _close(s1 + s2, s3):
            shared = set(s1_name).intersection(s2_name)
            endpoints = set(s3_name)
            if shared and not shared.intersection(endpoints):
                middle = next(iter(shared))
                hints.append(f"Geometry: {s1_name} + {s2_name} = {s3_name}, so the points are collinear and {middle} lies between {s3_name[0]} and {s3_name[1]}.")
            else:
                hints.append(f"Geometry: {s1_name} + {s2_name} = {s3_name}, so the three points are collinear.")
        elif _close(s1**2 + s2**2, s3**2):
            opposite = set(s3_name)
            all_points = set(s1_name + s2_name + s3_name)
            right_vertex = next(iter(all_points - opposite), "")
            hints.append(
                f"Geometry: {s1_name}^2 + {s2_name}^2 = {s3_name}^2, so the triangle is right-angled at {right_vertex}; the two force directions through that point are perpendicular."
            )

    if "equilateral triangle" in q:
        hints.append("Geometry: equilateral triangle means all sides are equal and each internal angle is 60 degrees.")
        hints.append("Geometry: two equal-magnitude repulsive forces at one vertex of an equilateral triangle combine to F_net = sqrt(3)*F.")

    if "perpendicular bisector" in q:
        base_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\s+apart", question, re.IGNORECASE)
        height_match = re.search(
            r"perpendicular bisector[^.]{0,120}?([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|m)\s+away",
            question,
            re.IGNORECASE,
        )
        if base_match and height_match:
            base = _to_meters(float(base_match.group(1)), base_match.group(2))
            height = _to_meters(float(height_match.group(1)), height_match.group(2))
            half_base = base / 2.0
            source_distance = math.sqrt(half_base**2 + height**2)
            hints.append(
                f"Geometry: point on perpendicular bisector has equal distances to both charges: r = sqrt((AB/2)^2 + h^2) = {source_distance:.6g} m."
            )
            hints.append(
                "Geometry: decompose each force into components along AB and the perpendicular bisector; use symmetry/signs to decide which components cancel or add."
            )

    return list(dict.fromkeys(hints))

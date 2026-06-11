"""
Topic hints for Electric Potential & Voltage — prefix DT.

Covers all 68 DT questions:
  - Potential from point charges (V = kq/r, scalar superposition)
  - Zero-potential point location
  - Voltage / potential difference
  - Work done by electric force
  - E-field from potential gradient
  - Symbolic / algebraic answers
"""
import math
import re
from typing import List


def _detect_scalar_superposition(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["potential", "điện thế", "thế năng", "v ="]):
        hints.append(
            "POTENTIAL IS SCALAR: V_total = V1 + V2 + ... "
            "(algebraic sum with signs, NOT vector addition)."
        )
        hints.append(
            "V = k·q/r — keep the SIGN of q (positive charge gives +V, "
            "negative charge gives −V)."
        )
    return hints


def _detect_zero_potential(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["v = 0", "potential is zero", "zero potential",
                               "điện thế bằng 0", "triệt tiêu"]):
        hints.append(
            "ZERO POTENTIAL: Set V_total = k·q1/r1 + k·q2/r2 = 0 "
            "→ q1/r1 = −q2/r2. Solve for the distance ratio."
        )
        hints.append(
            "For opposite-sign charges: there are TWO zero-potential points — "
            "one between the charges (internal) and one outside (external, "
            "on the side of the smaller |q|)."
        )
    return hints


def _detect_work_energy(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["work", "công", "energy", "năng lượng"]):
        hints.append(
            "Work by electric force: W = q·(V_A − V_B) = q·U_AB. "
            "Sign matters: positive work = charge moves in field direction."
        )
    return hints


def _detect_uniform_field(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["uniform field", "điện trường đều",
                               "parallel plates", "between the plates"]):
        hints.append(
            "Uniform E-field: E = U/d (voltage divided by plate separation). "
            "E points from high V to low V."
        )
    return hints


def _detect_symbolic_answer(question: str) -> List[str]:
    """If the question uses variables (a, q, k) instead of numbers."""
    hints = []
    # Check if question has algebraic variables as the main unknowns
    q = question.lower()
    if re.search(r"\bside\s+(?:length\s+)?['\"]?a['\"]?\b", q) or \
       re.search(r"\bside\s+a\s*=", q, re.IGNORECASE):
        pass  # has numeric value for a
    elif re.search(r"\bwith\s+side\s+(?:length\s+)?['\"]?a['\"]?\b", q):
        hints.append(
            "SYMBOLIC ANSWER: The question uses variable 'a' for side length. "
            "Express the answer in terms of a, k, q — do NOT substitute "
            "numeric values. Set answer to a string expression."
        )
    return hints


def _detect_geometry_dt(question: str) -> List[str]:
    """Detect geometry patterns specific to DT problems."""
    hints = []
    q = question.lower()

    if "perpendicular bisector" in q:
        hints.append(
            "Geometry: point on perpendicular bisector is equidistant from "
            "both charges. Use r = sqrt((AB/2)² + h²)."
        )
        hints.append(
            "For POTENTIAL on perpendicular bisector: if |q1| = |q2| and "
            "opposite signs → V = 0 everywhere on the bisector."
        )

    if "equilateral" in q:
        hints.append(
            "Geometry: equilateral triangle — all vertex-to-vertex distances "
            "are equal. The angle subtended at any vertex by the opposite "
            "side is 60°."
        )

    if "midpoint" in q or "mid-point" in q:
        hints.append(
            "At midpoint: r1 = r2 = AB/2. V = k·(q1+q2)/(AB/2). "
            "If q1 = −q2, V = 0."
        )
    return hints


def analyze(question: str) -> List[str]:
    """Return all applicable electric potential hints."""
    hints: List[str] = []
    hints.extend(_detect_scalar_superposition(question))
    hints.extend(_detect_zero_potential(question))
    hints.extend(_detect_work_energy(question))
    hints.extend(_detect_uniform_field(question))
    hints.extend(_detect_symbolic_answer(question))
    hints.extend(_detect_geometry_dt(question))
    return list(dict.fromkeys(hints))

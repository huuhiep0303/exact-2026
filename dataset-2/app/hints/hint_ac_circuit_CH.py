"""
Topic hints for AC/RLC Circuit — prefix CH.

Covers all 290 CH questions. CH already has 100% accuracy on the first 10,
so these hints are mainly reinforcement and edge-case coverage for the
remaining 280 questions.

Topics:
  - Impedance Z, reactances X_L and X_C
  - RMS current, voltage across components
  - Active power, reactive power, apparent power
  - Power factor, phase angle
  - Resonance detection and properties
"""
import re
from typing import List


def _detect_impedance(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["impedance", "tổng trở", " z "]):
        hints.append(
            "Impedance: Z = √(R² + (X_L − X_C)²). "
            "X_L = 2πfL = ωL, X_C = 1/(2πfC) = 1/(ωC)."
        )
    return hints


def _detect_power(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["power", "công suất"]):
        hints.append(
            "Active power: P = U·I·cos(φ) = I²·R = U_R²/R. "
            "Power factor: cos(φ) = R/Z. "
            "At resonance: P_max = U²/R."
        )
    return hints


def _detect_voltage_components(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["voltage across", "hiệu điện thế",
                               "u_r", "u_l", "u_c"]):
        hints.append(
            "Voltage across components: U_R = I·R, U_L = I·X_L, U_C = I·X_C. "
            "Total: U² = U_R² + (U_L − U_C)²."
        )
    return hints


def _detect_resonance(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["resonance", "cộng hưởng"]):
        hints.append(
            "At resonance: X_L = X_C → Z = R (minimum), "
            "I = U/R (maximum), cos(φ) = 1."
        )
    return hints


def _detect_phase(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["phase", "pha", "angle", "góc"]):
        hints.append(
            "Phase angle: tan(φ) = (X_L − X_C) / R. "
            "φ > 0 → inductive (U leads I), "
            "φ < 0 → capacitive (I leads U)."
        )
    return hints


def analyze(question: str) -> List[str]:
    """Return all applicable AC circuit hints."""
    hints: List[str] = []
    hints.extend(_detect_impedance(question))
    hints.extend(_detect_power(question))
    hints.extend(_detect_voltage_components(question))
    hints.extend(_detect_resonance(question))
    hints.extend(_detect_phase(question))
    return list(dict.fromkeys(hints))

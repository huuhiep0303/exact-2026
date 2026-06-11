"""
Topic hints for AC Circuit Resonance (Advanced) — prefix CHLT.

Covers all 20 CHLT questions:
  - Yes/No resonance determination
  - Resonant frequency calculation
  - Properties at resonance (Z_min, I_max, P_max)
  - Quality factor

CRITICAL: Most CHLT questions ask "Is the circuit at resonance?" → answer
must be "Yes" or "No" (not True/False, not a frequency value).
"""
import re
from typing import List


def _detect_yes_no_resonance(question: str) -> List[str]:
    """Detect Yes/No resonance questions."""
    hints = []
    q = question.lower()

    yes_no_kw = [
        "is it", "does it", "does the circuit", "is the circuit", "is this",
        "is the frequency", "is the given frequency", "is the operating frequency",
        "will resonance", "does resonance", "does electrical resonance",
        "resonate at", "the resonant frequency",
        "whether", "check if", "determine if", "verify",
        "có phải", "có cộng hưởng", "xảy ra cộng hưởng",
    ]

    resonance_kw = ["resonance", "resonant", "resonate", "cộng hưởng"]

    is_yes_no = any(kw in q for kw in yes_no_kw)
    is_resonance = any(kw in q for kw in resonance_kw)
    if not is_yes_no and is_resonance:
        is_yes_no = q.strip().startswith(("is ", "does ", "will ", "whether ", "check ", "verify "))

    if is_yes_no and is_resonance:
        hints.append(
            "ANSWER FORMAT: This is a YES/NO question about resonance. "
            "Your answer variable must be the STRING 'Yes' or 'No' "
            "(NOT True/False, NOT a number)."
        )
        hints.append(
            "RESONANCE CHECK METHOD:\n"
            "  1. Compute f0 = 1 / (2 * math.pi * math.sqrt(L * C))\n"
            "  2. Compare: if math.isclose(f_given, f0, rel_tol=0.02): "
            "answer = 'Yes' else: answer = 'No'\n"
            "  3. Set unit = '-' (dimensionless)."
        )
    return hints


def _detect_resonance_properties(question: str) -> List[str]:
    """General resonance property hints."""
    hints = []
    q = question.lower()

    if any(kw in q for kw in ["resonance", "resonant", "resonate", "cộng hưởng"]):
        hints.append(
            "Resonance condition: X_L = X_C, i.e. 2π·f·L = 1/(2π·f·C). "
            "At resonance: Z_min = R, I_max = U/R, P_max = U²/R, "
            "cos(φ) = 1."
        )
        hints.append(
            "Resonant frequency: f₀ = 1 / (2π√(LC))."
        )
    return hints


def analyze(question: str) -> List[str]:
    """Return all applicable CHLT hints."""
    hints: List[str] = []
    hints.extend(_detect_yes_no_resonance(question))
    hints.extend(_detect_resonance_properties(question))
    return list(dict.fromkeys(hints))

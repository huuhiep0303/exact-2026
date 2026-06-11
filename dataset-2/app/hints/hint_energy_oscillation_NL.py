"""
Topic hints for LC Oscillations & Electromagnetic Energy — prefix NL.

Covers all 190 NL questions:
  - Energy in capacitor (W_C = ½CU²) and inductor (W_L = ½LI²)
  - Total energy conservation (W_total = const in ideal LC)
  - Angular frequency, period, frequency of LC oscillation
  - Charge/current as function of time
  - Equal energy split (W_C = W_L)
  - Max charge, max current relationships
"""
import re
from typing import List


def _detect_energy_conservation(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["lc", "oscillation", "dao động",
                               "energy", "năng lượng"]):
        hints.append(
            "HARD RULE: LC ENERGY CONSERVATION. Total energy W_total is CONSTANT. "
            "Equation: W_total = 0.5 * C * U_max^2 = 0.5 * L * I_max^2 = 0.5 * C * u^2 + 0.5 * L * i^2. "
            "Use this exact equation to relate instantaneous values (u, i) with maximum values (U_max, I_max)."
        )
        hints.append(
            "Energy components: W_C = 0.5 * C * u^2 = q^2 / (2*C). W_L = 0.5 * L * i^2."
        )
    return hints


def _detect_equal_energy(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["equal", "bằng nhau", "w_c = w_l",
                               "half", "một nửa"]):
        if any(kw in q for kw in ["energy", "năng lượng"]):
            hints.append(
                "When W_C = W_L (equal energy split): "
                "U = U_max / √2, I = I_max / √2, "
                "and W_C = W_L = W_total / 2."
            )
    return hints


def _detect_oscillation_params(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["frequency", "period", "angular",
                               "tần số", "chu kỳ", "tần số góc", "omega"]):
        hints.append(
            "LC oscillation parameters: "
            "ω₀ = 1/√(LC), T = 2π√(LC), f = 1/(2π√(LC))."
        )
    return hints


def _detect_max_values(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["maximum", "max", "cực đại", "lớn nhất"]):
        hints.append(
            "Max values in LC: Q_max = C · U_max, "
            "I_max = ω₀ · Q_max = Q_max / √(LC). "
            "From energy: I_max = U_max · √(C/L)."
        )
    return hints


def _detect_time_function(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["at time", "tại thời điểm", "as a function",
                               "q(t)", "i(t)", "u(t)"]):
        hints.append(
            "Time functions: q(t) = Q_max · cos(ω₀t + φ), "
            "i(t) = −ω₀ · Q_max · sin(ω₀t + φ), "
            "u(t) = q(t) / C."
        )
    return hints


def _detect_energy_ratio(question: str) -> List[str]:
    """Detect problems asking for energy at a specific moment."""
    hints = []
    q = question.lower()
    if re.search(r"(energy|năng lượng).{0,30}(when|khi|at the moment|lúc)", q):
        hints.append(
            "At any moment: W_C + W_L = W_total. "
            "If W_C is known → W_L = W_total − W_C, and vice versa."
        )
    return hints


def analyze(question: str) -> List[str]:
    """Return all applicable LC oscillation hints."""
    hints: List[str] = []
    hints.extend(_detect_energy_conservation(question))
    hints.extend(_detect_equal_energy(question))
    hints.extend(_detect_oscillation_params(question))
    hints.extend(_detect_max_values(question))
    hints.extend(_detect_time_function(question))
    hints.extend(_detect_energy_ratio(question))
    return list(dict.fromkeys(hints))

"""
Topic hints for Measurement Errors — prefix THCB.

Covers all 80 THCB questions:
  - Absolute error, relative error, percentage error
  - Instrument error (= LCNS in Vietnamese standard)
  - Random error (max deviation from mean)
  - Error propagation for sum/diff, product/quotient, power
  - Common derived quantities (R=U/I, P=UI, ρ=m/V)
"""
import re
from typing import List


def _detect_instrument_error(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["instrument", "dụng cụ", "least count",
                               "smallest division", "độ chia nhỏ nhất",
                               "LCNS", "lcns"]):
        hints.append(
            "INSTRUMENT ERROR (Vietnamese standard): "
            "Δ_instrument = LCNS (the full least count of the instrument, "
            "NOT LCNS/2). For example, if the ruler has 1mm divisions, "
            "Δ_instrument = 1 mm = 0.001 m."
        )
    # Also trigger for common instruments
    if any(kw in q for kw in ["ammeter", "ampe kế", "voltmeter", "vôn kế",
                               "ruler", "thước", "thermometer", "nhiệt kế",
                               "scale", "cân"]):
        hints.append(
            "INSTRUMENT ERROR: Δ_instrument = LCNS (full least count). "
            "Read the smallest division from the problem statement."
        )
    return hints


def _detect_random_error(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["random error", "sai số ngẫu nhiên",
                               "measurement series", "chuỗi đo",
                               "multiple measurements", "nhiều lần đo",
                               "average", "trung bình"]):
        hints.append(
            "RANDOM ERROR (Vietnamese standard): "
            "Δ_random = max(|xᵢ − x̄|) — the MAXIMUM deviation from the "
            "mean, NOT the average deviation."
        )
        hints.append(
            "Mean value: x̄ = (x₁ + x₂ + ... + xₙ) / n. "
            "Total absolute error: Δx = max(Δ_random, Δ_instrument)."
        )
    return hints


def _detect_error_propagation(question: str) -> List[str]:
    hints = []
    q = question.lower()

    if any(kw in q for kw in ["error propagation", "sai số gián tiếp",
                               "relative error", "sai số tương đối",
                               "absolute error", "sai số tuyệt đối"]):
        hints.append(
            "ERROR PROPAGATION RULES:\n"
            "  • Sum/Diff: Z = X ± Y → ΔZ = ΔX + ΔY (absolute errors ADD)\n"
            "  • Product/Quotient: Z = X·Y or X/Y → δZ = δX + δY "
            "(RELATIVE errors add)\n"
            "  • Power: Z = Xⁿ → δZ = n · δX\n"
            "  • δ = Δ/|value| (relative = absolute / measured value)"
        )

    # Common derived quantities
    if any(kw in q for kw in ["r = u/i", "r=u/i", "resistance",
                               "điện trở"]) and "error" in q:
        hints.append(
            "R = U/I → δR = δU + δI. "
            "That is: ΔR/R = ΔU/U + ΔI/I."
        )

    if any(kw in q for kw in ["p = u*i", "p=ui", "power", "công suất"]) \
       and "error" in q:
        hints.append("P = U·I → δP = δU + δI.")

    return hints


def _detect_percentage(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["percentage", "percent", "phần trăm", "%", "relative error", "sai số tương đối"]):
        hints.append(
            "HARD RULE: If the question asks for 'relative error' or 'percentage error' or '%', "
            "Percentage error = relative error * 100. "
            "you MUST multiply the final relative error value by 100 before returning it. "
            "For example, if δ = 0.0421, output 4.21."
        )
    return hints


def _detect_basic_error(question: str) -> List[str]:
    hints = []
    q = question.lower()
    if any(kw in q for kw in ["error", "sai số", "uncertainty", "độ chính xác"]):
        hints.append(
            "Absolute error: Δ = |X_measured − X_true|. "
            "Relative error: δ = Δ / |X|. "
            "Result format: X = X̄ ± Δ."
        )
    return hints


def analyze(question: str) -> List[str]:
    """Return all applicable measurement error hints."""
    hints: List[str] = []
    hints.extend(_detect_instrument_error(question))
    hints.extend(_detect_random_error(question))
    hints.extend(_detect_error_propagation(question))
    hints.extend(_detect_percentage(question))
    hints.extend(_detect_basic_error(question))
    return list(dict.fromkeys(hints))

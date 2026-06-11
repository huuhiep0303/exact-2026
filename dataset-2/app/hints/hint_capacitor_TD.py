"""
Topic hints for Capacitors — prefix TD.

Covers all 177 TD questions:
  - Parallel-plate capacitor (C = ε₀εA/d)
  - Charge, voltage, energy calculations (Q=CU, W=½CU²)
  - Connected vs disconnected from source
  - Dielectric insertion
  - Series / parallel combinations
  - Merging capacitors (like-sign / unlike-sign plates)
  - Parameter changes (distance, area, dielectric)
"""
import re
from typing import List


def _detect_connected_disconnected(question: str) -> List[str]:
    """Critical: determine whether Q or U stays constant."""
    hints = []
    q = question.lower()

    disconnected_kw = [
        "disconnected", "disconnect", "removed from",
        "ngắt", "tách", "rời khỏi", "không nối",
        "then disconnected", "is then disconnected",
    ]
    connected_kw = [
        "still connected", "remains connected", "while connected",
        "connected to the source", "while still connected",
        "vẫn nối", "còn nối", "đang nối", "vẫn kết nối",
    ]

    is_disconnected = any(kw in q for kw in disconnected_kw)
    is_connected = any(kw in q for kw in connected_kw)

    if is_disconnected and not is_connected:
        hints.append(
            "HARD RULE: Capacitor is DISCONNECTED from the source. "
            "CHARGE Q is CONSTANT. Do NOT assume U is constant. "
            "If distance or dielectric changes, use Q=constant to find new U (U_new = Q/C_new) and new energy W_new = Q^2/(2*C_new)."
        )
    elif is_connected:
        hints.append(
            "HARD RULE: Capacitor is CONNECTED to the source. "
            "VOLTAGE U is CONSTANT. Do NOT calculate a new U; the new potential difference is exactly the same as the original. "
            "If C changes, Q will change (Q_new = C_new*U)."
        )

    return hints


def _detect_parameter_change(question: str) -> List[str]:
    """Detect changes in d, A, ε and their effect on C."""
    hints = []
    q = question.lower()

    if any(kw in q for kw in ["distance", "apart", "doubled", "halved",
                               "moved apart", "moved closer",
                               "khoảng cách", "tăng gấp", "giảm"]):
        if "doubled" in q or "doubles" in q or "gấp đôi" in q or "gấp 2" in q:
            hints.append(
                "Parameter change: plate distance DOUBLED → C_new = C/2 "
                "(capacitance halved, since C ∝ 1/d)."
            )
        elif "halved" in q or "giảm một nửa" in q:
            hints.append(
                "Parameter change: plate distance HALVED → C_new = 2·C "
                "(capacitance doubled)."
            )

    if any(kw in q for kw in ["dielectric", "điện môi", "immersed",
                               "filled with", "inserted"]):
        hints.append(
            "Dielectric effect: inserting dielectric with constant ε → "
            "C_new = ε · C_original."
        )

    return hints


def _detect_series_parallel(question: str) -> List[str]:
    hints = []
    q = question.lower()

    if any(kw in q for kw in ["in series", "nối tiếp", "mắc nối tiếp"]):
        hints.append(
            "Series capacitors: 1/C_eq = 1/C1 + 1/C2 + ... "
            "Same charge on each: Q1 = Q2 = Q_total. "
            "Voltages add: U_total = U1 + U2."
        )

    if any(kw in q for kw in ["in parallel", "song song", "mắc song song"]):
        hints.append(
            "Parallel capacitors: C_eq = C1 + C2 + ... "
            "Same voltage: U1 = U2 = U_total. "
            "Charges add: Q_total = Q1 + Q2."
        )

    return hints


def _detect_merging(question: str) -> List[str]:
    hints = []
    q = question.lower()

    if any(kw in q for kw in ["like-charged", "same-sign", "cùng dấu",
                               "like sign", "connected together"]):
        hints.append(
            "Merging (like-sign plates): Q_total = Q1 + Q2, "
            "C_total = C1 + C2, U_final = Q_total / C_total."
        )

    if any(kw in q for kw in ["unlike", "opposite", "trái dấu",
                               "unlike-sign"]):
        hints.append(
            "Merging (unlike-sign plates): Q_total = |Q1 − Q2|, "
            "C_total = C1 + C2, U_final = Q_total / C_total."
        )

    return hints


def _detect_basic_formulas(question: str) -> List[str]:
    """Reinforce basic capacitor formulas."""
    hints = []
    q = question.lower()

    if any(kw in q for kw in ["energy", "năng lượng", "electric field energy"]):
        hints.append(
            "Energy stored: W = ½·C·U² = Q²/(2C) = ½·Q·U."
        )

    if any(kw in q for kw in ["charge", "điện tích"]) and \
       any(kw in q for kw in ["calculate", "find", "tính", "xác định"]):
        hints.append("Charge on capacitor: Q = C · U.")

    if any(kw in q for kw in ["capacitance", "điện dung"]) and \
       any(kw in q for kw in ["plate area", "diện tích", "radius", "bán kính"]):
        hints.append(
            "Parallel-plate capacitance: C = ε₀ · ε_r · A / d. "
            "For air: ε_r = 1. ε₀ = 8.854 × 10⁻¹² F/m."
        )

    if any(kw in q for kw in ["electric field", "cường độ điện trường"]) and \
       any(kw in q for kw in ["between", "giữa"]):
        hints.append("E-field between plates: E = U / d.")

    return hints


def analyze(question: str) -> List[str]:
    """Return all applicable capacitor hints."""
    hints: List[str] = []
    hints.extend(_detect_connected_disconnected(question))
    hints.extend(_detect_parameter_change(question))
    hints.extend(_detect_series_parallel(question))
    hints.extend(_detect_merging(question))
    hints.extend(_detect_basic_formulas(question))
    return list(dict.fromkeys(hints))

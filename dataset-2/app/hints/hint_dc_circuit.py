"""
Topic hints for practical DC circuits: lamps, branches, resistors.

These hints cover branch-current and lamp-brightness problems such as parallel
lamp circuits. They are phrased by circuit behavior rather than dataset IDs.
"""
from typing import List


def _detect_parallel(question: str) -> List[str]:
    hints: List[str] = []
    q = question.lower()
    if any(term in q for term in ["parallel", "branch", "branches", "song song"]):
        hints.append(
            "DC parallel circuit: every branch has the same voltage U. "
            "Branch current is I_i = U / R_i, and total current is "
            "I_total = I_1 + I_2 + ..."
        )
        hints.append(
            "HARD RULE (PARALLEL): To find total current, you MUST compute the equivalent resistance first: "
            "1/R_eq = 1/R1 + 1/R2 + ... Then use I_total = U / R_eq. Do not just add currents unless you have explicitly calculated them."
        )
    return hints


def _detect_series(question: str) -> List[str]:
    hints: List[str] = []
    q = question.lower()
    if "series" in q or "nối tiếp" in q:
        hints.append(
            "DC series circuit: R_eq = R1 + R2 + ... and the same current "
            "flows through every component."
        )
    return hints


def _detect_power(question: str) -> List[str]:
    hints: List[str] = []
    q = question.lower()
    if any(term in q for term in ["power", "consumption", "watt", "w "]):
        hints.append(
            "DC power: P = U*I = I^2*R = U^2/R. Total power is the sum of "
            "branch powers or P_total = U*I_total."
        )
    return hints


def _detect_removed_branch(question: str) -> List[str]:
    hints: List[str] = []
    q = question.lower()
    if any(term in q for term in ["removed", "disconnected", "taken out", "lamp d₁ is removed", "branch is removed"]):
        hints.append(
            "Removed branch: recompute the circuit using only the remaining "
            "parallel branches; do not keep the removed branch current in "
            "I_total_new."
        )
    return hints


def _detect_brightness(question: str) -> List[str]:
    hints: List[str] = []
    q = question.lower()
    if any(term in q for term in ["brighter", "brightness", "glow", "shines", "lamp"]):
        hints.append(
            "Lamp brightness tracks current/power. At fixed voltage, decreasing "
            "a branch resistance increases that branch current and usually makes "
            "the lamp brighter."
        )
    return hints


def analyze(question: str) -> List[str]:
    """Return all applicable practical DC circuit hints."""
    hints: List[str] = []
    hints.extend(_detect_parallel(question))
    hints.extend(_detect_series(question))
    hints.extend(_detect_power(question))
    hints.extend(_detect_removed_branch(question))
    hints.extend(_detect_brightness(question))
    return list(dict.fromkeys(hints))

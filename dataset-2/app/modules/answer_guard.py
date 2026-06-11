"""
Post-computation sanity checks used to calibrate confidence.

These checks do not change the public answer. They flag contradictions between
the final answer/premises and deterministic hard facts from the problem text.
"""
from __future__ import annotations

import re

from app.modules.problem_facts import ProblemFacts


def _parse_number(text: str) -> float | None:
    match = re.search(r"^[\s=]*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)", text or "", re.IGNORECASE)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _to_si_length(value: float, unit: str) -> float | None:
    unit = (unit or "").strip()
    if unit == "m":
        return value
    if unit == "cm":
        return value * 1e-2
    if unit == "mm":
        return value * 1e-3
    return None


def sanity_warnings(
    *,
    question: str,
    facts: ProblemFacts,
    premises: list[str],
    final_answer: str,
    final_unit: str,
) -> list[str]:
    warnings: list[str] = []
    joined_premises = "\n".join(premises).lower()
    answer_text = f"{final_answer} {final_unit}".strip().lower()

    if facts.asks_zero_field and ("point where v = 0" in joined_premises or "zero-potential" in joined_premises):
        warnings.append("zero-field question used a zero-potential premise")

    if "j" in answer_text and re.search(r"\([^)]*j\)|[+-][0-9.]+j", answer_text):
        warnings.append("answer appears to be complex")

    if facts.asks_symbolic:
        if answer_text in {"answer", "answer n/c", "answer v/m"} or re.search(r"\b(a|q|h)\s*=\s*1\b", question.lower()):
            warnings.append("symbolic question produced placeholder answer")
        if _parse_number(final_answer) is not None:
            warnings.append("symbolic question produced a numeric placeholder")

    if facts.asks_zero_field and facts.distances_m:
        d = facts.distances_m.get("AB") or facts.distances_m.get("BA")
        numeric = _parse_number(final_answer)
        length_si = _to_si_length(numeric, final_unit) if numeric is not None else None
        if d and length_si is not None:
            if facts.zero_field_region == "between" and not (0 <= length_si <= d):
                warnings.append("same-sign zero-field distance is outside the source segment")
            if facts.zero_field_region == "outside" and length_si < d:
                warnings.append("opposite-sign zero-field distance is inside the source segment")

    if facts.has_midpoint and facts.same_sign_sources and facts.asks_field:
        numeric = _parse_number(final_answer)
        if numeric is not None and abs(numeric) > 1e-9:
            warnings.append("midpoint symmetry expects zero field")

    return list(dict.fromkeys(warnings))

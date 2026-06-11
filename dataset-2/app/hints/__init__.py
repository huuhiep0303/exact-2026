"""
Hint Engine Registry.

Unit-conversion hints and topic-specific hints are kept separate in the
pipeline context so prompt sections can describe them accurately.
"""
from typing import List

from app.modules.problem_facts import ProblemFacts, analyze_problem


def _dedupe(hints: List[str]) -> List[str]:
    """Deduplicate hints while preserving order."""
    return list(dict.fromkeys(hints))


def get_unit_hints(question: str) -> List[str]:
    """Return shared unit-conversion hints for any topic."""
    from app.hints.unit_conversion_hint import analyze as unit_analyze

    return _dedupe(unit_analyze(question))


def get_topic_hints(question: str, topic: str, facts: ProblemFacts | None = None) -> List[str]:
    """Return topic-specific deterministic hints for a routed question."""
    hints: List[str] = []
    facts = facts or analyze_problem(question)

    topic_analyzers = {
        "coulomb_force": "app.hints.hint_coulomb_force_LD",
        "electric_field": "app.hints.hint_coulomb_force_LD",
        "electric_field_zero": "app.hints.hint_coulomb_force_LD",
        "electric_potential": "app.hints.hint_electric_field_DT",
        "capacitor": "app.hints.hint_capacitor_TD",
        "dc_circuit": "app.hints.hint_dc_circuit",
        "ac_circuit": "app.hints.hint_ac_circuit_CH",
        "magnetism_induction": "app.hints.hint_magnetism_DDT",
        "measurement_error": "app.hints.hint_measurement_error_THCB",
        "energy_oscillation": "app.hints.hint_energy_oscillation_NL",
    }

    module_name = topic_analyzers.get(topic)
    if module_name:
        import importlib

        try:
            mod = importlib.import_module(module_name)
            try:
                hints.extend(mod.analyze(question, facts=facts))
            except TypeError:
                hints.extend(mod.analyze(question))
        except Exception as exc:  # pragma: no cover
            print(f"[Hints] Warning: {module_name} failed: {exc}")

    if topic == "ac_circuit":
        q = question.lower()
        resonance_kw = [
            "resonance",
            "resonant",
            "resonate",
            "cộng hưởng",
            "cong huong",
            "is it",
            "is the",
            "does it",
            "will",
            "yes",
            "no",
        ]
        if any(kw in q for kw in resonance_kw):
            from app.hints.hint_ac_resonance_CHLT import analyze as chlt_analyze

            hints.extend(chlt_analyze(question))

    return _dedupe(hints)


def get_hints(question: str, topic: str) -> List[str]:
    """
    Backward-compatible helper returning unit hints followed by topic hints.

    New pipeline code should prefer `get_unit_hints` and `get_topic_hints` so
    unit facts are not mislabeled as geometry/topic facts.
    """
    return _dedupe(get_unit_hints(question) + get_topic_hints(question, topic))

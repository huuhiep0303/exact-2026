"""Applicability filter for retrieved physics premises.

RAG is useful for recall, but broad topic retrieval can surface formulas with
the wrong use-case. This module separates accepted formulas from distractors
before the prompt sees them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class PremiseFilterResult:
    applicable: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


_CHARGE_SHARING_TERMS = (
    "connected together",
    "connect together",
    "joined together",
    "merged",
    "merging",
    "charge sharing",
    "like-sign",
    "like sign",
    "unlike-sign",
    "unlike sign",
    "same-sign",
    "opposite-sign",
    "opposite plates",
    "plates are connected",
)

_GENERAL_INTENTS = {
    "force_ma",
    "distance_vt",
    "work_energy",
    "elastic_energy",
    "constant_pressure_work",
    "ideal_gas",
    "wave_speed",
    "thin_lens",
}

_UNRELATED_FOR_GENERAL = (
    "coulomb",
    "electric field",
    "electric force",
    "electric potential",
    "point where e = 0",
    "point where v = 0",
    "zero-potential",
    "zero potential",
    "capacitor",
    "capacitance",
    "resonance",
    "resonant",
    "oscillation",
    "rlc",
    "solenoid",
    "faraday",
    "magnetic",
    "inductor",
)


def _has_any(text: str, terms: Iterable[str]) -> bool:
    return any(term in text for term in terms)


def _reject(reason: str, premise: str) -> str:
    return f"{premise} [rejected: {reason}]"


def _is_applicable_by_intent(question: str, topic: str, intent: str, premise: str) -> tuple[bool, str]:
    q = question.lower()
    p = premise.lower()
    intent = intent or "unknown"

    if ("zero field" in p or "point where e = 0" in p) and not _has_any(
        q, ("e = 0", "electric field is zero", "field is zero", "zero electric field", "where electric field")
    ):
        return False, "zero-field formula but question does not ask E = 0"

    if ("zero potential" in p or "zero-potential" in p or "point where v = 0" in p) and not _has_any(
        q, ("v = 0", "potential is zero", "voltage is zero", "zero potential", "zero-potential")
    ):
        return False, "zero-potential formula but question does not ask V = 0"

    if "merging capacitor" in p or "charge sharing" in p or "like-sign" in p or "unlike-sign" in p:
        if not _has_any(q, _CHARGE_SHARING_TERMS):
            return False, "charge-sharing formula without merging/connected-together context"

    if intent == "equivalent_capacitance_parallel":
        if "capacitors in parallel" in p or "parallel capacitors" in p:
            return True, ""
        if "capacitors in series" in p:
            return False, "series-capacitance formula for parallel-equivalent intent"
        return False, "premise is not the requested parallel-equivalent capacitance formula"

    if intent == "equivalent_capacitance_series":
        if "capacitors in series" in p or "series capacitors" in p:
            return True, ""
        if "capacitors in parallel" in p:
            return False, "parallel-capacitance formula for series-equivalent intent"
        return False, "premise is not the requested series-equivalent capacitance formula"

    if intent == "charge_from_CU":
        if "q = c" in p or "charge on capacitor" in p:
            return True, ""
    if intent == "voltage_from_QC":
        if "u = q" in p or "v = q" in p or "voltage" in p:
            return True, ""
    if intent == "energy_from_CU":
        if "energy stored in capacitor" in p or "1/2" in p or "½" in p:
            return True, ""

    if intent in {"energy_oscillation", "lc_current_percentage_from_energy", "energy_percentage"}:
        if _has_any(p, ("lc", "oscillation", "oscillating", "maximum current", "maximum voltage", "electromagnetic energy", "capacitor energy", "inductor energy")):
            return True, ""
        if _has_any(p, ("electric field from", "point charge", "coulomb", "zero electric field", "electric potential")):
            return False, "field/electrostatic premise conflicts with LC energy intent"
        if "energy" in p and _has_any(p, ("capacitor", "inductor", "magnetic field", "electric field")):
            return True, ""
        return False, "premise is not LC/electromagnetic energy related"

    if intent == "equivalent_resistance_parallel":
        if "parallel" in p and ("resistance" in p or "resistor" in p):
            return True, ""
        if "series" in p and ("resistance" in p or "resistor" in p):
            return False, "series-resistance formula for parallel-equivalent intent"

    if intent == "equivalent_resistance_series":
        if "series" in p and ("resistance" in p or "resistor" in p):
            return True, ""
        if "parallel" in p and ("resistance" in p or "resistor" in p):
            return False, "parallel-resistance formula for series-equivalent intent"

    if intent == "thin_lens":
        if "lens" in p or "1/f" in p:
            return True, ""
        return False, "non-optics premise for thin-lens intent"

    if intent == "wave_speed":
        if "wave" in p and ("speed" in p or "wavelength" in p or "frequency" in p):
            return True, ""
        return False, "non-wave premise for wave-speed intent"

    if intent == "force_ma":
        if ("f = m" in p or "newton" in p or "second law" in p) and ("mass" in p or "acceleration" in p):
            return True, ""
        return False, "premise is not Newton second law for F = ma intent"

    if intent == "elastic_energy":
        if "spring" in p or "elastic" in p or "1/2*k" in p or "0.5*k" in p:
            return True, ""
        return False, "premise is not elastic/spring energy"

    if intent == "work_energy":
        if _has_any(p, ("electric", "charge", "potential", "coulomb", "magnetic", "capacitor", "inductor")):
            return False, "field/circuit work premise for general work-energy intent"
        if "work" in p and _has_any(p, ("force", "pressure", "distance", "volume", "w =")):
            return True, ""
        return False, "premise is not general work-energy"

    if intent == "ideal_gas":
        if _has_any(p, ("ideal gas", "pv", "pressure", "volume", "temperature", "nrt")):
            return True, ""
        return False, "premise is not ideal-gas related"

    if intent == "distance_vt":
        if _has_any(p, ("distance", "speed", "velocity", "time")):
            return True, ""
        return False, "premise is not distance-speed-time related"

    if intent in {"force_ma", "distance_vt", "work_energy", "elastic_energy", "ideal_gas"}:
        if _has_any(p, _UNRELATED_FOR_GENERAL):
            return False, f"topic premise conflicts with general intent {intent}"

    if topic == "general" and intent in _GENERAL_INTENTS and _has_any(p, _UNRELATED_FOR_GENERAL):
        return False, f"retrieved topic premise conflicts with general intent {intent}"

    return True, ""


def filter_premises(
    question: str,
    topic: str,
    intent: str,
    premises: list[str],
) -> PremiseFilterResult:
    applicable: list[str] = []
    rejected: list[str] = []
    warnings: list[str] = []

    for premise in premises:
        ok, reason = _is_applicable_by_intent(question, topic, intent, premise)
        if ok:
            applicable.append(premise)
        else:
            rejected.append(_reject(reason, premise))

    if not applicable and premises:
        warnings.append(
            "No reliable retrieved formula passed the applicability filter; solve from first principles using the problem statement and Python verification."
        )

    return PremiseFilterResult(applicable=applicable, rejected=rejected, warnings=warnings)

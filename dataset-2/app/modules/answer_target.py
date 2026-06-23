"""Conservative detection of the quantity and answer form requested by a question."""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class AnswerTarget:
    answer_form: str = "numeric"
    quantity: str = "unknown"
    expected_dimensions: tuple[str, ...] = ()


_UNIT_DIMENSIONS = {
    "n": "force",
    "v/m": "electric_field",
    "n/c": "electric_field",
    "c": "charge",
    "uc": "charge",
    "nc": "charge",
    "pc": "charge",
    "h": "inductance",
    "mh": "inductance",
    "uh": "inductance",
    "f": "capacitance",
    "uf": "capacitance",
    "nf": "capacitance",
    "pf": "capacitance",
    "hz": "frequency",
    "rad/s": "angular_frequency",
    "ohm": "impedance",
    "omega": "impedance",
    "w": "power",
    "j": "energy",
    "mj": "energy",
    "uj": "energy",
    "j/m^3": "energy_density",
    "j/m3": "energy_density",
    "turns/m": "turn_density",
    "turn/m": "turn_density",
    "%": "percentage",
    "degree": "angle",
    "degrees": "angle",
    "deg": "angle",
    "rad": "angle",
    "m": "distance",
    "cm": "distance",
    "mm": "distance",
    "m/s": "speed",
    "m/s^2": "acceleration",
    "m/s2": "acceleration",
    "pa": "pressure",
    "v": "voltage",
    "a": "current",
}


def unit_dimension(unit: str) -> str:
    normalized = (unit or "").strip().lower()
    normalized = normalized.replace("\u03bc", "u").replace("\u00b5", "u")
    normalized = normalized.replace("\u03c9", "omega").replace("\u2126", "omega")
    normalized = normalized.replace("\u00b0", "degree")
    return _UNIT_DIMENSIONS.get(normalized, "")


def _request_focus(question: str) -> tuple[str, str]:
    q = (question or "").lower()
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", q) if part.strip()]
    questions = [part for part in sentences if "?" in part]
    requests = [
        part
        for part in sentences
        if re.search(r"\b(?:what|find|determine|calculate|state|derive|describe)\b", part)
    ]
    focus = questions[-1] if questions else (requests[-1] if requests else (sentences[-1] if sentences else q))
    return q, focus


def detect_answer_target(question: str) -> AnswerTarget:
    q, focus = _request_focus(question)

    yes_no = (
        bool(re.search(r"(?:^|[,.;?!]\s*)(?:does|do|will|is|are|can)\b", focus))
        or bool(re.search(r"\b(?:determine|state|check)\s+(?:whether|if)\b", focus))
    ) and any(term in focus for term in ["resonance", "resonate", "resonant"])
    if yes_no and not any(term in focus for term in ["calculate", "find the value", "what is the value"]):
        return AnswerTarget("yes_no", "resonance_state", ())

    asks_direction = bool(
        re.search(r"\b(?:what\s+is|find|determine|state)\s+(?:the\s+)?direction\b", focus)
    )
    asks_force_value = "force" in focus and any(
        term in focus for term in ["magnitude", "resultant", "calculate", "how large"]
    )
    asks_qualitative = any(
        term in focus for term in ["what happens", "increase or decrease", "state whether", "how does", "when does"]
    ) or bool(re.search(r"\bdescribe\s+(?:what|how|the)\b", focus))
    if (asks_direction and not asks_force_value) or asks_qualitative:
        return AnswerTarget("qualitative", "direction" if asks_direction else "qualitative", ())
    if "where is the energy stored" in focus:
        return AnswerTarget("qualitative", "energy_location", ())

    if "absolute error" in focus and any(term in focus for term in ["percentage relative error", "relative error"]):
        return AnswerTarget("numeric", "measurement_error_pair", ())
    if any(term in focus for term in ["percentage error", "percent error", "relative error"]):
        return AnswerTarget("numeric", "percentage", ("percentage",))
    if "percentage" in focus and "energy remains" in focus:
        return AnswerTarget("numeric", "percentage", ("percentage",))
    if re.search(r"\b(?:find|determine|calculate)\s+(?:the\s+)?angle\b", focus):
        return AnswerTarget("numeric", "angle", ("angle",))
    if any(term in focus for term in ["induced electromotive force", "induced emf", "induced e.m.f"]):
        return AnswerTarget("numeric", "emf", ("voltage",))
    if any(term in focus for term in ["potential difference", "voltage across", "new voltage"]) or re.search(
        r"\b(?:find|determine|calculate)\s+(?:the\s+)?voltage\b", focus
    ):
        return AnswerTarget("numeric", "voltage", ("voltage",))
    if re.search(
        r"\b(?:what\s+is|find|determine|calculate)\s+(?:the\s+)?(?:maximum\s+)?charge\b",
        focus,
    ):
        return AnswerTarget("numeric", "charge", ("charge",))
    if "dielectric constant" in focus or "relative permittivity" in focus:
        return AnswerTarget("numeric", "dielectric_constant", ("dimensionless",))
    if any(term in focus for term in ["coordinate", "position", "location", "where the electric field"]):
        return AnswerTarget("numeric", "distance", ("distance",))
    if "distance from" in focus or re.search(r"\bvalue\s+of\s+h\b", focus):
        return AnswerTarget("numeric", "distance", ("distance",))
    if "force" in focus or "forces" in focus:
        form = "symbolic" if any(x in focus for x in ["in terms of", "derive", "expression", "f0"]) else "numeric"
        return AnswerTarget(form, "force", ("force",))
    if "energy density" in focus:
        return AnswerTarget("numeric", "energy_density", ("energy_density",))
    if "number of turns per meter" in focus or "turn density" in focus:
        return AnswerTarget("numeric", "turn_density", ("turn_density",))
    if "energy" in focus:
        form = "symbolic" if any(term in focus for term in ["expression", "in terms of", "derive"]) else "numeric"
        return AnswerTarget(form, "energy", ("energy",))
    if "power factor" in focus or "cos phi" in focus:
        return AnswerTarget("numeric", "power_factor", ("dimensionless",))
    if "pure resistance" in focus or re.search(r"\b(?:find|determine|calculate)\s+(?:the\s+)?r\b", focus):
        return AnswerTarget("numeric", "resistance", ("impedance",))
    if "impedance" in focus or re.search(r"\bfind\s+z\b", focus):
        return AnswerTarget("numeric", "impedance", ("impedance",))
    if "angular frequency" in focus or re.search(r"\bomega\b", focus):
        return AnswerTarget("numeric", "angular_frequency", ("angular_frequency",))
    if "frequency" in focus or "f0" in focus:
        return AnswerTarget("numeric", "frequency", ("frequency",))
    if "inductance" in focus or re.search(r"\bfind\s+l\b|\bdetermine\s+l\b", focus):
        return AnswerTarget("numeric", "inductance", ("inductance",))
    if "capacitance" in focus or re.search(r"\bfind\s+c\b|\bdetermine\s+c\b", focus):
        return AnswerTarget("numeric", "capacitance", ("capacitance",))
    if "power" in focus and "power factor" not in focus:
        return AnswerTarget("numeric", "power", ("power",))
    if "current" in focus:
        return AnswerTarget("numeric", "current", ("current",))
    if "speed" in focus or "velocity" in focus:
        return AnswerTarget("numeric", "speed", ("speed",))
    if "acceleration" in focus:
        return AnswerTarget("numeric", "acceleration", ("acceleration",))
    if "pressure" in focus:
        return AnswerTarget("numeric", "pressure", ("pressure",))
    if "what distance" in focus or "how far" in focus or re.search(
        r"\b(?:find|calculate|determine)\s+(?:the\s+)?distance\b", focus
    ):
        return AnswerTarget("numeric", "distance", ("distance",))
    if any(term in focus for term in ["electric field", "field strength", "net field", "resultant field"]):
        form = "symbolic" if any(x in focus for x in ["in terms of", "derive", "expression"]) else "numeric"
        return AnswerTarget(form, "electric_field", ("electric_field",))
    if "angle" in focus:
        return AnswerTarget("numeric", "angle", ("angle",))
    if "distance" in focus:
        return AnswerTarget("numeric", "distance", ("distance",))
    return AnswerTarget()


def solver_result_is_compatible(target: AnswerTarget, answer: str, unit: str) -> bool:
    if target.answer_form == "yes_no":
        return (answer or "").strip().lower() in {"yes", "no"} and not (unit or "").strip()
    if target.answer_form == "qualitative":
        return not bool(re.search(r"\d", answer or "")) or not (unit or "").strip()
    if not target.expected_dimensions:
        return True
    dimension = unit_dimension(unit)
    if target.expected_dimensions == ("dimensionless",):
        return not (unit or "").strip() or (unit or "").strip() == "-"
    return dimension in target.expected_dimensions

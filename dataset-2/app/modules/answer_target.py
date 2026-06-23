"""Conservative detection of the quantity and answer form requested by a question."""
from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class AnswerTarget:
    answer_form: str = "numeric"
    quantity: str = "unknown"
    expected_dimensions: tuple[str, ...] = ()
    intent: str = "unknown"


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

    if "normal force" in q:
        return AnswerTarget("numeric", "force", ("force",), "elevator_normal_force")
    if any(term in q for term in ["where the electric field", "electric field is zero", "field strength is zero", "net electric field is zero", "e = 0"]):
        if any(term in q for term in ["coordinate", "position", "location", "where", "point"]):
            return AnswerTarget("numeric", "distance", ("distance",), "zero_field")
    if (
        ("percentage" in focus or "%" in focus)
        and "maximum current" in focus
        and any(term in q for term in ["lc", "oscillat", "electric field energy", "magnetic field energy"])
    ):
        return AnswerTarget("numeric", "percentage", ("percentage",), "lc_current_percentage_from_energy")
    if ("capacitor" in q or "capacitors" in q) and "charge stored" in q:
        return AnswerTarget("numeric", "charge", ("charge",), "series_capacitor_charge" if "series" in q else "charge_from_CU")
    if ("resistor" in q or "resistors" in q) and "current" in q:
        if "parallel" in q and "total current" in q:
            return AnswerTarget("numeric", "current", ("current",), "equivalent_resistance_parallel")
        if "series" in q:
            return AnswerTarget("numeric", "current", ("current",), "equivalent_resistance_series")
        return AnswerTarget("numeric", "current", ("current",), "ohm_current")
    if ("electric field" in q or "field magnitude" in q or "field strength" in q) and "charge" in q:
        intent = "zero_field" if any(term in q for term in ["zero", "e = 0", "field is zero"]) else "electric_field_point_charge"
        return AnswerTarget("numeric", "electric_field", ("electric_field",), intent)
    if "resistivity" in q and "resistance" in q:
        return AnswerTarget("numeric", "resistance", ("impedance",), "conductor_resistance")

    yes_no = (
        bool(re.search(r"(?:^|[,.;?!]\s*)(?:does|do|will|is|are|can)\b", focus))
        or bool(re.search(r"\b(?:determine|state|check)\s+(?:whether|if)\b", focus))
    ) and any(term in focus for term in ["resonance", "resonate", "resonant"])
    if yes_no and not any(term in focus for term in ["calculate", "find the value", "what is the value"]):
        return AnswerTarget("yes_no", "resonance_state", (), "resonance_state")

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
        return AnswerTarget("qualitative", "direction" if asks_direction else "qualitative", (), "qualitative")
    if "where is the energy stored" in focus:
        return AnswerTarget("qualitative", "energy_location", (), "energy_location")

    if ("work done" in focus or "work" in focus) and any(term in q for term in ["force", "pressure", "expands", "expansion", "volume"]):
        return AnswerTarget("numeric", "energy", ("energy",), "work_energy")
    if ("image distance" in focus or "image position" in focus) and ("lens" in q or "focal" in q):
        return AnswerTarget("numeric", "distance", ("distance",), "thin_lens")

    if "absolute error" in focus and any(term in focus for term in ["percentage relative error", "relative error"]):
        return AnswerTarget("numeric", "measurement_error_pair", (), "measurement_error_pair")
    if any(term in focus for term in ["percentage error", "percent error", "relative error"]):
        return AnswerTarget("numeric", "percentage", ("percentage",), "measurement_relative_error")
    if "percentage" in focus and "energy remains" in focus:
        return AnswerTarget("numeric", "percentage", ("percentage",), "energy_percentage")
    if re.search(r"\b(?:find|determine|calculate)\s+(?:the\s+)?angle\b", focus):
        return AnswerTarget("numeric", "angle", ("angle",), "angle")
    if any(term in focus for term in ["induced electromotive force", "induced emf", "induced e.m.f"]):
        return AnswerTarget("numeric", "emf", ("voltage",), "faraday_induced_emf")
    if any(term in focus for term in ["potential difference", "voltage across", "new voltage"]) or re.search(
        r"\b(?:find|determine|calculate)\s+(?:the\s+)?voltage\b", focus
    ):
        if "charge" in q and ("capacitance" in q or "capacitor" in q):
            return AnswerTarget("numeric", "voltage", ("voltage",), "voltage_from_QC")
        return AnswerTarget("numeric", "voltage", ("voltage",), "ohm_voltage")
    if re.search(
        r"\b(?:what\s+is|find|determine|calculate)\s+(?:the\s+)?(?:maximum\s+)?charge\b",
        focus,
    ):
        if "capacitance" in q or "capacitor" in q:
            return AnswerTarget("numeric", "charge", ("charge",), "charge_from_CU")
        return AnswerTarget("numeric", "charge", ("charge",), "charge")
    if "dielectric constant" in focus or "relative permittivity" in focus:
        return AnswerTarget("numeric", "dielectric_constant", ("dimensionless",), "dielectric_constant")
    if any(term in focus for term in ["coordinate", "position", "location", "where the electric field"]):
        intent = "zero_field" if "electric field" in focus else "distance"
        return AnswerTarget("numeric", "distance", ("distance",), intent)
    if "distance from" in focus or re.search(r"\bvalue\s+of\s+h\b", focus):
        return AnswerTarget("numeric", "distance", ("distance",), "distance")
    if "force" in focus or "forces" in focus:
        form = "symbolic" if any(x in focus for x in ["in terms of", "derive", "expression", "f0"]) else "numeric"
        intent = "force_ma" if any(term in q for term in ["mass", "acceleration", "kg", "m/s^2"]) else "coulomb_force"
        return AnswerTarget(form, "force", ("force",), intent)
    if "energy density" in focus:
        return AnswerTarget("numeric", "energy_density", ("energy_density",), "energy_density")
    if "number of turns per meter" in focus or "turn density" in focus:
        return AnswerTarget("numeric", "turn_density", ("turn_density",), "turn_density")
    if "energy" in focus:
        form = "symbolic" if any(term in focus for term in ["expression", "in terms of", "derive"]) else "numeric"
        if "spring" in q or "elastic" in q:
            return AnswerTarget(form, "energy", ("energy",), "elastic_energy")
        if "capacitor" in q and ("voltage" in q or "potential difference" in q):
            return AnswerTarget(form, "energy", ("energy",), "energy_from_CU")
        if "inductor" in q or "lc" in q or "oscillation" in q:
            return AnswerTarget(form, "energy", ("energy",), "energy_oscillation")
        return AnswerTarget(form, "energy", ("energy",), "work_energy")
    if "power factor" in focus or "cos phi" in focus:
        return AnswerTarget("numeric", "power_factor", ("dimensionless",), "ac_power_factor")
    if "pure resistance" in focus or re.search(r"\b(?:find|determine|calculate)\s+(?:the\s+)?r\b", focus):
        intent = "equivalent_resistance_parallel" if "parallel" in q else ("equivalent_resistance_series" if "series" in q else "ohm_resistance")
        return AnswerTarget("numeric", "resistance", ("impedance",), intent)
    if "impedance" in focus or re.search(r"\bfind\s+z\b", focus):
        return AnswerTarget("numeric", "impedance", ("impedance",), "ac_impedance")
    if "angular frequency" in focus or re.search(r"\bomega\b", focus):
        return AnswerTarget("numeric", "angular_frequency", ("angular_frequency",), "angular_frequency")
    if "inductance" in focus or re.search(r"\bfind\s+l\b|\bdetermine\s+l\b", focus):
        return AnswerTarget("numeric", "inductance", ("inductance",), "inductance")
    if "capacitance" in focus or re.search(r"\bfind\s+c\b|\bdetermine\s+c\b", focus):
        if "series" in q:
            return AnswerTarget("numeric", "capacitance", ("capacitance",), "equivalent_capacitance_series")
        if "parallel" in q and "plate" not in q:
            return AnswerTarget("numeric", "capacitance", ("capacitance",), "equivalent_capacitance_parallel")
        return AnswerTarget("numeric", "capacitance", ("capacitance",), "capacitance")
    if "frequency" in focus or "f0" in focus:
        return AnswerTarget("numeric", "frequency", ("frequency",), "frequency")
    if "power" in focus and "power factor" not in focus:
        return AnswerTarget("numeric", "power", ("power",), "power")
    if "current" in focus:
        return AnswerTarget("numeric", "current", ("current",), "ohm_current")
    if "speed" in focus or "velocity" in focus:
        if "wave" in q or "wavelength" in q:
            return AnswerTarget("numeric", "speed", ("speed",), "wave_speed")
        return AnswerTarget("numeric", "speed", ("speed",), "distance_vt")
    if "acceleration" in focus:
        return AnswerTarget("numeric", "acceleration", ("acceleration",), "acceleration")
    if "pressure" in focus:
        return AnswerTarget("numeric", "pressure", ("pressure",), "ideal_gas")
    if "what distance" in focus or "how far" in focus or re.search(
        r"\b(?:find|calculate|determine)\s+(?:the\s+)?distance\b", focus
    ):
        if "lens" in q or "focal" in q:
            return AnswerTarget("numeric", "distance", ("distance",), "thin_lens")
        return AnswerTarget("numeric", "distance", ("distance",), "distance_vt")
    if any(term in focus for term in ["electric field", "field strength", "net field", "resultant field"]):
        form = "symbolic" if any(x in focus for x in ["in terms of", "derive", "expression"]) else "numeric"
        intent = "zero_field" if any(term in focus for term in ["zero", "e = 0", "vanishes"]) else "electric_field_point_charge"
        return AnswerTarget(form, "electric_field", ("electric_field",), intent)
    if "angle" in focus:
        return AnswerTarget("numeric", "angle", ("angle",), "angle")
    if "distance" in focus:
        return AnswerTarget("numeric", "distance", ("distance",), "distance")
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

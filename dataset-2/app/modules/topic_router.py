"""
Lightweight topic router for physics questions.

This router intentionally uses question text, not dataset IDs such as LD001 or
TD401, so it also works for real user questions.
"""
from typing import Literal


Topic = Literal[
    "coulomb_force",
    "electric_field",
    "electric_field_zero",
    "electric_potential",
    "capacitor",
    "dc_circuit",
    "ac_circuit",
    "magnetism_induction",
    "measurement_error",
    "energy_oscillation",
    "general",
]


def detect_topic(question: str) -> Topic:
    """Classify a question into a coarse physics topic/intent."""
    q = question.lower()

    practical_dc_terms = [
        "lamp",
        "lamps",
        "light bulb",
        "light bulbs",
        "branch",
        "branches",
        "parallel circuit",
        "series circuit",
        "connected in series",
        "connected in parallel",
        "resistor",
        "resistors",
        "d1",
        "d2",
        "rtd",
        "equivalent resistance",
        "total resistance",
        "total current",
    ]
    capacitor_context_terms = ["capacitor", "capacitance", "plates", "dielectric", "microf", "uf", "pf", "nf"]
    if any(term in q for term in practical_dc_terms) and not any(term in q for term in capacitor_context_terms):
        if any(term in q for term in ["resistance", "current", "voltage", "power", "source", "ohm", "ω", "Ω".lower(), "watt"]):
            return "dc_circuit"

    zero_field_terms = [
        "e = 0",
        "electric field is zero",
        "net electric field is zero",
        "field strength is zero",
        "where is the electric field zero",
        "where the net electric field",
        "where the resultant electric field",
        "resultant electric field is zero",
        "find point m where",
        "find the point where",
        "point where",
    ]
    if any(term in q for term in zero_field_terms) and ("field" in q or " e " in f" {q} "):
        return "electric_field_zero"

    coulomb_terms = ["charge", "charges", "q1", "q2", "q3", "test charge", "coulomb"]
    force_terms = ["force", "forces", "acting on", "resultant", "magnitude"]
    if any(term in q for term in coulomb_terms) and any(term in q for term in force_terms):
        return "coulomb_force"

    electric_field_terms = ["electric field", "field strength", "resultant field", "net field", " v/m", " n/c"]
    geometry_vector_terms = [
        " at m",
        " at n",
        " at c",
        " point m",
        " point n",
        " point c",
        " midpoint",
        "mid-point",
        "perpendicular",
        "triangle",
        "square",
        " na =",
        " nb =",
        " ma =",
        " mb =",
        " ac =",
        " bc =",
        " ab =",
    ]
    if (
        any(term in q for term in electric_field_terms)
        and any(term in q for term in coulomb_terms)
        and any(term in q for term in geometry_vector_terms)
    ):
        return "coulomb_force"
    if any(term in q for term in electric_field_terms):
        return "electric_field"

    pure_vector_force_terms = [
        "two electric forces",
        "forces are acting",
        "forces act",
        "same direction",
        "opposite direction",
        "perpendicular forces",
        "angle of",
        "act at an angle",
    ]
    if ("force" in q or "forces" in q) and any(term in q for term in pure_vector_force_terms):
        return "coulomb_force"

    if any(term in q for term in ["error", "uncertainty", "least count", "relative error", "absolute error", "percentage error"]):
        return "measurement_error"

    if any(term in q for term in ["rlc", "resonance", "resonant", "resonate", "alternating", "ac circuit", "impedance", "reactance"]):
        return "ac_circuit"

    energy_terms = ["energy", "stored", "electric field energy", "magnetic field energy", "electromagnetic energy"]
    energy_devices = ["lc", "oscillation", "capacitor", "inductor", "inductance", "electric field energy", "magnetic field energy"]
    capacitor_structure_terms = ["parallel-plate", "parallel plate", "plate distance", "source", "battery", "connected", "disconnected", "dielectric"]
    if any(term in q for term in energy_terms) and any(term in q for term in energy_devices):
        if not any(term in q for term in capacitor_structure_terms):
            return "energy_oscillation"

    if any(term in q for term in ["lc oscillation", "oscillation", "capacitor energy", "inductor energy", "electromagnetic energy"]):
        return "energy_oscillation"

    if any(term in q for term in ["solenoid", "magnetic", "inductance", "inductor", "flux", "faraday"]):
        return "magnetism_induction"

    if any(term in q for term in ["voltage", "potential", "electric potential", " v = 0", "equipotential"]):
        if "capacitor" not in q and "plates" not in q:
            return "electric_potential"

    if any(term in q for term in ["capacitor", "capacitance", "plates", "dielectric", "microf", "uf", "pf"]):
        return "capacitor"

    return "general"

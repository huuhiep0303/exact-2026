"""
Shared unit-conversion hints — injected for ALL topics.

Detects SI prefixes and physical units in the question text, then produces
deterministic conversion hints so Qwen-7B does not need to memorise them.
Also detects the *expected output unit* when the question explicitly asks
for a particular unit (e.g. "Calculate … (in mJ)").
"""
import re
from typing import List

# ── Recognised unit tokens with their SI multiplier ──
_UNIT_TABLE: list[tuple[str, str, str, float]] = [
    # (pattern,        display,   SI_unit, factor)
    # Capacitance
    (r"\bpF\b",        "pF",      "F",     1e-12),
    (r"\bnF\b",        "nF",      "F",     1e-9),
    (r"[μµu]F\b",      "μF",      "F",     1e-6),
    (r"\bmF\b",        "mF",      "F",     1e-3),
    # Charge
    (r"\bnC\b",        "nC",      "C",     1e-9),
    (r"[μµu]C\b",      "μC",      "C",     1e-6),
    (r"\bmC\b",        "mC",      "C",     1e-3),
    # Length
    (r"\bmm\b",        "mm",      "m",     1e-3),
    (r"\bcm\b",        "cm",      "m",     1e-2),
    (r"\bkm\b",        "km",      "m",     1e3),
    # Inductance
    (r"[μµu]H\b",      "μH",      "H",     1e-6),
    (r"\bmH\b",        "mH",      "H",     1e-3),
    # Frequency
    (r"\bkHz\b",       "kHz",     "Hz",    1e3),
    (r"\bMHz\b",       "MHz",     "Hz",    1e6),
    # Resistance
    (r"\bkΩ\b",        "kΩ",      "Ω",     1e3),
    (r"\bMΩ\b",        "MΩ",      "Ω",     1e6),
    (r"\bmΩ\b",        "mΩ",      "Ω",     1e-3),
    # Voltage
    (r"\bkV\b",        "kV",      "V",     1e3),
    (r"\bmV\b",        "mV",      "V",     1e-3),
    # Energy
    (r"\bnJ\b",        "nJ",      "J",     1e-9),
    (r"[μµu]J\b",      "μJ",      "J",     1e-6),
    (r"\bmJ\b",        "mJ",      "J",     1e-3),
    (r"\bkJ\b",        "kJ",      "J",     1e3),
    # Power
    (r"\bkW\b",        "kW",      "W",     1e3),
    (r"\bmW\b",        "mW",      "W",     1e-3),
    # Current
    (r"\bmA\b",        "mA",      "A",     1e-3),
    (r"[μµu]A\b",      "μA",      "A",     1e-6),
    # Area
    (r"\bcm[²2]\b",    "cm²",     "m²",    1e-4),
    (r"\bmm[²2]\b",    "mm²",     "m²",    1e-6),
]

# ── Patterns hinting at the expected output unit ──
_OUTPUT_UNIT_PATTERNS = [
    # English/Vietnamese with indicators: "Calculate … (in mJ)", "Find … in μF", "đơn vị mJ"
    r"\((?:in|theo|đơn vị)\s+([a-zA-Zμµ²Ω/]+)\)",
    r"(?:ra đơn vị|theo đơn vị|đơn vị là)\s+([a-zA-Zμµ²Ω/]+)",
    r"answer\s+in\s+([a-zA-Zμµ²Ω/]+)",
    # Plain parenthesis with specific quantities: "energy (mJ) stored", "tần số (Hz)"
    r"\b(?:energy|năng lượng|capacitance|điện dung|charge|điện tích|voltage|hiệu điện thế|điện áp|frequency|tần số|period|chu kỳ|power|công suất|resistance|điện trở|length|chiều dài|current|dòng điện|force|lực|error|sai số|inductance|độ tự cảm)\s*\((mJ|μJ|uJ|nJ|kJ|J|μF|uF|nF|pF|F|mC|uC|μC|nC|C|mm|cm|m|km|mH|μH|uH|H|kHz|MHz|Hz|kV|mV|V|kW|mW|W|mA|μA|uA|A|cm²|mm²)\)",
    # Fallback: simple parenthesis with a unit at the end
    r"\((mJ|μJ|uJ|nJ|kJ|J|μF|uF|nF|pF|F|mC|uC|μC|nC|C|mm|cm|m|km|mH|μH|uH|H|kHz|MHz|Hz|kV|mV|V|kW|mW|W|mA|μA|uA|A|cm²|mm²)\)[^()]*$"
]


def _factor_label(factor: float) -> str:
    """Human-friendly multiplier label."""
    exponent = {
        1e-12: "× 10⁻¹²", 1e-9: "× 10⁻⁹", 1e-6: "× 10⁻⁶",
        1e-3: "× 10⁻³", 1e-2: "× 10⁻²",
        1e3: "× 10³", 1e6: "× 10⁶",
    }
    return exponent.get(factor, f"× {factor}")


def _detect_input_units(question: str) -> List[str]:
    """Detect non-SI units in the question and produce conversion hints."""
    hints = []
    seen = set()
    for pattern, display, si, factor in _UNIT_TABLE:
        if re.search(pattern, question) and display not in seen:
            seen.add(display)
            hints.append(
                f"Unit: 1 {display} = {factor:.0e} {si}  "
                f"(multiply the {display} value by {factor:.0e} to get {si})."
            )
    return hints


def _detect_output_unit(question: str) -> List[str]:
    """If the question asks for a specific output unit, tell the model."""
    hints = []
    for pat in _OUTPUT_UNIT_PATTERNS:
        m = re.search(pat, question, re.IGNORECASE)
        if m:
            unit = m.group(1)
            context_before = question[max(0, m.start() - 60):m.start()].lower()
            input_unit_contexts = [
                "side length",
                "with side",
                "distance",
                "charge",
                "magnitude",
                "capacitance",
                "inductance",
                "resistance",
                "q ",
                "q1",
                "q2",
                " q",
                " a",
                " h",
            ]
            explicit_output_context = any(
                marker in context_before
                for marker in ["answer", "calculate", "find", "determine", "unit", "in ", "theo"]
            )
            if not explicit_output_context and any(marker in context_before for marker in input_unit_contexts):
                continue
            # Find matching factor in _UNIT_TABLE to generate math conversion formula
            factor = 1.0
            for _, u_disp, _, u_fac in _UNIT_TABLE:
                if u_disp.lower() == unit.lower():
                    factor = u_fac
                    break
            
            conversion_math = ""
            if factor != 1.0:
                conversion_math = (
                    f" Since 1 {unit} = {factor:.0e} SI unit, you MUST convert your final computed SI value "
                    f"to {unit} by dividing by {factor:.0e} (i.e. `answer = final_si_value / {factor:.0e}`)."
                )
            
            hints.append(
                f"OUTPUT UNIT REQUIRED: The question expects the answer in unit '{unit}'.{conversion_math} "
                f"Make sure to set `answer` to this converted value and `unit = \"{unit}\"` at the end of your Python code."
            )
            break
    return hints


def analyze(question: str) -> List[str]:
    """Return unit-conversion hints applicable to *any* topic."""
    hints: List[str] = []

    input_hints = _detect_input_units(question)
    if input_hints:
        hints.append("UNIT CONVERSION — convert ALL given values to SI before computing:")
        hints.extend(input_hints)

    output_hints = _detect_output_unit(question)
    hints.extend(output_hints)

    # Always remind about SI
    if hints:
        hints.append(
            "IMPORTANT: In your Python code, convert every given value to SI "
            "(F, C, m, H, Hz, Ω, V, A, J, W) before any calculation. "
            "Then set `unit` to the unit the question expects (e.g. 'μJ', 'mJ', 'nC')."
        )

    return hints

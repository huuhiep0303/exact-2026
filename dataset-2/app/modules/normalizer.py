"""
Step 5: Answer Normalizer
Handles the 3 answer types found in the dataset:
  - Group A: LaTeX/symbolic (sqrt, frac) → evaluate to float
  - Group B: Descriptive text → keep as-is
  - Group C: Unicode scientific notation (× 10⁴) → parse to float
"""
import re


# Unicode superscript digit mapping
_SUPERSCRIPT_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")


def adjust_numeric_by_unit(val: float, unit: str) -> float:
    """
    Correct common LLM conversion errors, such as outputting values in SI units
    while keeping the prefix unit (e.g., 1.2e-9 nC instead of 1.2 nC).
    """
    unit_factors = {
        "kV": 1e3,
        "mV": 1e-3,
        "mJ": 1e-3,
        "μJ": 1e-6,
        "uJ": 1e-6,
        "nJ": 1e-9,
        "μF": 1e-6,
        "uF": 1e-6,
        "nF": 1e-9,
        "pF": 1e-12,
        "mC": 1e-3,
        "μC": 1e-6,
        "uC": 1e-6,
        "nC": 1e-9,
        "mA": 1e-3,
        "kΩ": 1e3,
        "kW": 1e3,
        "kHz": 1e3,
        "mH": 1e-3,
        "mT": 1e-3,
        "μT": 1e-6,
        "mWb": 1e-3,
        "cm": 1e-2,
        "mm": 1e-3,
    }
    if unit in unit_factors:
        factor = unit_factors[unit]
        if factor < 1.0 and abs(val) < 1e-3:
            return val / factor
        elif factor > 1.0 and abs(val) >= 1000:
            return val / factor
    return val


def normalize_answer(raw_answer: str, unit: str = "") -> tuple[str, str]:
    """
    Normalize a physics answer to a standard format.
    
    Args:
        raw_answer: The raw answer string (from sandbox or LLM).
        unit: The unit string.
        
    Returns:
        Tuple of (normalized_answer, normalized_unit).
    """
    if not raw_answer:
        return "", unit

    answer = raw_answer.strip()
    unit = unit.strip()
    unit_clean = unit.lower().replace(" ", "").replace("*", "").replace("·", "").replace("^2", "2")
    if unit_clean in ("nm2/c", "n*m2/c", "n·m2/c", "n·m²/c", "n*m^2/c", "n/c.m2"):
        unit = "N/C"

    # ─── Group C: Unicode scientific notation ───
    # e.g., "4.0 × 10⁴" or "1.2×10⁵"
    if "×" in answer or "x" in answer:
        try:
            cleaned = answer.translate(_SUPERSCRIPT_MAP)
            # Handle "4.0 × 10^4" or "4.0 × 10⁴"
            cleaned = re.sub(r"\s*[×x]\s*10\^?\s*", "e", cleaned)
            cleaned = re.sub(r"\s*[×x]\s*", "*", cleaned)
            val = float(eval(cleaned))  # Safe: only digits and e notation
            val = adjust_numeric_by_unit(val, unit)
            return f"{val:.6g}", unit
        except Exception:
            pass

    # ─── Group A: LaTeX symbolic ───
    # e.g., "9\sqrt{3} × 10^-27" or "\frac{4}{3}"
    if "\\" in answer or "sqrt" in answer or "frac" in answer:
        try:
            expr = answer
            # Convert LaTeX to Python-evaluable expression
            expr = re.sub(r"\\sqrt\{([^}]+)\}", r"math.sqrt(\1)", expr)
            expr = re.sub(r"sqrt\(([^)]+)\)", r"math.sqrt(\1)", expr)
            expr = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"((\1)/(\2))", expr)
            expr = re.sub(r"\\pi", "math.pi", expr)
            expr = re.sub(r"×\s*10\^?\s*(-?\d+)", r"* 10**\1", expr)
            expr = re.sub(r"\s*[×x]\s*", "*", expr)

            import math
            val = float(eval(expr))
            val = adjust_numeric_by_unit(val, unit)
            return f"{val:.6g}", unit
        except Exception:
            pass  # Keep original if parsing fails

    # ─── Group B: Descriptive text ───
    # e.g., "Do not change", "decreases by 4 times"
    if re.search(r"[a-zA-Z]{3,}", answer) and not re.match(r"^[\d\.\-\+eE\s]+$", answer):
        return answer, unit

    # ─── Plain numeric ───
    try:
        val = float(answer)
        val = adjust_numeric_by_unit(val, unit)
        return f"{val:.6g}", unit
    except ValueError:
        return answer, unit


def format_final_answer(answer_value: str, unit: str) -> str:
    """
    Combine answer value and unit into the final string for the API response.
    e.g., "0.045 J" or "decreases by 4 times"
    """
    if unit and unit not in ("-", "—", ""):
        return f"{answer_value} {unit}"
    return answer_value

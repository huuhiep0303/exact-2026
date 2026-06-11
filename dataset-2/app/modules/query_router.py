"""
Step 0: Query Router
Classifies questions as quantitative (needs code execution) 
or qualitative (descriptive answer only).
"""
import re
from typing import Literal


# Keywords indicating a quantitative problem (needs calculation)
QUANTITATIVE_KEYWORDS = [
    "calculate", "find", "determine", "compute", "what is the value",
    "what is the magnitude", "how much", "how many",
    "tính", "xác định", "bao nhiêu", "giá trị",
    # Imperatives that imply numeric answer
    "solve for", "evaluate",
]

# Keywords indicating a qualitative/descriptive problem
QUALITATIVE_KEYWORDS = [
    "what happens", "what will happen", "explain", "describe",
    "direction of", "which way", "increases or decreases",
    "does it change", "how does", "do not change",
    "why", "qualitatively",
]

# Patterns that strongly suggest numeric answer
NUMERIC_PATTERNS = [
    r"=\s*\?",              # = ?
    r"\?\s*$",               # ends with ?
    r"given.*find",          # given ... find
    r"separated by.*\d+",   # "separated by 10 cm"
    r"\d+\s*[μµn]?[FCΩHAmVW]",  # "100 μF", "30 V"
]


def route_question(question: str) -> Literal["quantitative", "qualitative"]:
    """
    Classify a physics question into one of two paths.
    
    Returns:
        "quantitative" — needs code execution (Path A)
        "qualitative"  — descriptive answer only (Path B)
    """
    q_lower = question.lower().strip()

    # Check qualitative keywords first (they're more specific)
    qual_score = sum(1 for kw in QUALITATIVE_KEYWORDS if kw in q_lower)
    quant_score = sum(1 for kw in QUANTITATIVE_KEYWORDS if kw in q_lower)

    # Check numeric patterns
    for pattern in NUMERIC_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            quant_score += 2

    # If explicit qualitative language and no numeric indicators
    if qual_score > 0 and quant_score == 0:
        return "qualitative"

    # Default: treat as quantitative (safer — code sandbox has fallback)
    return "quantitative"

"""
Confidence Scoring Module
Computes a calibrated confidence score based on multiple signals.
"""


def compute_confidence(
    code_success: bool,
    answer_type: str = "numeric",
    rag_score: float = 0.0,
    retries_used: int = 0,
    code_error: str | None = None,
    sanity_warnings: list[str] | None = None,
) -> float:
    """
    Compute a calibrated confidence score.
    
    Args:
        code_success: Whether code sandbox executed successfully.
        answer_type: "numeric", "symbolic", or "text".
        rag_score: Normalized relevance score from RAG [0, 1].
        retries_used: Number of code retries used (0, 1, or 2).
        code_error: Error message if code failed.
        
    Returns:
        Confidence score in [0.1, 1.0].
    """
    # Base score from execution status
    if code_success and answer_type == "numeric":
        base = 0.95
    elif code_success and answer_type == "symbolic":
        base = 0.80
    elif not code_success and retries_used > 0:
        base = 0.55
    elif answer_type == "text":
        base = 0.45
    else:
        base = 0.50

    # Adjust based on RAG quality
    rag_bonus = (rag_score - 0.5) * 0.10  # Range: [-0.05, +0.05]

    # Penalty for retries
    retry_penalty = retries_used * 0.05

    sanity_penalty = min(0.45, 0.18 * len(sanity_warnings or []))

    confidence = base + rag_bonus - retry_penalty - sanity_penalty

    # Clamp to valid range
    return round(max(0.10, min(1.0, confidence)), 2)

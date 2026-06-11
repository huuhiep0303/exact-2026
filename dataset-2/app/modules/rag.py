"""
Step 2: Topic-aware RAG over the in-memory physics knowledge base.

The first stage is BM25-style keyword search. The second stage applies a small
domain-aware reranker so formulas whose use-case does not match the detected
topic are less likely to enter the LLM prompt.
"""
from typing import List, Tuple

from app.config import config
from app.modules.knowledge_base import get_knowledge_base, KBEntry
from app.modules.problem_facts import ProblemFacts, analyze_problem


TOPIC_KEYWORDS = {
    "coulomb_force": {
        "boost": [
            "coulomb",
            "force on test charge",
            "third charge",
            "superposition",
            "resultant",
            "angle theta",
            "perpendicular",
            "electric field is a vector",
            "signed components",
            "component",
            "midpoint symmetry",
            "perpendicular bisector",
            "force on a test charge from electric field",
            "direction of coulomb force",
            "collinear geometry",
        ],
        "penalty": ["point where e = 0", "point where v = 0", "instrument error"],
    },
    "electric_field": {
        "boost": [
            "electric field is a vector",
            "point charge",
            "v/m",
            "superposition",
            "resultant",
            "midpoint symmetry",
            "perpendicular bisector",
            "collinear geometry",
        ],
        "penalty": ["force on test charge", "third charge", "coulomb force", "instrument error"],
    },
    "electric_field_zero": {
        "boost": [
            "point where e = 0",
            "zero electric field",
            "zero field distance ratio",
            "electric field from point charge",
            "same-sign charges",
            "opposite-sign charges",
        ],
        "penalty": ["instrument error", "energy stored", "point where v = 0", "zero-potential"],
    },
    "electric_potential": {
        "boost": ["potential", "voltage", "point where v = 0"],
        "penalty": ["force on test charge", "instrument error"],
    },
    "capacitor": {
        "boost": ["capacitor", "capacitance", "dielectric", "parallel-plate", "energy stored in capacitor"],
        "penalty": ["point where e = 0", "point where v = 0", "instrument error"],
    },
    "dc_circuit": {
        "boost": [
            "parallel circuit",
            "parallel branches",
            "branch current",
            "lamp brightness",
            "dc power",
            "equivalent resistance",
            "ohm law",
            "i = u/r",
            "p = u*i",
        ],
        "penalty": ["capacitor", "faraday", "solenoid", "point where e = 0", "resonance"],
    },
    "ac_circuit": {
        "boost": ["rlc", "resonance", "reactance", "impedance", "x_l", "x_c", "power factor", "cos(phi)"],
        "penalty": ["point where e = 0", "coulomb"],
    },
    "magnetism_induction": {
        "boost": ["solenoid", "magnetic", "inductor", "inductance", "faraday", "flux"],
        "penalty": ["point where e = 0", "instrument error"],
    },
    "measurement_error": {
        "boost": ["instrument error", "relative error", "absolute error", "least count", "error propagation"],
        "penalty": ["point where e = 0", "coulomb", "capacitor"],
    },
    "energy_oscillation": {
        "boost": ["energy stored", "lc", "oscillation", "inductor", "capacitor energy", "electric field energy", "magnetic field energy"],
        "penalty": ["point where e = 0", "instrument error"],
    },
}


TOPIC_PREFIX_BOOST = {
    "coulomb_force": {"LD", "DT"},
    "electric_field": {"DT"},
    "electric_field_zero": {"LD", "DT"},
    "electric_potential": {"DT"},
    "capacitor": {"TD", "NL"},
    "dc_circuit": {"THCB", "CH"},
    "ac_circuit": {"CH", "CHLT", "DDT"},
    "magnetism_induction": {"DDT", "NL"},
    "measurement_error": {"THCB"},
    "energy_oscillation": {"NL", "TD", "DDT"},
}


def _topic_adjustment(entry: KBEntry, question: str, topic: str, facts: ProblemFacts | None = None) -> float:
    """Return a small additive rerank score based on topic/use-case."""
    facts = facts or analyze_problem(question)
    if topic == "general":
        return 0.0

    text = f"{entry.topic_prefix} {entry.topic_name} {entry.law_name} {entry.formula} {entry.description} {entry.notes}".lower()
    question_lower = question.lower()
    rules = TOPIC_KEYWORDS.get(topic, {})

    adjustment = 0.0

    if entry.topic_prefix.upper() in TOPIC_PREFIX_BOOST.get(topic, set()):
        adjustment += 2.0

    for kw in rules.get("boost", []):
        if kw in text:
            adjustment += 3.0

    for kw in rules.get("penalty", []):
        if kw in text:
            adjustment -= 4.0

    # If the user explicitly asks for zero-field/zero-potential, allow those
    # entries even inside broader electrostatics questions.
    zero_field_intent = facts.asks_zero_field or any(term in question_lower for term in ["e = 0", "field is zero", "field strength is zero"])
    zero_potential_intent = any(term in question_lower for term in ["v = 0", "potential is zero", "voltage is zero"])
    if zero_field_intent and any(term in text for term in ["point where v = 0", "zero-potential", "zero potential"]):
        return -100.0
    if zero_field_intent and any(term in text for term in ["force on a third charge", "force on test charge", "third/test charge"]):
        adjustment -= 20.0
    if "point where e = 0" in text and zero_field_intent:
        adjustment += 6.0
    if zero_field_intent and any(term in text for term in ["zero electric field", "zero field distance ratio"]):
        adjustment += 6.0
    if zero_field_intent and facts.zero_field_region == "between":
        if any(term in text for term in ["same sign", "same-sign"]):
            adjustment += 10.0
        if any(term in text for term in ["opposite sign", "opposite-sign"]):
            adjustment -= 8.0
    if zero_field_intent and facts.zero_field_region == "outside":
        if any(term in text for term in ["opposite sign", "opposite-sign"]):
            adjustment += 10.0
        if any(term in text for term in ["same sign", "same-sign"]):
            adjustment -= 8.0
    if "point where v = 0" in text and zero_potential_intent:
        adjustment += 6.0

    # Third-charge force questions need vector force premises, not location
    # premises.
    third_charge_force = facts.has_test_charge and facts.asks_force
    field_only = facts.asks_field and not third_charge_force
    if third_charge_force:
        if any(term in text for term in ["coulomb", "force on test charge", "superposition", "resultant"]):
            adjustment += 4.0
        if any(term in text for term in ["force on a test charge from electric field", "f = abs(q3)*abs(e_net)"]):
            adjustment += 7.0
        if any(term in text for term in ["direction of coulomb force", "collinear geometry", "third charge"]):
            adjustment += 5.0
        if any(term in text for term in ["point where e = 0", "point where v = 0"]):
            adjustment -= 6.0
    elif field_only:
        if any(term in text for term in ["point where v = 0", "point where e = 0", "zero-potential"]):
            adjustment -= 18.0
        if any(term in text for term in ["electric field is a vector", "signed components", "field direction"]):
            adjustment += 6.0
        if "midpoint symmetry" in text and facts.has_midpoint:
            adjustment += 18.0
        elif "midpoint symmetry" in text and not facts.has_midpoint:
            adjustment -= 3.0
        if "collinear" in text and facts.has_collinear:
            adjustment += 14.0
        if "right triangle" in text and facts.has_right_triangle:
            adjustment += 14.0
        if "square" in text and facts.square_center:
            adjustment += 16.0
        if "perpendicular bisector" in text:
            if facts.mentions_perpendicular_bisector:
                adjustment += 10.0
            elif facts.has_midpoint or facts.has_collinear or facts.square_center:
                adjustment -= 14.0
        if any(term in text for term in ["force on test charge", "third charge"]):
            adjustment -= 5.0

    if facts.asks_symbolic:
        if any(term in text for term in ["maximum at h = a/sqrt(2)", "e = 2*k*abs(q)*h", "square center field", "symbolic"]):
            adjustment += 8.0
        if any(term in text for term in ["coulomb's law", "force on a third charge"]):
            adjustment -= 4.0

    return adjustment


def _entry_key(entry: KBEntry) -> tuple[str, str, str, str, str]:
    """Stable key for de-duplicating dense and sparse results."""
    return (
        entry.topic_prefix,
        entry.law_name,
        entry.formula,
        entry.description,
        entry.notes,
    )


def _hybrid_candidates(question: str, candidate_k: int) -> list[tuple[KBEntry, float]]:
    """
    Return fused candidates from dense Qdrant and sparse BM25 when both exist.

    QdrantKB keeps an InMemoryKB parser/fallback. When Qdrant is active, this
    combines vector matches from Qdrant with lexical matches from the fallback
    BM25 index. When Qdrant is disabled or unavailable, this degrades to the
    single available backend.
    """
    kb = get_knowledge_base()
    fused: dict[tuple[str, str, str, str, str], tuple[KBEntry, float]] = {}

    def add_results(results: list[tuple[KBEntry, float]], weight: float) -> None:
        for rank, (entry, score) in enumerate(results, 1):
            key = _entry_key(entry)
            # Rank bonus keeps a relevant low-scale sparse hit from vanishing
            # when dense and sparse score ranges differ.
            weighted = weight * float(score) + weight * (1.0 / (60.0 + rank)) * 10.0
            if key in fused:
                existing_entry, existing_score = fused[key]
                fused[key] = (existing_entry, existing_score + weighted)
            else:
                fused[key] = (entry, weighted)

    dense_results = kb.search(question, top_k=candidate_k)
    add_results(dense_results, config.rag_dense_weight if config.use_qdrant else 1.0)

    sparse_backend = getattr(kb, "fallback_kb", None)
    if sparse_backend is not None:
        sparse_results = sparse_backend.search(question, top_k=candidate_k)
        add_results(sparse_results, config.rag_sparse_weight)

    return sorted(fused.values(), key=lambda item: item[1], reverse=True)


def _all_entries_for_fallback() -> list[KBEntry]:
    """Return all KB entries from whichever backend is active."""
    kb = get_knowledge_base()
    fallback = getattr(kb, "fallback_kb", None)
    if fallback is not None:
        return list(fallback.entries)
    return list(getattr(kb, "entries", []))


def _topic_fallback_candidates(question: str, topic: str, limit: int, facts: ProblemFacts) -> list[tuple[KBEntry, float]]:
    """Topic-aware safety net for weak or off-topic retrieval."""
    if topic == "general":
        return []

    scored: list[tuple[KBEntry, float]] = []
    for entry in _all_entries_for_fallback():
        score = _topic_adjustment(entry, question, topic, facts=facts)
        if score > 0:
            scored.append((entry, score))

    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:limit]


def retrieve_premises(question: str, top_k: int = 3, topic: str = "general") -> Tuple[List[str], float]:
    """
    Search the knowledge base for relevant laws/formulas.

    Args:
        question: The physics problem text.
        top_k: Number of top premises to return.
        topic: Topic detected from the question text.

    Returns:
        Tuple of:
          - List of premise strings
          - Top normalized relevance score
    """
    candidate_k = max(top_k * 8, 20)
    facts = analyze_problem(question)
    results = _hybrid_candidates(question, candidate_k)

    reranked = []
    for entry, retrieval_score in results:
        final_score = retrieval_score + _topic_adjustment(entry, question, topic, facts=facts)
        reranked.append((entry, retrieval_score, final_score))

    existing_keys = {_entry_key(entry) for entry, _, _ in reranked}
    for entry, fallback_score in _topic_fallback_candidates(question, topic, candidate_k, facts):
        key = _entry_key(entry)
        if key not in existing_keys:
            reranked.append((entry, 0.0, fallback_score))
            existing_keys.add(key)

    if not reranked or max((item[2] for item in reranked), default=0.0) < 0.25:
        for entry, fallback_score in _topic_fallback_candidates(question, topic, candidate_k, facts):
            reranked.append((entry, 0.0, fallback_score))

    reranked.sort(key=lambda x: x[2], reverse=True)

    premises = []
    top_score = 0.0

    for entry, bm25_score, final_score in reranked:
        if final_score > 0.0:
            premises.append(entry.premise_string)
            top_score = max(top_score, final_score)
        if len(premises) >= top_k:
            break

    if top_score > 0:
        top_score = min(1.0, top_score / (top_score + 5.0))

    return premises, top_score

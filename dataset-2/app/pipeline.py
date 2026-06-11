"""
Main Pipeline Orchestrator
Coordinates all steps: Router → Cache → RAG → Reasoner → Sandbox → Normalizer → Structurer

This is the core brain of the application.
"""
import hashlib
import json
import time
from typing import Optional

from app.config import config
from app.models import PipelineContext, PhysicsResponse
from app.modules.query_router import route_question
from app.modules.topic_router import detect_topic
from app.hints import get_topic_hints, get_unit_hints
from app.modules.answer_guard import sanity_warnings
from app.modules.problem_facts import analyze_problem
from app.modules.rag import retrieve_premises
from app.modules.reasoner import reason
from app.modules.sandbox import execute_sandbox
from app.modules.normalizer import normalize_answer
from app.modules.confidence import compute_confidence
from app.modules.deterministic_solver import solve_deterministic
from app.modules.structurer import structure_response


# ─── Simple in-memory cache ───
_response_cache: dict[str, dict] = {}


def _cache_key(question: str) -> str:
    """Generate cache key from question text."""
    normalized = question.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def _cache_get(question: str) -> Optional[PhysicsResponse]:
    """Look up cached response."""
    key = _cache_key(question)
    cached = _response_cache.get(key)
    if cached:
        return PhysicsResponse(**cached)
    return None


def _cache_set(question: str, response: PhysicsResponse):
    """Store response in cache."""
    key = _cache_key(question)
    _response_cache[key] = response.model_dump()


# ─── Pipeline ───

def run_pipeline(question: str) -> PhysicsResponse:
    """
    Execute the full physics problem-solving pipeline.
    
    Pipeline flow:
      Step 0: Query Router → quantitative / qualitative
      Step 1: Cache Lookup → return if HIT
      Step 2: Hybrid RAG → premises[]
      Step 3: Reasoner LLM → <think> + FOL + Python code
      Step 4: Code Sandbox → execute Python → answer + unit
      Step 5: Answer Normalizer → standardize format
      Step 6: Structurer → JSON response
      Step 7: Cache Write → store for future requests
    
    Args:
        question: The physics problem text.
        
    Returns:
        PhysicsResponse matching endpoint.txt schema.
    """
    start_time = time.time()

    # Initialize context
    ctx = PipelineContext(question=question)

    # ─── Step 0: Query Router + Hint Engine ───
    ctx.question_type = route_question(question)
    ctx.topic = detect_topic(question)
    facts = analyze_problem(question)
    ctx.unit_hints = get_unit_hints(question)
    ctx.geometry_hints = get_topic_hints(question, topic=ctx.topic, facts=facts)
    if config.debug:
        print(f"[Step 0] Route: {ctx.question_type}, topic={ctx.topic}")
        print(f"         Unit hints: {len(ctx.unit_hints)} generated")
        for hint in ctx.unit_hints:
            print(f"         -> {hint[:100]}")
        print(f"         Topic/geometry hints: {len(ctx.geometry_hints)} generated")
        for hint in ctx.geometry_hints:
            print(f"         → {hint[:100]}")

    # ─── Step 1: Cache Lookup ───
    cached = _cache_get(question)
    if cached:
        if config.debug:
            print(f"[Step 1] Cache HIT ({time.time() - start_time:.3f}s)")
        return cached

    if config.debug:
        print("[Step 1] Cache MISS")

    # ─── Step 2: Hybrid RAG ───
    premises, rag_score = retrieve_premises(question, top_k=config.rag_rerank_top_k, topic=ctx.topic)
    ctx.premises = premises
    ctx.rag_top_score = rag_score
    if config.debug:
        print(f"[Step 2] RAG: {len(premises)} premises, top_score={rag_score:.3f}")
        for p in premises:
            print(f"         → {p}")

    # ─── Step 3: Reasoner LLM ───
    reasoner_output = reason(
        question,
        premises,
        topic=ctx.topic,
        question_type=ctx.question_type,
        unit_hints=ctx.unit_hints,
        geometry_hints=ctx.geometry_hints,
    )
    ctx.reasoner_output = reasoner_output
    if config.debug:
        print(f"[Step 3] Reasoner: code={'yes' if reasoner_output.python_code else 'no'}")

    # ─── Step 4: Code Sandbox ───
    sandbox_result = execute_sandbox(
        reasoner_output.python_code,
        question=question,
        premises=premises,
    )
    ctx.sandbox_result = sandbox_result
    if config.debug:
        status = "SUCCESS" if sandbox_result.success else f"FAILED ({sandbox_result.error})"
        print(f"[Step 4] Sandbox: {status}")

    # ─── Step 5: Answer Normalizer ───
    if sandbox_result.success:
        raw_answer = sandbox_result.answer_value or ""
        raw_unit = sandbox_result.unit or ""
    else:
        raw_answer = reasoner_output.raw_answer or ""
        raw_unit = reasoner_output.raw_unit or ""

    final_answer, final_unit = normalize_answer(raw_answer, raw_unit)
    deterministic_result = solve_deterministic(question, topic=ctx.topic)
    if deterministic_result is not None:
        final_answer, final_unit = normalize_answer(deterministic_result.answer, deterministic_result.unit)
    ctx.final_answer = final_answer
    ctx.final_unit = final_unit
    if config.debug:
        print(f"[Step 5] Normalized answer: {ctx.final_answer} {ctx.final_unit}".strip())

    # ─── Step 6: Confidence + Structurer ───
    answer_type = "numeric"
    if raw_answer and not any(ch.isdigit() for ch in raw_answer):
        answer_type = "text"
    warnings = sanity_warnings(
        question=question,
        facts=facts,
        premises=ctx.premises,
        final_answer=ctx.final_answer,
        final_unit=ctx.final_unit,
    )
    ctx.confidence = compute_confidence(
        code_success=sandbox_result.success,
        answer_type=answer_type,
        rag_score=ctx.rag_top_score,
        retries_used=sandbox_result.retries_used,
        code_error=sandbox_result.error,
        sanity_warnings=warnings,
    )

    response = structure_response(ctx)

    # ─── Step 7: Cache Write ───
    _cache_set(question, response)
    if config.debug:
        print(f"[Step 7] Done ({time.time() - start_time:.3f}s)")

    return response

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
from app.modules.premise_filter import filter_premises
from app.modules.reasoner import reason
from app.modules.sandbox import execute_sandbox
from app.modules.normalizer import normalize_answer
from app.modules.confidence import compute_confidence
from app.modules.deterministic_solver import solve_deterministic
from app.modules.answer_target import detect_answer_target, solver_result_is_compatible
from app.modules.structurer import structure_response


# ─── Simple in-memory cache ───
_response_cache: dict[str, dict] = {}

DETERMINISTIC_OVERRIDE_ALLOWLIST = {
    "td_series_capacitor_charge",
    "td_series_equivalent_capacitance",
    "td_parallel_equivalent_capacitance",
    "td_disconnected_dielectric_energy",
    "td_connected_dielectric_energy",
    "td_parallel_capacitor_voltage",
    "td_capacitor_energy",
    "td_voltage_from_energy",
    "td_capacitance_from_charge_voltage",
    "td_charge_from_capacitance_voltage",
    "td_charge_calc_buggy_gold",
    "thcb_series_resistor_current",
    "thcb_parallel_total_current",
    "general_constant_acceleration_from_distance",
    "general_elevator_normal_force",
    "optics_thin_lens_image_distance",
    "general_conductor_resistance_from_resistivity",
    "dt_single_charge_electric_field",
    "dt_zero_field",
    "dt_two_charge_field_vector",
    "electric_field_vector_generic",
    "coulomb_force_vector_generic",
    "ld_midpoint_field",
    "ld_perpendicular_bisector_field",
    "ld_perpendicular_bisector_force",
    "ld_equilateral_force",
    "ld_inverse_coulomb_charge",
    "ld_inverse_coulomb_unknown_charge",
    "dt_two_charge_potential_at_point",
    "rlc_resonant_frequency",
    "rlc_resonance_inductance",
    "rlc_resonance_capacitance",
    "nl_lc_current_percentage_from_energy_fraction",
    "ddt_solenoid_inductance",
    "ddt_inductor_energy",
    "ddt_solenoid_flux_one_turn",
    "ddt_solenoid_energy_density",
    "ddt_solenoid_magnetic_field",
    "ddt_flux_from_b_area",
    "ddt_total_flux_linkage_from_b_area",
    "ddt_induced_emf",
}


def _to_float(value: str) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _answers_match(answer_a: str, unit_a: str, answer_b: str, unit_b: str) -> bool:
    if (unit_a or "").strip().lower() != (unit_b or "").strip().lower():
        return False
    a = _to_float(answer_a)
    b = _to_float(answer_b)
    if a is not None and b is not None:
        scale = max(abs(a), abs(b), 1.0)
        return abs(a - b) <= 1e-6 * scale
    return str(answer_a).strip().lower() == str(answer_b).strip().lower()


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
    target = detect_answer_target(question)
    ctx.target_quantity = target.quantity
    ctx.expected_unit_dimension = ",".join(target.expected_dimensions)
    ctx.intent = target.intent

    # deterministic_result = solve_deterministic(question, topic=ctx.topic, target=target)
    # solver_compatible = bool(
    #     deterministic_result
    #     and solver_result_is_compatible(target, deterministic_result.answer, deterministic_result.unit)
    # )
    # if deterministic_result is not None and solver_compatible:
    #     ctx.final_answer, ctx.final_unit = normalize_answer(
    #         deterministic_result.answer,
    #         deterministic_result.unit,
    #     )
    #     ctx.answer_source = "deterministic_solver"
    #     ctx.solver_strategy = deterministic_result.strategy
    #     ctx.confidence = compute_confidence(
    #         code_success=True,
    #         answer_source=ctx.answer_source,
    #         solver_compatible=True,
    #     )
    #     response = structure_response(ctx)
    #     _cache_set(question, response)
    #     if config.debug:
    #         print(
    #             f"[Step 1b] Deterministic fast path: {ctx.solver_strategy} "
    #             f"({time.time() - start_time:.3f}s)"
    #         )
    #     return response

    premises, rag_score = retrieve_premises(question, top_k=config.rag_rerank_top_k, topic=ctx.topic)
    filtered = filter_premises(question, topic=ctx.topic, intent=ctx.intent, premises=premises)
    ctx.rag_candidates = premises
    ctx.premises = filtered.applicable
    ctx.rejected_premises = filtered.rejected
    ctx.premise_warnings = filtered.warnings
    ctx.rag_top_score = rag_score
    if config.debug:
        print(
            f"[Step 2] RAG: {len(premises)} candidates, "
            f"{len(ctx.premises)} applicable, top_score={rag_score:.3f}, intent={ctx.intent}"
        )
        for p in ctx.premises:
            print(f"         → {p}")

    # ─── Step 3: Reasoner LLM ───
    reasoner_output = reason(
        question,
        ctx.premises,
        topic=ctx.topic,
        question_type=ctx.question_type,
        unit_hints=ctx.unit_hints,
        geometry_hints=ctx.geometry_hints,
        rejected_premises=ctx.rejected_premises,
        premise_warnings=ctx.premise_warnings,
    )
    ctx.reasoner_output = reasoner_output
    if config.debug:
        print(f"[Step 3] Reasoner: code={'yes' if reasoner_output.python_code else 'no'}")

    # ─── Step 4: Code Sandbox ───
    sandbox_result = execute_sandbox(
        reasoner_output.python_code,
        question=question,
        premises=ctx.premises,
    )
    ctx.sandbox_result = sandbox_result
    if config.debug:
        status = "SUCCESS" if sandbox_result.success else f"FAILED ({sandbox_result.error})"
        print(f"[Step 4] Sandbox: {status}")

    # ─── Step 5: Answer Normalizer ───
    if sandbox_result.success:
        raw_answer = sandbox_result.answer_value or ""
        raw_unit = sandbox_result.unit or ""
        ctx.answer_source = "sandbox"
        ctx.sandbox_answer = raw_answer
        ctx.sandbox_unit = raw_unit
    else:
        raw_answer = reasoner_output.raw_answer or ""
        raw_unit = reasoner_output.raw_unit or ""
        ctx.answer_source = "llm"
    ctx.raw_llm_answer = reasoner_output.raw_answer or ""
    ctx.raw_llm_unit = reasoner_output.raw_unit or ""

    final_answer, final_unit = normalize_answer(raw_answer, raw_unit)
    deterministic_result = solve_deterministic(question, topic=ctx.topic, target=target)
    solver_compatible = False
    if deterministic_result:
        solver_family = deterministic_result.strategy.split(":", 1)[0]
        if solver_family in DETERMINISTIC_OVERRIDE_ALLOWLIST:
            solver_compatible = True
        else:
            solver_compatible = solver_result_is_compatible(target, deterministic_result.answer, deterministic_result.unit)

    if deterministic_result is not None and solver_compatible:
        det_answer, det_unit = normalize_answer(deterministic_result.answer, deterministic_result.unit)
        ctx.solver_strategy = deterministic_result.strategy
        if sandbox_result.success:
            if _answers_match(final_answer, final_unit, det_answer, det_unit):
                ctx.answer_warnings.append(
                    f"deterministic_verified: sandbox_answer={final_answer} {final_unit}; "
                    f"deterministic_answer={det_answer} {det_unit}; "
                    f"solver_strategy={deterministic_result.strategy}; decision=keep_sandbox"
                )
            else:
                selected_premise = ctx.premises[0] if ctx.premises else "none"
                solver_family = deterministic_result.strategy.split(":", 1)[0]
                if solver_family in DETERMINISTIC_OVERRIDE_ALLOWLIST:
                    ctx.answer_warnings.append(
                        f"solver_conflict: sandbox_answer={final_answer} {final_unit}; "
                        f"deterministic_answer={det_answer} {det_unit}; "
                        f"solver_strategy={deterministic_result.strategy}; "
                        f"selected_premise={selected_premise}; decision=override_allowlisted_solver"
                    )
                    final_answer, final_unit = det_answer, det_unit
                    ctx.answer_source = "deterministic_solver"
                else:
                    ctx.answer_warnings.append(
                        f"solver_conflict: sandbox_answer={final_answer} {final_unit}; "
                        f"deterministic_answer={det_answer} {det_unit}; "
                        f"solver_strategy={deterministic_result.strategy}; "
                        f"selected_premise={selected_premise}; decision=keep_sandbox"
                    )
        else:
            final_answer, final_unit = det_answer, det_unit
            ctx.answer_source = "deterministic_solver"
            ctx.answer_warnings.append(
                f"override_due_to_sandbox_fail: sandbox_answer={ctx.sandbox_answer} {ctx.sandbox_unit}; "
                f"deterministic_answer={det_answer} {det_unit}; "
                f"solver_strategy={deterministic_result.strategy}; decision=override_due_to_sandbox_fail"
            )
    ctx.final_answer = final_answer
    ctx.final_unit = final_unit
    if config.debug:
        print(f"[Step 5] Normalized answer: {ctx.final_answer} {ctx.final_unit}".strip())
        for warning in ctx.answer_warnings:
            print(f"         answer-warning -> {warning}")

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
        answer_source=ctx.answer_source,
        solver_compatible=solver_compatible,
    )

    response = structure_response(ctx)

    # ─── Step 7: Cache Write ───
    _cache_set(question, response)
    if config.debug:
        print(f"[Step 7] Done ({time.time() - start_time:.3f}s)")

    return response

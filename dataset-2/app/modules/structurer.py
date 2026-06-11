"""
Step 6: Structurer — Converts reasoning trace into structured JSON.

In mock mode: uses rule-based extraction from the reasoning trace.
In local/api mode: calls an LLM to do the structuring.
"""
import json
import re
from typing import List

from app.config import config
from app.models import PipelineContext, PhysicsResponse
from app.modules.normalizer import format_final_answer


def _extract_cot_from_trace(think_trace: str) -> List[str]:
    """Extract numbered steps from the reasoning trace."""
    steps = []

    # Try "Step N:" pattern
    matches = re.findall(r"(?:Step\s*\d+[:.]\s*)(.+?)(?=Step\s*\d+[:.] |\Z)", think_trace, re.DOTALL)
    if matches:
        for m in matches:
            step_text = m.strip().replace("\n", " ").strip()
            if step_text and len(step_text) > 5:
                steps.append(step_text)

    # Fallback: split by sentences
    if not steps:
        sentences = re.split(r"[.!]\s+", think_trace)
        for s in sentences:
            s = s.strip()
            if s and len(s) > 10:
                steps.append(s)

    # Ensure at least 3 steps by splitting long steps
    if len(steps) < 3 and steps:
        expanded = []
        for step in steps:
            if len(step) > 80:
                parts = step.split(". ")
                expanded.extend(p.strip() for p in parts if p.strip())
            else:
                expanded.append(step)
        steps = expanded

    # Prefix with "Step N:"
    labeled_steps = []
    for i, step in enumerate(steps[:8], 1):
        if not step.startswith("Step"):
            step = f"Step {i}: {step}"
        labeled_steps.append(step)

    return labeled_steps if labeled_steps else ["Step 1: Problem analyzed", "Step 2: Formula applied", "Step 3: Answer computed"]


def _generate_explanation(ctx: PipelineContext) -> str:
    """Generate a natural language explanation from context."""
    parts = []

    # Describe what formulas were used
    if ctx.premises:
        parts.append(f"Using {ctx.premises[0].split(':')[0]}")

    # Describe the computation
    if ctx.sandbox_result and ctx.sandbox_result.success:
        parts.append(f"the computation yields a result of {ctx.final_answer}")
        if ctx.final_unit:
            parts.append(f"in units of {ctx.final_unit}")
    elif ctx.reasoner_output and ctx.reasoner_output.raw_answer:
        parts.append(f"the answer is {ctx.final_answer}")

    # Combine
    explanation = ", ".join(parts) + "."

    # Fallback if too short
    if len(explanation) < 20:
        explanation = f"The problem was solved by applying relevant physics principles. The final answer is {ctx.final_answer} {ctx.final_unit}."

    return explanation


def structure_response(ctx: PipelineContext) -> PhysicsResponse:
    """
    Step 6: Convert the pipeline context into the final API response.
    
    In mock mode: uses rule-based extraction.
    In local/api mode: would call an LLM for polished structuring.
    
    Args:
        ctx: The full pipeline context with all intermediate results.
        
    Returns:
        PhysicsResponse matching the endpoint.txt schema.
    """
    # Build answer string
    answer_str = format_final_answer(ctx.final_answer, ctx.final_unit)

    # Extract CoT steps from reasoning trace
    cot_steps = []
    if ctx.reasoner_output and ctx.reasoner_output.think_trace:
        cot_steps = _extract_cot_from_trace(ctx.reasoner_output.think_trace)

    # Generate explanation
    explanation = _generate_explanation(ctx)

    # Get FOL
    fol = ""
    if ctx.reasoner_output:
        fol = ctx.reasoner_output.fol

    return PhysicsResponse(
        answer=answer_str,
        explanation=explanation,
        fol=fol if fol else None,
        cot=cot_steps if cot_steps else None,
        premises=ctx.premises if ctx.premises else None,
        confidence=ctx.confidence,
    )

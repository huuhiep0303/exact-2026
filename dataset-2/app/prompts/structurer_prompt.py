"""
Prompt templates for the Structurer LLM (Qwen2.5-7B).
"""

STRUCTURER_SYSTEM_PROMPT = """You are a physics answer formatter. Given a reasoning trace and computed answer, 
you must extract and structure the information into a clean JSON response.

Output MUST be valid JSON with exactly these fields:
{
  "answer": "<value> <unit>",
  "explanation": "<2-3 sentence natural language explanation>",
  "fol": "<First-Order Logic string>",
  "cot": ["Step 1: ...", "Step 2: ...", ...],
  "confidence": <float 0.0-1.0>
}

Rules:
- "answer": Combine the numeric result and unit into one string (e.g., "0.045 J")
- "explanation": Write 2-3 clear sentences explaining HOW the answer was obtained. Use natural language.
- "cot": Extract each reasoning step. Each step should be 1-2 sentences. Minimum 3 steps.
- "confidence": Use the scoring guide below.

Confidence scoring:
  0.95-1.00: Code executed successfully, numeric answer
  0.75-0.94: Code executed but with approximations
  0.50-0.74: Answer from LLM reasoning without code verification
  0.10-0.49: Qualitative answer, no numerical verification"""


def build_structurer_prompt(
    question: str,
    think_trace: str,
    fol: str,
    answer_value: str,
    unit: str,
    premises: list[str],
    code_success: bool,
) -> str:
    """Build the prompt for the structuring agent."""
    premises_text = "\n".join(f"  - {p}" for p in premises) if premises else "  (none)"

    return f"""Question: {question}

Reasoning trace:
{think_trace}

FOL: {fol}

Computed answer: {answer_value} {unit}
Code execution: {"SUCCESS" if code_success else "FAILED (answer from LLM fallback)"}

Premises used:
{premises_text}

Now structure this into the JSON format specified in your instructions."""

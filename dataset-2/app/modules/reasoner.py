"""
Step 3: Reasoner — LLM that generates reasoning, FOL, and Python code.

Supports backends:
  - "mock": Returns pre-built responses (for testing pipeline flow)
  - "local": Uses vLLM or HuggingFace transformers (GPU required)
  - "api": Calls external API (OpenAI-compatible)
"""
import re
from typing import Optional

from app.config import config
from app.models import ReasonerOutput
from app.prompts.reasoner_prompt import REASONER_SYSTEM_PROMPT, build_reasoner_prompt


def _parse_reasoner_output(raw_text: str) -> ReasonerOutput:
    """Parse the structured output from the reasoner LLM."""
    output = ReasonerOutput()

    # Extract <think> content if present
    think_match = re.search(r"<think>(.*?)</think>", raw_text, re.DOTALL)
    if think_match:
        output.think_trace = think_match.group(1).strip()
    else:
        output.think_trace = raw_text  # Use full text as reasoning trace

    # Extract FOL
    fol_match = re.search(r"\[FOL\]:\s*(.*?)(?:\n\n|\[CODE\])", raw_text, re.DOTALL)
    if fol_match:
        output.fol = fol_match.group(1).strip()

    # Extract Python code block
    code_match = re.search(r"```python\s*(.*?)```", raw_text, re.DOTALL)
    if code_match:
        output.python_code = code_match.group(1).strip()

    # Extract answer line
    answer_match = re.search(r"\[ANSWER\]:\s*(.+)", raw_text)
    if answer_match:
        answer_text = answer_match.group(1).strip()
        # Try to split value and unit
        parts = answer_text.rsplit(" ", 1)
        if len(parts) == 2:
            output.raw_answer = parts[0]
            output.raw_unit = parts[1]
        else:
            output.raw_answer = answer_text

    return output


def _mock_reason(question: str, premises: list[str]) -> str:
    """Generate a mock response for pipeline testing."""
    # Try to detect problem type from premises and question
    premises_text = " ".join(premises)

    if "coulomb" in premises_text.lower() or "force" in question.lower():
        return """<think>
This is an electrostatics problem. I need to apply Coulomb's Law.
The question asks about the force between charges.
I will identify the charges, convert units to SI, and compute the force.
</think>

[FOL]: ∀q1,q2,r (PointCharge(q1) ∧ PointCharge(q2) ∧ Distance(q1,q2,r) → Force(q1,q2, k*|q1*q2|/r²))

[CODE]:
```python
import math

# Given values (converted to SI)
k = 9e9  # Coulomb's constant [N·m²/C²]
q1 = 6e-8  # [C]
q2 = 6e-8  # [C]
r = 0.08  # 8 cm -> m

# Apply Coulomb's Law
F = k * abs(q1 * q2) / r**2

answer = round(F, 6)
unit = "N"
```

[ANSWER]: 0.005063 N"""

    elif "capacit" in premises_text.lower() or "capacitor" in question.lower():
        return """<think>
This is a capacitor problem. I need to use capacitor formulas.
I will identify C, U, Q and compute the requested quantity.
</think>

[FOL]: ∀C,U (Capacitor(C) ∧ Voltage(U) → Energy(C, 0.5*C*U²))

[CODE]:
```python
import math

# Given values (converted to SI)
C = 100e-6  # 100 μF -> F
U = 30  # V

# Energy stored in capacitor
W = 0.5 * C * U**2

answer = round(W, 4)
unit = "J"
```

[ANSWER]: 0.045 J"""

    else:
        # Generic physics response
        return """<think>
I need to analyze this physics problem step by step.
Let me identify the given values and the required quantity.
</think>

[FOL]: ∀x (PhysicalQuantity(x) → HasValue(x))

[CODE]:
```python
import math

# Given values - placeholder
answer = 0.0
unit = ""
```

[ANSWER]: 0.0"""


def _local_reason(
    question: str,
    premises: list[str],
    topic: str = "general",
    question_type: str = "quantitative",
    unit_hints: list[str] | None = None,
    geometry_hints: list[str] | None = None,
) -> str:
    """Call local vLLM / HuggingFace model. Requires GPU."""
    try:
        from openai import OpenAI
        # vLLM serves an OpenAI-compatible API
        # client = OpenAI(base_url="http://localhost:8001/v1", api_key="not-needed")
        client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )
        prompt = build_reasoner_prompt(
            question,
            premises,
            topic=topic,
            question_type=question_type,
            unit_hints=unit_hints,
            geometry_hints=geometry_hints,
        )
        response = client.chat.completions.create(
            model=config.reasoner_model,
            messages=[
                {"role": "system", "content": REASONER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=config.reasoner_max_tokens,
            temperature=config.reasoner_temperature,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"[Reasoner] Local model error: {e}")
        return _mock_reason(question, premises)


def _api_reason(
    question: str,
    premises: list[str],
    topic: str = "general",
    question_type: str = "quantitative",
    unit_hints: list[str] | None = None,
    geometry_hints: list[str] | None = None,
) -> str:
    """Call external API (OpenAI-compatible)."""
    import os
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY") or "not-needed",
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            timeout=float(os.getenv("REASONER_API_TIMEOUT", "40")),
        )
        prompt = build_reasoner_prompt(
            question,
            premises,
            topic=topic,
            question_type=question_type,
            unit_hints=unit_hints,
            geometry_hints=geometry_hints,
        )
        response = client.chat.completions.create(
            model=os.getenv("REASONER_API_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": REASONER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=config.reasoner_max_tokens,
            temperature=config.reasoner_temperature,
        )
        return response.choices[0].message.content or ""
    except Exception as e:
        print(f"[Reasoner] API error: {e}")
        return _mock_reason(question, premises)


def reason(
    question: str,
    premises: list[str],
    topic: str = "general",
    question_type: str = "quantitative",
    unit_hints: list[str] | None = None,
    geometry_hints: list[str] | None = None,
) -> ReasonerOutput:
    """
    Step 3: Generate reasoning, FOL, and Python code for a physics problem.
    
    Args:
        question: The physics problem text.
        premises: List of relevant laws/formulas from RAG.
        
    Returns:
        ReasonerOutput with think_trace, fol, python_code, raw_answer, raw_unit.
    """
    if config.mode == "mock":
        raw = _mock_reason(question, premises)
    elif config.mode == "local":
        raw = _local_reason(
            question,
            premises,
            topic=topic,
            question_type=question_type,
            unit_hints=unit_hints,
            geometry_hints=geometry_hints,
        )
    elif config.mode == "api":
        raw = _api_reason(
            question,
            premises,
            topic=topic,
            question_type=question_type,
            unit_hints=unit_hints,
            geometry_hints=geometry_hints,
        )
    else:
        raw = _mock_reason(question, premises)

    return _parse_reasoner_output(raw)

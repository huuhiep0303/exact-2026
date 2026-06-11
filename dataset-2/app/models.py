"""
Pydantic models for API request/response and internal data flow.
Maps directly to the endpoint.txt schema.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


# ─── API Request ───
class QuestionRequest(BaseModel):
    """Incoming question from the API."""
    question: str = Field(..., min_length=5, description="Physics problem text")


# ─── API Response (matches endpoint.txt) ───
class PhysicsResponse(BaseModel):
    """Output schema matching endpoint.txt specification."""
    # Required
    answer: str = Field(..., description="Final answer value with unit, e.g. '0.045 J'")
    explanation: str = Field(..., description="Natural language explanation of solution")

    # Optional (Encouraged)
    fol: Optional[str] = Field(None, description="First-Order Logic representation")
    cot: Optional[List[str]] = Field(None, description="Chain-of-thought reasoning steps")
    premises: Optional[List[str]] = Field(None, description="Laws/formulas applied")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")


# ─── Internal pipeline data containers ───
class ReasonerOutput(BaseModel):
    """Output from the Reasoner LLM (Step 3)."""
    think_trace: str = ""           # Raw <think> content
    fol: str = ""                   # FOL string
    python_code: str = ""           # Extracted Python code block
    raw_answer: Optional[str] = None  # LLM's own answer (fallback)
    raw_unit: Optional[str] = None


class SandboxResult(BaseModel):
    """Output from the Code Sandbox (Step 4)."""
    success: bool = False
    answer_value: Optional[str] = None
    unit: Optional[str] = None
    error: Optional[str] = None
    retries_used: int = 0


class PipelineContext(BaseModel):
    """Carries all intermediate state through the pipeline."""
    question: str
    question_type: str = "quantitative"  # "quantitative" | "qualitative"
    topic: str = "general"

    # Step 2: RAG
    premises: List[str] = Field(default_factory=list)
    rag_top_score: float = 0.0
    unit_hints: List[str] = Field(default_factory=list)
    geometry_hints: List[str] = Field(default_factory=list)

    # Step 3: Reasoner
    reasoner_output: Optional[ReasonerOutput] = None

    # Step 4: Sandbox
    sandbox_result: Optional[SandboxResult] = None

    # Step 5: Normalized answer
    final_answer: str = ""
    final_unit: str = ""

    # Step 6: Structured output
    cot_steps: List[str] = Field(default_factory=list)
    explanation: str = ""
    fol: str = ""
    confidence: float = 0.0

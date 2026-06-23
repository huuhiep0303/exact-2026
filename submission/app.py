import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import re
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import asyncio

# --- Models ---

class QueryRequest(BaseModel):
    query_id: str
    type: str
    query: str
    premises: List[str]
    options: List[str]

class ReasoningBlock(BaseModel):
    type: str
    steps: List[str]

class QueryResponse(BaseModel):
    query_id: str
    answer: str
    unit: str
    explanation: str
    premises_used: List[int]
    reasoning: Optional[ReasoningBlock] = None

# --- Configuration ---
# Configurable vLLM URL (e.g., http://localhost:8000/v1 or Modal internal URL)
VLLM_API_URL = os.getenv("VLLM_API_URL", "http://localhost:8000/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen3-8B") # Or whatever model ID you serve
TYPE1_MODEL = os.getenv("TYPE1_MODEL", "exact-lora")
TYPE2_MODEL = os.getenv("TYPE2_MODEL", "exact-lora-type2")
VLLM_REQUEST_TIMEOUT = float(os.getenv("VLLM_REQUEST_TIMEOUT", "45"))
TYPE1_MAX_TOKENS = int(os.getenv("TYPE1_MAX_TOKENS", "512"))
TYPE2_PIPELINE_TIMEOUT = float(os.getenv("TYPE2_PIPELINE_TIMEOUT", "50"))


SYSTEM_PROMPT = """You are an expert in formal logical reasoning. Analyze the premises and answer the question using rigorous logical deduction.

Rules:
1. Select ONLY the MINIMUM premises needed to answer the question.
2. Provide clear, step-by-step reasoning based strictly on the selected premises.
3. For truth-status questions, answer positively only when the conclusion is derived, negatively only when it is contradicted, and use the request's uncertainty option when the premises are insufficient.
4. For multiple-choice questions, select the option best supported by the premises.
5. For open questions, return the requested number, name, or short text instead of a generic truth-status label.
6. The final answer MUST be consistent with the reasoning and MUST obey the answer choices supplied in the user message."""

app = FastAPI(title="EXACT 2026 Submission API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helpers ---

def extract_premise_indices(text: str, max_premises: int) -> List[int]:
    """Extract used premise indices from text (converts 1-indexed SFT outputs to 0-indexed)."""
    indices = []
    # Match P1, P2, P3... (1-indexed format from SFT model)
    matches = re.finditer(r'P(\d+)', text)
    for match in matches:
        idx = int(match.group(1))
        zero_idx = idx - 1  # Convert to 0-indexed for competition
        if 0 <= zero_idx < max_premises and zero_idx not in indices:
            indices.append(zero_idx)
    return sorted(indices)


def extract_written_premise_indices(text: str, max_premises: int) -> List[int]:
    """Extract written references such as 'premises 1, 3 and 5' (1-based)."""
    indices = []
    for match in re.finditer(
        r'\bpremises?\s+((?:\d+\s*(?:,|and|&)\s*)*\d+)',
        text,
        re.IGNORECASE,
    ):
        for value in re.findall(r'\d+', match.group(1)):
            zero_idx = int(value) - 1
            if 0 <= zero_idx < max_premises and zero_idx not in indices:
                indices.append(zero_idx)
    return sorted(indices)


def is_mcq(options: List[str]) -> bool:
    normalized = [option.strip().upper() for option in options]
    return bool(normalized) and all(re.fullmatch(r'[A-Z]', option) for option in normalized)


def build_answer_instruction(options: List[str]) -> str:
    if options:
        choices = " | ".join(option.strip() for option in options)
        uncertainty_note = ""
        lowered = {option.strip().lower() for option in options}
        if "uncertain" in lowered or "unknown" in lowered:
            uncertainty_note = (
                " 'Unknown' and 'Uncertain' have the same uncertainty meaning, "
                "but output the exact spelling present in ALLOWED ANSWERS."
            )
        return (
            f"ALLOWED ANSWERS: {choices}. Return exactly one of these values."
            f"{uncertainty_note}"
        )
    return (
        "This is an open-answer question. Return only the concise value, number, "
        "name, or text requested. Do not return Yes/No/Unknown when the premises "
        "provide a concrete answer."
    )


def extract_answer_text(raw_response: str) -> tuple[str, bool]:
    """Return the answer candidate and whether an explicit Answer label existed."""
    answer_match = re.search(
        r'(?:\*\*)?Answer(?:\*\*)?\s*:\s*(.+)',
        raw_response,
        re.IGNORECASE,
    )
    if answer_match:
        return answer_match.group(1).splitlines()[0].strip(), True

    after_think = re.search(r'</think>\s*(.*)', raw_response, re.DOTALL | re.IGNORECASE)
    if after_think and after_think.group(1).strip():
        return after_think.group(1).strip().splitlines()[0], False
    return raw_response.strip().splitlines()[0] if raw_response.strip() else "", False


def clean_answer_text(text: str) -> str:
    answer = re.sub(r'^\s*(?:final\s+)?answer\s*:\s*', '', text, flags=re.IGNORECASE)
    answer = answer.replace("**", "").strip().strip('"\'`')
    return answer[:-1].strip() if answer.endswith('.') else answer


def parse_query_options(query: str) -> Dict[str, str]:
    parsed = {}
    for match in re.finditer(r'^\s*([A-Z])\s*[\.)]\s*(.+?)\s*$', query, re.MULTILINE):
        parsed[match.group(1)] = match.group(2).strip()
    return parsed


def extract_conclusion(reasoning: str) -> str:
    """Return the final stated conclusion without assuming a specific topic."""
    return re.split(
        r'\b(?:therefore|thus|hence|consequently)\b[:,]?\s*',
        reasoning.strip(),
        flags=re.IGNORECASE,
    )[-1].strip()


def infer_status_from_reasoning(reasoning: str) -> Optional[str]:
    lowered = reasoning.lower()
    uncertain_signals = (
        "cannot be determined", "cannot determine", "not enough information",
        "insufficient information", "no premise", "not stated", "unknown",
        "uncertain", "undetermined",
    )
    if any(signal in lowered for signal in uncertain_signals):
        return "uncertain"

    conclusion = extract_conclusion(lowered)
    negative_signals = (
        " no", "is false", "is contradicted", "contradicts the", "does not",
        "cannot ", "is not ", "has no ",
    )
    if conclusion.startswith("no") or any(signal in conclusion for signal in negative_signals):
        return "no"

    if conclusion != lowered.strip():
        return "yes"
    if "can be derived" in lowered or "is logically supported" in lowered:
        return "yes"
    return None


def infer_open_answer(query: str, reasoning: str, premises: List[str]) -> Optional[str]:
    """Repair common malformed open answers using the model's own deduction."""
    if re.search(r'\b(how many|what number|number of)\b', query, re.IGNORECASE):
        conclusion = extract_conclusion(reasoning)
        numbers = re.findall(r'(?<![A-Za-z])[-+]?\d+(?:\.\d+)?', conclusion)
        if numbers:
            return numbers[-1]

        query_words = set(re.findall(r'[a-z]+', query.lower()))
        ranked = sorted(
            premises,
            key=lambda premise: len(query_words & set(re.findall(r'[a-z]+', premise.lower()))),
            reverse=True,
        )
        for premise in ranked:
            numbers = re.findall(r'(?<![A-Za-z])[-+]?\d+(?:\.\d+)?', premise)
            if numbers:
                return numbers[-1]

    if re.search(r'\b(who|which)\b', query, re.IGNORECASE):
        conclusion = extract_conclusion(reasoning)
        conclusion = re.sub(
            r'^(?:premise\s+P?\d+\s+)?(?:implies|shows|establishes)\s+that\s+',
            '',
            conclusion,
            flags=re.IGNORECASE,
        )
        subject_match = re.match(
            r'^(?:the\s+)?(.+?)\s+(?:may|can|is|are|has|have|does|do|will|must|should)\b',
            conclusion,
            re.IGNORECASE,
        )
        if subject_match:
            candidate = subject_match.group(1).strip(' ,.:;"\'`')
            if candidate and any(
                re.search(rf'\b{re.escape(candidate)}\b', premise, re.IGNORECASE)
                for premise in premises
            ):
                return candidate
    return None


def normalize_answer(
    candidate: str,
    options: List[str],
    query: str,
    reasoning: str,
    premises: List[str],
) -> str:
    answer = clean_answer_text(candidate)

    if options:
        option_map = {option.strip().lower(): option.strip() for option in options}
        if answer.lower() in option_map:
            return option_map[answer.lower()]

        if is_mcq(options):
            available = {option.strip().upper(): option.strip() for option in options}
            label_match = re.search(
                r'^\s*(?:option\s*)?([A-D])(?:\s*[\.)]|\s*[-:]|\s*$)',
                answer,
                re.IGNORECASE,
            )
            if not label_match:
                label_match = re.search(r'\boption\s+([A-D])\b', answer, re.IGNORECASE)
            if label_match and label_match.group(1).upper() in available:
                return available[label_match.group(1).upper()]

            conclusion = extract_conclusion(reasoning)
            combined = f"{answer}\n{conclusion}".lower()
            for label, option_text in parse_query_options(query).items():
                if label in available and option_text.lower() in combined:
                    return available[label]

        status_option_names = {"yes", "no", "unknown", "uncertain"}
        if not (set(option_map) & status_option_names):
            conclusion = extract_conclusion(reasoning)
            combined = f"{answer}\n{conclusion}".lower()
            textual_matches = [
                original for normalized, original in option_map.items()
                if len(normalized) > 1 and normalized in combined
            ]
            if len(textual_matches) == 1:
                return textual_matches[0]

        status = None
        status_match = re.search(r'\b(yes|no|unknown|uncertain)\b', answer, re.IGNORECASE)
        if status_match:
            status = status_match.group(1).lower()
        if status in (None, "unknown", "uncertain"):
            status = infer_status_from_reasoning(reasoning) or status

        if status in ("unknown", "uncertain"):
            for synonym in ("uncertain", "unknown"):
                if synonym in option_map:
                    return option_map[synonym]
        if status and status in option_map:
            return option_map[status]

        # Prefer a semantic uncertainty option, but never invent a choice by position.
        for synonym in ("uncertain", "unknown"):
            if synonym in option_map:
                return option_map[synonym]
        return answer or "Unknown"

    if (
        answer
        and answer.lower() not in {"unknown", "uncertain", "yes", "no"}
        and re.search(r'\b(how many|what number|number of)\b', query, re.IGNORECASE)
    ):
        numbers = re.findall(r'(?<![A-Za-z])[-+]?\d+(?:\.\d+)?', answer)
        if numbers:
            return numbers[-1]
    if answer and answer.lower() not in {"unknown", "uncertain", "yes", "no"}:
        return answer
    repaired = infer_open_answer(query, reasoning, premises)
    return repaired or answer or "Unknown"


def content_words(text: str) -> set[str]:
    stopwords = {
        "a", "an", "the", "is", "are", "was", "were", "does", "do", "did",
        "has", "have", "had", "of", "to", "in", "on", "for", "with", "whether",
        "which", "who", "what", "how", "many",
    }
    return {
        word for word in re.findall(r'[a-z0-9]+', text.lower())
        if len(word) > 1 and word not in stopwords
    }


def infer_meta_premises(query: str, premises: List[str]) -> List[int]:
    """Find an explicit premise saying that the queried fact is unstated."""
    query_words = content_words(query)
    candidates = []
    meta_signals = (
        "no premise", "no record", "no information", "no evidence",
        "not stated", "not specified", "not provided", "does not state",
        "cannot be determined", "unknown whether",
    )
    for index, premise in enumerate(premises):
        lowered = premise.lower()
        overlap = len(query_words & content_words(premise))
        if overlap and any(signal in lowered for signal in meta_signals):
            candidates.append((overlap, index))
    if not candidates:
        return []
    best_overlap = max(score for score, _ in candidates)
    return [index for score, index in candidates if score == best_overlap]

def call_vllm(user_message: str) -> str:
    """Call the vLLM OpenAI-compatible endpoint."""
    # Since we need to respond within 60s, we use httpx for async API call.
    # But for simplicity, we can do a blocking call or async call. Let's do async.
    pass

async def async_call_vllm(user_message: str, model_name: str = MODEL_NAME) -> str:
    timeout = httpx.Timeout(VLLM_REQUEST_TIMEOUT, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.0,
            "top_p": 1.0,
            "max_tokens": TYPE1_MAX_TOKENS,
        }

        try:
            response = await client.post(f"{VLLM_API_URL}/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"vLLM Error: {e}")
            raise HTTPException(status_code=502, detail=f"vLLM request failed: {e}") from e

# --- Pipelines ---

async def handle_type1(request: QueryRequest) -> QueryResponse:
    # 1. Format user prompt using 1-indexed premises to match SFT training
    premises_text = "\n".join([f"P{i}: {p}" for i, p in enumerate(request.premises, 1)])
    
    answer_instruction = build_answer_instruction(request.options)

    # Keep the SFT response structure while making its answer contract request-specific.
    user_message = f"""Given the following premises, answer the question below.

Premises:
{premises_text}

Question: {request.query}

{answer_instruction}

Premise labels are 1-based: P1 corresponds to premises[0]. If a premise explicitly
states that the queried information is absent, that premise supports an uncertain
answer and MUST be listed under Relevant Premises.

Provide your response in EXACTLY this format:
<think>
**Relevant Premises:** [List only the premise numbers you used, e.g., P1, P3, P5]
**Reasoning:** [Step-by-step logical deduction using only the selected premises]
</think>
**Answer:** [One final answer obeying the answer contract above]"""

    # 2. Call Model
    raw_response = await async_call_vllm(user_message, model_name=TYPE1_MODEL)
    
    # 3. Parse output
    think_match = re.search(r'<think>\n?(.*?)\n?</think>', raw_response, re.DOTALL)
    think_block = think_match.group(1) if think_match else raw_response

    # Extract relevant premises
    premises_section = think_block
    if "**Relevant Premises:**" in think_block:
        start = think_block.find("**Relevant Premises:**")
        end = think_block.find("**Reasoning:**", start)
        if end == -1: end = len(think_block)
        premises_section = think_block[start:end]
        
    premises_used = extract_premise_indices(premises_section, len(request.premises))
        
    # Extract Explanation
    explanation = ""
    if "**Reasoning:**" in think_block:
        start = think_block.find("**Reasoning:**") + len("**Reasoning:**")
        explanation = think_block[start:].strip()
    else:
        explanation = think_block.strip()
        
    if not explanation:
        explanation = "No explanation provided."

    answer_candidate, _ = extract_answer_text(raw_response)
    answer = normalize_answer(
        answer_candidate,
        request.options,
        request.query,
        explanation,
        request.premises,
    )

    if not premises_used:
        premises_used = extract_premise_indices(raw_response, len(request.premises))
    if not premises_used:
        premises_used = extract_written_premise_indices(raw_response, len(request.premises))
    if not premises_used and answer.lower() in {"unknown", "uncertain"}:
        premises_used = infer_meta_premises(request.query, request.premises)

    return QueryResponse(
        query_id=request.query_id,
        answer=answer,
        unit="",
        explanation=explanation,
        premises_used=premises_used,
        reasoning=ReasoningBlock(
            type="fol",
            steps=[explanation] # Add more detailed splitting if needed
        )
    )

def split_type2_answer(answer: str) -> tuple[str, str]:
    ans_str = (answer or "").strip()
    if not ans_str:
        return "", ""
    if ";" not in ans_str:
        match = re.fullmatch(
            r"(?:[A-Za-z][A-Za-z0-9_]*\s*=\s*)?"
            r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)"
            r"\s*([^\d\s].*)?",
            ans_str,
            re.I,
        )
        if match:
            return match.group(1), (match.group(2) or "").strip()
    parts = ans_str.split(" ", 1)
    return parts[0], parts[1].strip() if len(parts) > 1 else ""

async def handle_type2(request: QueryRequest) -> QueryResponse:
    # Configure environment variables for dataset-2 BEFORE importing its modules
    os.environ["PIPELINE_MODE"] = "api"
    os.environ["OPENAI_BASE_URL"] = VLLM_API_URL
    os.environ["REASONER_API_MODEL"] = TYPE2_MODEL

    try:
        from app.pipeline import run_pipeline
    except ImportError as e:
        print(f"Error importing dataset-2 pipeline: {e}")
        return QueryResponse(
            query_id=request.query_id,
            answer="0",
            unit="",
            explanation=f"Type 2 pipeline import failed: {e}",
            premises_used=[],
            reasoning=None
        )

    # Run the pipeline in a thread to avoid blocking FastAPI event loop
    try:
        physics_response = await asyncio.wait_for(
            asyncio.to_thread(run_pipeline, request.query),
            timeout=TYPE2_PIPELINE_TIMEOUT,
        )
    except asyncio.TimeoutError:
        print(f"Type 2 Pipeline Error: exceeded {TYPE2_PIPELINE_TIMEOUT}s budget")
        return QueryResponse(
            query_id=request.query_id,
            answer="0",
            unit="",
            explanation="Type 2 pipeline exceeded the internal time budget.",
            premises_used=[],
            reasoning=None
        )
    except Exception as e:
        print(f"Type 2 Pipeline Error: {e}")
        return QueryResponse(
            query_id=request.query_id,
            answer="0",
            unit="",
            explanation=f"Error executing Type 2 pipeline: {str(e)}",
            premises_used=[],
            reasoning=None
        )
    
    # Parse answer string (e.g., "5 A" or "I = 0.5 A") into value and unit.
    ans_val, ans_unit = split_type2_answer(physics_response.answer)
    
    # Build reasoning block
    reasoning_steps = physics_response.cot if physics_response.cot else []
    if physics_response.fol:
        reasoning_steps.insert(0, f"FOL: {physics_response.fol}")
        
    reasoning = None
    if reasoning_steps:
        reasoning = ReasoningBlock(
            type="cot",
            steps=reasoning_steps
        )

    return QueryResponse(
        query_id=request.query_id,
        answer=ans_val,
        unit=ans_unit,
        explanation=physics_response.explanation,
        premises_used=[],  # Type 2 has empty premises_used per EXACT rules
        reasoning=reasoning
    )

# --- Routes ---

@app.post("/predict", response_model=List[QueryResponse])
async def predict(request: QueryRequest):
    if request.type == "type1":
        result = await handle_type1(request)
    elif request.type == "type2":
        result = await handle_type2(request)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported query type: {request.type}")
    
    # Competition requires returning a list with exactly one object per query
    return [result]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)

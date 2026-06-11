import os
import re
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException
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

SYSTEM_PROMPT = """You are an expert in formal logical reasoning. Your task is to analyze premises and answer questions using rigorous logical deduction.

Rules:
1. Select ONLY the MINIMUM premises needed to answer the question.
2. Provide clear, step-by-step reasoning based strictly on the selected premises.
3. For Yes/No questions: Answer "Yes" ONLY if the conclusion can be logically DERIVED from the premises. Answer "No" if the premises CONTRADICT the conclusion. Answer "Unknown" if the premises are INSUFFICIENT to determine the truth of the conclusion.
4. For multiple choice questions: Select the option that is BEST supported by the premises.
5. Your answer MUST be consistent with your reasoning. Do NOT contradict your own analysis."""

app = FastAPI(title="EXACT 2026 Submission API")

# --- Helpers ---

def extract_premise_indices(text: str, max_premises: int) -> List[int]:
    """Extract used premise indices from text."""
    indices = []
    # Match P0, P1, P2...
    matches = re.finditer(r'P(\d+)', text)
    for match in matches:
        idx = int(match.group(1))
        if 0 <= idx < max_premises and idx not in indices:
            indices.append(idx)
    return sorted(indices)

def call_vllm(user_message: str) -> str:
    """Call the vLLM OpenAI-compatible endpoint."""
    # Since we need to respond within 60s, we use httpx for async API call.
    # But for simplicity, we can do a blocking call or async call. Let's do async.
    pass

async def async_call_vllm(user_message: str) -> str:
    async with httpx.AsyncClient(timeout=55.0) as client:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.6,
            "top_p": 0.95,
            "max_tokens": 2048,
        }
        try:
            response = await client.post(f"{VLLM_API_URL}/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"vLLM Error: {e}")
            return ""

# --- Pipelines ---

async def handle_type1(request: QueryRequest) -> QueryResponse:
    # 1. Format user prompt
    premises_text = "\n".join([f"P{i}: {p}" for i, p in enumerate(request.premises)])
    
    user_message = f"""Given the following premises, answer the question below.

Premises:
{premises_text}

Question: {request.query}

Provide your response in EXACTLY this format:
<think>
**Relevant Premises:** [List only the premise numbers you used, e.g., P1, P3, P5]
**Reasoning:** [Step-by-step logical deduction using only the selected premises]
</think>
**Answer:** [Your final answer: A/B/C/D or Yes/No/Unknown]"""

    # 2. Call Model
    raw_response = await async_call_vllm(user_message)
    
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
    
    # Extract Answer
    answer_section = raw_response
    if "**Answer:**" in raw_response:
        start = raw_response.find("**Answer:**") + len("**Answer:**")
        answer_section = raw_response[start:].strip()
    else:
        after_think = re.search(r'</think>\s*(.*)', raw_response, re.DOTALL)
        if after_think:
            answer_section = after_think.group(1).strip()
            
    # Clean answer
    answer = answer_section.split("\n")[0].strip()
    # Basic fallback cleaning
    if not answer:
        answer = "Unknown"
        
    # Extract Explanation
    explanation = ""
    if "**Reasoning:**" in think_block:
        start = think_block.find("**Reasoning:**") + len("**Reasoning:**")
        explanation = think_block[start:].strip()
    else:
        explanation = think_block.strip()
        
    if not explanation:
        explanation = "No explanation provided."

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

async def handle_type2(request: QueryRequest) -> QueryResponse:
    # TODO: Integrate Type 2 pipeline here once the other member finishes.
    # Currently returns a dummy response matching EXACT Type 2 format.
    return QueryResponse(
        query_id=request.query_id,
        answer="0",
        unit="A",
        explanation="Type 2 pipeline not yet integrated.",
        premises_used=[],
        reasoning=None
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

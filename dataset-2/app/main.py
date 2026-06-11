"""
FastAPI Application — Physics AI Endpoint
The main API server for the physics problem-solving pipeline.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.models import QuestionRequest, PhysicsResponse
from app.pipeline import run_pipeline

# ─── App setup ───
app = FastAPI(
    title="Physics AI Solver",
    description="AI-powered physics problem solver with Chain-of-Thought reasoning",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Endpoints ───

@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "running",
        "mode": config.mode,
        "debug": config.debug,
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    from app.modules.knowledge_base import get_knowledge_base
    kb = get_knowledge_base()
    return {
        "status": "healthy",
        "mode": config.mode,
        "kb_entries": len(kb.entries),
        "cache_enabled": config.use_redis,
    }


@app.post("/solve", response_model=PhysicsResponse)
async def solve_question(request: QuestionRequest):
    """
    Solve a physics problem.
    
    Accepts a question and returns a structured response with:
    - answer (required)
    - explanation (required)
    - fol, cot, premises, confidence (optional but encouraged)
    """
    try:
        response = run_pipeline(request.question)
        return response
    except Exception as e:
        if config.debug:
            import traceback
            traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.post("/batch")
async def solve_batch(questions: list[QuestionRequest]):
    """Solve multiple physics problems at once."""
    results = []
    for q in questions:
        try:
            response = run_pipeline(q.question)
            results.append(response.model_dump())
        except Exception as e:
            results.append({
                "answer": "Error",
                "explanation": str(e),
                "confidence": 0.0,
            })
    return results


# ─── Run directly ───
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.api_host, port=config.api_port)

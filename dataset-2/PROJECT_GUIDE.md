# Huong Dan Chay, Test Va Doc Code Du An

## 1. Tong quan

Du an nay la mot Physics AI Solver dung FastAPI de nhan cau hoi Vat ly va tra ve ket qua co cau truc. Luong xu ly chinh nam trong `app/pipeline.py`, dieu phoi cac buoc:

`Query Router -> Cache -> RAG -> Reasoner -> Sandbox -> Normalizer -> Confidence -> Structurer`

Che do mac dinh hien tai la `mock`, nen co the chay va test pipeline ma khong can GPU, Qdrant, Redis hay external LLM API.

## 2. Cai dat va chay

### Cai dependencies

```powershell
pip install -r requirements.txt
```

Neu dung virtual environment san co trong repo:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Chay test nhanh pipeline

```powershell
python test_pipeline.py
```

Script nay ep `config.mode = "mock"` va `config.debug = True`, sau do chay mot vai cau hoi mau qua toan bo pipeline.

### Chay API server

Cach khuyen dung khi dev:

```powershell
python -m uvicorn app.main:app --reload
```

Hoac chay truc tiep file app:

```powershell
python app/main.py
```

Server mac dinh chay o:

```text
http://127.0.0.1:8000
```

### Endpoint chinh

| Method | Endpoint | Cong dung |
| --- | --- | --- |
| `GET` | `/` | Health check don gian, tra ve status, mode, debug |
| `GET` | `/health` | Health check chi tiet, load knowledge base va tra ve so entry |
| `POST` | `/solve` | Giai mot cau hoi Vat ly |
| `POST` | `/batch` | Giai nhieu cau hoi cung luc |

Vi du test API:

```powershell
curl -X POST "http://127.0.0.1:8000/solve" `
  -H "Content-Type: application/json" `
  -d "{\"question\":\"Calculate the energy stored in capacitor C when C = 100 μF and U = 30 V.\"}"
```

## 3. Moi file dang lam gi

| File / thu muc | Vai tro |
| --- | --- |
| `app/main.py` | Tao FastAPI app, cau hinh CORS, khai bao endpoint `/`, `/health`, `/solve`, `/batch` |
| `app/pipeline.py` | Dieu phoi pipeline chinh tu cau hoi dau vao den `PhysicsResponse` dau ra |
| `app/models.py` | Dinh nghia Pydantic models cho request, response va internal context |
| `app/config.py` | Cau hinh tap trung: mode, debug, path dataset, Qdrant, Redis, model, sandbox, API |
| `app/modules/query_router.py` | Phan loai cau hoi thanh `quantitative` hoac `qualitative` |
| `app/modules/rag.py` | Lay premises/cong thuc lien quan tu knowledge base |
| `app/modules/knowledge_base.py` | Load `physics_knowledge_base.json`, build BM25-style in-memory index, search cong thuc |
| `app/modules/reasoner.py` | Sinh reasoning, FOL, Python code va raw answer bang mock/local/api backend |
| `app/modules/sandbox.py` | Chay Python code do reasoner sinh ra trong moi truong bi gioi han va lay `answer`, `unit` |
| `app/modules/normalizer.py` | Chuan hoa answer: so, scientific notation, LaTeX/symbolic, text |
| `app/modules/confidence.py` | Tinh confidence dua tren sandbox success, answer type, RAG score, retry |
| `app/modules/structurer.py` | Dong goi `PipelineContext` thanh `PhysicsResponse` cuoi cung |
| `app/prompts/reasoner_prompt.py` | System prompt va ham build prompt cho Reasoner LLM |
| `app/prompts/structurer_prompt.py` | System prompt va ham build prompt cho Structurer LLM |
| `test_pipeline.py` | Script test nhanh pipeline o mock mode, khong can external service |
| `requirements.txt` | Dependency can thiet va cac dependency optional dang comment |
| `pipeline.md` | Tai lieu y tuong/tong quan pipeline ban dau |
| `pipeline_optimized_plan.md` | Ke hoach toi uu pipeline chi tiet hon |
| `enpoint.txt` | Schema response mong muon cua endpoint |
| `dataset_2/physics_knowledge_base.json` | Knowledge base cong thuc/dinh luat Vat ly |
| `dataset_2/Physics_Problems_Text_Only.csv` | Tap cau hoi Vat ly dang text-only |
| `dataset_2/dataset_analysis.md` | Phan tich dataset |

## 4. Import dependency

| File | Import noi bo quan trong |
| --- | --- |
| `app/main.py` | `config` tu `app.config`; `QuestionRequest`, `PhysicsResponse` tu `app.models`; `run_pipeline` tu `app.pipeline` |
| `app/pipeline.py` | `PipelineContext`, `PhysicsResponse`; `route_question`; `retrieve_premises`; `reason`; `execute_sandbox`; `normalize_answer`; `compute_confidence`; `structure_response` |
| `app/modules/rag.py` | `get_knowledge_base`, `KBEntry` tu `app.modules.knowledge_base` |
| `app/modules/knowledge_base.py` | `config` tu `app.config` |
| `app/modules/reasoner.py` | `config`; `ReasonerOutput`; `REASONER_SYSTEM_PROMPT`, `build_reasoner_prompt` |
| `app/modules/sandbox.py` | `config`; `SandboxResult` |
| `app/modules/structurer.py` | `config`; `PipelineContext`, `PhysicsResponse`; `format_final_answer` |
| `test_pipeline.py` | `config`; `run_pipeline` |

## 5. Luong goi ham chinh

### Khi goi API `/solve`

```text
POST /solve
  -> solve_question(request)
  -> run_pipeline(request.question)
```

### Ben trong `run_pipeline(question)`

```text
run_pipeline(question)
  -> route_question(question)
  -> _cache_get(question)
  -> retrieve_premises(question, top_k=config.rag_rerank_top_k)
      -> get_knowledge_base()
          -> InMemoryKB.load_from_json(config.kb_path)
          -> InMemoryKB._build_index()
      -> InMemoryKB.search(question, top_k)
  -> reason(question, premises)
      -> _mock_reason(...) hoac _local_reason(...) hoac _api_reason(...)
      -> _parse_reasoner_output(raw)
  -> execute_sandbox(reasoner_output.python_code, question=question, premises=premises)
      -> _execute_code(python_code, timeout=config.sandbox_timeout)
          -> _validate_code(code)
  -> normalize_answer(raw_ans, raw_unit)
  -> compute_confidence(...)
  -> structure_response(ctx)
      -> format_final_answer(ctx.final_answer, ctx.final_unit)
      -> _extract_cot_from_trace(ctx.reasoner_output.think_trace)
      -> _generate_explanation(ctx)
  -> _cache_set(question, response)
  -> return PhysicsResponse
```

### Khi goi API `/health`

```text
GET /health
  -> health()
  -> get_knowledge_base()
  -> len(kb.entries)
```

### Khi chay `python test_pipeline.py`

```text
test_questions()
  -> run_pipeline(question_1)
  -> run_pipeline(question_2)
  -> run_pipeline(question_3)
  -> run_pipeline(question_2)  # test cache hit
```

## 6. Ghi chu khi test

- Da xac nhan `python test_pipeline.py` chay duoc voi Python `3.12.6`.
- Test hien chay o `mock` mode va load `72` entries tu `physics_knowledge_base.json`.
- `mock` mode khong can GPU, Qdrant, Redis hay OpenAI-compatible API.
- Co mot behavior dang chu y: cau hoi qualitative mau trong `test_pipeline.py` hien bi route thanh `quantitative` vi rule pattern `?` trong `app/modules/query_router.py`. Neu muon cai thien chat luong phan loai, can xem lai thu tu tinh diem va pattern cua router.
- Mot so comment/string trong file hien thi co dau tieng Viet/ky tu dac biet bi loi encoding, nhung pipeline test van chay duoc.

## 7. Cau truc response mong muon

Endpoint `/solve` tra ve object theo `PhysicsResponse`:

```json
{
  "answer": "0.045 J",
  "explanation": "Using Energy stored in capacitor, the computation yields a result of 0.045, in units of J.",
  "fol": "∀C,U (Capacitor(C) ∧ Voltage(U) → Energy(C, 0.5*C*U²))",
  "cot": [
    "Step 1: This is a capacitor problem",
    "Step 2: I need to use capacitor formulas",
    "Step 3: I will identify C, U, Q and compute the requested quantity."
  ],
  "premises": [
    "Energy stored in capacitor: W = 0.5 * C * U^2 = Q^2/(2*C) = Q*U/2"
  ],
  "confidence": 0.96
}
```

Trong do `answer` va `explanation` la required; `fol`, `cot`, `premises`, `confidence` la optional nhung du an dang co gang dien day du.

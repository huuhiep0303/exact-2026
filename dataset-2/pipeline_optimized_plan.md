d:\Work\Learn\AI_X_Challenge\
├── app/
│   ├── config.py           # Cấu hình (mock/local/api mode)
│   ├── models.py           # Pydantic schemas (endpoint.txt compliant)
│   ├── pipeline.py         # 🧠 Orchestrator chính — 7 bước
│   ├── main.py             # FastAPI server (/solve, /health, /batch)
│   ├── modules/
│   │   ├── query_router.py   # Step 0: Phân loại câu hỏi
│   │   ├── knowledge_base.py # KB với BM25 search (72 công thức)
│   │   ├── rag.py            # Step 2: Hybrid RAG
│   │   ├── reasoner.py       # Step 3: LLM (mock/local/api)
│   │   ├── sandbox.py        # Step 4: Safe Python exec
│   │   ├── normalizer.py     # Step 5: Answer normalization
│   │   ├── confidence.py     # Confidence scoring
│   │   └── structurer.py     # Step 6: JSON formatting
│   └── prompts/
│       ├── reasoner_prompt.py   # DeepSeek prompt template
│       └── structurer_prompt.py # Qwen prompt template
├── dataset_2/
│   └── physics_knowledge_base.json  # 72 curated formulas
├── test_pipeline.py        # Test script
└── requirements.txt


# 🚀 Kế Hoạch Tối Ưu Hóa Pipeline — AI × Physics Challenge

> Dựa trên phân tích `pipeline.md` hiện tại và tiêu chí `endpoint.txt`  
> Mục tiêu: Đảm bảo **100% output** đúng schema, tối đa điểm P1 (Correctness) + P2 (Explanation Quality)

---

## 0. Phân Tích Gap: Pipeline Hiện Tại vs Yêu Cầu Endpoint

### Schema endpoint.txt yêu cầu:

| Trường | Bắt buộc | Mô tả |
|--------|:--------:|-------|
| `answer` | ✅ Required | Đáp án cuối (số hoặc chuỗi + đơn vị) |
| `explanation` | ✅ Required | Giải thích bằng ngôn ngữ tự nhiên |
| `fol` | ⭕ Optional | First-Order Logic string |
| `cot` | ⭕ Optional | Mảng các bước suy luận |
| `premises` | ⭕ Optional | Mảng các công thức/định luật áp dụng |
| `confidence` | ⭕ Optional | Điểm tin cậy [0.0, 1.0] |

### Những gì pipeline hiện tại **đã có**:

| Thành phần | Trạng thái |
|------------|-----------|
| Hybrid RAG (Qdrant + BM25) → `premises` | ✅ Có |
| DeepSeek-R1-7B reasoning → `fol`, `cot` | ✅ Có |
| Code Sandbox → `answer` (số + đơn vị) | ✅ Có |
| Qwen2.5-7B + Instructor → JSON output | ✅ Có |
| `confidence` scoring | ✅ Có (nhưng sơ lược) |

### Những gì pipeline hiện tại **CÒN THIẾU / YẾU**:

| Gap | Mức độ | Chi tiết |
|-----|:------:|---------|
| **Không có Query Routing** | 🔴 Cao | Câu hỏi THCB (sai số đo) khác hoàn toàn LD (Coulomb) – cần route riêng |
| **Không có Answer Normalization** | 🔴 Cao | Dataset có `4.0 × 10⁴`, `\sqrt{2}×F₀`, `Do not change` – nếu không chuẩn hóa sẽ sai format |
| **Không có Unit Validation** | 🔴 Cao | Chưa có bước kiểm tra đơn vị output khớp với đơn vị đúng |
| **Code Sandbox thiếu fallback** | 🔴 Cao | Nếu Python code lỗi runtime → pipeline crash, không có recovery |
| **FOL chưa được validate** | 🟡 Trung bình | FOL sinh ra có thể sai cú pháp logic → điểm bị trừ |
| **Confidence chưa có calibration** | 🟡 Trung bình | Chỉ dựa vào code exec success/fail – thiếu nhiều tín hiệu |
| **Không có Response Cache** | 🟡 Trung bình | Endpoint chậm nếu gặp câu hỏi lặp lại |
| **Không xử lý câu hỏi định tính** | 🟡 Trung bình | ~88 câu đáp án dạng văn bản (Nhóm B) không chạy được Python |
| **Thiếu Reranker** | 🟠 Thấp | RAG trả về 2-3 chunk nhưng không rank lại → premise kém chính xác |
| **Không có Evaluation Loop** | 🟠 Thấp | Không tự kiểm tra lại kết quả trước khi trả về |

---

## 1. Kiến Trúc Pipeline Tối Ưu (Đề Xuất)

```
[OFFLINE Phase]
┌─────────────────────────────────────────────────────────────────┐
│  Textbooks/PDF                                                  │
│      └──► LlamaParse/Marker ──► Markdown + LaTeX               │
│               └──► Chunker (by Law/Formula/300-500 tokens)     │
│                        └──► Dual Indexing                       │
│                               ├── Dense: bge-m3 → Qdrant       │
│                               └── Sparse: BM25 → Qdrant        │
│  Dataset (1,352 QA)                                             │
│      └──► Fine-tune DeepSeek-R1-7B (Unsloth/LoRA)              │
│               └──► LoRA adapter saved                          │
│  Answer Cache (Redis)                                           │
│      └──► Pre-compute ~200 "seed" questions                     │
└─────────────────────────────────────────────────────────────────┘

[ONLINE Phase — Per Request]
Question ──► [Step 0] Query Router
               ├──► TYPE: Quantitative (Tính toán số) ──► Path A
               └──► TYPE: Qualitative (Định tính/mô tả) ──► Path B

PATH A (Quantitative):
  ──► [Step 1] Redis Cache Lookup ──► HIT → Return cached response
                                  └──► MISS → Continue
  ──► [Step 2] Hybrid RAG (Qdrant) + Reranker (bge-reranker-v2)
               └──► premises[] (top-3 relevant laws/formulas)
  ──► [Step 3] DeepSeek-R1-7B (LoRA) Reasoning
               └──► <think> + FOL string + Python code block
  ──► [Step 4] Code Sandbox Executor (RestrictedPython)
               ├──► SUCCESS → (answer_value, unit) + confidence=0.95+
               └──► FAIL → Self-Repair Loop (max 2 retries) → fallback to LLM answer
  ──► [Step 5] Answer Normalizer
               └──► Convert to standard format (float, scientific, unit label)
  ──► [Step 6] Structuring Agent (Qwen2.5-7B + Instructor/Pydantic)
               └──► JSON: {answer, explanation, fol, cot[], premises[], confidence}
  ──► [Step 7] Redis Cache WRITE + Return Response

PATH B (Qualitative):
  ──► [Step 2] Hybrid RAG → premises[]
  ──► [Step 3] DeepSeek-R1-7B → text explanation + FOL
  ──► [Step 6] Structuring Agent → JSON (no code execution)
  ──► Return Response
```

---

## 2. Quyết Định Fine-Tune

### ✅ **NÊN Fine-tune** — Đây là lựa chọn bắt buộc cho bài toán này

**Lý do:**

| Yếu tố | Phân tích |
|--------|----------|
| **Dataset có CoT sẵn** | 1,352 mẫu × 5 bước CoT trung bình = ~6,760 bước suy luận có nhãn → gold data |
| **Domain hẹp** | Chỉ gồm 8 chủ đề Vật lý điện từ → base model 7B biết quá nhiều "rác" ngoài domain |
| **Format output cứng** | Endpoint yêu cầu JSON schema chính xác → fine-tune format compliance |
| **FOL generation** | Base model không tự nhiên sinh FOL đúng cú pháp → cần few-shot hoặc fine-tune |
| **Unit handling** | Dataset dạy cách xử lý µF→F, mC→C → fine-tune học được pattern này |

### Chiến lược Fine-tune:

#### Giai đoạn A: SFT (Supervised Fine-Tuning) — **Bắt buộc**
```
Dataset: 1,352 mẫu từ Physics_Problems_Text_Only.csv
Format training sample:
  INPUT:  <question> + <premises from RAG>
  OUTPUT: <think>...</think>
          [FOL]: ∀x...
          [CODE]: ```python ... ```
          [ANSWER]: {value} {unit}
          [COT]: ["Step 1:...", "Step 2:...", ...]
          [EXPLANATION]: "..."

Model: DeepSeek-R1-Distill-Qwen-7B
Tool:  Unsloth (4-bit QLoRA, r=16, alpha=32)
VRAM:  ~14GB (RTX 3090/4090 đủ dùng)
Time:  ~3-5 giờ train, 3 epochs
```

#### Giai đoạn B: ORPO/DPO — **Tùy chọn, nâng cao**
```
Nếu có thời gian: Dùng ORPO để dạy model prefer output đúng format
Tạo negative samples: Cố ý sinh output sai format / sai đơn vị → reject
Library: TRL (Transformer Reinforcement Learning)
```

---

## 3. Database & Tools — Chọn Lựa Cụ Thể

### 3.1 Vector Database: **Qdrant** ✅ (Giữ nguyên, đúng hướng)

```yaml
Lý do chọn Qdrant:
  - Hỗ trợ Hybrid Search (dense + sparse) native
  - Collection có thể filter theo metadata (prefix: LD, CH, TD...)
  - On-premise deployment, không cần cloud
  - Python client ổn định

Config đề xuất:
  Collection: "physics_kb"
  Vector size: 1024 (bge-m3)
  Distance: Cosine
  Sparse vector: BM25 tokenized
  Payload fields:
    - topic_code: "LD" | "CH" | "NL" | "TD" | "DDT" | "THCB" | "DT" | "CHLT"
    - formula_type: "law" | "definition" | "derivation"
    - content: str (chunk text)
    - source: "textbook_chapter_X"

Query strategy:
  - Dense weight: 0.7
  - Sparse weight: 0.3
  - Top-K: 5 → Reranker → Top-3 cho vào prompt
```

### 3.2 Response Cache: **Redis** 🆕 (Bổ sung mới)

```yaml
Mục đích:
  - Cache kết quả cho câu hỏi đã từng trả lời → response < 50ms
  - Pre-warm với ~200 câu seed từ dataset

Config:
  Backend: Redis 7.x (hoặc Valkey)
  Key: SHA256(question.strip().lower())
  Value: JSON response (stringify)
  TTL: 24 giờ (hoặc không TTL nếu câu hỏi tĩnh)
  Max memory: 512MB

Khi nào invalidate:
  - Khi model được re-fine-tune
  - Khi textbook KB được cập nhật

Python client: redis-py
```

### 3.3 Reranker: **bge-reranker-v2-m3** 🆕 (Bổ sung mới)

```yaml
Vị trí: Sau RAG retrieval, trước khi đưa premises vào prompt

Cách hoạt động:
  Input:  question + [chunk_1, chunk_2, ..., chunk_5]
  Output: Ranked list → lấy top-3 chunk có relevance score cao nhất

Model: BAAI/bge-reranker-v2-m3
  - Tốt với scientific/math text
  - CrossEncoder architecture → chính xác hơn bi-encoder retrieval
  - Chạy được trên CPU (nhẹ, ~560MB)

Code mẫu:
  from FlagEmbedding import FlagReranker
  reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)
  scores = reranker.compute_score([[question, chunk] for chunk in candidates])
  top3 = sorted(zip(scores, candidates), reverse=True)[:3]
```

### 3.4 Code Sandbox: **RestrictedPython + timeout** 🔧 (Cần nâng cấp)

```python
# Hiện tại: dùng exec() đơn giản → RỦI RO
# Đề xuất: RestrictedPython + resource limit

import RestrictedPython
import signal
import math, sympy

ALLOWED_MODULES = {'math', 'sympy', 'numpy'}

def safe_execute(code_str: str, timeout: int = 5) -> dict:
    """
    Returns: {"success": bool, "result": Any, "unit": str, "error": str}
    """
    # 1. Pre-check: phải có biến 'answer' và 'unit' trong code
    if 'answer' not in code_str or 'unit' not in code_str:
        return {"success": False, "error": "Missing answer/unit variable"}

    # 2. Compile với RestrictedPython
    try:
        byte_code = compile_restricted(code_str)
    except SyntaxError as e:
        return {"success": False, "error": str(e)}

    # 3. Execute với timeout
    local_vars = {'__builtins__': safe_globals, 'math': math}
    try:
        with timeout_context(timeout):
            exec(byte_code, local_vars)
        return {
            "success": True,
            "result": local_vars.get('answer'),
            "unit": local_vars.get('unit', '')
        }
    except TimeoutError:
        return {"success": False, "error": "Execution timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### 3.5 Answer Normalizer 🆕 (Bổ sung hoàn toàn mới)

```python
# Xử lý 3 nhóm đáp án đặc biệt trong dataset:

def normalize_answer(raw_answer: str, unit: str) -> tuple[str, str]:
    """
    Nhóm A – LaTeX/symbolic: parse và evaluate nếu có thể
      Input:  "9\\sqrt{3} × 10^-27", unit="N"
      Output: "1.559e-26", "N"

    Nhóm B – Text descriptive: giữ nguyên string
      Input:  "decreases by 4 times", unit=""
      Output: "decreases by 4 times", ""

    Nhóm C – Unicode scientific: chuẩn hóa về float string
      Input:  "4.0 × 10⁴", unit="V/m"
      Output: "40000.0", "V/m"   (hoặc "4.0e4")
    """
    import re, sympy

    # Detect Nhóm C: có × và superscript digits
    superscript_map = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁻', '0123456789-')
    if '×' in raw_answer or '×' in raw_answer:
        cleaned = raw_answer.translate(superscript_map)
        cleaned = cleaned.replace('×', 'e').replace(' ', '')
        try:
            val = float(cleaned.replace('10e', '1e1').replace('e10^', 'e'))
            return f"{val:.4g}", unit
        except: pass

    # Detect Nhóm A: LaTeX
    if '\\' in raw_answer or 'sqrt' in raw_answer or 'frac' in raw_answer:
        try:
            expr = sympy.sympify(raw_answer.replace('\\sqrt', 'sqrt')
                                           .replace('\\frac', '/'))
            val = float(expr.evalf())
            return f"{val:.4g}", unit
        except: pass

    # Nhóm B hoặc thuần số: trả về nguyên
    return raw_answer.strip(), unit
```

### 3.6 Query Router 🆕 (Bổ sung mới)

```python
# Phân loại câu hỏi trước khi vào pipeline
# Dùng rule-based + nhẹ, không cần LLM call

QUANTITATIVE_KEYWORDS = [
    'calculate', 'find', 'determine', 'compute', 'what is the value',
    'how much', 'magnitude', 'tính', 'xác định', 'bao nhiêu'
]
QUALITATIVE_KEYWORDS = [
    'explain', 'describe', 'what happens', 'direction', 'which way',
    'increases or decreases', 'qualitatively'
]

PREFIX_TYPES = {
    'LD': 'quantitative',   # Coulomb → tính lực, E
    'CH': 'quantitative',   # AC → tính Z, I, P
    'NL': 'quantitative',   # LC → tính W, f
    'TD': 'mixed',          # Tụ → tính C,Q,W; một số định tính
    'DDT': 'quantitative',  # Từ trường → tính B, Φ, L
    'THCB': 'mixed',        # Thực hành → sai số (mixed)
    'DT': 'quantitative',   # Điện thế → tính V, E
    'CHLT': 'quantitative', # Cộng hưởng → tính f0
}

def route_question(question: str) -> str:
    q_lower = question.lower()
    if any(kw in q_lower for kw in QUALITATIVE_KEYWORDS):
        return 'qualitative'
    return 'quantitative'  # default
```

---

## 4. Prompt Engineering Chi Tiết

### 4.1 System Prompt cho DeepSeek-R1-7B (Reasoner)

```
You are an expert physics problem solver. You MUST follow this exact output format:

[FOL]: <First-Order Logic representation of the problem>
[CODE]:
```python
import math

# Given values (always convert to SI units)
# ... (parse from question)

# Apply formula
# ...

answer = <computed_value>  # MUST be a number
unit = "<unit_string>"     # e.g., "N", "V/m", "J", "μF"
```

[ANSWER]: {answer} {unit}

Rules:
- ALWAYS define variables `answer` and `unit` in Python code
- Convert ALL units to SI before computing (μF→F, cm→m, mC→C)
- Use math.sqrt(), not ** 0.5 for clarity
- FOL must use standard first-order logic syntax
- Never guess: if formula not in premises, say so in explanation
```

### 4.2 Prompt cho Structuring Agent (Qwen2.5-7B)

```
Given the reasoning trace below, extract and structure into JSON.

REASONING TRACE:
{think_content}

COMPUTED ANSWER: {answer} {unit}
PREMISES USED: {premises_list}

Output MUST match this Pydantic schema:
class PhysicsResponse(BaseModel):
    answer: str                    # "0.045 J" or "decreases by 4 times"
    explanation: str               # 2-3 sentences, natural language
    fol: str                       # FOL string
    cot: List[str]                 # List of step strings, max 8 steps
    premises: List[str]            # Copied from input
    confidence: float = Field(ge=0.0, le=1.0)

Confidence scoring guide:
  0.95-1.00: Code executed successfully, answer is numeric
  0.75-0.94: Code executed but answer required approximation
  0.50-0.74: Answer from LLM reasoning without code verification
  0.10-0.49: Qualitative answer, no numerical verification
```

---

## 5. Kế Hoạch Tối Ưu Hóa Độ Trễ (Latency)

| Bước | Thời gian dự kiến | Giải pháp tối ưu |
|------|:-----------------:|-----------------|
| Redis Cache Lookup | < 5ms | Luôn check đầu tiên |
| Hybrid RAG (Qdrant) | 50-100ms | Index on SSD, HNSW graph |
| Reranker (bge-v2) | 80-150ms | Run on CPU (batch=1) |
| DeepSeek-R1-7B (4-bit) | 3-8s | vLLM engine, max_new_tokens=512 |
| Code Sandbox | 10-50ms | timeout=5s, pre-import scipy |
| Qwen2.5-7B Structuring | 1-3s | Smaller model, constrained decoding |
| **Tổng (cache miss)** | **~5-12s** | Acceptable for API |
| **Tổng (cache hit)** | **< 50ms** | Excellent |

### Tối ưu thêm:
- **vLLM**: Dùng thay cho HuggingFace generate → 3-5x nhanh hơn nhờ PagedAttention + continuous batching
- **Speculative Decoding**: DeepSeek-R1-7B làm draft, kiểm tra bằng model nhỏ hơn (1.5B)
- **Parallel Step 1+3**: RAG và prompt construction chạy song song
- **Quantization**: 4-bit AWQ (không phải GPTQ) → ít degradation hơn

---

## 6. Confidence Scoring — Calibration Chi Tiết

```python
def compute_confidence(
    code_success: bool,
    code_error: str | None,
    answer_type: str,          # "numeric" | "symbolic" | "text"
    rag_score: float,          # Top-1 reranker score [0,1]
    retries_used: int,         # 0, 1, or 2
) -> float:
    base = 0.0

    if code_success and answer_type == "numeric":
        base = 0.95
    elif code_success and answer_type == "symbolic":
        base = 0.80
    elif not code_success and retries_used > 0:
        base = 0.55
    elif answer_type == "text":
        base = 0.45

    # Điều chỉnh theo chất lượng RAG
    rag_bonus = (rag_score - 0.5) * 0.1  # [-0.05, +0.05]
    confidence = min(1.0, max(0.1, base + rag_bonus))

    # Phạt nếu phải retry
    confidence -= retries_used * 0.05

    return round(confidence, 2)
```

---

## 7. Xử Lý Đặc Biệt Cho Câu Hỏi Định Tính (Path B)

Khoảng **88 câu** trong dataset có đáp án là văn bản mô tả (như `"the voltage is halved"`, `"decreases by 4 times"`). Pipeline cần xử lý riêng:

```
PATH B Flow:
Question ──► Router (detect: qualitative) 
         ──► Hybrid RAG (premises)
         ──► DeepSeek-R1-7B [NO CODE requirement]
              Prompt: "Explain qualitatively what happens to [X] when [Y].
                       Answer in 1-2 sentences. Then list your reasoning steps."
         ──► Structuring Agent:
              {
                "answer": "decreases by 4 times",   # direct text
                "explanation": "When charge Q halves while C stays constant...",
                "fol": "∀cap(Capacitor(cap) ∧ ChargeHalved(cap) → EnergyQuartered(cap))",
                "cot": ["Step 1: W = Q²/2C ...", "Step 2: If Q→Q/2 ..."],
                "premises": ["Capacitor energy: W = Q²/(2C)"],
                "confidence": 0.45
              }
```

---

## 8. Chiến Lược Evaluation & Self-Correction Loop

```
Sau Code Sandbox thực thi:
  IF code fails:
    1. Parse error message
    2. Append error to prompt: "Your code had error: {error}. Fix it."
    3. Re-call DeepSeek-R1-7B (max 2 lần)
    4. If still fails: dùng LLM answer trực tiếp, confidence = 0.5

Sau Structuring Agent:
  1. Validate JSON vs Pydantic schema → auto-retry nếu invalid
  2. Sanity check answer: nếu answer là float và unit là N/V/m, kiểm tra order of magnitude hợp lý không
  3. Check cot[] có ≥ 3 bước không → nếu thiếu thì bổ sung từ <think>
```

---

## 9. Kế Hoạch Triển Khai Theo Giai Đoạn

### Giai đoạn 0 — Chuẩn bị (Tuần 1)
- [ ] Chuẩn hóa dataset: sửa 14 unit rỗng, normalize `µF→μF`, `—→-`
- [ ] Parse & chunk sách giáo khoa vật lý (LlamaParse)
- [ ] Setup Qdrant local + index KB
- [ ] Setup Redis local

### Giai đoạn 1 — Baseline Pipeline (Tuần 2)
- [ ] Implement Hybrid RAG + Reranker
- [ ] Implement Code Sandbox với RestrictedPython
- [ ] Implement Answer Normalizer (3 nhóm A/B/C)
- [ ] Implement Structuring Agent với Pydantic schema
- [ ] Implement Query Router
- [ ] Test end-to-end với 50 câu mẫu từ dataset

### Giai đoạn 2 — Fine-tuning (Tuần 3)
- [ ] Chuẩn bị training data: convert 1,352 mẫu sang format SFT
- [ ] Fine-tune DeepSeek-R1-7B bằng Unsloth (LoRA r=16)
- [ ] Đánh giá trên validation set (20% split)
- [ ] So sánh F1 answer accuracy: base model vs fine-tuned

### Giai đoạn 3 — Tối ưu (Tuần 4)
- [ ] Deploy với vLLM engine
- [ ] Pre-warm Redis cache với ~200 câu seed
- [ ] Implement Self-Correction loop (max 2 retries)
- [ ] Calibrate confidence scoring
- [ ] Load test: target < 10s/request (P95)
- [ ] Final evaluation trên test set

---

## 10. Tóm Tắt Stack Công Nghệ Cuối Cùng

| Layer | Công nghệ | Lý do chọn |
|-------|-----------|-----------|
| **PDF Parsing** | LlamaParse / Marker | Giữ LaTeX formula nguyên vẹn |
| **Embedding** | bge-m3 (BAAI) | Tốt nhất cho scientific text, multilingual |
| **Vector DB** | **Qdrant** | Hybrid search native, on-premise, fast |
| **Sparse Search** | BM25 (rank-bm25) | Bắt được keyword chính xác (đơn vị, định luật) |
| **Reranker** | bge-reranker-v2-m3 | CrossEncoder, chính xác hơn ANN retrieval |
| **Response Cache** | **Redis** | Sub-millisecond lookup, TTL support |
| **Reasoner** | DeepSeek-R1-Distill-Qwen-7B (LoRA) | Chain-of-thought native, code generation |
| **Fine-tune** | Unsloth + QLoRA (4-bit) | 2x faster, 60% less VRAM |
| **Code Sandbox** | RestrictedPython + timeout | An toàn, kiểm soát output |
| **Math Engine** | sympy + math (Python) | Exact symbolic + numeric computation |
| **Structuring** | Qwen2.5-7B-Instruct + Instructor | Constrained JSON generation via Pydantic |
| **Inference** | vLLM | 3-5x faster than naive HF generate |
| **Orchestration** | LangGraph hoặc custom async Python | Kiểm soát flow, retry, branching |
| **API** | FastAPI + Pydantic | Schema validation, async support |

---

## 11. Checklist Đảm Bảo Endpoint Compliance

```
✅ answer   : Code Sandbox output → normalize → string
✅ explanation: Qwen2.5 Structuring Agent → natural language
✅ fol      : DeepSeek-R1 generate → validate syntax
✅ cot[]    : Extract from <think> → list of Step strings ≥ 3
✅ premises[]: Qdrant Hybrid RAG + Reranker top-3
✅ confidence: Calibrated score với 5 tín hiệu
✅ JSON schema: Pydantic model validate trước khi return
✅ Unit     : Code always define `unit` variable → validate vs KB
✅ Edge cases: Qualitative answers → Path B (no code exec required)
✅ Latency  : Redis cache + vLLM → < 10s P95
```

# FLOW HOÀN CHỈNH - TYPE 1: LOGIC-BASED EDUCATIONAL QUERIES

## 📋 TỔNG QUAN

**Mục tiêu**: Xây dựng hệ thống reasoning cho bài toán logic với:

- ✅ Độ chính xác cao (accuracy)
- ✅ Reasoning tự nhiên (natural language explanation)
- ✅ Phân tích sâu (deep reasoning với premises tối thiểu)

**Ràng buộc**:

- Model open-source < 8B parameters
- Không dùng closed-source API (GPT, Claude, Gemini)
- Compute resources không giới hạn

---

## 🎯 CHIẾN LƯỢC TỔNG THỂ

### Phase 1: Data Understanding & Preprocessing

### Phase 2: Model Selection & Fine-tuning

### Phase 3: Reasoning Pipeline Development

### Phase 4: Evaluation & Optimization

---

## 📊 PHASE 1: DATA UNDERSTANDING & PREPROCESSING

### 1.1. Phân tích Dataset

```
Dataset: 411 records, 808 questions
Format: JSON với các trường:
- premises-FOL: Logic dạng First-Order Logic
- premises-NL: Logic dạng Natural Language
- questions: Câu hỏi (MCQ hoặc Yes/No/Unknown)
- answers: Đáp án
- explanations: Giải thích
- idx: Chỉ số premises tối thiểu cần dùng
```

**Action Items:**

- [ ] Load và explore dataset
- [ ] Phân tích phân bố:
  - Số premises trên mỗi record (min/max/avg)
  - Tỷ lệ MCQ vs Yes/No questions
  - Độ dài premises và questions
  - Phân bố idx (số premises cần thiết)
- [ ] Kiểm tra data quality (sau khi đã fix bugs)

### 1.2. Data Preprocessing

**Chuẩn bị dữ liệu cho training:**

```python
# Cấu trúc input-output
INPUT = {
    "premises": List[str],  # Danh sách premises (NL)
    "question": str,        # Câu hỏi
}

OUTPUT = {
    "answer": str,                    # A/B/C/D hoặc Yes/No/Unknown
    "reasoning": str,                 # Giải thích tự nhiên
    "relevant_premises_idx": List[int] # Premises được sử dụng
}
```

**Action Items:**

- [ ] Tạo train/val/test split (70/15/15 hoặc 80/10/10)
- [ ] Chuẩn hóa format:
  - Đánh số premises rõ ràng (P1, P2, ...)
  - Format câu hỏi MCQ nhất quán
  - Chuẩn hóa answer labels
- [ ] Tạo prompt templates cho các loại câu hỏi
- [ ] Augment data (nếu cần):
  - Shuffle thứ tự premises
  - Paraphrase questions
  - Tạo negative examples

---

## 🤖 PHASE 2: MODEL SELECTION & FINE-TUNING

### 2.1. Lựa chọn Base Model

**Tiêu chí chọn model:**

- Size < 8B parameters
- Khả năng reasoning tốt
- Hỗ trợ long context (nhiều premises)
- Open-source với license thân thiện

**Các model đề xuất (theo thứ tự ưu tiên):**

1. **Qwen2.5-7B-Instruct** ⭐ (Khuyến nghị)
   - 7B params
   - Context length: 128K tokens
   - Reasoning capability xuất sắc
   - Multilingual support tốt

2. **Llama-3.1-8B-Instruct**
   - 8B params
   - Context length: 128K tokens
   - Strong reasoning
   - Cộng đồng lớn

3. **Mistral-7B-Instruct-v0.3**
   - 7B params
   - Context length: 32K tokens
   - Hiệu quả, nhanh

4. **Phi-3-Medium-4K-Instruct**
   - 3.8B params (nhỏ hơn)
   - Context length: 4K tokens
   - Reasoning tốt cho size nhỏ

**Action Items:**

- [ ] Benchmark các model trên sample data
- [ ] Đánh giá:
  - Accuracy trên validation set
  - Quality của reasoning output
  - Inference speed
  - Memory usage
- [ ] Chọn model chính + backup

### 2.2. Fine-tuning Strategy

**Approach 1: Full Fine-tuning** (nếu có GPU đủ mạnh)

```
- Fine-tune toàn bộ model
- Cần: GPU 40GB+ (A100/H100)
- Training time: 6-12 hours
- Best performance
```

**Approach 2: LoRA/QLoRA** ⭐ (Khuyến nghị)

```
- Parameter-efficient fine-tuning
- Cần: GPU 24GB (RTX 4090/A5000)
- Training time: 3-6 hours
- Performance gần bằng full fine-tuning
```

**Approach 3: Prompt Engineering + Few-shot** (baseline)

```
- Không cần training
- Chỉ cần inference GPU
- Nhanh nhưng performance thấp hơn
```

**Training Configuration:**

```python
# LoRA config (đề xuất)
lora_config = {
    "r": 16,              # Rank
    "lora_alpha": 32,     # Scaling factor
    "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
    "lora_dropout": 0.05,
    "bias": "none",
}

# Training args
training_args = {
    "num_epochs": 3-5,
    "batch_size": 4-8,
    "learning_rate": 2e-4,
    "warmup_steps": 100,
    "gradient_accumulation_steps": 4,
    "max_seq_length": 4096,
}
```

**Action Items:**

- [ ] Setup training environment (transformers, peft, bitsandbytes)
- [ ] Prepare training data với format phù hợp
- [ ] Implement training script
- [ ] Train model với hyperparameter tuning
- [ ] Save checkpoints và evaluate

---

## 🔄 PHASE 3: REASONING PIPELINE DEVELOPMENT

### 3.1. Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT PROCESSING                          │
│  - Parse premises (P1, P2, ..., Pn)                         │
│  - Parse question                                            │
│  - Format prompt                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 1: PREMISE SELECTION                      │
│  Model identifies relevant premises for the question         │
│  Output: List of premise indices [i, j, k, ...]             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 2: REASONING GENERATION                   │
│  Model generates step-by-step reasoning using selected      │
│  premises in natural language                                │
│  Output: Detailed explanation                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 3: ANSWER EXTRACTION                      │
│  Extract final answer from reasoning                         │
│  Output: A/B/C/D or Yes/No/Unknown                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              STAGE 4: VERIFICATION (Optional)                │
│  - Check logical consistency                                 │
│  - Verify premise usage                                      │
│  - Confidence scoring                                        │
└─────────────────────────────────────────────────────────────┘
```

### 3.2. Prompt Engineering

**Template cho Multi-stage Reasoning:**

```python
STAGE_1_PROMPT = """You are a logical reasoning expert. Given a set of premises and a question, identify which premises are NECESSARY to answer the question.

Premises:
{premises_numbered}

Question: {question}

Task: List the premise numbers (e.g., P1, P5, P7) that are directly needed to answer this question. Use the MINIMUM number of premises.

Relevant Premises:"""

STAGE_2_PROMPT = """You are a logical reasoning expert. Using ONLY the following premises, provide a clear, step-by-step explanation to answer the question.

Relevant Premises:
{selected_premises}

Question: {question}

Provide your reasoning in natural language, explaining each logical step clearly. Then state your final answer.

Reasoning:"""

STAGE_3_PROMPT = """Extract the final answer from the reasoning below.

Reasoning: {reasoning}

Question Type: {question_type}  # MCQ or Yes/No

Final Answer (only A/B/C/D or Yes/No/Unknown):"""
```

**Template cho Single-stage (End-to-end):**

```python
E2E_PROMPT = """You are a logical reasoning expert. Given premises and a question, you must:
1. Identify which premises are relevant
2. Provide step-by-step reasoning
3. Give the final answer

Premises:
{premises_numbered}

Question: {question}

Provide your response in this format:
**Relevant Premises:** [List premise numbers]
**Reasoning:** [Step-by-step explanation in natural language]
**Answer:** [A/B/C/D or Yes/No/Unknown]

Response:"""
```

**Action Items:**

- [ ] Implement prompt templates
- [ ] Test với different prompt variations
- [ ] A/B testing để chọn prompt tốt nhất
- [ ] Implement prompt chaining (multi-stage)

### 3.3. Post-processing & Validation

**Answer Extraction:**

```python
def extract_answer(text, question_type):
    """Extract answer from model output"""
    if question_type == "MCQ":
        # Look for A, B, C, D
        pattern = r'\b([ABCD])\b'
    else:
        # Look for Yes, No, Unknown
        pattern = r'\b(Yes|No|Unknown)\b'

    matches = re.findall(pattern, text, re.IGNORECASE)
    return matches[-1] if matches else "Unknown"
```

**Premise Index Extraction:**

```python
def extract_premise_indices(text, num_premises):
    """Extract premise numbers from text"""
    pattern = r'P(\d+)'
    indices = [int(m) for m in re.findall(pattern, text)]
    # Validate indices
    indices = [i for i in indices if 1 <= i <= num_premises]
    return sorted(set(indices))
```

**Action Items:**

- [ ] Implement robust parsing functions
- [ ] Handle edge cases (malformed outputs)
- [ ] Add confidence scoring
- [ ] Implement fallback mechanisms

---

## 📈 PHASE 4: EVALUATION & OPTIMIZATION

### 4.1. Evaluation Metrics

**1. Answer Accuracy**

```python
accuracy = correct_answers / total_questions
```

**2. Premise Selection Quality**

```python
# Precision: Tỷ lệ premises được chọn đúng
precision = |predicted ∩ ground_truth| / |predicted|

# Recall: Tỷ lệ premises cần thiết được tìm ra
recall = |predicted ∩ ground_truth| / |ground_truth|

# F1 Score
f1 = 2 * (precision * recall) / (precision + recall)

# Efficiency: Số premises dư thừa
efficiency = 1 - (|predicted - ground_truth| / |predicted|)
```

**3. Reasoning Quality** (Manual evaluation hoặc LLM-as-judge)

```
Criteria:
- Clarity (1-5): Reasoning có rõ ràng không?
- Naturalness (1-5): Có giống lời nói tự nhiên không?
- Depth (1-5): Phân tích có sâu không?
- Logical Consistency (1-5): Logic có nhất quán không?

Overall Score = Average of 4 criteria
```

**4. Combined Score**

```python
final_score = (
    0.4 * accuracy +           # 40% trọng số
    0.2 * premise_f1 +         # 20% trọng số
    0.4 * reasoning_quality    # 40% trọng số
)
```

### 4.2. Evaluation Pipeline

**Action Items:**

- [ ] Implement automatic metrics (accuracy, F1)
- [ ] Setup manual evaluation framework
- [ ] Create evaluation dataset (100-200 samples)
- [ ] Run baseline evaluation
- [ ] Identify failure cases

### 4.3. Optimization Strategies

**If Accuracy is Low:**

- [ ] Increase training data (augmentation)
- [ ] Try different base models
- [ ] Adjust training hyperparameters
- [ ] Implement ensemble methods

**If Premise Selection is Poor:**

- [ ] Add explicit premise selection training
- [ ] Use chain-of-thought prompting
- [ ] Implement attention visualization
- [ ] Add premise relevance scoring

**If Reasoning Quality is Low:**

- [ ] Fine-tune on high-quality reasoning examples
- [ ] Use reasoning templates
- [ ] Implement self-consistency checking
- [ ] Add human feedback (RLHF-style)

**Advanced Techniques:**

- [ ] Self-consistency: Generate multiple reasoning paths, vote
- [ ] Retrieval-augmented: Use similar examples
- [ ] Iterative refinement: Model critiques its own output
- [ ] Ensemble: Combine multiple models

---

## 🛠️ IMPLEMENTATION ROADMAP

### Week 1: Setup & Data Preparation

- [ ] Day 1-2: Environment setup, data exploration
- [ ] Day 3-4: Data preprocessing, train/val/test split
- [ ] Day 5-7: Prompt engineering, baseline testing

### Week 2: Model Training

- [ ] Day 1-2: Model selection, benchmark
- [ ] Day 3-5: Fine-tuning (LoRA)
- [ ] Day 6-7: Evaluation, checkpoint selection

### Week 3: Pipeline Development

- [ ] Day 1-3: Implement reasoning pipeline
- [ ] Day 4-5: Post-processing, validation
- [ ] Day 6-7: Integration testing

### Week 4: Optimization & Evaluation

- [ ] Day 1-3: Full evaluation on test set
- [ ] Day 4-5: Error analysis, optimization
- [ ] Day 6-7: Final testing, documentation

---

## 📦 DELIVERABLES

### Code

- [ ] Data preprocessing scripts
- [ ] Training scripts (with configs)
- [ ] Inference pipeline
- [ ] Evaluation scripts
- [ ] Demo notebook/app

### Models

- [ ] Fine-tuned model checkpoints
- [ ] LoRA adapters
- [ ] Model cards with performance metrics

### Documentation

- [ ] Technical report
- [ ] API documentation
- [ ] Usage examples
- [ ] Performance analysis

### Results

- [ ] Evaluation metrics on test set
- [ ] Error analysis report
- [ ] Comparison with baselines
- [ ] Sample outputs showcase

---

## 🔧 TECHNICAL STACK

### Core Libraries

```
- transformers (Hugging Face)
- peft (LoRA/QLoRA)
- bitsandbytes (quantization)
- torch / pytorch
- datasets (Hugging Face)
```

### Utilities

```
- pandas, numpy (data processing)
- scikit-learn (metrics)
- wandb / tensorboard (tracking)
- jupyter (experimentation)
```

### Deployment (Optional)

```
- fastapi (API server)
- gradio (demo UI)
- docker (containerization)
```

---

## 📝 NOTES & CONSIDERATIONS

### Challenges

1. **Long context**: Nhiều premises (10-30) → cần model với long context
2. **Premise selection**: Khó xác định premises tối thiểu
3. **Natural reasoning**: Khó generate reasoning tự nhiên
4. **Small model**: < 8B params → trade-off performance

### Solutions

1. Use models with 128K context (Qwen, Llama 3.1)
2. Multi-stage pipeline: separate premise selection
3. Fine-tune on high-quality reasoning data
4. Optimize with LoRA, quantization

### Future Improvements

- [ ] Implement symbolic reasoning (Z3 solver) as verification
- [ ] Add multi-modal support (diagrams)
- [ ] Explore mixture-of-experts
- [ ] Build reasoning dataset from scratch

---

## 🎓 LEARNING RESOURCES

### Papers

- Chain-of-Thought Prompting (Wei et al., 2022)
- Self-Consistency (Wang et al., 2022)
- LoRA (Hu et al., 2021)
- Llama 3 Technical Report

### Tutorials

- Hugging Face Fine-tuning Guide
- PEFT Documentation
- Prompt Engineering Guide

---

**Last Updated**: 2026-05-18
**Version**: 1.0
**Status**: Ready for Implementation

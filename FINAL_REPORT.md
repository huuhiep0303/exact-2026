# EXACT 2026 - Type 1 (Logic-Based Educational Queries) - Báo Cáo Hoàn Chỉnh

## 📋 Tổng Quan

Dự án này xây dựng một hệ thống AI để giải quyết các câu hỏi logic dựa trên tập dữ liệu EXACT 2026 Type 1. Hệ thống sử dụng mô hình ngôn ngữ lớn (LLM) mã nguồn mở với kỹ thuật fine-tuning hiệu quả để tạo ra câu trả lời chính xác kèm theo quá trình reasoning tự nhiên.

### Mục Tiêu

- **Trả lời chính xác**: Đưa ra đáp án đúng cho các câu hỏi logic
- **Reasoning tự nhiên**: Giải thích quá trình suy luận như lời nói tự nhiên
- **Chọn premises phù hợp**: Xác định các tiền đề cần thiết để trả lời câu hỏi

### Tiêu Chí Đánh Giá

- **40%** - Độ chính xác của câu trả lời (Accuracy)
- **20%** - Độ chính xác chọn premises (Premise F1)
- **40%** - Chất lượng reasoning (Reasoning Quality)

---

## 🏗️ Kiến Trúc Hệ Thống

### 1. Lựa Chọn Mô Hình: Qwen2.5-7B-Instruct

**Lý do chọn Qwen2.5-7B-Instruct:**

1. **Tuân thủ ràng buộc**:
   - Mã nguồn mở (Open-source)
   - Kích thước < 8B parameters (7B params)
   - Không sử dụng closed-source APIs

2. **Hiệu suất vượt trội**:
   - Top model trong phân khúc 7B parameters
   - Khả năng reasoning logic mạnh mẽ
   - Hỗ trợ context dài (4096 tokens)
   - Được huấn luyện trên dữ liệu đa dạng

3. **Tối ưu cho tác vụ**:
   - Instruction-following tốt
   - Khả năng phân tích logic cao
   - Tạo văn bản tự nhiên
   - Hỗ trợ tiếng Việt và tiếng Anh

### 2. Kỹ Thuật Fine-tuning: LoRA (Low-Rank Adaptation)

**Lý do sử dụng LoRA:**

1. **Hiệu quả về tài nguyên**:
   - Chỉ train một phần nhỏ parameters (~1-2% của model)
   - Giảm memory footprint đáng kể
   - Tăng tốc độ training

2. **Chất lượng cao**:
   - Đạt hiệu suất tương đương full fine-tuning
   - Tránh catastrophic forgetting
   - Dễ dàng merge với base model

3. **Cấu hình LoRA**:
   ```yaml
   r: 16 # Rank của LoRA matrices
   lora_alpha: 32 # Scaling factor
   target_modules: # Các modules được fine-tune
     - q_proj # Query projection
     - v_proj # Value projection
     - k_proj # Key projection
     - o_proj # Output projection
   lora_dropout: 0.05 # Dropout để regularization
   ```

### 3. Quantization: 4-bit NF4

**Lý do sử dụng 4-bit quantization:**

1. **Giảm memory usage**:
   - Model 7B từ ~14GB xuống ~4GB
   - Cho phép train trên GPU consumer-grade
   - Tăng batch size

2. **Duy trì chất lượng**:
   - NF4 (Normal Float 4-bit) tối ưu cho neural networks
   - Double quantization để giảm thêm memory
   - Compute dtype float16 cho tính toán

### 4. Pipeline Xử Lý

Hệ thống sử dụng **Multi-stage Reasoning Pipeline**:

```
Input (Premises + Question)
    ↓
Stage 1: Premise Selection
    → Xác định premises liên quan
    ↓
Stage 2: Reasoning Generation
    → Tạo quá trình suy luận
    ↓
Stage 3: Answer Extraction
    → Trích xuất đáp án cuối cùng
    ↓
Output (Answer + Reasoning + Relevant Premises)
```

**Ưu điểm của pipeline này:**

- Tách biệt các bước xử lý
- Dễ debug và cải thiện từng stage
- Tạo reasoning có cấu trúc rõ ràng
- Cho phép đánh giá từng component

---

## 📁 Cấu Trúc Dự Án

```
EXACT 2026/Project/
│
├── configs/
│   └── config.yaml                 # Cấu hình toàn bộ hệ thống
│
├── src/
│   ├── data/
│   │   ├── data_loader.py         # Load dữ liệu từ file
│   │   ├── data_processor.py      # Xử lý và split dữ liệu
│   │   └── dataset.py             # PyTorch Dataset class
│   │
│   ├── models/
│   │   ├── model_loader.py        # Load model với LoRA
│   │   └── inference.py           # Pipeline inference
│   │
│   ├── training/
│   │   └── trainer.py             # Training logic
│   │
│   ├── evaluation/
│   │   ├── metrics.py             # Các metrics đánh giá
│   │   └── evaluator.py           # Evaluator class
│   │
│   └── utils/
│       ├── config_loader.py       # Load config
│       ├── logger.py              # Logging
│       └── helpers.py             # Helper functions
│
├── 02_preprocess_data.py          # Script tiền xử lý dữ liệu
├── 03_train.py                    # Script training
├── 04_evaluate.py                 # Script đánh giá
├── 05_inference.py                # Script inference
│
├── requirements.txt               # Dependencies
└── FINAL_REPORT.md               # Báo cáo này
```

---

## 🔧 Chi Tiết Các Module

### 1. Data Processing (`src/data/`)

**data_loader.py**: Load dữ liệu từ JSON

- Đọc file JSON dataset
- Validate format
- Trả về list of samples

**data_processor.py**: Xử lý và split dữ liệu

- Format dữ liệu cho training
- Split train/val/test (70/15/15)
- Tạo prompts theo template
- Lưu processed data

**dataset.py**: PyTorch Dataset

- Custom Dataset class
- Tokenization
- Padding và truncation
- Batch processing

### 2. Model (`src/models/`)

**model_loader.py**: Load model với LoRA

- Load base model (Qwen2.5-7B-Instruct)
- Apply 4-bit quantization
- Setup LoRA adapters
- Prepare for training

**inference.py**: Inference pipeline

- Multi-stage reasoning
- Premise selection
- Answer extraction
- Post-processing

### 3. Training (`src/training/`)

**trainer.py**: Training logic

- Setup training arguments
- Create Trainer instance
- Training loop
- Validation
- Checkpoint saving

### 4. Evaluation (`src/evaluation/`)

**metrics.py**: Các metrics

- `calculate_accuracy()`: Độ chính xác câu trả lời
- `calculate_premise_f1()`: F1 score cho premise selection
- `evaluate_reasoning_quality()`: Đánh giá chất lượng reasoning
- `calculate_combined_score()`: Tổng hợp điểm

**evaluator.py**: Evaluator class

- Load test data
- Run inference
- Calculate metrics
- Save results

### 5. Utils (`src/utils/`)

**config_loader.py**: Load configuration từ YAML

**logger.py**: Logging system với colors và file output

**helpers.py**: Helper functions (set seed, format time, etc.)

---

## 🚀 Hướng Dẫn Sử Dụng

### Bước 0: Cài Đặt Môi Trường

```bash
# Tạo virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

**Yêu cầu hệ thống:**

- Python 3.8+
- CUDA 11.8+ (khuyến nghị)
- GPU với ít nhất 8GB VRAM (khuyến nghị 16GB+)
- 50GB disk space

### Bước 1: Tiền Xử Lý Dữ Liệu

```bash
python 02_preprocess_data.py
```

**Chức năng:**

- Load dữ liệu từ `EXACT2026_dataset_2026-05-15/Logic_Based_Educational_Queries_Text_Only/`
- Xử lý và format dữ liệu
- Split thành train/val/test (70/15/15)
- Lưu vào `outputs/processed_data/`

**Output:**

- `outputs/processed_data/train.json` (~288 samples)
- `outputs/processed_data/val.json` (~62 samples)
- `outputs/processed_data/test.json` (~61 samples)

### Bước 2: Training Model

```bash
python 03_train.py
```

**Chức năng:**

- Load Qwen2.5-7B-Instruct với 4-bit quantization
- Apply LoRA adapters
- Fine-tune trên training data
- Validate trên validation data
- Save checkpoints

**Thời gian ước tính:**

- GPU RTX 3090: ~2-3 giờ
- GPU RTX 4090: ~1-2 giờ
- GPU A100: ~1 giờ

**Output:**

- Checkpoints: `outputs/checkpoints/checkpoint-{step}/`
- Final model: `outputs/checkpoints/final_model/`
- Logs: `outputs/logs/`

**Theo dõi training:**

- Logs được lưu trong `outputs/logs/`
- Metrics: loss, learning rate, training speed
- Validation metrics mỗi 50 steps

### Bước 3: Đánh Giá Model

```bash
python 04_evaluate.py
```

**Chức năng:**

- Load trained model
- Run inference trên test set
- Calculate metrics
- Save results và predictions

**Output:**

- `outputs/results/evaluation_results.json`: Metrics tổng hợp
- `outputs/results/evaluation_results_predictions.json`: Chi tiết predictions

**Metrics được tính:**

- Accuracy: Độ chính xác câu trả lời
- Premise F1/Precision/Recall: Độ chính xác chọn premises
- Reasoning Quality: Chất lượng reasoning (1-5)
- Combined Score: Điểm tổng hợp (40% accuracy + 20% premise F1 + 40% reasoning)

### Bước 4: Inference

**Batch inference:**

```bash
python 05_inference.py --input_file input.json --output_file output.json
```

**Interactive mode:**

```bash
python 05_inference.py --interactive
```

**Format input file (JSON):**

```json
[
  {
    "id": "sample_1",
    "premises": [
      "Premise 1 text",
      "Premise 2 text",
      ...
    ],
    "question": "Question text?"
  }
]
```

**Format output:**

```json
[
  {
    "id": "sample_1",
    "question": "Question text?",
    "answer": "A",
    "reasoning": "Detailed reasoning...",
    "relevant_premises": [0, 2, 5]
  }
]
```

---

## ⚙️ Cấu Hình Chi Tiết

File `configs/config.yaml` chứa tất cả cấu hình:

### Data Configuration

```yaml
data:
  raw_data_path: "path/to/raw/data.json"
  processed_dir: "outputs/processed_data"
  train_file: "outputs/processed_data/train.json"
  val_file: "outputs/processed_data/val.json"
  test_file: "outputs/processed_data/test.json"

split:
  train: 0.70
  val: 0.15
  test: 0.15
  random_seed: 42
```

### Model Configuration

```yaml
model:
  name: "Qwen/Qwen2.5-7B-Instruct"
  max_length: 4096
  temperature: 0.7
  top_p: 0.9
  do_sample: true
```

### LoRA Configuration

```yaml
lora:
  r: 16 # Rank
  lora_alpha: 32 # Alpha
  target_modules: # Target modules
    - "q_proj"
    - "v_proj"
    - "k_proj"
    - "o_proj"
  lora_dropout: 0.05
  bias: "none"
  task_type: "CAUSAL_LM"
```

### Training Configuration

```yaml
training:
  output_dir: "outputs/checkpoints"
  num_train_epochs: 3
  per_device_train_batch_size: 4
  gradient_accumulation_steps: 4
  learning_rate: 2.0e-4
  weight_decay: 0.01
  warmup_steps: 100
  fp16: true
  optim: "paged_adamw_8bit"
```

### Quantization Configuration

```yaml
quantization:
  load_in_4bit: true
  bnb_4bit_compute_dtype: "float16"
  bnb_4bit_quant_type: "nf4"
  bnb_4bit_use_double_quant: true
```

---

## 📊 Kết Quả Dự Kiến

### Baseline Performance (Ước tính)

| Metric             | Score      | Weight | Contribution |
| ------------------ | ---------- | ------ | ------------ |
| Accuracy           | 75-85%     | 40%    | 30-34%       |
| Premise F1         | 70-80%     | 20%    | 14-16%       |
| Reasoning Quality  | 3.5-4.5/5  | 40%    | 28-36%       |
| **Combined Score** | **72-86%** | -      | -            |

### Phân Tích Kết Quả

**Accuracy (75-85%)**:

- Model có khả năng reasoning logic tốt
- Fine-tuning giúp adapt với domain cụ thể
- Có thể cải thiện bằng data augmentation

**Premise F1 (70-80%)**:

- Model học được cách chọn premises liên quan
- Có thể cải thiện bằng explicit premise selection training
- Trade-off giữa precision và recall

**Reasoning Quality (3.5-4.5/5)**:

- Model tạo reasoning tự nhiên
- Có cấu trúc logic rõ ràng
- Có thể cải thiện bằng prompt engineering

---

## 🔍 Phân Tích Kỹ Thuật

### 1. Prompt Engineering

**Template được sử dụng:**

```
You are an expert in logical reasoning. Given a set of premises and a question,
you need to:
1. Identify the relevant premises needed to answer the question
2. Provide clear reasoning based on those premises
3. Give the final answer

Premises:
{premises}

Question: {question}

Please provide:
1. Your reasoning process (explain step by step)
2. The relevant premise indices you used
3. Your final answer

Format your response as:
REASONING: [your reasoning]
PREMISES: [comma-separated indices]
ANSWER: [your answer]
```

**Ưu điểm:**

- Rõ ràng, có cấu trúc
- Hướng dẫn model từng bước
- Dễ parse output

### 2. Training Strategy

**Curriculum Learning:**

- Epoch 1: Học basic reasoning patterns
- Epoch 2: Học complex logical relationships
- Epoch 3: Fine-tune và polish

**Regularization:**

- LoRA dropout: 0.05
- Weight decay: 0.01
- Gradient clipping: 1.0

**Optimization:**

- AdamW 8-bit (paged)
- Cosine learning rate schedule
- Warmup: 100 steps

### 3. Evaluation Strategy

**Multi-faceted Evaluation:**

1. **Accuracy**: Exact match với ground truth
2. **Premise F1**:
   - Precision: Tỷ lệ premises đúng trong predictions
   - Recall: Tỷ lệ premises cần thiết được tìm thấy
   - F1: Harmonic mean của precision và recall

3. **Reasoning Quality**:
   - Clarity: Độ rõ ràng (sentence structure)
   - Naturalness: Tính tự nhiên (natural language markers)
   - Depth: Độ sâu phân tích (length, complexity)
   - Consistency: Tính nhất quán (logical connectors)

---

## 🚧 Cải Thiện Trong Tương Lai

### 1. Model Improvements

**Ensemble Methods:**

- Kết hợp nhiều checkpoints
- Voting mechanism
- Confidence-based selection

**Advanced Fine-tuning:**

- QLoRA với higher rank
- Full fine-tuning (nếu có resources)
- Multi-task learning

### 2. Data Improvements

**Data Augmentation:**

- Paraphrase premises và questions
- Synthetic data generation
- Back-translation

**Hard Negative Mining:**

- Tìm các premises gây nhiễu
- Train model phân biệt relevant/irrelevant

### 3. Pipeline Improvements

**Better Premise Selection:**

- Separate model cho premise selection
- Attention-based selection
- Retrieval-augmented approach

**Better Reasoning Generation:**

- Chain-of-thought prompting
- Self-consistency
- Reasoning verification

### 4. Evaluation Improvements

**Better Reasoning Metrics:**

- LLM-as-judge (sử dụng model khác đánh giá)
- Human evaluation
- Structured reasoning evaluation

---

## 🐛 Troubleshooting

### Lỗi Thường Gặp

**1. CUDA Out of Memory:**

```
Solution:
- Giảm batch_size trong config.yaml
- Tăng gradient_accumulation_steps
- Sử dụng 4-bit quantization
- Clear cache: torch.cuda.empty_cache()
```

**2. Model Loading Error:**

```
Solution:
- Kiểm tra internet connection (download model)
- Kiểm tra HuggingFace token (nếu cần)
- Xóa cache và download lại: rm -rf ~/.cache/huggingface
```

**3. Training Too Slow:**

```
Solution:
- Kiểm tra GPU được sử dụng: nvidia-smi
- Tăng batch_size nếu có memory
- Sử dụng fp16=true
- Giảm max_length nếu có thể
```

**4. Poor Performance:**

```
Solution:
- Tăng num_epochs
- Điều chỉnh learning_rate
- Cải thiện prompt template
- Augment training data
```

---

## 📚 Dependencies

Các thư viện chính trong `requirements.txt`:

```
torch>=2.0.0              # Deep learning framework
transformers>=4.36.0      # HuggingFace transformers
peft>=0.7.0              # LoRA implementation
bitsandbytes>=0.41.0     # Quantization
accelerate>=0.25.0       # Training acceleration
datasets>=2.16.0         # Dataset handling
tqdm>=4.66.0             # Progress bars
pyyaml>=6.0              # Config loading
numpy>=1.24.0            # Numerical operations
scikit-learn>=1.3.0      # Metrics
```

---

## 📖 Tài Liệu Tham Khảo

### Papers

1. **LoRA**: "LoRA: Low-Rank Adaptation of Large Language Models" (Hu et al., 2021)
2. **QLoRA**: "QLoRA: Efficient Finetuning of Quantized LLMs" (Dettmers et al., 2023)
3. **Qwen2.5**: "Qwen2.5 Technical Report" (Alibaba, 2024)

### Resources

- HuggingFace Transformers: https://huggingface.co/docs/transformers
- PEFT Documentation: https://huggingface.co/docs/peft
- Qwen2.5 Model Card: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct

---

## 👥 Liên Hệ & Hỗ Trợ

Nếu có vấn đề hoặc câu hỏi:

1. Kiểm tra phần Troubleshooting
2. Xem logs trong `outputs/logs/`
3. Kiểm tra config trong `configs/config.yaml`

---

## 📝 Ghi Chú

### Thời Gian Thực Hiện

- Data preprocessing: ~5 phút
- Training: ~2-3 giờ (GPU RTX 3090)
- Evaluation: ~10-15 phút
- Total: ~3-4 giờ

### Disk Space

- Model weights: ~4GB (quantized)
- Checkpoints: ~12GB (3 checkpoints)
- Processed data: ~10MB
- Logs & results: ~50MB
- Total: ~16GB

### Memory Requirements

- Training: 8-12GB VRAM
- Inference: 4-6GB VRAM
- RAM: 16GB khuyến nghị

---

## ✅ Checklist Hoàn Thành

- [x] Phân tích dataset và requirements
- [x] Thiết kế kiến trúc hệ thống
- [x] Implement data processing pipeline
- [x] Implement model loading với LoRA
- [x] Implement training pipeline
- [x] Implement evaluation metrics
- [x] Implement inference pipeline
- [x] Tạo scripts chạy end-to-end
- [x] Viết documentation chi tiết
- [x] Tạo configuration file
- [x] Setup logging system

---

## 🎯 Kết Luận

Hệ thống đã được xây dựng hoàn chỉnh với:

✅ **Kiến trúc chuyên nghiệp**: Modular, dễ maintain và extend

✅ **Model phù hợp**: Qwen2.5-7B-Instruct với LoRA - tối ưu cho task

✅ **Pipeline hiệu quả**: Multi-stage reasoning với premise selection

✅ **Evaluation toàn diện**: Đánh giá đa chiều (accuracy, premise, reasoning)

✅ **Documentation đầy đủ**: Hướng dẫn chi tiết từng bước

✅ **Production-ready**: Có thể deploy và scale

Hệ thống sẵn sàng để:

1. Train trên dữ liệu EXACT 2026 Type 1
2. Đánh giá hiệu suất
3. Deploy cho inference
4. Cải thiện và tối ưu tiếp

---

**Chúc bạn thành công với EXACT 2026! 🚀**

# 🚀 QUICK START GUIDE - EXACT 2026 TYPE 1

## 📌 TÓM TẮT NHANH

**Mục tiêu**: Xây dựng model reasoning cho bài toán logic
**Dataset**: 411 records, 808 câu hỏi logic
**Model**: Open-source < 8B params (Qwen2.5-7B khuyến nghị)
**Đánh giá**: Accuracy + Reasoning Quality + Premise Selection

---

## 🎯 ROADMAP 4 TUẦN

### ✅ TUẦN 1: Setup & Data Preparation

**Mục tiêu**: Hiểu data, chuẩn bị môi trường

**Ngày 1-2: Setup**

```bash
# 1. Setup environment
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Verify installation
python test_installation.py
```

**Ngày 3-4: Data Exploration**

```bash
# Run exploration script
python 01_explore_data.py

# Review outputs
# - outputs/exploration/premises_distribution.png
# - outputs/exploration/answer_distribution.png
# - outputs/exploration/summary_statistics.csv
```

**Ngày 5-7: Data Preprocessing**

```bash
# Run preprocessing
python 02_preprocess_data.py

# Review outputs
# - outputs/processed_data/train.json
# - outputs/processed_data/val.json
# - outputs/processed_data/test.json
# - outputs/processed_data/*_samples.txt
```

**Deliverables**:

- ✅ Environment setup hoàn tất
- ✅ Data exploration report
- ✅ Processed train/val/test splits

---

### ✅ TUẦN 2: Model Selection & Training

**Mục tiêu**: Chọn model, fine-tune

**Ngày 1-2: Model Benchmark**

```python
# Test các model candidates
models_to_test = [
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3"
]

# Run baseline inference trên validation set
# Đánh giá: accuracy, reasoning quality, speed
```

**Ngày 3-5: Fine-tuning với LoRA**

```python
# Training script (sẽ tạo sau)
python scripts/train.py \
    --model_name "Qwen/Qwen2.5-7B-Instruct" \
    --train_file "outputs/processed_data/train.json" \
    --val_file "outputs/processed_data/val.json" \
    --output_dir "outputs/checkpoints/qwen-lora" \
    --num_epochs 3 \
    --batch_size 4 \
    --learning_rate 2e-4 \
    --lora_r 16 \
    --lora_alpha 32
```

**Ngày 6-7: Evaluation & Checkpoint Selection**

```bash
# Evaluate checkpoints
python scripts/evaluate.py \
    --checkpoint_dir "outputs/checkpoints/qwen-lora" \
    --test_file "outputs/processed_data/val.json"

# Select best checkpoint based on metrics
```

**Deliverables**:

- ✅ Model benchmark report
- ✅ Fine-tuned model checkpoints
- ✅ Training logs & metrics

---

### ✅ TUẦN 3: Pipeline Development

**Mục tiêu**: Xây dựng inference pipeline

**Ngày 1-3: Implement Reasoning Pipeline**

```
Components:
1. Premise Selection Module
2. Reasoning Generation Module
3. Answer Extraction Module
4. Post-processing & Validation
```

**Ngày 4-5: Testing & Debugging**

```bash
# Test pipeline trên validation set
python scripts/inference.py \
    --model_path "outputs/checkpoints/qwen-lora/best" \
    --input_file "outputs/processed_data/val.json" \
    --output_file "outputs/results/val_predictions.json"
```

**Ngày 6-7: Integration & Optimization**

```
- Optimize inference speed
- Add batch processing
- Implement caching
- Error handling
```

**Deliverables**:

- ✅ Complete inference pipeline
- ✅ Validation results
- ✅ Performance benchmarks

---

### ✅ TUẦN 4: Evaluation & Optimization

**Mục tiêu**: Đánh giá toàn diện, tối ưu

**Ngày 1-3: Full Evaluation**

```bash
# Run on test set
python scripts/evaluate.py \
    --model_path "outputs/checkpoints/qwen-lora/best" \
    --test_file "outputs/processed_data/test.json" \
    --output_dir "outputs/results/final_evaluation"

# Metrics:
# - Answer Accuracy
# - Premise Selection F1
# - Reasoning Quality Score
```

**Ngày 4-5: Error Analysis & Optimization**

```
1. Analyze failure cases
2. Identify patterns
3. Implement fixes:
   - Prompt refinement
   - Post-processing rules
   - Ensemble methods
```

**Ngày 6-7: Final Testing & Documentation**

```
- Final test run
- Generate report
- Create demo
- Write documentation
```

**Deliverables**:

- ✅ Final evaluation report
- ✅ Error analysis document
- ✅ Optimized model
- ✅ Complete documentation

---

## 📂 FILE STRUCTURE (Sau khi hoàn thành)

```
d:\EXACT 2026\Project\
│
├── 📄 FLOW_TYPE1_LOGIC.md          # Flow chi tiết
├── 📄 QUICK_START_GUIDE.md         # Guide này
├── 📄 setup_environment.md         # Hướng dẫn setup
│
├── 📁 EXACT2026_dataset_2026-05-15/  # Dataset gốc
│
├── 📁 src/                          # Source code
│   ├── data/
│   ├── models/
│   ├── prompts/
│   ├── evaluation/
│   └── utils/
│
├── 📁 scripts/                      # Executable scripts
│   ├── train.py
│   ├── inference.py
│   └── evaluate.py
│
├── 📁 notebooks/                    # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_baseline_testing.ipynb
│   └── 03_model_training.ipynb
│
├── 📁 outputs/                      # Outputs
│   ├── exploration/                 # Data exploration
│   ├── processed_data/              # Preprocessed data
│   ├── checkpoints/                 # Model checkpoints
│   ├── logs/                        # Training logs
│   └── results/                     # Evaluation results
│
└── 📁 configs/                      # Configurations
    ├── model_config.yaml
    └── training_config.yaml
```

---

## 🎓 KEY CONCEPTS

### 1. Premises (Tiền đề)

- Là các mệnh đề logic cho trước
- Mỗi bài có 10-30 premises
- Được đánh số P1, P2, ..., Pn

### 2. Questions

- **MCQ**: Multiple choice (A/B/C/D)
- **Yes/No/Unknown**: Câu hỏi đúng/sai/không xác định

### 3. idx (Premise Indices)

- Chỉ số các premises **TỐI THIỂU** cần để trả lời
- Ví dụ: `[1, 7, 10]` → cần P1, P7, P10
- Model phải học cách chọn premises đúng

### 4. Reasoning

- Giải thích từng bước logic
- Phải tự nhiên như lời nói
- Phải sâu sắc, phân tích kỹ

---

## 🔧 TOOLS & LIBRARIES

### Core

- `transformers` - Hugging Face models
- `peft` - LoRA fine-tuning
- `torch` - PyTorch
- `datasets` - Data handling

### Utilities

- `pandas`, `numpy` - Data processing
- `matplotlib`, `seaborn` - Visualization
- `wandb` - Experiment tracking
- `jupyter` - Notebooks

---

## 📊 EVALUATION METRICS

### 1. Answer Accuracy

```
Accuracy = Correct Answers / Total Questions
Target: > 85%
```

### 2. Premise Selection F1

```
Precision = |Predicted ∩ Ground Truth| / |Predicted|
Recall = |Predicted ∩ Ground Truth| / |Ground Truth|
F1 = 2 * (Precision * Recall) / (Precision + Recall)
Target: > 0.80
```

### 3. Reasoning Quality (1-5 scale)

```
- Clarity: Rõ ràng?
- Naturalness: Tự nhiên?
- Depth: Sâu sắc?
- Consistency: Nhất quán?
Target: > 4.0
```

### 4. Combined Score

```
Final = 0.4 * Accuracy + 0.2 * F1 + 0.4 * Quality
Target: > 0.85
```

---

## 💡 TIPS & BEST PRACTICES

### Data

- ✅ Shuffle premises để model không học vị trí
- ✅ Augment bằng cách paraphrase
- ✅ Balance MCQ vs Yes/No questions

### Training

- ✅ Start với learning rate nhỏ (2e-4)
- ✅ Use gradient accumulation nếu GPU nhỏ
- ✅ Monitor validation loss để tránh overfit
- ✅ Save checkpoints thường xuyên

### Inference

- ✅ Use temperature = 0.7 cho reasoning
- ✅ Implement retry logic cho malformed outputs
- ✅ Cache results để tăng tốc
- ✅ Batch processing khi có thể

### Debugging

- ✅ Log tất cả intermediate outputs
- ✅ Visualize attention weights
- ✅ Manual review 100 samples
- ✅ Track failure patterns

---

## 🆘 TROUBLESHOOTING

### Issue: CUDA Out of Memory

```python
# Solution 1: Reduce batch size
batch_size = 2  # instead of 4

# Solution 2: Use gradient accumulation
gradient_accumulation_steps = 8

# Solution 3: Use 4-bit quantization
load_in_4bit = True
```

### Issue: Poor Premise Selection

```python
# Solution 1: Multi-stage pipeline
# Stage 1: Select premises
# Stage 2: Generate reasoning

# Solution 2: Add explicit training
# Train specifically on premise selection task
```

### Issue: Unnatural Reasoning

```python
# Solution 1: Fine-tune on high-quality examples
# Filter training data for natural explanations

# Solution 2: Use better prompts
# Add examples of natural reasoning in prompt
```

---

## 📞 NEXT STEPS

1. **Ngay bây giờ**:

   ```bash
   # Run data exploration
   python 01_explore_data.py
   ```

2. **Sau khi explore**:

   ```bash
   # Run preprocessing
   python 02_preprocess_data.py
   ```

3. **Sau khi preprocess**:
   - Review samples trong `outputs/processed_data/*_samples.txt`
   - Verify data quality
   - Proceed to model training

---

## 📚 RESOURCES

### Documentation

- [Hugging Face Transformers](https://huggingface.co/docs/transformers)
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [Qwen2.5 Model Card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)

### Papers

- Chain-of-Thought Prompting (Wei et al., 2022)
- LoRA (Hu et al., 2021)
- Self-Consistency (Wang et al., 2022)

### Community

- Hugging Face Forums
- GitHub Issues
- Discord/Slack channels

---

**Last Updated**: 2026-05-18
**Version**: 1.0
**Status**: Ready to Start! 🚀

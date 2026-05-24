# EXACT 2026 - Logic-Based Educational Queries

## 🎯 Tổng Quan Dự Án

Dự án này tham gia cuộc thi **EXACT 2026**, tập trung vào **Type 1: Logic-Based Educational Queries** - xây dựng hệ thống AI reasoning cho bài toán logic.

### Mục Tiêu

1. ✅ **Accuracy**: Trả lời đúng câu hỏi logic
2. ✅ **Natural Reasoning**: Giải thích tự nhiên như lời nói
3. ✅ **Deep Analysis**: Phân tích sâu với premises tối thiểu

### Ràng Buộc

- 🔒 Model open-source < 8B parameters
- 🔒 Không dùng closed-source API (GPT, Claude, Gemini)
- ✅ Compute resources không giới hạn

---

## 📊 Dataset

### Type 1: Logic-Based Educational Queries

```
Records:   411
Questions: 808
Format:    JSON

Structure:
- premises-FOL: Logic dạng First-Order Logic
- premises-NL:  Logic dạng Natural Language
- questions:    Câu hỏi (MCQ hoặc Yes/No/Unknown)
- answers:      Đáp án
- explanations: Giải thích
- idx:          Chỉ số premises tối thiểu cần dùng
```

### Question Types

- **MCQ**: 40% (A/B/C/D)
- **Yes/No/Unknown**: 60%

### Key Challenge: Premise Selection

- Mỗi bài có 10-30 premises
- Model phải chọn **premises tối thiểu** để trả lời
- Ví dụ: Có 20 premises, chỉ cần P1, P7, P10 để trả lời

---

## 📁 Cấu Trúc Dự Án

```
d:\EXACT 2026\Project\
│
├── 📄 README.md                      ← Bạn đang đọc file này
├── 📄 QUICK_START_GUIDE.md           ← Hướng dẫn bắt đầu nhanh
├── 📄 FLOW_TYPE1_LOGIC.md            ← Flow chi tiết đầy đủ
├── 📄 setup_environment.md           ← Hướng dẫn setup môi trường
│
├── 📄 01_explore_data.py             ← Script explore dataset
├── 📄 02_preprocess_data.py          ← Script preprocess data
│
├── 📁 EXACT2026_dataset_2026-05-15/  ← Dataset gốc
│   ├── Logic_Based_Educational_Queries_Text_Only/
│   │   └── Logic_Based_Educational_Queries.json
│   ├── Physics_Problems_Text_Only/
│   ├── CHANGELOG_TYPE1.md
│   ├── CHANGELOG_TYPE2.md
│   └── README.txt
│
├── 📁 outputs/                       ← Outputs (sẽ tạo khi chạy)
│   ├── exploration/                  ← Data exploration results
│   ├── processed_data/               ← Preprocessed train/val/test
│   ├── checkpoints/                  ← Model checkpoints
│   ├── logs/                         ← Training logs
│   └── results/                      ← Evaluation results
│
├── 📁 src/                           ← Source code (sẽ tạo)
│   ├── data/
│   ├── models/
│   ├── prompts/
│   ├── evaluation/
│   └── utils/
│
├── 📁 scripts/                       ← Executable scripts (sẽ tạo)
│   ├── train.py
│   ├── inference.py
│   └── evaluate.py
│
├── 📁 notebooks/                     ← Jupyter notebooks (sẽ tạo)
│   ├── 01_data_exploration.ipynb
│   ├── 02_baseline_testing.ipynb
│   └── 03_model_training.ipynb
│
└── 📁 configs/                       ← Configurations (sẽ tạo)
    ├── model_config.yaml
    └── training_config.yaml
```

---

## 🚀 Bắt Đầu Nhanh

### Bước 1: Setup Environment

```bash
# Tạo virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install torch transformers peft accelerate bitsandbytes
pip install datasets pandas numpy scikit-learn matplotlib seaborn
pip install jupyter wandb tensorboard
```

### Bước 2: Explore Data

```bash
# Chạy script exploration
python 01_explore_data.py

# Xem kết quả trong outputs/exploration/
# - premises_distribution.png
# - answer_distribution.png
# - summary_statistics.csv
```

### Bước 3: Preprocess Data

```bash
# Chạy script preprocessing
python 02_preprocess_data.py

# Xem kết quả trong outputs/processed_data/
# - train.json (70%)
# - val.json (15%)
# - test.json (15%)
# - *_samples.txt (samples để review)
```

### Bước 4: Review & Next Steps

```bash
# Review samples
cat outputs/processed_data/train_samples.txt

# Đọc QUICK_START_GUIDE.md để tiếp tục
```

---

## 🤖 Model Strategy

### Recommended Model: Qwen2.5-7B-Instruct

**Lý do chọn:**

- ✅ 7B parameters (< 8B requirement)
- ✅ 128K context length (xử lý nhiều premises)
- ✅ Reasoning capability xuất sắc
- ✅ Multilingual support tốt
- ✅ Open-source với license thân thiện

### Alternative Models

1. **Llama-3.1-8B-Instruct** (8B, 128K context)
2. **Mistral-7B-Instruct-v0.3** (7B, 32K context)
3. **Phi-3-Medium-4K-Instruct** (3.8B, 4K context)

### Training Approach: LoRA Fine-tuning

```python
# LoRA Configuration
lora_config = {
    "r": 16,
    "lora_alpha": 32,
    "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
    "lora_dropout": 0.05,
}

# Training Configuration
training_args = {
    "num_epochs": 3-5,
    "batch_size": 4-8,
    "learning_rate": 2e-4,
    "gradient_accumulation_steps": 4,
}
```

---

## 🔄 Reasoning Pipeline

```
┌─────────────────────────────────────────┐
│  INPUT: Premises + Question             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  STAGE 1: Premise Selection             │
│  → Identify relevant premises           │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  STAGE 2: Reasoning Generation          │
│  → Step-by-step explanation             │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  STAGE 3: Answer Extraction             │
│  → Final answer (A/B/C/D or Yes/No)     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  OUTPUT: Answer + Reasoning + Premises  │
└─────────────────────────────────────────┘
```

---

## 📈 Evaluation Metrics

### 1. Answer Accuracy

```
Target: > 85%
Formula: Correct / Total
```

### 2. Premise Selection F1

```
Target: > 0.80
Precision = |Predicted ∩ Truth| / |Predicted|
Recall = |Predicted ∩ Truth| / |Truth|
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

### 3. Reasoning Quality (1-5)

```
Target: > 4.0
Criteria:
- Clarity (rõ ràng)
- Naturalness (tự nhiên)
- Depth (sâu sắc)
- Consistency (nhất quán)
```

### 4. Combined Score

```
Target: > 0.85
Final = 0.4 * Accuracy + 0.2 * F1 + 0.4 * Quality
```

---

## 📅 Timeline (4 Tuần)

### Tuần 1: Setup & Data Preparation

- [x] Setup environment
- [x] Data exploration
- [x] Data preprocessing
- [ ] Prompt engineering

### Tuần 2: Model Training

- [ ] Model selection & benchmark
- [ ] LoRA fine-tuning
- [ ] Checkpoint evaluation
- [ ] Best model selection

### Tuần 3: Pipeline Development

- [ ] Implement reasoning pipeline
- [ ] Testing & debugging
- [ ] Integration & optimization
- [ ] Validation testing

### Tuần 4: Evaluation & Optimization

- [ ] Full evaluation on test set
- [ ] Error analysis
- [ ] Model optimization
- [ ] Final testing & documentation

---

## 📚 Documentation

### Core Documents

1. **QUICK_START_GUIDE.md** - Hướng dẫn bắt đầu nhanh
2. **FLOW_TYPE1_LOGIC.md** - Flow chi tiết đầy đủ
3. **setup_environment.md** - Setup môi trường

### Scripts

1. **01_explore_data.py** - Explore dataset
2. **02_preprocess_data.py** - Preprocess data

### Future Documents (sẽ tạo)

- Training guide
- Inference guide
- Evaluation guide
- API documentation

---

## 🛠️ Tech Stack

### Core

- **PyTorch** - Deep learning framework
- **Transformers** - Hugging Face models
- **PEFT** - Parameter-efficient fine-tuning
- **Datasets** - Data handling

### Utilities

- **pandas, numpy** - Data processing
- **matplotlib, seaborn** - Visualization
- **wandb** - Experiment tracking
- **jupyter** - Interactive development

---

## 💡 Key Insights

### Challenge 1: Long Context

**Problem**: Mỗi bài có 10-30 premises
**Solution**: Dùng model với long context (128K tokens)

### Challenge 2: Premise Selection

**Problem**: Phải chọn premises tối thiểu
**Solution**: Multi-stage pipeline + explicit training

### Challenge 3: Natural Reasoning

**Problem**: Reasoning phải tự nhiên như lời nói
**Solution**: Fine-tune trên high-quality examples

### Challenge 4: Small Model

**Problem**: Model < 8B params
**Solution**: LoRA + quantization + optimization

---

## 🎓 Learning Resources

### Papers

- [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)
- [LoRA: Low-Rank Adaptation](https://arxiv.org/abs/2106.09685)
- [Self-Consistency](https://arxiv.org/abs/2203.11171)

### Tutorials

- [Hugging Face Fine-tuning Guide](https://huggingface.co/docs/transformers/training)
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)

---

## 📞 Contact & Support

### Issues

- GitHub Issues (nếu có repo)
- Email: [your-email]

### Discussion

- Discord/Slack channel
- Hugging Face Forums

---

## 📝 Notes

### Current Status

- ✅ Dataset explored
- ✅ Flow designed
- ✅ Scripts prepared
- ⏳ Ready to start training

### Next Immediate Steps

1. Run `python 01_explore_data.py`
2. Run `python 02_preprocess_data.py`
3. Review samples
4. Read QUICK_START_GUIDE.md
5. Proceed to model training

---

## 🏆 Success Criteria

### Minimum Viable Product (MVP)

- ✅ Accuracy > 70%
- ✅ Reasoning quality > 3.5
- ✅ Premise F1 > 0.70

### Target Performance

- 🎯 Accuracy > 85%
- 🎯 Reasoning quality > 4.0
- 🎯 Premise F1 > 0.80
- 🎯 Combined score > 0.85

### Stretch Goals

- 🚀 Accuracy > 90%
- 🚀 Reasoning quality > 4.5
- 🚀 Premise F1 > 0.90
- 🚀 Combined score > 0.90

---

**Project Start Date**: 2026-05-18
**Competition**: EXACT 2026
**Type**: Logic-Based Educational Queries (Type 1)
**Status**: 🚀 Ready to Launch!

---

## 🙏 Acknowledgments

- EXACT 2026 Competition Organizers
- Hugging Face Team
- Open-source AI Community

---

**Last Updated**: 2026-05-18
**Version**: 1.0

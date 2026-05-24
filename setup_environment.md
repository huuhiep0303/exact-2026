# HƯỚNG DẪN SETUP ENVIRONMENT

## 🖥️ YÊU CẦU HỆ THỐNG

### Hardware

- **GPU**: NVIDIA GPU với ít nhất 24GB VRAM (RTX 4090, A5000, A100)
  - Cho LoRA fine-tuning: 24GB
  - Cho full fine-tuning: 40GB+
- **RAM**: 32GB+ khuyến nghị
- **Storage**: 100GB+ free space

### Software

- **OS**: Linux (Ubuntu 20.04+) hoặc Windows với WSL2
- **Python**: 3.9 - 3.11
- **CUDA**: 11.8 hoặc 12.1
- **Git**: Latest version

---

## 📦 INSTALLATION STEPS

### Step 1: Clone Repository & Setup Project

```bash
# Tạo thư mục project
cd "d:\EXACT 2026\Project"

# Tạo virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### Step 2: Install Core Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install PyTorch (CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install Transformers & PEFT
pip install transformers>=4.36.0
pip install peft>=0.7.0
pip install accelerate>=0.25.0
pip install bitsandbytes>=0.41.0

# Install datasets & utilities
pip install datasets>=2.15.0
pip install pandas numpy scikit-learn
pip install tqdm wandb tensorboard

# Install evaluation tools
pip install rouge-score nltk
pip install sentencepiece protobuf

# Install Jupyter (optional)
pip install jupyter ipywidgets
```

### Step 3: Verify Installation

```python
# test_installation.py
import torch
import transformers
import peft
import bitsandbytes

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'}")
print(f"Transformers version: {transformers.__version__}")
print(f"PEFT version: {peft.__version__}")
print(f"Bitsandbytes version: {bitsandbytes.__version__}")
```

Run: `python test_installation.py`

---

## 📁 PROJECT STRUCTURE

```
d:\EXACT 2026\Project\
│
├── EXACT2026_dataset_2026-05-15/     # Dataset gốc
│   ├── Logic_Based_Educational_Queries_Text_Only/
│   └── Physics_Problems_Text_Only/
│
├── src/                               # Source code
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py                 # Load dataset
│   │   ├── preprocessor.py           # Preprocess data
│   │   └── augmentation.py           # Data augmentation
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── model_loader.py           # Load base models
│   │   ├── trainer.py                # Training logic
│   │   └── inference.py              # Inference pipeline
│   │
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── templates.py              # Prompt templates
│   │   └── formatter.py              # Format prompts
│   │
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── metrics.py                # Evaluation metrics
│   │   └── evaluator.py              # Evaluation pipeline
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config.py                 # Configuration
│       └── helpers.py                # Helper functions
│
├── notebooks/                         # Jupyter notebooks
│   ├── 01_data_exploration.ipynb
│   ├── 02_baseline_testing.ipynb
│   ├── 03_model_training.ipynb
│   └── 04_evaluation.ipynb
│
├── configs/                           # Configuration files
│   ├── model_config.yaml
│   ├── training_config.yaml
│   └── inference_config.yaml
│
├── scripts/                           # Executable scripts
│   ├── train.py
│   ├── inference.py
│   └── evaluate.py
│
├── outputs/                           # Training outputs
│   ├── checkpoints/
│   ├── logs/
│   └── results/
│
├── requirements.txt                   # Dependencies
├── README.md                          # Project README
└── FLOW_TYPE1_LOGIC.md               # Flow document
```

---

## 🚀 QUICK START

### 1. Create Project Structure

```bash
# Windows
mkdir src\data src\models src\prompts src\evaluation src\utils
mkdir notebooks configs scripts outputs\checkpoints outputs\logs outputs\results

# Linux/Mac
mkdir -p src/{data,models,prompts,evaluation,utils}
mkdir -p notebooks configs scripts outputs/{checkpoints,logs,results}
```

### 2. Create requirements.txt

```bash
# Save current environment
pip freeze > requirements.txt
```

### 3. Download Model (Example: Qwen2.5-7B)

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_name = "Qwen/Qwen2.5-7B-Instruct"

# Download tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.save_pretrained("./models/qwen2.5-7b-instruct")

# Download model (will take time)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto"
)
model.save_pretrained("./models/qwen2.5-7b-instruct")
```

---

## 🔍 TROUBLESHOOTING

### Issue: CUDA Out of Memory

**Solution:**

```python
# Use 4-bit quantization
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto"
)
```

### Issue: Slow Training

**Solution:**

- Reduce batch size
- Use gradient accumulation
- Enable mixed precision training (fp16)
- Use gradient checkpointing

### Issue: Import Errors

**Solution:**

```bash
# Reinstall with specific versions
pip install transformers==4.36.0 --force-reinstall
pip install peft==0.7.0 --force-reinstall
```

---

## 📊 MONITORING & LOGGING

### Setup Weights & Biases (Optional)

```bash
pip install wandb
wandb login
```

### Setup TensorBoard

```bash
# Start TensorBoard
tensorboard --logdir=outputs/logs
```

---

## 🔗 USEFUL LINKS

- [Hugging Face Transformers](https://huggingface.co/docs/transformers)
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [Qwen2.5 Model Card](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)

---

**Last Updated**: 2026-05-18

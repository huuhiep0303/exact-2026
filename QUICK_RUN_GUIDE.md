# 🚀 Hướng Dẫn Chạy Nhanh - EXACT 2026 Type 1

## ✅ Tổng Quan Hoàn Thành

Toàn bộ hệ thống đã được implement hoàn chỉnh với:

### 📁 Cấu Trúc Code

```
✅ src/data/          - Data processing modules
✅ src/models/        - Model loading & inference
✅ src/training/      - Training logic
✅ src/evaluation/    - Evaluation metrics
✅ src/utils/         - Utilities (config, logger, helpers)
✅ configs/           - Configuration files
✅ requirements.txt   - All dependencies
```

### 📝 Scripts Chính

```
✅ 01_explore_data.py      - Khám phá dữ liệu
✅ 02_preprocess_data.py   - Tiền xử lý dữ liệu
✅ 03_train.py             - Training model
✅ 04_evaluate.py          - Đánh giá model
✅ 05_inference.py         - Chạy inference
```

### 📚 Documentation

```
✅ FINAL_REPORT.md         - Báo cáo chi tiết đầy đủ
✅ QUICK_RUN_GUIDE.md      - File này (hướng dẫn nhanh)
```

---

## 🎯 Chạy Từng Bước (4 Bước Đơn Giản)

### Bước 0: Setup (Chỉ làm 1 lần)

```bash
# Tạo và activate virtual environment
python -m venv venv
venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### Bước 1: Khám Phá Dữ Liệu (Tùy chọn)

```bash
python 01_explore_data.py
```

**Output**: Thống kê về dataset (số lượng, phân bố, samples)

### Bước 2: Tiền Xử Lý Dữ Liệu

```bash
python 02_preprocess_data.py
```

**Output**:

- `outputs/processed_data/train.json` (~288 samples)
- `outputs/processed_data/val.json` (~62 samples)
- `outputs/processed_data/test.json` (~61 samples)

**Thời gian**: ~5 phút

### Bước 3: Training Model

```bash
python 03_train.py
```

**Output**:

- Checkpoints: `outputs/checkpoints/checkpoint-{step}/`
- Final model: `outputs/checkpoints/final_model/`
- Logs: `outputs/logs/`

**Thời gian**:

- GPU RTX 3090: ~2-3 giờ
- GPU RTX 4090: ~1-2 giờ
- GPU A100: ~1 giờ

**Yêu cầu**: GPU với ít nhất 8GB VRAM

### Bước 4: Đánh Giá Model

```bash
python 04_evaluate.py
```

**Output**:

- `outputs/results/evaluation_results.json` - Metrics
- `outputs/results/evaluation_results_predictions.json` - Predictions

**Metrics**:

- Accuracy (40% weight)
- Premise F1 (20% weight)
- Reasoning Quality (40% weight)
- Combined Score

**Thời gian**: ~10-15 phút

---

## 🔧 Inference (Sử Dụng Model)

### Interactive Mode (Thử nghiệm)

```bash
python 05_inference.py --interactive
```

Nhập premises và question để xem kết quả ngay lập tức.

### Batch Mode (Xử lý nhiều samples)

```bash
python 05_inference.py --input_file input.json --output_file output.json
```

**Format input.json**:

```json
[
  {
    "id": "1",
    "premises": ["Premise 1", "Premise 2", ...],
    "question": "Your question?"
  }
]
```

---

## 📊 Kết Quả Dự Kiến

| Metric             | Expected Score |
| ------------------ | -------------- |
| Accuracy           | 75-85%         |
| Premise F1         | 70-80%         |
| Reasoning Quality  | 3.5-4.5/5      |
| **Combined Score** | **72-86%**     |

---

## ⚙️ Tùy Chỉnh (Nếu Cần)

Chỉnh sửa `configs/config.yaml`:

### Giảm Memory Usage

```yaml
training:
  per_device_train_batch_size: 2 # Giảm từ 4
  gradient_accumulation_steps: 8 # Tăng từ 4
```

### Tăng Performance

```yaml
training:
  num_train_epochs: 5 # Tăng từ 3
  learning_rate: 3.0e-4 # Tăng từ 2.0e-4
```

### Thay Đổi Model

```yaml
model:
  name: "Qwen/Qwen2.5-7B-Instruct" # Hoặc model khác <8B
```

---

## 🐛 Xử Lý Lỗi Thường Gặp

### 1. CUDA Out of Memory

```bash
# Giảm batch size trong config.yaml
training:
  per_device_train_batch_size: 2
  gradient_accumulation_steps: 8
```

### 2. Model Download Lỗi

```bash
# Kiểm tra internet
# Hoặc download manual từ HuggingFace
```

### 3. File Not Found

```bash
# Đảm bảo chạy đúng thứ tự:
# 02_preprocess_data.py → 03_train.py → 04_evaluate.py
```

---

## 📖 Đọc Thêm

Xem **FINAL_REPORT.md** để hiểu chi tiết:

- Tại sao chọn Qwen2.5-7B-Instruct
- Tại sao dùng LoRA
- Kiến trúc pipeline
- Cách cải thiện performance
- Troubleshooting chi tiết

---

## 📋 Checklist Thực Hiện

- [ ] Setup environment (Bước 0)
- [ ] Explore data (Bước 1 - optional)
- [ ] Preprocess data (Bước 2)
- [ ] Train model (Bước 3)
- [ ] Evaluate model (Bước 4)
- [ ] Test inference (Bước 5)
- [ ] Đọc FINAL_REPORT.md để hiểu sâu hơn

---

## 💡 Tips

1. **Chạy explore trước**: Hiểu data trước khi train
2. **Monitor training**: Xem logs trong `outputs/logs/`
3. **Save checkpoints**: Mặc định save mỗi 100 steps
4. **Test inference**: Thử interactive mode trước khi batch
5. **Đọc report**: FINAL_REPORT.md có tất cả chi tiết

---

## 🎓 Kiến Trúc Tóm Tắt

```
Model: Qwen2.5-7B-Instruct (7B params)
  ↓
Quantization: 4-bit NF4 (~4GB VRAM)
  ↓
Fine-tuning: LoRA (r=16, alpha=32)
  ↓
Pipeline: Premise Selection → Reasoning → Answer
  ↓
Evaluation: 40% Accuracy + 20% Premise F1 + 40% Reasoning
```

---

## ✅ Tất Cả Đã Sẵn Sàng!

Bạn có thể bắt đầu ngay với:

```bash
# Activate environment
venv\Scripts\activate

# Bắt đầu từ bước 1
python 01_explore_data.py
```

**Chúc bạn thành công! 🚀**

---

## 📞 Cần Trợ Giúp?

1. Xem phần Troubleshooting trong FINAL_REPORT.md
2. Kiểm tra logs: `outputs/logs/`
3. Kiểm tra config: `configs/config.yaml`

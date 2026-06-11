# Hướng Dẫn Cài Đặt và Vận Hành Hệ Thống Physics AI Solver

Dự án này là hệ thống giải bài tập Vật lý tự động sử dụng RAG Hybrid (Qdrant + Dense/Sparse Retrieval) kết hợp với mô hình ngôn ngữ lớn (LLM) chạy local qua Ollama và môi trường chạy Code Sandbox an toàn.

Tài liệu này hướng dẫn chi tiết các bước để thiết lập toàn bộ môi trường từ đầu trên hệ điều hành Windows (hoặc Linux/macOS).

---

## 📋 Yêu Cầu Hệ Thống Cần Chuẩn Bị
1. **Python**: Phiên bản `3.10` - `3.12`.
2. **Docker Desktop**: Dùng để chạy cơ sở dữ liệu vector Qdrant.
3. **Ollama**: Dùng để tải và chạy mô hình ngôn ngữ lớn local.
4. **GPU (Khuyên dùng)**: Có tối thiểu **12GB VRAM** (ví dụ: RTX 3060 trở lên) để chạy mô hình local mượt mà. Nếu không có GPU, mô hình sẽ chạy trên CPU nhưng tốc độ phản hồi sẽ rất chậm.

---

## 🛠️ Các Bước Cài Đặt Chi Tiết
wsl --install
### Bước 1: Cài đặt và cấu hình Ollama (LLM Local)
1. Truy cập trang chủ [Ollama.com](https://ollama.com/) để tải về và cài đặt Ollama tương ứng với hệ điều hành của bạn.
2. Sau khi cài đặt xong, mở Terminal (PowerShell hoặc CMD) và kéo mô hình `qwen2.5:7b` (hoặc mô hình bạn cấu hình trong dự án) về máy bằng lệnh:
   ```bash
   ollama pull qwen2.5:7b
   ```
3. Kiểm tra danh sách mô hình đã tải thành công:
   ```bash
   ollama list
   ```
   *Bạn sẽ thấy `qwen2.5:7b` hiển thị trong danh sách.*
4. Đảm bảo Ollama đang chạy ở chế độ nền (kiểm tra biểu tượng Ollama ở khay hệ thống hoặc truy cập địa chỉ `http://localhost:11434` trên trình duyệt thấy báo `Ollama is running`).

---

### Bước 2: Cài đặt Docker và Chạy Qdrant Vector Database
Qdrant được dùng làm cơ sở dữ liệu vector lưu trữ các định luật và công thức vật lý phục vụ cho bước RAG (Retrieval-Augmented Generation).

1. Tải và cài đặt [Docker Desktop](https://www.docker.com/products/docker-desktop/) cho Windows/macOS. Nếu dùng Linux, hãy cài đặt Docker engine.
2. Mở Terminal và chạy lệnh sau để kéo và khởi chạy Qdrant container có lưu trữ dữ liệu bền vững (persistence):
   * **Trên Windows PowerShell**:
     ```powershell
     docker run -d -p 6333:6333 -p 6334:6334 -v ${PWD}\qdrant_storage:/qdrant/storage qdrant/qdrant
     ```
   * **Trên Linux hoặc macOS (Bash)**:
     ```bash
     docker run -d -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
     ```
3. Kiểm tra xem container Qdrant có đang hoạt động hay không:
   ```bash
   docker ps
   ```
   *Mở trình duyệt truy cập `http://localhost:6333/dashboard` để vào giao diện quản trị trực quan của Qdrant.*

---

### Bước 3: Thiết Lập Môi Trường Ảo Python và Cài Đặt Thư Viện
1. Mở Terminal tại thư mục gốc của dự án (`AI_X_Challenge`).
2. Tạo môi trường ảo Python tên là `.venv`:
   ```bash
   python -m venv .venv
   ```
3. Kích hoạt môi trường ảo vừa tạo:
   * **Trên Windows PowerShell**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   * **Trên Windows CMD**:
     ```cmd
     .\.venv\Scripts\activate.bat
     ```
   * **Trên Linux hoặc macOS (Bash)**:
     ```bash
     source .venv/bin/activate
     ```
   *(Sau khi kích hoạt thành công, bạn sẽ thấy tiền tố `(.venv)` xuất hiện ở đầu dòng lệnh).*
4. Nâng cấp `pip` và cài đặt toàn bộ các thư viện cần thiết trong file `requirements.txt`:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

### Bước 4: Cấu Hình File Môi Trường (`.env`)
1. Tạo một file tên là `.env` ở thư mục gốc của dự án (cùng cấp với file `requirements.txt`).
2. Sao chép và dán nội dung cấu hình sau vào file `.env`:
   ```ini
   USE_QDRANT=true
   QDRANT_HOST=localhost
   # Nếu bạn có sử dụng Hugging Face Token để tải các model tự động, điền vào đây:
   # HF_TOKEN=your_token_here
   ```

---

### Bước 5: Chuẩn Bị Phase 5 LoRA Fine-Tuning
Phase 5 dùng LoRA/QLoRA để fine-tune reasoner. Mặc định project dùng `Qwen/Qwen2.5-7B-Instruct` làm base model và train chính trên Modal GPU `A10`. RTX 3050/4050 local chỉ nên dùng để smoke test.

#### 5.1. Modal-first: không cần train local
Nếu muốn tiết kiệm thời gian, bạn có thể bỏ toàn bộ bước local smoke test. Trên máy cá nhân chỉ cần cài Modal:
```powershell
pip install modal
modal setup
```

Sau đó chạy smoke test trực tiếp trên Modal:
```powershell
modal run finetuning/modal/train_lora_modal.py --max-steps 20
```

Nếu smoke test ổn, chạy full train trên Modal A10:
```powershell
modal run finetuning/modal/train_lora_modal.py
```

Script Modal sẽ tự chạy data prep trên remote nếu cần, nên bạn không bắt buộc phải cài `torch`, `unsloth`, `bitsandbytes`, hay chạy train local.

#### 5.2. Tạo dataset SFT chia stratified theo topic (tuỳ chọn local)
```powershell
python finetuning/scripts/prepare_sft_dataset.py
```

Kết quả được ghi vào:
```text
finetuning/data/processed/train.jsonl
finetuning/data/processed/val.jsonl
finetuning/data/processed/test.jsonl
finetuning/data/processed/manifest.json
```

Mỗi topic (`LD`, `CH`, `NL`, `TD`, `DDT`, `THCB`, `DT`, `CHLT`) được shuffle riêng bằng seed `42`, rồi chia `80/10/10`. Không chia theo thứ tự từ trên xuống dưới trong CSV. Bước này chỉ cần chạy local nếu bạn muốn kiểm tra manifest trước khi train.

#### 5.3. Local smoke test (tuỳ chọn)
Cài dependency fine-tuning trong môi trường riêng nếu muốn thử local:
```powershell
pip install torch transformers datasets accelerate peft bitsandbytes unsloth trl
```

Kiểm tra GPU:
```powershell
python finetuning/scripts/inspect_gpu.py
```

Chạy smoke train 20 steps:
```powershell
python finetuning/scripts/train_lora_unsloth.py --config finetuning/configs/qwen2_5_7b_local_smoke.yaml
```

#### 5.4. Modal training
Cài và đăng nhập Modal:
```powershell
pip install modal
modal setup
```

Nếu file `.env` local có `HF_TOKEN=...`, script Modal sẽ tự truyền token đó lên remote dưới dạng Modal Secret tạm. Với model public như `Qwen/Qwen2.5-7B-Instruct`, thường không cần `HF_TOKEN`.

Smoke test trên Modal:
```powershell
modal run finetuning/modal/train_lora_modal.py --max-steps 20
```

Full train trên Modal A10:
```powershell
modal run finetuning/modal/train_lora_modal.py
```

Sau khi train xong, tải kết quả từ Modal Volume:
```powershell
modal volume get physics-lora-runs <run_id> .\finetuning\runs\<run_id>
```

#### 5.5. Export sang Ollama
Train xong chỉ có LoRA adapter. Để chạy bằng Ollama cần merge và export:
```text
LoRA adapter -> merged Qwen2.5-7B -> GGUF -> ollama create physics-qwen-lora
```

Bước merge nên chạy trên Modal để tránh tải/merge model 7B trên máy local:
```powershell
modal run finetuning/modal/merge_lora_modal.py --run-id qwen2_5_7b_lora_20260605_185537
```

Nếu A10 thiếu bộ nhớ khi merge:
```powershell
modal run finetuning/modal/merge_lora_modal.py --run-id qwen2_5_7b_lora_20260605_185537 --gpu L40S
```

Xem chi tiết tại:
```text
finetuning/scripts/export_ollama_gguf.md
```

Sau khi tạo Ollama model, thêm vào `.env`:
```ini
REASONER_MODEL=physics-qwen-lora
```

---

## 🏃 Hướng Dẫn Vận Hành & Chạy Thử Nghiệm

### 1. Chạy Thử Nghiệm Pipeline Đơn Giản
Chương trình cung cấp một script `test_pipeline.py` để chạy thử nghiệm nhanh luồng hoạt động của hệ thống với một vài câu hỏi mẫu:
```bash
python test_pipeline.py
```
*Script này sẽ chạy giải thử 3 câu hỏi với chế độ giả lập (`mock`) để kiểm tra xem cấu trúc API và code sandbox có hoạt động trơn tru hay không.*

---

### 2. Chạy Đánh Giá Độ Chính Xác (Evaluator)
Các lệnh test trên 20 câu đầu của các topic

python evaluate_pipeline.py --id-prefix LD --start 0 --limit 20 --mode local --output eval_results/LD/qdrant_upgrade_20_v3.jsonl --report eval_results/LD/qdrant_upgrade_20_v3.md --report-misses-only

python evaluate_pipeline.py --id-prefix DT --start 0 --limit 20 --mode local --output eval_results/DT/qdrant_upgrade_20.jsonl --report eval_results/DT/qdrant_upgrade_20.md --report-misses-only

python evaluate_pipeline.py --id-prefix TD --start 0 --limit 20 --mode local --output eval_results/TD/qdrant_upgrade_20.jsonl --report eval_results/TD/qdrant_upgrade_20.md --report-misses-only

python evaluate_pipeline.py --id-prefix THCB --start 0 --limit 20 --mode local --output eval_results/THCB/qdrant_upgrade_20.jsonl --report eval_results/THCB/qdrant_upgrade_20.md --report-misses-only

python evaluate_pipeline.py --id-prefix CH --start 0 --limit 20 --mode local --output eval_results/CH/qdrant_upgrade_20.jsonl --report eval_results/CH/qdrant_upgrade_20.md --report-misses-only

python evaluate_pipeline.py --id-prefix CHLT --start 0 --limit 20 --mode local --output eval_results/CHLT/qdrant_upgrade_20.jsonl --report eval_results/CHLT/qdrant_upgrade_20.md --report-misses-only

python evaluate_pipeline.py --id-prefix DDT --start 0 --limit 20 --mode local --output eval_results/DDT/qdrant_upgrade_20.jsonl --report eval_results/DDT/qdrant_upgrade_20.md --report-misses-only

python evaluate_pipeline.py --id-prefix NL --start 0 --limit 20 --mode local --output eval_results/NL/qdrant_upgrade_20.jsonl --report eval_results/NL/qdrant_upgrade_20.md --report-misses-only


Script `evaluate_pipeline.py` dùng để đo đạc độ chính xác của hệ thống trên tập dữ liệu benchmark `dataset_2/Physics_Problems_Text_Only.csv`.

**Lệnh chạy đánh giá local chi tiết (ví dụ trên 20 câu đầu thuộc chủ đề AC Resonance - CHLT):**
```bash
python evaluate_pipeline.py --id-prefix CHLT --start 0 --limit 20 --mode local --output eval_results/CHLT/qdrant_upgrade_20.jsonl --report eval_results/CHLT/qdrant_upgrade_20.md --report-misses-only
```

**Giải thích các tham số chính:**
* `--mode local`: Sử dụng mô hình chạy local qua Ollama (thay vì mock hoặc API đám mây).
* `--id-prefix CHLT`: Chỉ đánh giá các câu hỏi có mã ID bắt đầu bằng tiền tố `CHLT`. Các mã tiền tố khác gồm có: `LD`, `TD`, `DT`, `DDT`, `NL`, `CH`, `THCB`.
* `--start 0`: Bắt đầu chạy từ dòng số 0.
* `--limit 20`: Giới hạn số lượng câu hỏi chạy đánh giá là 20 câu.
* `--output <path>`: Đường dẫn lưu file kết quả chi tiết dạng `.jsonl`.
* `--report <path>`: Đường dẫn xuất file báo cáo markdown thân thiện với người dùng.
* `--report-misses-only`: Chỉ thống kê chi tiết các câu giải sai (`MISS`) vào mục báo cáo chi tiết để tiện debug.
* `--allow-fallback`: (Tùy chọn) Cho phép khi LLM local lỗi kết nối sẽ lấy kết quả mock. *Lưu ý: Không dùng cờ này khi đo độ chính xác thực tế của mô hình.*

---

### 3. Khởi Chạy API Server (FastAPI)
Khi bạn muốn triển khai hoặc tích hợp với các ứng dụng khác:

1. Chạy server phát triển (development) hỗ trợ tự động tải lại code khi lưu file:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
2. Server sẽ được kích hoạt tại địa chỉ mặc định: `http://127.0.0.1:8000`.
3. Bạn có thể test nhanh API giải bài tập bằng lệnh `curl` gửi request dạng JSON:
   ```bash
   curl -X POST "http://127.0.0.1:8000/solve" `
     -H "Content-Type: application/json" `
     -d "{\"question\":\"Calculate the energy stored in capacitor C when C = 100 μF and U = 30 V.\"}"
   ```
   *Kết quả phản hồi sẽ là JSON chứa đáp án (`answer`), giải thích (`explanation`), các bước suy luận CoT (`cot`), công thức áp dụng (`premises`) và độ tin cậy (`confidence`).*

---

## 🔍 Khắc Phục Lỗi Thường Gặp (Troubleshooting)

1. **Lỗi `Connection error` khi dự đoán (pred=trống):**
   * *Nguyên nhân:* Server Ollama chưa được bật hoặc chưa kéo mô hình `qwen2.5:7b`.
   * *Khắc phục:* Mở ứng dụng Ollama hoặc chạy lệnh `ollama run qwen2.5:7b` trên Terminal để chắc chắn mô hình đang hoạt động tốt.

2. **Lỗi `QdrantKB Connection failed`:**
   * *Nguyên nhân:* Container Docker chứa Qdrant chưa được chạy hoặc sai cổng kết nối.
   * *Khắc phục:* Chạy lệnh `docker ps` để kiểm tra. Nếu container chưa chạy, hãy khởi chạy lại bằng lệnh ở **Bước 2**.

3. **Lỗi `ModuleNotFoundError` khi chạy script:**
   * *Nguyên nhân:* Bạn chưa kích hoạt môi trường ảo `.venv` hoặc chưa cài đặt đủ dependencies.
   * *Khắc phục:* Chạy lại lệnh kích hoạt môi trường ảo tương ứng với hệ điều hành ở **Bước 3** và chạy lại `pip install -r requirements.txt`.

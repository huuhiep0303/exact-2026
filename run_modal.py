import os
import shutil
import subprocess
import modal

# Khởi tạo Modal App
app = modal.App("exact-2026-type1")

# Khởi tạo Volume để lưu trữ model checkpoints và logs lâu dài
volume = modal.Volume.from_name("exact-2026-volume", create_if_missing=True)

# Khởi tạo Image chứa các thư viện Deep Learning cần thiết
image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install(
        "torch>=2.1.0",
        "transformers>=4.36.0",
        "peft>=0.7.0",
        "accelerate>=0.25.0",
        "bitsandbytes>=0.41.0",
        "datasets>=2.15.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0",
        "pyyaml>=6.0",
        "tqdm>=4.66.0",
        "wandb>=0.16.0",
        "tensorboard>=2.15.0",
        "rouge-score>=0.1.2",
        "nltk>=3.8.1",
        "modal>=0.62.0"
    )
    .add_local_dir(
        ".",
        remote_path="/workspace",
        ignore=["venv", "EXACT2026_dataset_2026-05-15", "outputs/checkpoints", "outputs/logs", "outputs/results", "outputs/exploration", ".git"]
    )
)

def setup_symlinks():
    """
    Tạo symlink để chuyển hướng lưu trữ (checkpoints, logs, results)
    từ thư mục dự án cục bộ sang Modal Volume để lưu trữ bền vững.
    """
    os.makedirs("/modal_vol/checkpoints", exist_ok=True)
    os.makedirs("/modal_vol/logs", exist_ok=True)
    os.makedirs("/modal_vol/results", exist_ok=True)
    
    for folder in ["checkpoints", "logs", "results"]:
        target = f"outputs/{folder}"
        # Xóa thư mục trống nếu có để tạo symlink
        if os.path.exists(target) and not os.path.islink(target):
            shutil.rmtree(target, ignore_errors=True)
        
        # Tạo symlink
        if not os.path.exists(target):
            os.symlink(f"/modal_vol/{folder}", target)

@app.function(
    image=image,
    gpu="A100", # Sử dụng GPU A100 cho quá trình fine-tuning LoRA
    timeout=86400, # Giới hạn 24 giờ
    volumes={"/modal_vol": volume}
)
def train_model():
    """Khởi chạy quá trình huấn luyện trên Modal Cloud."""
    os.chdir("/workspace")
    setup_symlinks()
    
    print("🚀 Bắt đầu huấn luyện mô hình trên Modal Cloud (A100 GPU)...")
    subprocess.run(["python", "03_train.py"], check=True)

@app.function(
    image=image,
    gpu="A100",
    timeout=14400,
    volumes={"/modal_vol": volume}
)
def evaluate_model():
    """Khởi chạy quá trình đánh giá trên Modal Cloud."""
    os.chdir("/workspace")
    setup_symlinks()
    
    print("📊 Bắt đầu đánh giá mô hình trên Modal Cloud...")
    subprocess.run(["python", "04_evaluate.py"], check=True)

@app.function(
    image=image,
    gpu="A100",
    timeout=14400,
    volumes={"/modal_vol": volume}
)
def run_inference():
    """Khởi chạy quá trình suy luận trên Modal Cloud."""
    os.chdir("/workspace")
    setup_symlinks()
    
    print("🧠 Bắt đầu chạy suy luận trên Modal Cloud...")
    subprocess.run(["python", "05_inference.py"], check=True)

if __name__ == "__main__":
    print("Sử dụng CLI của Modal để chạy:")
    print("modal run run_modal.py::train_model")

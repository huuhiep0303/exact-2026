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

import os
import zipfile
import shutil
from pathlib import Path

def build_submission():
    base_dir = Path(__file__).resolve().parent.parent
    submission_dir = base_dir / "submission"
    dist_dir = submission_dir / "dist"
    
    # Clean previous build
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Create source_code.zip
    print("Building source_code.zip...")
    source_code_zip_path = dist_dir / "source_code.zip"
    with zipfile.ZipFile(source_code_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Include dataset-1, dataset-2, submission, and any config files
        for folder in ["dataset-1", "dataset-2", "submission"]:
            folder_path = base_dir / folder
            if folder_path.exists():
                for root, dirs, files in os.walk(folder_path):
                    # Ignore standard exclusions
                    if "__pycache__" in root or ".git" in root or "venv" in root or "node_modules" in root:
                        continue
                    # Ignore the dist directory itself
                    if str(dist_dir) in root:
                        continue
                        
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Add to zip with relative path
                        rel_path = os.path.relpath(file_path, base_dir)
                        zipf.write(file_path, rel_path)
    
    # 2. Create notation_mapping.csv (Template)
    print("Generating notation_mapping.csv...")
    notation_path = dist_dir / "notation_mapping.csv"
    with open(notation_path, 'w', encoding='utf-8') as f:
        f.write("canonical_latex,meaning,your_notation\n")
        f.write("\\frac{a}{b},phân số,\n")
        f.write("\\times,nhân,\n")
        # Empty cells mean use canonical
        
    # 3. Create urls.txt (Template)
    print("Generating urls.txt...")
    urls_path = dist_dir / "urls.txt"
    with open(urls_path, 'w', encoding='utf-8') as f:
        f.write("Prediction Endpoint: https://<your-vllm-fastapi-app-url.modal.run>/predict\n")
        f.write("vLLM Model Endpoint: https://<your-vllm-engine-url.modal.run>/v1/models\n")
        
    # 4. Create solution.md (Template for PDF conversion)
    print("Generating solution.md (please convert to PDF as solution.pdf)...")
    solution_path = dist_dir / "solution.md"
    with open(solution_path, 'w', encoding='utf-8') as f:
        f.write("# Giải pháp EXACT 2026\n\n")
        f.write("## 1. Datasets đã dùng\n")
        f.write("- EXACT 2026 Type 1 (Logic): 565 mẫu train (đã làm sạch dữ liệu nhiễu).\n")
        f.write("- EXACT 2026 Type 2 (Physics): Dữ liệu vật lý cơ bản.\n\n")
        f.write("## 2. Approach và phương pháp\n")
        f.write("Hệ thống kết hợp 2 pipeline:\n")
        f.write("- **Type 1 (Logic)**: Xử lý bằng hệ chuyên gia kết hợp prompt engineering chuẩn.\n")
        f.write("- **Type 2 (Physics)**: Dùng RAG kết hợp Code Sandbox để tính toán đáp án và unit.\n\n")
        f.write("## 3. Kích thước mô hình\n")
        f.write("Tổng số lượng tham số đang được load đồng thời là dưới 8B. Chúng tôi sử dụng Qwen3-8B phục vụ cho cả Type 1 và Type 2 thông qua 1 instance vLLM duy nhất.\n")
        
    print("\n" + "="*50)
    print(f"DONE! Build artifacts are in: {dist_dir}")
    print("="*50)
    print("ACTIONS REQUIRED BEFORE SUBMISSION:")
    print("1. Edit dist/urls.txt with your actual Modal deployment URLs.")
    print("2. Review dist/notation_mapping.csv if you have custom math notations.")
    print("3. Convert dist/solution.md to solution.pdf (e.g. using VSCode Markdown PDF extension or print to PDF).")
    print("4. Select source_code.zip, urls.txt, notation_mapping.csv, and solution.pdf -> Create a new zip named <your_team_name>.zip")
    print("="*50)

if __name__ == "__main__":
    build_submission()

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
                    # Ignore standard and large exclusions
                    exclude_dirs = {
                        "__pycache__", ".git", "venv", ".venv", "node_modules", 
                        "checkpoints", "qdrant_storage", "eval_results", "outputs", 
                        "dist", "EXACT2026_dataset_2026-05-15", ".codegraph",
                        "external", "runs", ".svelte-kit", "CMakeFiles",
                        "data", "processed", "processed_v2", "modal_logs", "wandb"
                    }
                    if any(exclude in Path(root).parts for exclude in exclude_dirs):
                        continue
                        
                    for file in files:
                        # Skip large non-code files
                        if file.lower().endswith(('.pdf', '.jsonl', '.csv', '.pyc', '.zip', '.tar.gz', '.log', '.out', '.png', '.jpg', '.jpeg')):
                            continue
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
        
    # 3. Create urls.txt with the real active URLs
    print("Generating urls.txt...")
    urls_path = dist_dir / "urls.txt"
    with open(urls_path, 'w', encoding='utf-8') as f:
        f.write("Prediction Endpoint: https://hirocao0710--exact-2026-submission-fastapi-app.modal.run/predict\n")
        f.write("vLLM Model Endpoint: https://hirocao0710--exact-2026-vllm-serve.modal.run/v1/models\n")
        
    # 4. Copy solution.docx to dist/
    print("Copying solution.docx to dist/...")
    src_solution = base_dir / "solution.docx"
    dest_solution = dist_dir / "solution.docx"
    if src_solution.exists():
        shutil.copy2(src_solution, dest_solution)
    else:
        print("Warning: solution.docx not found in workspace root.")
        
    print("\n" + "="*50)
    print(f"DONE! Build artifacts are in: {dist_dir}")
    print("="*50)
    print("ACTIONS REQUIRED BEFORE SUBMISSION:")
    print("1. Review dist/urls.txt (already configured with active Modal endpoints).")
    print("2. Review dist/notation_mapping.csv if you have custom math notations.")
    print("3. Convert dist/solution.docx to solution.pdf (as required by the guidelines).")
    print("4. Select source_code.zip, urls.txt, notation_mapping.csv, and solution.pdf -> Create a new zip named <your_team_name>.zip")
    print("="*50)

if __name__ == "__main__":
    build_submission()

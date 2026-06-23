import os
import argparse
import zipfile
import shutil
from pathlib import Path

MAX_SOURCE_ZIP_BYTES = 4 * 1024 * 1024
SOURCE_FOLDERS = ("dataset-1", "dataset-2", "submission")
EXCLUDED_DIRS = {
    "__pycache__", ".git", "venv", ".venv", "node_modules",
    "checkpoints", "qdrant_storage", "eval_results", "outputs",
    "dist", "EXACT2026_dataset_2026-05-15", ".codegraph",
    "external", "runs", ".svelte-kit", "CMakeFiles", "data",
    "processed", "processed_v2", "modal_logs", "wandb",
}
EXCLUDED_SUFFIXES = {
    ".pdf", ".jsonl", ".csv", ".pyc", ".zip", ".gz", ".log",
    ".out", ".png", ".jpg", ".jpeg", ".safetensors", ".bin",
    ".gguf", ".pt", ".pth",
}
EXCLUDED_NAMES = {".env"}


def build_source_code_zip(base_dir: Path, dist_dir: Path) -> Path:
    """Create the source archive without touching other submission artifacts."""
    dist_dir.mkdir(parents=True, exist_ok=True)
    output_path = dist_dir / "source_code.zip"

    with zipfile.ZipFile(
        output_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as zipf:
        for folder in SOURCE_FOLDERS:
            folder_path = base_dir / folder
            if not folder_path.exists():
                continue

            for root, dirs, files in os.walk(folder_path):
                dirs[:] = [name for name in dirs if name not in EXCLUDED_DIRS]
                root_path = Path(root)

                for filename in files:
                    file_path = root_path / filename
                    if filename in EXCLUDED_NAMES:
                        continue
                    if file_path.suffix.lower() in EXCLUDED_SUFFIXES:
                        continue
                    zipf.write(file_path, file_path.relative_to(base_dir))

    size = output_path.stat().st_size
    if size > MAX_SOURCE_ZIP_BYTES:
        output_path.unlink()
        raise RuntimeError(
            f"source_code.zip is {size / 1024 / 1024:.2f} MB; limit is 4 MB"
        )

    print(f"Built {output_path} ({size / 1024 / 1024:.2f} MB)")
    return output_path


def build_submission():
    base_dir = Path(__file__).resolve().parent.parent
    submission_dir = base_dir / "submission"
    dist_dir = submission_dir / "dist"
    
    # Clean previous build
    if dist_dir.exists():
        for item in dist_dir.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                print(f"Skipping deletion of {item} due to: {e}")
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Create source_code.zip
    print("Building source_code.zip...")
    build_source_code_zip(base_dir, dist_dir)
    
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
        f.write("Prediction Endpoint: https://m3pminh15112005--exact-2026-submission-fastapi-app.modal.run/predict\n")
        f.write("vLLM Model Endpoint: https://m3pminh15112005--exact-2026-vllm-serve.modal.run/v1/models\n")
        
    # 4. Copy solution.docx to dist/
    print("Copying solution.docx to dist/...")
    src_solution = base_dir / "solution.docx"
    dest_solution = dist_dir / "solution.docx"
    if src_solution.exists():
        try:
            shutil.copy2(src_solution, dest_solution)
        except Exception as e:
            print(f"Warning: Could not copy solution.docx (already exists or locked): {e}")
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
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-only",
        action="store_true",
        help="Only rebuild dist/source_code.zip and preserve other artifacts.",
    )
    args = parser.parse_args()

    if args.source_only:
        project_dir = Path(__file__).resolve().parent.parent
        build_source_code_zip(project_dir, project_dir / "submission" / "dist")
    else:
        build_submission()

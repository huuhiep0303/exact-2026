import subprocess
import os
import sys
import shutil

def upload_checkpoints():
    volume_name = "exact-2026-volume"
    
    # Lấy đường dẫn tuyệt đối của thư mục chứa script hiện tại (dataset-2/outputs)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_dir = os.path.join(script_dir, "checkpoints", "final")
    
    # LƯU Ý: Đặt tên thư mục đích khác với Type 1 (checkpoints/type2-final) để tránh ghi đè model Type 1
    remote_dir = "checkpoints/type2-final"
    
    if not os.path.exists(local_dir):
        print(f"❌ Lỗi: Không tìm thấy thư mục local tại {local_dir}")
        print("Vui lòng đảm bảo bạn đã train xong và thư mục này tồn tại.")
        sys.exit(1)
        
    print("=" * 60)
    print("🚀 BẮT ĐẦU UPLOAD LORA (TYPE 2) LÊN MODAL CLOUD")
    print("=" * 60)
    print(f"📁 Nguồn (Local): {local_dir}")
    print(f"☁️ Đích (Modal) : Volume '{volume_name}' -> /{remote_dir}")
    print("⏳ Đang chọn lọc các file (CHỈ LẤY Model Fine-tuned)...")
    
    # Chỉ định các định dạng file thuộc về Weights và Config của Model
    allowed_extensions = {".json", ".safetensors", ".bin", ".md", ".txt"}
    
    # Thư mục staging (trung gian) để gom các file hợp lệ vào trước khi upload 1 lượt
    staging_dir = os.path.join(script_dir, "checkpoints", "staging_upload")
    os.makedirs(staging_dir, exist_ok=True)
    
    files_to_upload = []
    
    # Lọc file trong thư mục final
    for root, _, files in os.walk(local_dir):
        # Bỏ qua các thư mục lưu trữ trung gian (vd: checkpoint-500) nếu có lọt vào
        if "checkpoint-" in root and "final" not in root:
            continue
            
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in allowed_extensions:
                file_path = os.path.join(root, file)
                files_to_upload.append(file_path)
                
    if not files_to_upload:
        print("❌ Không tìm thấy file Model hợp lệ nào (.safetensors, .json...) để upload.")
        shutil.rmtree(staging_dir, ignore_errors=True)
        sys.exit(1)
        
    print(f"\n✅ Đã tìm thấy {len(files_to_upload)} file Model/Config hợp lệ:")
    for f in files_to_upload:
        filename = os.path.basename(f)
        print(f"  - {filename}")
        # Copy các file an toàn sang thư mục staging
        shutil.copy2(f, os.path.join(staging_dir, filename))
        
    print("\n⏳ Đang tiến hành đồng bộ lên Modal...")
    
    # Sử dụng Modal CLI qua subprocess. Thêm dấu "/" vào cuối staging_dir để copy toàn bộ nội dung
    cmd = [
        sys.executable, "-m", "modal", "volume", "put", 
        volume_name, 
        staging_dir + "/", 
        remote_dir
    ]
    
    try:
        # Chạy lệnh và hiển thị progress bar ra terminal
        subprocess.run(cmd, check=True)
        print(f"\n✅ Upload hoàn tất! LoRA Type 2 đã nằm an toàn tại: /{remote_dir}")
        print("Bây giờ bạn có thể thêm đường dẫn này vào module Reasoner của Type 2.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Lỗi trong quá trình upload (Exit code: {e.returncode})")
    except KeyboardInterrupt:
        print("\n⚠️ Quá trình upload bị hủy bởi người dùng.")
    finally:
        # Dọn dẹp sạch sẽ thư mục trung gian sau khi hoàn tất
        shutil.rmtree(staging_dir, ignore_errors=True)

if __name__ == "__main__":
    upload_checkpoints()

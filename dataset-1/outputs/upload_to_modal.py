import subprocess
import os
import sys

def upload_checkpoints():
    volume_name = "exact-2026-volume"
    
    # Lấy đường dẫn tuyệt đối của thư mục chứa script hiện tại (dataset-1/outputs)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Nối đường dẫn để trỏ tới dataset-1/outputs/checkpoints/final
    local_dir = os.path.join(script_dir, "checkpoints", "final")
    
    # Đường dẫn đích trên Modal Volume (trùng với cấu hình trong vllm_serve.py)
    remote_dir = "checkpoints/final"
    
    if not os.path.exists(local_dir):
        print(f"❌ Lỗi: Không tìm thấy thư mục local tại {local_dir}")
        print("Vui lòng đảm bảo bạn đã train xong và thư mục này tồn tại.")
        sys.exit(1)
        
    print("=" * 60)
    print("🚀 BẮT ĐẦU UPLOAD CHECKPOINT LÊN MODAL CLOUD")
    print("=" * 60)
    print(f"📁 Nguồn (Local): {local_dir}")
    print(f"☁️ Đích (Modal) : Volume '{volume_name}' -> /{remote_dir}")
    print("⏳ Đang tiến hành đồng bộ, vui lòng chờ trong giây lát...\n")
    
    # Sử dụng Modal CLI qua subprocess để có thanh tiến trình (progress bar) đẹp và ổn định nhất
    cmd = [
        sys.executable, "-m", "modal", "volume", "put", 
        volume_name, 
        local_dir, 
        remote_dir
    ]
    
    try:
        # Chạy lệnh và hiển thị output trực tiếp ra terminal
        subprocess.run(cmd, check=True)
        print("\n✅ Upload hoàn tất thành công! Checkpoint đã sẵn sàng trên Modal.")
        print("Bạn có thể chạy lại lệnh deploy vLLM để load model mới.")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Lỗi trong quá trình upload (Exit code: {e.returncode})")
    except KeyboardInterrupt:
        print("\n⚠️ Quá trình upload bị hủy bởi người dùng.")

if __name__ == "__main__":
    upload_checkpoints()

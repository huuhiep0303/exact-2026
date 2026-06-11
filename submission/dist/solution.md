# Giải pháp EXACT 2026

## 1. Datasets đã dùng
- EXACT 2026 Type 1 (Logic): 565 mẫu train (đã làm sạch dữ liệu nhiễu).
- EXACT 2026 Type 2 (Physics): Dữ liệu vật lý cơ bản.

## 2. Approach và phương pháp
Hệ thống kết hợp 2 pipeline:
- **Type 1 (Logic)**: Xử lý bằng hệ chuyên gia kết hợp prompt engineering chuẩn.
- **Type 2 (Physics)**: Dùng RAG kết hợp Code Sandbox để tính toán đáp án và unit.

## 3. Kích thước mô hình
Tổng số lượng tham số đang được load đồng thời là dưới 8B. Chúng tôi sử dụng Qwen3-8B phục vụ cho cả Type 1 và Type 2 thông qua 1 instance vLLM duy nhất.

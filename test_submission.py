import requests
import json
import time

def test_system():
    # URL của API FastAPI đã deploy trên Modal
    api_url = "https://hiephc0303--exact-2026-submission-fastapi-app.modal.run/predict"
    
    print(f"Bắt đầu gửi request tới: {api_url}")
    print("-" * 50)
    
    # 1. Test Type 1 (Câu hỏi Logic)
    type1_payload = {
        "query_id": "TEST_T1_001",
        "type": "type1",
        "query": "If all cats are animals, and Fluffy is a cat, is Fluffy an animal?",
        "premises": [
            "All cats are animals.",
            "Fluffy is a cat."
        ],
        "options": ["Yes", "No"]
    }
    
    print("\n[TEST TYPE 1 - LOGIC]")
    start = time.time()
    try:
        response = requests.post(api_url, json=type1_payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        print(f"Thời gian phản hồi: {time.time() - start:.2f}s")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Lỗi khi gọi Type 1: {e}")

    # 2. Test Type 2 (Câu hỏi Vật Lý)
    type2_payload = {
        "query_id": "TEST_T2_001",
        "type": "type2",
        "query": "Calculate the energy stored in capacitor C when C = 100 μF and U = 30 V.",
        "premises": [],
        "options": []
    }
    
    print("\n" + "="*50)
    print("\n[TEST TYPE 2 - PHYSICS]")
    start = time.time()
    try:
        response = requests.post(api_url, json=type2_payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        print(f"Thời gian phản hồi: {time.time() - start:.2f}s")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Lỗi khi gọi Type 2: {e}")

if __name__ == "__main__":
    test_system()

import urllib.request
import json
import time

url = "https://m3pminh15112005--exact-2026-vllm-serve.modal.run/v1/chat/completions"

payload = {
    "model": "exact-lora-type2",
    "messages": [
        {"role": "system", "content": "You are a helpful physics assistant."},
        {"role": "user", "content": "Calculate the force between two charges of 2 nC separated by 10 cm."}
    ],
    "max_tokens": 512,
    "temperature": 0.1
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode('utf-8'),
    headers={"Content-Type": "application/json"},
    method="POST"
)

start = time.perf_counter()
try:
    with urllib.request.urlopen(req, timeout=60) as res:
        response_text = res.read().decode('utf-8')
        elapsed = time.perf_counter() - start
        print(f"Success in {elapsed:.2f}s!")
        print(response_text[:1000])
except Exception as e:
    print(f"Error: {e}")

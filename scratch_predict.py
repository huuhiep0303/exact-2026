import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://m3pminh15112005--exact-2026-submission-fastapi-app.modal.run/predict"

payload = {
    "query_id": "T2_0015",
    "type": "type2",
    "query": "A particle of mass m = 1.0 × 10^-5 g and charge q = +2.0 μC is moving in a circular orbit around a fixed charge Q = -4.0 μC. Calculate the speed of the particle if the radius of the orbit is r = 2.0 cm. Use k = 9.0 × 10^9 N·m²/C².",
    "premises": [],
    "options": []
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode('utf-8'),
    headers={"Content-Type": "application/json"},
    method="POST"
)

try:
    with urllib.request.urlopen(req) as res:
        print(res.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")

import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, r"d:\Work\Learn\Exact_XAI\exact-2026\dataset-2")
os.environ["PIPELINE_MODE"] = "api"
os.environ["OPENAI_BASE_URL"] = "https://m3pminh15112005--exact-2026-vllm-serve.modal.run/v1"
os.environ["REASONER_API_MODEL"] = "exact-lora-type2"

from app.modules.reasoner import reason
from app.modules.rag import retrieve_premises

question = "A point P is 10 cm from a charge q1 = +6.0 nC and 20 cm from a charge q2 = -2.0 nC. Calculate the electric potential at P. Use k = 9.0 × 10^9 N·m²/C²."

print("Retrieving premises...")
premises, score = retrieve_premises(question, top_k=3, topic="electric_potential")

print("Calling reasoner...")
output = reason(
    question,
    premises,
    topic="electric_potential",
    question_type="quantitative"
)

print("\n--- THINK TRACE ---")
print(output.think_trace)

print("\n--- FOL ---")
print(output.fol)

print("\n--- PYTHON CODE ---")
print(output.python_code)

print("\n--- RAW ANSWER ---")
print(output.raw_answer)
print(output.raw_unit)

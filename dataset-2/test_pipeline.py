"""
Test script - Run the pipeline on sample questions.
No GPU needed, no external services needed (uses mock mode).
"""
import sys
import json
from pathlib import Path

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import config
from app.pipeline import run_pipeline

# Ensure mock mode
# config.mode = "mock"
config.mode = "local"
config.debug = True


def test_questions():
    """Test with sample physics questions from the dataset."""
    test_cases = [
        # LD - Coulomb force
        "Two charges, q1 = 6 × 10^-8 C and q2 = -6 × 10^-8 C, are placed at points A and B in air, 8 cm apart. A third charge, q3 = 6 × 10^-8 C, is placed at point C. Determine the force acting on q3.",

        # TD - Capacitor energy
        "Calculate the energy stored in capacitor C when C = 100 μF and U = 30 V.",

        # Qualitative
        "What happens to the voltage across a capacitor when its plates are moved apart while disconnected from the source?",
    ]

    print("=" * 70)
    print("PHYSICS AI PIPELINE — TEST RUN")
    print(f"Mode: {config.mode}")
    print("=" * 70)

    for i, question in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"TEST {i}: {question[:80]}...")
        print(f"{'─' * 70}\n")

        response = run_pipeline(question)

        print(f"\n--- RESPONSE ---")
        print(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))
        print()

    # Test cache hit
    print(f"\n{'─' * 70}")
    print("TEST CACHE HIT (repeat question 2):")
    print(f"{'─' * 70}\n")
    response = run_pipeline(test_cases[1])
    print(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_questions()

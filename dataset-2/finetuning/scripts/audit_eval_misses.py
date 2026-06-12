"""Classify evaluator misses into stable, reviewable buckets."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.modules.topic_router import detect_topic


def classify(row: dict) -> str:
    prediction = str(row.get("pred_answer", "")).strip()
    question = str(row.get("question", "")).lower()
    gold_unit = str(row.get("gold_unit", ""))
    pred_unit = str(row.get("pred_unit", ""))
    if row.get("error"):
        return "runtime_error"
    if not prediction:
        return "blank_prediction"
    if row.get("numeric_value_match") and not row.get("strict_unit_match"):
        return "evaluator_format"
    if gold_unit and pred_unit and gold_unit != pred_unit:
        return "unit_scale"
    if any(term in question for term in ["triangle", "square", "perpendicular", "midpoint", "collinear", "vertices"]):
        return "geometry"
    if any(term in question for term in ["direction", "shape of the graph", "increase", "decrease", "what happens"]):
        return "qualitative"
    if any(term in question for term in ["electric field", "force", "charge", "angle"]):
        return "wrong_target_or_formula"
    return "formula_selection"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    misses = []
    for path in sorted(args.input_dir.glob("*_0_1000.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("final_match"):
                continue
            row["miss_type"] = classify(row)
            row["routed_topic"] = detect_topic(str(row.get("question", "")))
            misses.append(row)

    counts = Counter(row["miss_type"] for row in misses)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in misses:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"misses={len(misses)}")
    for name, count in counts.most_common():
        print(f"{name}={count}")


if __name__ == "__main__":
    main()

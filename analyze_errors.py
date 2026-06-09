"""
Error Analysis Script for EXACT 2026 Type 1 Dataset
Analyzes dataset quality AND evaluation predictions to find root causes of low accuracy.
"""

import json
import re
from pathlib import Path
from collections import defaultdict, Counter


# ─────────────────────────────────────────────────────────────────
# PART 1: Dataset Quality Analysis
# ─────────────────────────────────────────────────────────────────

def extract_answer_from_output(output_text: str) -> str | None:
    """Extract the final answer token from the output string."""
    # Match **Answer:** followed by answer token
    match = re.search(r'\*\*Answer:\*\*\s*([A-D]|Yes|No|Unknown)', output_text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def detect_reasoning_answer_contradiction(sample: dict) -> dict:
    """
    Detect if the reasoning text contradicts the final answer.
    Returns a dict with findings.
    """
    output = sample.get("output", "")
    metadata = sample.get("metadata", {})
    labeled_answer = metadata.get("answer", "")
    extracted_answer = extract_answer_from_output(output)
    
    # Extract reasoning section
    reasoning_match = re.search(
        r'\*\*Reasoning:\*\*\s*(.*?)\s*\*\*Answer:\*\*',
        output, re.DOTALL
    )
    reasoning_text = reasoning_match.group(1).strip() if reasoning_match else ""
    
    # Heuristic: look for affirmative signals in reasoning when answer is No/Unknown
    # and negative signals when answer is Yes
    affirmative_signals = [
        "is true", "is correct", "it follows", "confirms", "can be inferred",
        "so it's true", "making the statement true", "thus,", "therefore,",
        "it is explicitly stated", "directly states", "applies modus ponens",
        "is satisfied", "are satisfied", "must be true", "holds true"
    ]
    negative_signals = [
        "is false", "is not supported", "cannot be inferred", "does not follow",
        "no premise guarantees", "uncertain", "cannot determine", "insufficient"
    ]
    
    reasoning_lower = reasoning_text.lower()
    aff_count = sum(1 for s in affirmative_signals if s.lower() in reasoning_lower)
    neg_count = sum(1 for s in negative_signals if s.lower() in reasoning_lower)
    
    contradiction = False
    contradiction_type = None
    
    if extracted_answer == "No" and labeled_answer == "No":
        if aff_count > neg_count and aff_count >= 2:
            contradiction = True
            contradiction_type = "reasoning_says_YES_but_answer_is_NO"
    elif extracted_answer == "Yes" and labeled_answer == "Yes":
        if neg_count > aff_count and neg_count >= 1:
            contradiction = True
            contradiction_type = "reasoning_says_NO_but_answer_is_YES"
    elif extracted_answer == "Unknown" and labeled_answer == "Unknown":
        if aff_count > neg_count and aff_count >= 2:
            contradiction = True
            contradiction_type = "reasoning_says_YES_but_answer_is_UNKNOWN"
    
    # Check for direct in-text contradiction
    # e.g., "the statement is TRUE" -> Answer: No
    if re.search(r'the statement is true|making the statement true|statement is true', reasoning_lower):
        if extracted_answer in ["No", "Unknown"] and labeled_answer in ["No", "Unknown"]:
            contradiction = True
            contradiction_type = "explicit_TRUE_in_reasoning_but_answer_is_NO/UNKNOWN"
    
    if re.search(r'the statement is false|statement is false|statement is not true', reasoning_lower):
        if extracted_answer == "Yes" and labeled_answer == "Yes":
            contradiction = True
            contradiction_type = "explicit_FALSE_in_reasoning_but_answer_is_YES"

    return {
        "contradiction": contradiction,
        "contradiction_type": contradiction_type,
        "extracted_answer": extracted_answer,
        "labeled_answer": labeled_answer,
        "reasoning_aff_signals": aff_count,
        "reasoning_neg_signals": neg_count,
    }


def analyze_dataset_file(filepath: Path, split_name: str, max_samples: int = 500) -> dict:
    """Analyze a dataset file for quality issues."""
    print(f"\n{'='*60}")
    print(f"  Analyzing: {split_name} ({filepath.name})")
    print(f"{'='*60}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    total = len(data)
    sample_count = min(max_samples, total)
    print(f"Total samples: {total} | Analyzing first {sample_count}")
    
    # Statistics
    answer_dist = Counter()
    question_type_dist = Counter()
    contradictions = []
    missing_answer_format = []
    reasoning_answer_mismatches = 0
    
    for i, sample in enumerate(data[:sample_count]):
        metadata = sample.get("metadata", {})
        output = sample.get("output", "")
        
        # Track distributions
        labeled_answer = metadata.get("answer", "MISSING")
        q_type = metadata.get("question_type", "UNKNOWN")
        answer_dist[labeled_answer] += 1
        question_type_dist[q_type] += 1
        
        # Check if output has proper format
        if "**Answer:**" not in output:
            missing_answer_format.append(i)
        
        # Detect contradictions
        finding = detect_reasoning_answer_contradiction(sample)
        if finding["contradiction"]:
            contradictions.append({
                "index": i,
                "type": finding["contradiction_type"],
                "labeled_answer": finding["labeled_answer"],
                "reasoning_aff": finding["reasoning_aff_signals"],
                "reasoning_neg": finding["reasoning_neg_signals"],
                "input_snippet": sample.get("input", "")[:150],
                "reasoning_snippet": output[:300],
            })
        
        # Check reasoning vs answer match at word level
        extracted = finding.get("extracted_answer")
        labeled = labeled_answer
        if extracted and extracted.lower() != labeled.lower():
            reasoning_answer_mismatches += 1
    
    # Print findings
    print(f"\n📊 Answer Distribution (first {sample_count} samples):")
    for ans, cnt in sorted(answer_dist.items()):
        pct = cnt / sample_count * 100
        print(f"   {ans:10s}: {cnt:5d}  ({pct:.1f}%)")
    
    print(f"\n📝 Question Type Distribution:")
    for qtype, cnt in sorted(question_type_dist.items()):
        pct = cnt / sample_count * 100
        print(f"   {qtype:10s}: {cnt:5d}  ({pct:.1f}%)")
    
    print(f"\n🔴 CRITICAL: Reasoning↔Answer Contradictions: {len(contradictions)} / {sample_count}  ({len(contradictions)/sample_count*100:.1f}%)")
    
    if contradictions:
        print("\n   --- Contradiction Examples (first 5) ---")
        for c in contradictions[:5]:
            print(f"   [Sample #{c['index']}] Type: {c['type']}")
            print(f"     Labeled answer: {c['labeled_answer']} | Aff signals: {c['reasoning_aff']} | Neg signals: {c['reasoning_neg']}")
            snippet = c['reasoning_snippet'].replace('\n', ' ')[:200]
            print(f"     Output: {snippet}...")
            print()
    
    print(f"⚠️  Missing **Answer:** format in output: {len(missing_answer_format)} / {sample_count}")
    print(f"⚠️  Extracted answer ≠ labeled answer: {reasoning_answer_mismatches} / {sample_count}  ({reasoning_answer_mismatches/sample_count*100:.1f}%)")
    
    return {
        "split": split_name,
        "total": total,
        "analyzed": sample_count,
        "answer_dist": dict(answer_dist),
        "question_type_dist": dict(question_type_dist),
        "contradiction_count": len(contradictions),
        "contradiction_rate": len(contradictions) / sample_count,
        "contradiction_examples": contradictions[:20],
        "missing_format_count": len(missing_answer_format),
        "extracted_mismatch_count": reasoning_answer_mismatches,
    }


# ─────────────────────────────────────────────────────────────────
# PART 2: Prediction Error Analysis
# ─────────────────────────────────────────────────────────────────

def analyze_predictions(pred_filepath: Path) -> dict:
    """Analyze existing model predictions to understand failure patterns."""
    if not pred_filepath.exists():
        print(f"\n⚠️  Predictions file not found: {pred_filepath}")
        return {}
    
    print(f"\n{'='*60}")
    print(f"  Analyzing Predictions: {pred_filepath.name}")
    print(f"{'='*60}")
    
    with open(pred_filepath, "r", encoding="utf-8") as f:
        preds = json.load(f)
    
    total = len(preds)
    print(f"Total predictions: {total}")
    
    # Categorize errors
    correct = 0
    wrong_answer = []
    parse_failures = []  # couldn't parse answer
    
    question_type_correct = defaultdict(int)
    question_type_total = defaultdict(int)
    
    # Answer-level confusion matrix
    confusion = defaultdict(lambda: defaultdict(int))
    
    for pred in preds:
        gt = pred.get("ground_truth", {}).get("answer", pred.get("answer", ""))
        model_ans = pred.get("prediction", {}).get("answer", "")
        if not model_ans:
            model_ans = pred.get("predicted_answer", pred.get("model_answer", ""))
            
        q_type = pred.get("question_type", pred.get("type", "YesNo"))
        
        question_type_total[q_type] += 1
        
        if not model_ans:
            parse_failures.append(pred)
        elif model_ans.lower() == gt.lower():
            correct += 1
            question_type_correct[q_type] += 1
        else:
            wrong_answer.append({
                "gt": gt,
                "pred": model_ans,
                "q_type": q_type,
                "pred_output": pred.get("prediction", {}).get("reasoning", "")[:200]
            })
            confusion[gt][model_ans] += 1
    
    accuracy = correct / total * 100 if total > 0 else 0
    print(f"\n📈 Computed Accuracy: {accuracy:.2f}%  ({correct}/{total})")
    
    print(f"\n📊 Accuracy by Question Type:")
    for qtype in sorted(question_type_total.keys()):
        tot = question_type_total[qtype]
        cor = question_type_correct[qtype]
        pct = cor / tot * 100 if tot > 0 else 0
        print(f"   {qtype:10s}: {cor:4d}/{tot:4d} = {pct:.1f}%")
    
    print(f"\n🔴 Wrong answers: {len(wrong_answer)} | Parse failures: {len(parse_failures)}")
    
    print(f"\n📉 Confusion Matrix (GT → Predicted):")
    all_labels = sorted(set(confusion.keys()) | {v for vs in confusion.values() for v in vs.keys()})
    for gt_label in all_labels:
        for pred_label in all_labels:
            cnt = confusion[gt_label].get(pred_label, 0)
            if cnt > 0:
                print(f"   GT={gt_label:8s} → Pred={pred_label:8s}: {cnt:4d}")
    
    if wrong_answer:
        print(f"\n--- Wrong Answer Examples (first 5) ---")
        for e in wrong_answer[:5]:
            print(f"  GT={e['gt']} | Pred={e['pred']} | Type={e['q_type']}")
            snippet = e['pred_output'].replace('\n', ' ')[:200]
            print(f"  Output: {snippet}...")
            print()
    
    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "wrong_answer_count": len(wrong_answer),
        "parse_failure_count": len(parse_failures),
        "question_type_accuracy": {
            qt: question_type_correct[qt] / question_type_total[qt] * 100
            for qt in question_type_total
        },
        "confusion_matrix": {k: dict(v) for k, v in confusion.items()},
    }


# ─────────────────────────────────────────────────────────────────
# PART 3: Deep Dataset Sampling Check
# ─────────────────────────────────────────────────────────────────

def deep_sample_check(filepath: Path, split_name: str, n_samples: int = 20):
    """
    Manually sample N examples and check for reasoning vs answer consistency.
    Uses a simple heuristic: if reasoning mentions the statement is 'true' 
    but answer is No (or vice versa), flag it.
    """
    print(f"\n{'='*60}")
    print(f"  Deep Sample Check: {split_name}")
    print(f"{'='*60}")
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    flagged = 0
    import random
    random.seed(42)
    indices = random.sample(range(len(data)), min(n_samples, len(data)))
    
    print(f"Checking {len(indices)} random samples...\n")
    
    for idx in indices:
        sample = data[idx]
        output = sample.get("output", "")
        metadata = sample.get("metadata", {})
        labeled = metadata.get("answer", "?")
        
        # Look for explicit verdict words in reasoning
        reasoning_match = re.search(r'\*\*Reasoning:\*\*(.*?)\*\*Answer:\*\*', output, re.DOTALL)
        reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
        
        has_true_signal = bool(re.search(
            r'\b(is true|are true|is correct|it follows that|so it follows|'
            r'making the statement true|confirms that|can be inferred|must be true|'
            r'it follows that .{0,50}is true|so .{0,50}is true)\b',
            reasoning, re.IGNORECASE
        ))
        has_false_signal = bool(re.search(
            r'\b(is false|not supported|cannot be inferred|does not follow|'
            r'is not necessarily|no premise guarantees)\b',
            reasoning, re.IGNORECASE
        ))
        
        # Flag mismatches
        if has_true_signal and labeled in ["No", "Unknown"]:
            flagged += 1
            print(f"⚠️  [Sample #{idx}] Reasoning says YES/TRUE → Labeled answer: {labeled}")
            r_snip = reasoning.replace('\n', ' ')[:250]
            print(f"   Reasoning: {r_snip}...")
            print()
        elif has_false_signal and labeled == "Yes":
            flagged += 1
            print(f"⚠️  [Sample #{idx}] Reasoning says NO/FALSE → Labeled answer: {labeled}")
            r_snip = reasoning.replace('\n', ' ')[:250]
            print(f"   Reasoning: {r_snip}...")
            print()
    
    print(f"Flagged: {flagged} / {len(indices)} samples ({flagged/len(indices)*100:.1f}%)")
    return flagged


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

def main():
    base_dir = Path(__file__).parent
    data_dir = base_dir / "outputs" / "processed_data"
    results_dir = base_dir / "outputs" / "results" / "results"
    
    print("=" * 70)
    print("   EXACT 2026 — ERROR ANALYSIS REPORT")
    print("=" * 70)
    
    # ── 1. Dataset Quality Analysis ──────────────────────────────
    results = {}
    for split, filename in [("train", "train.json"), ("val", "val.json"), ("test", "test.json")]:
        filepath = data_dir / filename
        if filepath.exists():
            results[split] = analyze_dataset_file(filepath, split, max_samples=300)
        else:
            print(f"\n⚠️  {filename} not found at {filepath}")
    
    # ── 2. Deep Sampling Check ───────────────────────────────────
    for split, filename in [("train", "train.json"), ("val", "val.json")]:
        filepath = data_dir / filename
        if filepath.exists():
            deep_sample_check(filepath, split, n_samples=50)
    
    # ── 3. Predictions Analysis ──────────────────────────────────
    pred_files = [
        results_dir / "evaluation_results_predictions.json",
        results_dir / "predictions.json",
        base_dir / "outputs" / "results" / "predictions.json",
    ]
    for pf in pred_files:
        if pf.exists():
            pred_results = analyze_predictions(pf)
            results["predictions"] = pred_results
            break
    
    # ── 4. Summary ────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("   SUMMARY & ROOT CAUSE FINDINGS")
    print("=" * 70)
    
    for split in ["train", "val", "test"]:
        if split in results:
            r = results[split]
            total_contradiction_rate = r.get("contradiction_rate", 0) * 100
            mismatch_rate = r.get("extracted_mismatch_count", 0) / r.get("analyzed", 1) * 100
            print(f"\n[{split.upper()}] {r.get('total', 0)} total samples")
            print(f"  - Reasoning-Answer Contradiction Rate : {total_contradiction_rate:.1f}%")
            print(f"  - Answer Format Issues                : {r.get('missing_format_count', 0)}")
            print(f"  - Extracted vs Labeled mismatch       : {mismatch_rate:.1f}%")
    
    print("\n\n📌 ROOT CAUSE PRIORITY LIST:")
    print("  1. ❓ Check if dataset has systematic answer label errors (Yes↔No swap)")
    print("  2. ❓ Check if reasoning contradicts the final answer label")
    print("  3. ❓ Check answer format consistency (MCQ vs YesNo)")
    print("  4. ❓ Check inference prompt/template format alignment with training")
    
    # Save report
    report_path = base_dir / "outputs" / "error_analysis_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        # Remove non-serializable objects
        clean_results = {}
        for k, v in results.items():
            if isinstance(v, dict):
                clean_v = {kk: vv for kk, vv in v.items() if isinstance(vv, (int, float, str, list, dict))}
                clean_results[k] = clean_v
        json.dump(clean_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Full report saved to: {report_path}")


if __name__ == "__main__":
    main()

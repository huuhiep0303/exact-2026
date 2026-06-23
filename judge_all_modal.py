#!/usr/bin/env python3
"""
EXACT 2026 Live Judge Script
Act as the competition judge to test both Type 1 (Logic) and Type 2 (Physics) requests
against a deployed /predict endpoint using exact_eval_round1_hi_fine.json as baseline.
"""

import argparse
import json
import math
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
DEFAULT_EVAL_FILE = ROOT / "exact_eval_round1_hi_fine.json"
DEFAULT_ENDPOINT = "https://m3pminh15112005--exact-2026-submission-fastapi-app.modal.run/predict"
DEFAULT_OUT_DIR = ROOT / "eval_results" / "full_judge"

SUPERSCRIPT_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")

UNIT_FACTORS: dict[str, tuple[str, float]] = {
    "": ("dimensionless", 1.0),
    "-": ("dimensionless", 1.0),
    "—": ("dimensionless", 1.0),
    "%": ("percent", 1.0),
    "N": ("force", 1.0),
    "V/m": ("electric_field", 1.0),
    "N/C": ("electric_field", 1.0),
    "V": ("voltage", 1.0),
    "kV": ("voltage", 1e3),
    "mV": ("voltage", 1e-3),
    "J": ("energy", 1.0),
    "mJ": ("energy", 1e-3),
    "μJ": ("energy", 1e-6),
    "uJ": ("energy", 1e-6),
    "nJ": ("energy", 1e-9),
    "F": ("capacitance", 1.0),
    "mF": ("capacitance", 1e-3),
    "μF": ("capacitance", 1e-6),
    "uF": ("capacitance", 1e-6),
    "nF": ("capacitance", 1e-9),
    "pF": ("capacitance", 1e-12),
    "C": ("charge", 1.0),
    "mC": ("charge", 1e-3),
    "μC": ("charge", 1e-6),
    "uC": ("charge", 1e-6),
    "nC": ("charge", 1e-9),
    "pC": ("charge", 1e-12),
    "A": ("current", 1.0),
    "mA": ("current", 1e-3),
    "μA": ("current", 1e-6),
    "uA": ("current", 1e-6),
    "Ω": ("resistance", 1.0),
    "ohm": ("resistance", 1.0),
    "ohms": ("resistance", 1.0),
    "kΩ": ("resistance", 1e3),
    "m": ("length", 1.0),
    "cm": ("length", 1e-2),
    "mm": ("length", 1e-3),
    "m/s": ("speed", 1.0),
    "m/s^2": ("acceleration", 1.0),
    "m/s²": ("acceleration", 1.0),
    "Pa": ("pressure", 1.0),
    "kPa": ("pressure", 1e3),
    "W": ("power", 1.0),
    "kW": ("power", 1e3),
    "Hz": ("frequency", 1.0),
    "kHz": ("frequency", 1e3),
    "T": ("magnetic_field", 1.0),
    "mT": ("magnetic_field", 1e-3),
    "μT": ("magnetic_field", 1e-6),
    "uT": ("magnetic_field", 1e-6),
}


def normalize_text(text: Any) -> str:
    value = "" if text is None else str(text)
    value = value.strip()
    value = value.replace("µ", "μ").replace("−", "-").replace("–", "-")
    value = value.replace("×", "x").replace("·", "*")
    value = re.sub(r"\s+", " ", value)
    return value


def normalize_unit(unit: Any) -> str:
    value = normalize_text(unit)
    replacements = {
        "Ohms": "Ω",
        "Ohm": "Ω",
        "ohms": "ohm",
        "uF": "μF",
        "uC": "μC",
        "uJ": "μJ",
        "uA": "μA",
        "uT": "μT",
        "degC": "°C",
        "° C": "°C",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def parse_numeric(value: Any) -> float | None:
    text = normalize_text(value).translate(SUPERSCRIPT_MAP).replace(",", "")
    if not text:
        return None

    if "=" in text:
        parsed = parse_numeric(text.rsplit("=", 1)[-1])
        if parsed is not None:
            return parsed

    text = re.sub(r"\^\{([+-]?\d+)\}", r"^\1", text)

    textbook_power = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s*\.\s*10\s*\^?\s*([+-]?\d+)\s*", text)
    if textbook_power:
        return float(textbook_power.group(1)) * (10 ** int(textbook_power.group(2)))

    power_only = re.fullmatch(r"\s*10\s*\^\s*([+-]?\d+)\s*", text)
    if power_only:
        return 10 ** int(power_only.group(1))

    sci = re.search(
        r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(?:x|\*)\s*10\s*\^?\s*([+-]?\d+)",
        text,
        flags=re.IGNORECASE,
    )
    if sci:
        return float(sci.group(1)) * (10 ** int(sci.group(2)))

    plain = re.search(r"^[\s=]*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)", text, flags=re.IGNORECASE)
    if not plain:
        return None
    return float(plain.group(1))


def split_answer_unit(answer: Any) -> tuple[str, str]:
    text = normalize_text(answer)
    for unit in sorted((u for u in UNIT_FACTORS if u), key=len, reverse=True):
        match = re.match(rf"^(.*?)\s*({re.escape(unit)})\s*$", text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(), normalize_unit(match.group(2))

    numeric_match = re.match(
        r"^\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:\s*(?:x|\*)\s*10\s*\^?\s*[+-]?\d+|e[+-]?\d+)?)(?:\s+(.+))?\s*$",
        text,
        flags=re.IGNORECASE,
    )
    if numeric_match:
        return numeric_match.group(1).strip(), normalize_unit(numeric_match.group(2) or "")
    return text, ""


def unit_value(value: float, unit: str) -> tuple[str, float] | None:
    norm = normalize_unit(unit)
    if norm not in UNIT_FACTORS:
        return None
    dimension, factor = UNIT_FACTORS[norm]
    return dimension, value * factor


def compare_prediction_type2(
    pred_answer: str,
    gold_answer: str,
    gold_unit: str,
    aliases: list[str] | None = None,
    rel_tol: float = 1e-2,
    abs_tol: float = 1e-9,
) -> dict[str, Any]:
    gold_candidates = [gold_answer] + list(aliases or [])
    pred_value_text, pred_unit = split_answer_unit(pred_answer)
    pred_num = parse_numeric(pred_value_text)

    best: dict[str, Any] | None = None
    for candidate in gold_candidates:
        gold_value_text, embedded_unit = split_answer_unit(candidate)
        expected_unit = normalize_unit(embedded_unit or gold_unit)
        if expected_unit in {"-", "—"}:
            expected_unit = ""

        exact = normalize_text(pred_answer).lower() == normalize_text(f"{candidate} {expected_unit}".strip()).lower()
        gold_num = parse_numeric(gold_value_text)
        pred_unit_norm = normalize_unit(pred_unit)
        strict_unit = pred_unit_norm.lower() == expected_unit.lower()
        numeric_match = False
        physical_match = False

        if pred_num is not None and gold_num is not None:
            effective_abs_tol = abs_tol
            if "." in normalize_text(gold_value_text):
                decimals = len(normalize_text(gold_value_text).split(".", 1)[1].split()[0])
                effective_abs_tol = max(abs_tol, 0.5 * 10 ** (-decimals))
            numeric_match = math.isclose(pred_num, gold_num, rel_tol=rel_tol, abs_tol=effective_abs_tol)

            pred_physical = unit_value(pred_num, pred_unit_norm)
            gold_physical = unit_value(gold_num, expected_unit)
            if pred_physical and gold_physical:
                pred_dim, pred_si = pred_physical
                gold_dim, gold_si = gold_physical
                scaled_abs_tol = effective_abs_tol
                if gold_num:
                    scaled_abs_tol = max(abs_tol, abs(effective_abs_tol * gold_si / gold_num))
                physical_match = pred_dim == gold_dim and math.isclose(
                    pred_si,
                    gold_si,
                    rel_tol=rel_tol,
                    abs_tol=scaled_abs_tol,
                )

        ok = exact or (numeric_match and strict_unit) or physical_match
        result = {
            "ok": ok,
            "exact": exact,
            "numeric_match": numeric_match,
            "strict_unit": strict_unit,
            "physical_equiv": physical_match,
            "pred_value": pred_value_text,
            "pred_unit": pred_unit,
            "gold_value": gold_value_text,
            "gold_unit": expected_unit,
        }
        if ok:
            return result
        if best is None or result["numeric_match"] or result["physical_equiv"]:
            best = result

    return best or {
        "ok": False,
        "exact": False,
        "numeric_match": False,
        "strict_unit": False,
        "physical_equiv": False,
        "pred_value": pred_value_text,
        "pred_unit": pred_unit,
        "gold_value": gold_answer,
        "gold_unit": normalize_unit(gold_unit),
    }


def calculate_f1_score(pred: list[int], gold: list[int]) -> float:
    pred_set = set(pred)
    gold_set = set(gold)
    if not pred_set and not gold_set:
        return 1.0
    if not pred_set or not gold_set:
        return 0.0
    intersection = len(pred_set.intersection(gold_set))
    precision = intersection / len(pred_set)
    recall = intersection / len(gold_set)
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)


def post_json(endpoint: str, payload: dict[str, Any], timeout: float) -> tuple[int, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
        return response.status, json.loads(raw)


def unwrap_response(body: Any) -> dict[str, Any]:
    if isinstance(body, list):
        return body[0] if body else {}
    if isinstance(body, dict):
        return body
    return {"raw": body}


def response_answer_text(response: dict[str, Any]) -> str:
    answer = normalize_text(response.get("answer", ""))
    unit = normalize_unit(response.get("unit", ""))
    if not unit:
        return answer
    answer_unit = split_answer_unit(answer)[1]
    if answer_unit:
        return answer
    return f"{answer} {unit}".strip()


def evaluate_case(row: dict, got_response: dict, elapsed_sec: float) -> dict:
    query_id = row.get("query_id")
    q_type = row.get("type", "type1")
    expected = row.get("expected") or {}
    
    # 1. Extract parsed values
    got_answer = got_response.get("answer", "")
    got_unit = got_response.get("unit", "")
    got_premises = got_response.get("premises_used", [])
    if not isinstance(got_premises, list):
        got_premises = []
    
    expected_answer = str(expected.get("answer", ""))
    expected_aliases = list(expected.get("aliases") or [])
    expected_unit = str(expected.get("unit", ""))
    expected_premises = list(expected.get("premises_used") or [])
    
    p1_score = 0.0
    p2_score = 0.0
    status = "wrong_answer"
    compare_meta = {}
    
    if q_type == "type1":
        # Evaluate Answer (P1)
        accepted_answers = [expected_answer.strip().lower()] + [a.strip().lower() for a in expected_aliases]
        if got_answer.strip().lower() in accepted_answers:
            p1_score = 100.0
            
        # Evaluate Premises (P2)
        p2_score = calculate_f1_score(got_premises, expected_premises) * 100.0
        
        sample_score = 0.5 * p1_score + 0.5 * p2_score
        
        if p1_score == 100.0:
            if p2_score == 100.0:
                status = "correct"
            else:
                status = "wrong_premises_used"
        else:
            status = "wrong_answer"
            
    else:  # type2
        # Evaluate Physical equivalence (P1)
        got_combined_text = response_answer_text(got_response)
        compare = compare_prediction_type2(
            got_combined_text,
            expected_answer,
            expected_unit,
            expected_aliases
        )
        if compare["ok"]:
            p1_score = 100.0
            status = "correct"
        else:
            p1_score = 0.0
            status = "wrong_answer"
            
        p2_score = 0.0  # Not applicable to type2
        sample_score = p1_score
        compare_meta = {k: v for k, v in compare.items() if k not in ["pred_value", "pred_unit", "gold_value", "gold_unit"]}

    return {
        "query_id": query_id,
        "type": q_type,
        "ok": status == "correct",
        "status": status,
        "p1_score": p1_score,
        "p2_score": p2_score if q_type == "type1" else None,
        "sample_score": sample_score,
        "elapsed_sec": elapsed_sec,
        "expected": {
            "answer": expected_answer,
            "unit": expected_unit,
            "premises_used": expected_premises
        },
        "got": {
            "answer": got_answer,
            "unit": got_unit,
            "premises_used": got_premises
        },
        **compare_meta
    }


def main():
    parser = argparse.ArgumentParser(description="Judge deployed EXACT API Endpoint against baseline.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Deployed /predict endpoint URL.")
    parser.add_argument("--eval-file", type=Path, default=DEFAULT_EVAL_FILE, help="Baseline JSON logs.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory to save reports.")
    parser.add_argument("--timeout", type=float, default=60.0, help="Timeout in seconds per query.")
    parser.add_argument("--sleep", type=float, default=1.0, help="Delay between requests.")
    parser.add_argument("--only", default="", help="Comma-separated query IDs to run.")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit on cases to run.")
    args = parser.parse_args()

    if not args.eval_file.exists():
        print(f"❌ Error: Baseline file not found: {args.eval_file}")
        sys.exit(1)

    print(f"⚖️ LOADING BASELINE DATA: {args.eval_file.name}")
    try:
        data = json.loads(args.eval_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ Error reading baseline JSON: {e}")
        sys.exit(1)

    baseline_logs = data.get("logs", [])
    if not baseline_logs:
        print("❌ Error: No logs found in baseline file.")
        sys.exit(1)

    baseline_map = {log["query_id"]: log for log in baseline_logs}
    
    wanted = {item.strip() for item in args.only.split(",") if item.strip()}
    cases_to_run = []
    for log in baseline_logs:
        qid = log["query_id"]
        if wanted and qid not in wanted:
            continue
        cases_to_run.append(log)

    if args.limit:
        cases_to_run = cases_to_run[:args.limit]

    print(f"🚀 TARGET ENDPOINT: {args.endpoint}")
    print(f"📊 Running {len(cases_to_run)} evaluation cases...")
    print("-" * 60)

    results = []
    for index, row in enumerate(cases_to_run, start=1):
        query_id = row["query_id"]
        q_type = row["type"]
        payload = row["request_payload"]
        
        baseline_info = baseline_map[query_id]
        baseline_score = baseline_info.get("sample_score", 0.0)
        baseline_status = baseline_info.get("status", "wrong_answer")
        baseline_sec = baseline_info.get("duration_seconds", 0.0)

        print(f"[{index:02d}/{len(cases_to_run):02d}] Sending {query_id} ({q_type})...")
        started = time.perf_counter()
        
        try:
            status_code, body = post_json(args.endpoint, payload, args.timeout)
            elapsed = time.perf_counter() - started
            got_response = unwrap_response(body)
            eval_res = evaluate_case(row, got_response, elapsed)
            
            improvement = eval_res["sample_score"] - baseline_score
            sign = "+" if improvement >= 0 else ""
            status_diff = f"{baseline_status} -> {eval_res['status']}" if baseline_status != eval_res['status'] else eval_res['status']
            
            print(f"    ↳ {status_diff} | Score: {baseline_score:.2f} -> {eval_res['sample_score']:.2f} ({sign}{improvement:.2f}) | {elapsed:.2f}s (base: {baseline_sec:.2f}s)")
            results.append(eval_res)
            
        except Exception as exc:
            elapsed = time.perf_counter() - started
            print(f"    ↳ ❌ ERROR calling endpoint: {exc}")
            results.append({
                "query_id": query_id,
                "type": q_type,
                "ok": False,
                "status": "error",
                "p1_score": 0.0,
                "p2_score": 0.0 if q_type == "type1" else None,
                "sample_score": 0.0,
                "elapsed_sec": elapsed,
                "error": str(exc),
                "expected": {
                    "answer": str(row.get("expected", {}).get("answer", "")),
                    "unit": str(row.get("expected", {}).get("unit", "")),
                    "premises_used": list(row.get("expected", {}).get("premises_used") or [])
                },
                "got": {}
            })
            
        if args.sleep and index < len(cases_to_run):
            time.sleep(args.sleep)

    # Calculate overall stats
    total_cases = len(results)
    correct_count = sum(1 for r in results if r["ok"])
    
    t1_results = [r for r in results if r["type"] == "type1"]
    t2_results = [r for r in results if r["type"] == "type2"]
    
    t1_sum_score = sum(r["sample_score"] for r in t1_results)
    t2_sum_score = sum(r["sample_score"] for r in t2_results)
    
    # EXACT rules: base points is the sum of sample scores divided by 100
    new_t1_points = t1_sum_score / 100.0
    new_t2_points = t2_sum_score / 100.0
    new_base_points = new_t1_points + new_t2_points
    
    # Calculate speed/time bonus on CORRECT predictions
    correct_durations = [r["elapsed_sec"] for r in results if r["ok"]]
    new_avg_dur = sum(correct_durations) / len(correct_durations) if correct_durations else 0.0
    new_time_bonus = new_base_points * 0.1 * max(0.0, 1.0 - new_avg_dur / 60.0) if correct_durations else 0.0
    
    new_total_score = new_base_points + new_time_bonus

    # Get baseline comparison summaries
    base_summary = data.get("summary", {})
    old_t1_points = base_summary.get("type1_points", 0.0)
    old_t2_points = base_summary.get("type2_points", 0.0)
    old_base_points = base_summary.get("base_points", 0.0)
    old_time_bonus = base_summary.get("time_bonus_points", 0.0)
    old_total_score = base_summary.get("score", 0.0)
    old_correct_count = total_cases - len(base_summary.get("errors", []))

    # Write report
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = args.out_dir / f"full_judge_results_{stamp}.json"
    md_path = args.out_dir / f"full_judge_results_{stamp}.md"

    report_data = {
        "summary": {
            "old_correct_count": old_correct_count,
            "new_correct_count": correct_count,
            "old_t1_points": old_t1_points,
            "new_t1_points": new_t1_points,
            "old_t2_points": old_t2_points,
            "new_t2_points": new_t2_points,
            "old_base_points": old_base_points,
            "new_base_points": new_base_points,
            "old_time_bonus": old_time_bonus,
            "new_time_bonus": new_time_bonus,
            "old_total_score": old_total_score,
            "new_total_score": new_total_score,
            "new_avg_duration_correct": new_avg_dur
        },
        "results": results
    }

    json_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")

    # Generate Markdown comparison report
    diff_t1 = new_t1_points - old_t1_points
    diff_t2 = new_t2_points - old_t2_points
    diff_base = new_base_points - old_base_points
    diff_bonus = new_time_bonus - old_time_bonus
    diff_total = new_total_score - old_total_score

    md_content = f"""# EXACT 2026 Judge Evaluation Report

**Time generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Endpoint evaluated:** `{args.endpoint}`
**Baseline file:** `{args.eval_file.name}`

## 📊 Score Summary Comparison

| Metric | Baseline Score (Old) | New Run Score | Difference |
| :--- | :---: | :---: | :---: |
| **Correct Answers** | {old_correct_count}/{total_cases} | {correct_count}/{total_cases} | {correct_count - old_correct_count:+} |
| **Type 1 (Logic) Points** | {old_t1_points:.4f} | {new_t1_points:.4f} | {diff_t1:+.4f} |
| **Type 2 (Physics) Points** | {old_t2_points:.4f} | {new_t2_points:.4f} | {diff_t2:+.4f} |
| **Base Points** | {old_base_points:.4f} | {new_base_points:.4f} | {diff_base:+.4f} |
| **Time Bonus Points** | {old_time_bonus:.4f} | {new_time_bonus:.4f} | {diff_bonus:+.4f} |
| **Overall Score** | **{old_total_score:.4f}** | **{new_total_score:.4f}** | **{diff_total:+.4f}** |
| **Avg. Query Speed (Correct)** | - | {new_avg_dur:.2f}s | - |

## 🔍 Case-by-Case Breakdown

| ID | Type | Baseline Status | New Status | Baseline Score | New Score | Diff | Speed |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
"""

    for r in results:
        qid = r["query_id"]
        b_info = baseline_map[qid]
        b_status = b_info.get("status", "wrong_answer")
        b_score = b_info.get("sample_score", 0.0)
        
        diff = r["sample_score"] - b_score
        diff_str = f"{diff:+.2f}" if diff != 0 else "-"
        
        status_md = f"**{r['status']}**" if r["status"] == "correct" else r["status"]
        b_status_md = f"**{b_status}**" if b_status == "correct" else b_status
        
        md_content += f"| {qid} | {r['type']} | {b_status_md} | {status_md} | {b_score:.2f} | {r['sample_score']:.2f} | {diff_str} | {r['elapsed_sec']:.2f}s |\n"

    md_path.write_text(md_content, encoding="utf-8")

    print("\n" + "=" * 60)
    print("⚖️ EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Correct queries: {old_correct_count} -> {correct_count} ({correct_count - old_correct_count:+})")
    print(f"Base Points:     {old_base_points:.4f} -> {new_base_points:.4f} ({diff_base:+.4f})")
    print(f"Time Bonus:      {old_time_bonus:.4f} -> {new_time_bonus:.4f} ({diff_bonus:+.4f})")
    print(f"Overall Score:   {old_total_score:.4f} -> {new_total_score:.4f} ({diff_total:+.4f})")
    print("=" * 60)
    print(f"💾 JSON report saved to: {json_path}")
    print(f"💾 Markdown report saved to: {md_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()

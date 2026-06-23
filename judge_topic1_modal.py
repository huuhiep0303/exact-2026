#!/usr/bin/env python3
"""Mini judge for EXACT Type 1 requests against a deployed /predict endpoint.

Reads Type 1 samples from ../exact_eval_round1_hi_fine.json, sends each
request_payload to the endpoint, and scores:
  P1: answer match
  P2: premises_used F1 score
  sample_score: 50% P1 + 50% P2
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
DEFAULT_EVAL_FILE = ROOT.parent / "exact_eval_round1_hi_fine.json"
DEFAULT_ENDPOINT = "https://ngocthaodn0109--exact-2026-submission-fastapi-app.modal.run/predict"
DEFAULT_OUT_DIR = ROOT / "eval_results" / "live_topic1_judge"


def normalize_answer(value: Any) -> str:
    return "" if value is None else str(value).strip().lower()


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
    return 2 * precision * recall / (precision + recall)


def load_type1_cases(eval_file: Path) -> list[dict[str, Any]]:
    data = json.loads(eval_file.read_text(encoding="utf-8"))
    rows = data.get("logs", data if isinstance(data, list) else [])
    cases = [row for row in rows if row.get("type") == "type1"]
    return sorted(cases, key=lambda row: row.get("query_id", ""))


def build_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row.get("request_payload") or {})
    payload.setdefault("query_id", row.get("query_id", ""))
    payload.setdefault("type", "type1")
    payload.setdefault("query", "")
    payload.setdefault("premises", [])
    payload.setdefault("options", [])
    return payload


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


def evaluate_case(row: dict[str, Any], response: dict[str, Any], elapsed_sec: float) -> dict[str, Any]:
    expected = row.get("expected") or {}
    expected_answer = str(expected.get("answer", ""))
    expected_aliases = [str(alias) for alias in expected.get("aliases") or []]
    expected_premises = list(expected.get("premises_used") or [])

    got_answer = str(response.get("answer", ""))
    got_premises = response.get("premises_used", [])
    if not isinstance(got_premises, list):
        got_premises = []

    accepted_answers = [normalize_answer(expected_answer)] + [
        normalize_answer(alias) for alias in expected_aliases
    ]
    p1_score = 100.0 if normalize_answer(got_answer) in accepted_answers else 0.0
    p2_score = calculate_f1_score(got_premises, expected_premises) * 100.0
    sample_score = 0.5 * p1_score + 0.5 * p2_score

    if p1_score == 100.0 and p2_score == 100.0:
        status = "correct"
    elif p1_score == 100.0:
        status = "wrong_premises_used"
    else:
        status = "wrong_answer"

    return {
        "query_id": row.get("query_id", ""),
        "ok": status == "correct",
        "status": status,
        "p1_score": p1_score,
        "p2_score": p2_score,
        "sample_score": sample_score,
        "elapsed_sec": elapsed_sec,
        "expected": {
            "answer": expected_answer,
            "aliases": expected_aliases,
            "premises_used": expected_premises,
        },
        "got": {
            "answer": got_answer,
            "premises_used": got_premises,
        },
        "response": response,
        "request_payload": build_payload(row),
    }


def write_reports(results: list[dict[str, Any]], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"topic1_judge_results_{stamp}.json"
    md_path = out_dir / f"topic1_judge_results_{stamp}.md"

    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    total_score = sum(row.get("sample_score", 0.0) for row in results)
    avg_score = total_score / len(results) if results else 0.0
    correct = sum(1 for row in results if row.get("ok"))
    answer_correct = sum(1 for row in results if row.get("p1_score") == 100.0)

    lines = [
        "# Topic 1 Live Judge Results",
        "",
        f"- Total: {len(results)}",
        f"- Fully correct: {correct}",
        f"- Answer correct: {answer_correct}",
        f"- Average sample score: {avg_score:.2f}",
        "",
        "| ID | Status | Expected | Got | Expected Premises | Got Premises | P1 | P2 | Score | Seconds |",
        "|---|---|---|---|---|---|---:|---:|---:|---:|",
    ]
    for row in results:
        expected = row.get("expected") or {}
        got = row.get("got") or {}
        status = "PASS" if row.get("ok") else row.get("status", "FAIL")
        lines.append(
            f"| {row.get('query_id')} | {status} | `{expected.get('answer')}` | "
            f"`{got.get('answer')}` | `{expected.get('premises_used')}` | "
            f"`{got.get('premises_used')}` | {row.get('p1_score', 0):.1f} | "
            f"{row.get('p2_score', 0):.1f} | {row.get('sample_score', 0):.1f} | "
            f"{row.get('elapsed_sec', 0):.2f} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Judge deployed EXACT Type 1 endpoint.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Deployed /predict endpoint URL.")
    parser.add_argument("--eval-file", type=Path, default=DEFAULT_EVAL_FILE, help="Eval JSON containing logs.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory for JSON/Markdown reports.")
    parser.add_argument("--timeout", type=float, default=90.0, help="Per-request timeout in seconds.")
    parser.add_argument("--sleep", type=float, default=0.0, help="Delay between requests in seconds.")
    parser.add_argument("--only", default="", help="Comma-separated query IDs to run, e.g. T1_0007,T1_0008.")
    parser.add_argument("--limit", type=int, default=25, help="Optional number of Type 1 cases to run.")
    parser.add_argument("--dry-run", action="store_true", help="Print selected payloads without calling endpoint.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = load_type1_cases(args.eval_file)
    wanted = {item.strip() for item in args.only.split(",") if item.strip()}
    if wanted:
        cases = [row for row in cases if row.get("query_id") in wanted]
    if args.limit:
        cases = cases[: args.limit]

    print(f"Endpoint: {args.endpoint}")
    print(f"Eval file: {args.eval_file}")
    print(f"Selected Type 1 cases: {len(cases)}")

    if args.dry_run:
        for row in cases:
            print(json.dumps(build_payload(row), ensure_ascii=False))
        return 0

    results: list[dict[str, Any]] = []
    for index, row in enumerate(cases, start=1):
        query_id = row.get("query_id", "")
        started = time.perf_counter()
        try:
            status_code, body = post_json(args.endpoint, build_payload(row), args.timeout)
            response = unwrap_response(body)
            result = evaluate_case(row, response, time.perf_counter() - started)
            result["status_code"] = status_code
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            result = {
                "query_id": query_id,
                "ok": False,
                "status": "error",
                "p1_score": 0.0,
                "p2_score": 0.0,
                "sample_score": 0.0,
                "elapsed_sec": time.perf_counter() - started,
                "request_payload": build_payload(row),
                "error": repr(exc),
            }

        results.append(result)
        expected = (result.get("expected") or {}).get("answer", "")
        got = (result.get("got") or {}).get("answer", "")
        print(
            f"[{index:02d}/{len(cases):02d}] {result.get('status', 'unknown')} {query_id}: "
            f"expected={expected!r} got={got!r} "
            f"P1={result.get('p1_score', 0):.1f} P2={result.get('p2_score', 0):.1f} "
            f"score={result.get('sample_score', 0):.1f} "
            f"({result.get('elapsed_sec', 0):.2f}s)"
        )
        if args.sleep and index < len(cases):
            time.sleep(args.sleep)

    json_path, md_path = write_reports(results, args.out_dir)
    fully_correct = sum(1 for row in results if row.get("ok"))
    answer_correct = sum(1 for row in results if row.get("p1_score") == 100.0)
    avg_score = sum(row.get("sample_score", 0.0) for row in results) / len(results) if results else 0.0
    print(f"\nSummary: fully_correct={fully_correct}/{len(results)}, answer_correct={answer_correct}/{len(results)}, avg_score={avg_score:.2f}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    return 0 if fully_correct == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

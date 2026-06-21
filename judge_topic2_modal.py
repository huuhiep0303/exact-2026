"""Mini judge for EXACT Type 2 requests against a deployed /predict endpoint.

This script reads Type 2 samples from ../exact_eval_round1_hi_fine.json,
sends the original request_payload to the endpoint, and compares the response
against the expected answer/unit with numeric and physical-unit equivalence.
"""

from __future__ import annotations

import argparse
import json
import math
import re
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
DEFAULT_OUT_DIR = ROOT / "eval_results" / "live_topic2_judge"

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


def compare_prediction(
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


def load_type2_cases(eval_file: Path) -> list[dict[str, Any]]:
    data = json.loads(eval_file.read_text(encoding="utf-8"))
    rows = data.get("logs", data if isinstance(data, list) else [])
    cases = [row for row in rows if row.get("type") == "type2"]
    return sorted(cases, key=lambda row: row.get("query_id", ""))


def build_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row.get("request_payload") or {})
    payload.setdefault("query_id", row.get("query_id", ""))
    payload.setdefault("type", "type2")
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


def response_answer_text(response: dict[str, Any]) -> str:
    answer = normalize_text(response.get("answer", ""))
    unit = normalize_unit(response.get("unit", ""))
    if not unit:
        return answer
    answer_unit = split_answer_unit(answer)[1]
    if answer_unit:
        return answer
    return f"{answer} {unit}".strip()


def write_reports(results: list[dict[str, Any]], out_dir: Path) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"topic2_judge_results_{stamp}.json"
    md_path = out_dir / f"topic2_judge_results_{stamp}.md"

    json_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    passed = sum(1 for row in results if row.get("ok"))
    lines = [
        "# Topic 2 Live Judge Results",
        "",
        f"- Total: {len(results)}",
        f"- Passed: {passed}",
        f"- Failed/Error: {len(results) - passed}",
        "",
        "| ID | Status | Expected | Got | Flags | Seconds |",
        "|---|---|---|---|---|---:|",
    ]
    for row in results:
        status = "PASS" if row.get("ok") else "FAIL"
        if row.get("error"):
            status = "ERROR"
        flags = ", ".join(
            name
            for name in ["exact", "numeric_match", "strict_unit", "physical_equiv"]
            if row.get(name)
        )
        lines.append(
            f"| {row.get('query_id')} | {status} | `{row.get('expected')}` | "
            f"`{row.get('got')}` | {flags or '-'} | {row.get('elapsed_sec', 0):.2f} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Judge deployed EXACT Type 2 endpoint.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Deployed /predict endpoint URL.")
    parser.add_argument("--eval-file", type=Path, default=DEFAULT_EVAL_FILE, help="Eval JSON containing logs.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Directory for JSON/Markdown reports.")
    parser.add_argument("--timeout", type=float, default=180.0, help="Per-request timeout in seconds.")
    parser.add_argument("--sleep", type=float, default=0.0, help="Delay between requests in seconds.")
    parser.add_argument("--only", default="", help="Comma-separated query IDs to run, e.g. T2_0003,T2_0004.")
    parser.add_argument("--limit", type=int, default=0, help="Optional number of Type 2 cases to run.")
    parser.add_argument("--dry-run", action="store_true", help="Print selected payloads without calling endpoint.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = load_type2_cases(args.eval_file)
    wanted = {item.strip() for item in args.only.split(",") if item.strip()}
    if wanted:
        cases = [row for row in cases if row.get("query_id") in wanted]
    if args.limit:
        cases = cases[: args.limit]

    print(f"Endpoint: {args.endpoint}")
    print(f"Eval file: {args.eval_file}")
    print(f"Selected Type 2 cases: {len(cases)}")

    if args.dry_run:
        for row in cases:
            print(json.dumps(build_payload(row), ensure_ascii=False))
        return 0

    results: list[dict[str, Any]] = []
    for index, row in enumerate(cases, start=1):
        query_id = row.get("query_id", "")
        expected = row.get("expected") or {}
        expected_text = f"{expected.get('answer', '')} {expected.get('unit', '')}".strip()
        payload = build_payload(row)
        started = time.perf_counter()

        try:
            status_code, body = post_json(args.endpoint, payload, args.timeout)
            response = unwrap_response(body)
            got_text = response_answer_text(response)
            compare = compare_prediction(
                got_text,
                str(expected.get("answer", "")),
                str(expected.get("unit", "")),
                list(expected.get("aliases") or []),
            )
            elapsed = time.perf_counter() - started
            result = {
                "query_id": query_id,
                "ok": bool(compare["ok"]),
                "expected": expected_text,
                "got": got_text,
                "status_code": status_code,
                "elapsed_sec": elapsed,
                "request_payload": payload,
                "response": response,
                **compare,
            }
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            elapsed = time.perf_counter() - started
            result = {
                "query_id": query_id,
                "ok": False,
                "expected": expected_text,
                "got": "",
                "elapsed_sec": elapsed,
                "request_payload": payload,
                "error": repr(exc),
            }

        results.append(result)
        status = "PASS" if result.get("ok") else "FAIL"
        if result.get("error"):
            status = "ERROR"
        print(
            f"[{index:02d}/{len(cases):02d}] {status} {query_id}: "
            f"expected={expected_text!r} got={result.get('got', '')!r} "
            f"({result.get('elapsed_sec', 0):.2f}s)"
        )
        if args.sleep and index < len(cases):
            time.sleep(args.sleep)

    json_path, md_path = write_reports(results, args.out_dir)
    passed = sum(1 for row in results if row.get("ok"))
    print(f"\nSummary: {passed}/{len(results)} passed")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

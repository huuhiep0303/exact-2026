"""Audit trainable coverage in prepared SFT JSONL files."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


DEFAULT_PROCESSED_DIR = Path("finetuning/data/processed_v2")


def load_records(processed_dir: Path) -> list[dict]:
    records: list[dict] = []
    for split in ("train", "val", "test"):
        path = processed_dir / f"{split}.jsonl"
        if not path.exists():
            raise FileNotFoundError(f"Missing split file: {path}")
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                record["_split_file"] = split
                records.append(record)
    return records


def audit(processed_dir: Path) -> dict:
    records = load_records(processed_dir)
    topics = sorted({record["topic_prefix"] for record in records})
    by_topic: dict[str, dict[str, int]] = {}
    strategies: dict[str, dict[str, int]] = {}
    excluded: dict[str, list[str]] = defaultdict(list)

    for topic in topics:
        topic_records = [record for record in records if record["topic_prefix"] == topic]
        strategy_counts = Counter(record["code_strategy"] for record in topic_records)
        trainable = sum(bool(record["trainable"]) for record in topic_records)
        by_topic[topic] = {
            "total": len(topic_records),
            "trainable": trainable,
            "untrainable": len(topic_records) - trainable,
            "no_synthesized_code": strategy_counts.get("no_synthesized_code", 0),
        }
        strategies[topic] = dict(sorted(strategy_counts.items()))

    for record in records:
        if not record["trainable"]:
            excluded[record["topic_prefix"]].append(record["id"])

    return {
        "processed_dir": str(processed_dir),
        "total": len(records),
        "trainable_total": sum(bool(record["trainable"]) for record in records),
        "topics": by_topic,
        "code_strategies": strategies,
        "excluded_ids": dict(sorted(excluded.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit prepared SFT trainability.")
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED_DIR)
    parser.add_argument("--json", action="store_true", help="Print full JSON audit.")
    args = parser.parse_args()

    report = audit(args.processed_dir)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    print(f"Processed dir: {report['processed_dir']}")
    print(f"Total: {report['total']} | Trainable: {report['trainable_total']}")
    print("Topic\tTotal\tTrainable\tUntrainable\tNoSynth")
    for topic, counts in report["topics"].items():
        print(
            f"{topic}\t{counts['total']}\t{counts['trainable']}\t"
            f"{counts['untrainable']}\t{counts['no_synthesized_code']}"
        )
    if report["excluded_ids"]:
        print("\nExcluded IDs:")
        for topic, ids in report["excluded_ids"].items():
            print(f"{topic}: {', '.join(ids)}")


if __name__ == "__main__":
    main()

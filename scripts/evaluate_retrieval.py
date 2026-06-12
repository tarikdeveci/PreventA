import argparse
import json
from pathlib import Path
from typing import Any


def recall_at_k(expected: set[str], retrieved: list[str], k: int) -> float:
    if not expected:
        return 1.0
    return len(expected.intersection(retrieved[:k])) / len(expected)


def citation_accuracy(allowed: set[str], cited: list[str]) -> float:
    if not cited:
        return 0.0
    return sum(citation in allowed for citation in cited) / len(cited)


def evaluate(rows: list[dict[str, Any]], k: int) -> dict[str, float | int]:
    recalls = [
        recall_at_k(set(row["expected_chunk_ids"]), row["retrieved_chunk_ids"], k)
        for row in rows
    ]
    citation_scores = [
        citation_accuracy(set(row["retrieved_chunk_ids"]), row["cited_chunk_ids"])
        for row in rows
    ]
    count = len(rows)
    return {
        "examples": count,
        f"recall@{k}": sum(recalls) / count if count else 0.0,
        "citation_accuracy": sum(citation_scores) / count if count else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()

    rows = [
        json.loads(line)
        for line in args.dataset.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    print(json.dumps(evaluate(rows, args.k), indent=2))


if __name__ == "__main__":
    main()


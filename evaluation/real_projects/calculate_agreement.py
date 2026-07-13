"""Calcula concordancia observada e kappa de Cohen para TP/FP."""

import csv
from collections import Counter
from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "results" / "double_review_sample.csv"


def main() -> int:
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    pairs = [
        (row["reviewer_a"].upper(), row["reviewer_b"].upper())
        for row in rows
        if row["reviewer_a"].upper() in {"TP", "FP"}
        and row["reviewer_b"].upper() in {"TP", "FP"}
    ]
    if not pairs:
        print("Nenhuma classificacao dupla completa.")
        return 2
    observed = sum(a == b for a, b in pairs) / len(pairs)
    count_a = Counter(a for a, _ in pairs)
    count_b = Counter(b for _, b in pairs)
    expected = sum(
        (count_a[label] / len(pairs)) * (count_b[label] / len(pairs))
        for label in ("TP", "FP")
    )
    kappa = (observed - expected) / (1 - expected) if expected < 1 else 1.0
    print(f"Itens: {len(pairs)}")
    print(f"Concordancia observada: {observed:.2%}")
    print(f"Kappa de Cohen: {kappa:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

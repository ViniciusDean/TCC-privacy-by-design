"""Cria amostra estratificada e deterministica para dupla adjudicacao."""

import csv
import hashlib
import math
from pathlib import Path
import random


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "results" / "latest_raw_findings.csv"
TARGET = ROOT / "results" / "double_review_sample.csv"
SEED = 11042026


def main() -> int:
    if not SOURCE.exists():
        print(f"Resultado nao encontrado: {SOURCE}")
        return 2
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for row in rows:
        key = (row["project_id"], row["category"], row["risk"])
        groups.setdefault(key, []).append(row)

    selected = []
    for key, group in sorted(groups.items()):
        local_seed = int(hashlib.sha256(f"{SEED}|{key}".encode()).hexdigest()[:16], 16)
        shuffled = list(group)
        random.Random(local_seed).shuffle(shuffled)
        selected.extend(shuffled[: max(1, math.ceil(len(group) * 0.25))])

    fields = list(rows[0]) + ["reviewer_a", "reviewer_b"] if rows else []
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with TARGET.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in sorted(selected, key=lambda item: item["finding_id"]):
            writer.writerow({**row, "reviewer_a": "", "reviewer_b": ""})
    print(f"Amostra: {len(selected)}/{len(rows)} achados; semente: {SEED}")
    print(TARGET)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

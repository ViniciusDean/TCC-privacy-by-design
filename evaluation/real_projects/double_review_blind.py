"""Exporta e importa a planilha cega do segundo revisor."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CANONICAL = ROOT / "results" / "double_review_sample.csv"
DEFAULT_BLIND = ROOT / "results" / "double_review_reviewer_b.csv"
HIDDEN_FIELDS = {
    "manual_classification",
    "reviewer_notes",
    "suggested_fix",
    "reviewed_at",
    "reviewer_a",
}


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def blind_rows(fields: list[str], rows: list[dict]) -> tuple[list[str], list[dict]]:
    public_fields = [field for field in fields if field not in HIDDEN_FIELDS]
    if "reviewer_b" not in public_fields:
        public_fields.append("reviewer_b")
    return public_fields, [
        {**{field: row.get(field, "") for field in public_fields}, "reviewer_b": ""}
        for row in rows
    ]


def merge_reviewer_b(canonical: list[dict], blind: list[dict]) -> list[dict]:
    expected_ids = {row["finding_id"] for row in canonical}
    supplied = {row.get("finding_id", ""): row for row in blind}
    if set(supplied) != expected_ids:
        raise ValueError("A planilha do revisor B não corresponde à amostra congelada.")
    invalid = [
        finding_id for finding_id, row in supplied.items()
        if row.get("reviewer_b", "").upper() not in {"TP", "FP"}
    ]
    if invalid:
        raise ValueError("Todos os itens do revisor B devem ser TP ou FP.")
    return [
        {**row, "reviewer_b": supplied[row["finding_id"]]["reviewer_b"].upper()}
        for row in canonical
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    export = subparsers.add_parser("export", help="Gera planilha sem os rótulos do revisor A.")
    export.add_argument("--output", type=Path, default=DEFAULT_BLIND)
    import_cmd = subparsers.add_parser("import", help="Importa rótulos completos do revisor B.")
    import_cmd.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()

    fields, canonical = read_csv(CANONICAL)
    if args.command == "export":
        blind_fields, rows = blind_rows(fields, canonical)
        write_csv(args.output, blind_fields, rows)
        print(args.output)
        return 0

    _, blind = read_csv(args.input)
    try:
        merged = merge_reviewer_b(canonical, blind)
    except ValueError as exc:
        print(exc)
        return 2
    write_csv(CANONICAL, fields, merged)
    print(f"Classificações importadas: {len(merged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

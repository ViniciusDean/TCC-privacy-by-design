"""Executa o benchmark experimental e calcula metricas de classificacao."""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DIR = Path(__file__).resolve().parent
BENCHMARK_DIR = EVALUATION_DIR / "benchmark"
GABARITO_PATH = BENCHMARK_DIR / "gabarito.json"
RESULTS_DIR = EVALUATION_DIR / "results"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from code_analyzer import analisar_arquivo  # noqa: E402
from db_analyzer import analisar_banco  # noqa: E402


CATEGORY_UNIVERSES = {
    "python": {
        "DADO_HARDCODED",
        "CRIPTOGRAFIA_FRACA",
        "DADO_EM_LOG",
        "TRANSFERENCIA_SEM_BASE_LEGAL",
        "COLETA_EXCESSIVA",
        "AUSENCIA_EXCLUSAO",
        "DADO_SEM_CRIPTOGRAFIA",
    },
    "java": {
        "DADO_HARDCODED",
        "CRIPTOGRAFIA_FRACA",
        "DADO_EM_LOG",
        "TRANSFERENCIA_SEM_BASE_LEGAL",
        "COLETA_EXCESSIVA",
        "AUSENCIA_EXCLUSAO",
        "DADO_SEM_CRIPTOGRAFIA",
    },
    "sqlite": {
        "CAMPO_SEM_HASH",
        "AUSENCIA_SOFT_DELETE",
        "AUSENCIA_RETENCAO",
        "MISTURA_DADOS",
        "AUSENCIA_CONSENTIMENTO",
        "DADO_SENSIVEL_COMO_PK",
    },
}


def safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def metrics_from_counts(tp: int, fp: int, fn: int, tn: int) -> dict:
    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": safe_divide(2 * precision * recall, precision + recall),
        "specificity": safe_divide(tn, tn + fp),
    }


def classify(expected: set[str], predicted: set[str], universe: set[str]) -> dict:
    return metrics_from_counts(
        tp=len(expected & predicted),
        fp=len(predicted - expected),
        fn=len(expected - predicted),
        tn=len(universe - expected - predicted),
    )


def create_database(sql_path: Path, destination: Path) -> None:
    connection = sqlite3.connect(destination)
    try:
        connection.executescript(sql_path.read_text(encoding="utf-8"))
        connection.commit()
    finally:
        connection.close()


def analyze_case(case: dict, temporary_dir: Path) -> list:
    source_path = BENCHMARK_DIR / case["path"]
    if case["type"] in {"python", "java"}:
        return analisar_arquivo(str(source_path))
    if case["type"] == "sqlite":
        database_path = temporary_dir / f"{case['id']}.db"
        create_database(source_path, database_path)
        return analisar_banco(str(database_path))
    raise ValueError(f"Tipo de caso desconhecido: {case['type']}")


def evaluate(gabarito: dict) -> dict:
    case_results = []
    totals = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    by_category = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
    by_type = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})

    with tempfile.TemporaryDirectory(prefix="privacy-benchmark-") as temp:
        temporary_dir = Path(temp)
        for case in gabarito["cases"]:
            universe = CATEGORY_UNIVERSES[case["type"]]
            expected = set(case["expected"])
            unknown = expected - universe
            if unknown:
                raise ValueError(
                    f"Categorias fora do universo no caso {case['id']}: "
                    f"{sorted(unknown)}"
                )

            findings = analyze_case(case, temporary_dir)
            predicted = {finding.categoria for finding in findings}
            counts = classify(expected, predicted, universe)

            for key in totals:
                totals[key] += counts[key]
                by_type[case["type"]][key] += counts[key]

            for category in universe:
                expected_positive = category in expected
                predicted_positive = category in predicted
                key = (
                    "tp" if expected_positive and predicted_positive
                    else "fn" if expected_positive
                    else "fp" if predicted_positive
                    else "tn"
                )
                by_category[category][key] += 1

            case_results.append({
                "id": case["id"],
                "type": case["type"],
                "path": case["path"],
                "expected": sorted(expected),
                "predicted": sorted(predicted),
                "missing": sorted(expected - predicted),
                "unexpected": sorted(predicted - expected),
                "metrics": counts,
            })

    return {
        "benchmark_version": gabarito["version"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_unit": "caso-categoria",
        "case_count": len(case_results),
        "decision_count": sum(totals.values()),
        "scope_note": (
            "Benchmark controlado de regressão: as métricas descrevem aderência "
            "ao gabarito das fixtures e não desempenho generalizável em projetos reais."
        ),
        "overall": metrics_from_counts(**totals),
        "by_type": {
            key: metrics_from_counts(**counts)
            for key, counts in sorted(by_type.items())
        },
        "by_category": {
            key: metrics_from_counts(**counts)
            for key, counts in sorted(by_category.items())
        },
        "cases": case_results,
    }


def percentage(value: float) -> str:
    return f"{value * 100:.2f}%"


def render_markdown(results: dict) -> str:
    overall = results["overall"]
    lines = [
        "# Benchmark controlado de regressão",
        "",
        f"Gerado em: `{results['generated_at']}`",
        "",
        f"Casos avaliados: **{results['case_count']}**; decisões `{results['evaluation_unit']}`: **{results['decision_count']}**.",
        "",
        "> As métricas abaixo medem aderência ao gabarito das fixtures sintéticas. Elas não devem ser apresentadas como estimativa de precisão, recall ou eficácia em projetos reais.",
        "",
        "## Resultado no corpus controlado",
        "",
        "| TP | FP | FN | TN | Precisao | Recall | F1 | Especificidade |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
        (
            f"| {overall['tp']} | {overall['fp']} | {overall['fn']} | "
            f"{overall['tn']} | {percentage(overall['precision'])} | "
            f"{percentage(overall['recall'])} | {percentage(overall['f1'])} | "
            f"{percentage(overall['specificity'])} |"
        ),
        "",
        "## Por tipo",
        "",
        "| Tipo | Precisao | Recall | F1 |",
        "|---|---:|---:|---:|",
    ]
    for artifact_type, metrics in results["by_type"].items():
        lines.append(
            f"| {artifact_type} | {percentage(metrics['precision'])} | "
            f"{percentage(metrics['recall'])} | {percentage(metrics['f1'])} |"
        )

    lines.extend([
        "",
        "## Divergencias por caso",
        "",
        "| Caso | Tipo | Ausentes | Inesperadas |",
        "|---|---|---|---|",
    ])
    for case in results["cases"]:
        missing = ", ".join(case["missing"]) or "-"
        unexpected = ", ".join(case["unexpected"]) or "-"
        lines.append(
            f"| {case['id']} | {case['type']} | {missing} | {unexpected} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    gabarito = json.loads(GABARITO_PATH.read_text(encoding="utf-8"))
    results = evaluate(gabarito)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "latest.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (RESULTS_DIR / "latest.md").write_text(
        render_markdown(results),
        encoding="utf-8",
    )

    overall = results["overall"]
    print(f"Casos: {results['case_count']}")
    print(f"Precisao: {percentage(overall['precision'])}")
    print(f"Recall: {percentage(overall['recall'])}")
    print(f"F1: {percentage(overall['f1'])}")
    print(f"Resultados: {RESULTS_DIR / 'latest.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

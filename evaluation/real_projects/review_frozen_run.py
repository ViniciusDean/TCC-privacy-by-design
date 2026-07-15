"""Recompõe a revisão manual de uma execução congelada sem reanalisar projetos."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import run_real_projects as runner


SAMPLE_PATH = runner.RESULTS_DIR / "double_review_sample.csv"


def agreement_from_rows(rows: list[dict]) -> dict:
    """Retorna o estado da dupla revisão e calcula Kappa somente quando completa."""
    pairs = [
        (row.get("reviewer_a", "").upper(), row.get("reviewer_b", "").upper())
        for row in rows
        if row.get("reviewer_a", "").upper() in {"TP", "FP"}
        and row.get("reviewer_b", "").upper() in {"TP", "FP"}
    ]
    result = {
        "sample_size": len(rows),
        "completed_pairs": len(pairs),
        "ready": bool(rows) and len(pairs) == len(rows),
        "observed_agreement": None,
        "cohen_kappa": None,
    }
    if not result["ready"]:
        return result

    observed = sum(a == b for a, b in pairs) / len(pairs)
    count_a = Counter(a for a, _ in pairs)
    count_b = Counter(b for _, b in pairs)
    expected = sum(
        (count_a[label] / len(pairs)) * (count_b[label] / len(pairs))
        for label in ("TP", "FP")
    )
    result["observed_agreement"] = observed
    result["cohen_kappa"] = (
        (observed - expected) / (1 - expected) if expected < 1 else 1.0
    )
    return result


def current_project_flags() -> dict[str, bool]:
    return {
        project["id"]: bool(project.get("fn_review_complete", False))
        for project in runner.load_projects()
    }


def recompute_review(run_id: str) -> dict:
    """Mescla adjudicações ao run informado e preserva os artefatos originais."""
    run_dir = runner.RUNS_DIR / run_id
    source_path = run_dir / "findings.json"
    if not source_path.exists():
        raise FileNotFoundError(f"Execução congelada não encontrada: {source_path}")

    frozen = json.loads(source_path.read_text(encoding="utf-8"))
    if frozen.get("run_id") != run_id:
        raise ValueError("O identificador interno não corresponde ao diretório do run.")

    flags = current_project_flags()
    projects = [
        {**project, "fn_review_complete": flags.get(project["id"], False)}
        for project in frozen["projects"]
    ]
    findings = runner.merge_adjudications(
        frozen["findings"], runner.load_adjudications()
    )

    by_project = {}
    for project in projects:
        project_rows = [row for row in findings if row["project_id"] == project["id"]]
        by_project[project["id"]] = runner.external_metrics(
            project_rows,
            {project["id"]},
            bool(project["fn_review_complete"]),
        )

    by_role = {}
    for role in sorted({project.get("evaluation_role", "validation") for project in projects}):
        role_projects = [
            project for project in projects
            if project.get("evaluation_role", "validation") == role
        ]
        role_ids = {project["id"] for project in role_projects}
        role_rows = [row for row in findings if row["project_id"] in role_ids]
        by_role[role] = runner.external_metrics(
            role_rows,
            role_ids,
            bool(role_projects) and all(
                project["fn_review_complete"] for project in role_projects
            ),
        )

    project_ids = {project["id"] for project in projects}
    manual_review = runner.external_metrics(
        findings,
        project_ids,
        bool(projects) and all(project["fn_review_complete"] for project in projects),
    )
    agreement = agreement_from_rows(runner.read_csv_rows(SAMPLE_PATH))

    review = {
        **frozen,
        "projects": projects,
        "findings": findings,
        "manual_review": manual_review,
        "manual_review_by_project": by_project,
        "manual_review_by_role": by_role,
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "agreement": agreement,
        "publication_ready": manual_review["ready"] and agreement["ready"],
    }
    review["review_status"] = (
        "complete" if review["publication_ready"]
        else "awaiting_independent_review" if manual_review["ready"]
        else "incomplete_manual_review"
    )
    return review


def render_review(review: dict) -> str:
    lines = [runner.render_summary(review).rstrip(), "", "## Dupla revisão", ""]
    agreement = review["agreement"]
    lines.append(
        f"- Amostra: **{agreement['sample_size']}** itens; pares completos: "
        f"**{agreement['completed_pairs']}**."
    )
    if agreement["ready"]:
        lines.extend([
            f"- Concordância observada: **{agreement['observed_agreement']:.2%}**.",
            f"- Kappa de Cohen: **{agreement['cohen_kappa']:.4f}**.",
            "- Revisão independente completa; métricas liberadas para publicação com as ressalvas de escopo.",
        ])
    else:
        lines.append(
            "- Revisão independente pendente; métricas primárias não devem ser publicadas na dissertação."
        )
    lines.append("")
    return "\n".join(lines)


def write_review(review: dict) -> None:
    run_dir = runner.RUNS_DIR / review["run_id"]
    summary = render_review(review)
    payload = json.dumps(review, indent=2, ensure_ascii=False) + "\n"
    targets = (
        (run_dir / "review.json", runner.RESULTS_DIR / "latest_review.json"),
        (run_dir / "review_summary.md", runner.RESULTS_DIR / "latest_review_summary.md"),
    )
    targets[0][0].write_text(payload, encoding="utf-8")
    targets[0][1].write_text(payload, encoding="utf-8")
    targets[1][0].write_text(summary, encoding="utf-8")
    targets[1][1].write_text(summary, encoding="utf-8")
    runner.write_csv_rows(
        run_dir / "review_findings.csv", runner.FINDING_FIELDS, review["findings"]
    )
    runner.write_csv_rows(
        runner.RESULTS_DIR / "latest_review_findings.csv",
        runner.FINDING_FIELDS,
        review["findings"],
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Recompõe a revisão de um run sem executar os analisadores."
    )
    parser.add_argument("--run-id", required=True, help="Diretório imutável em results/runs.")
    args = parser.parse_args()
    try:
        review = recompute_review(args.run_id)
    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        return 2
    write_review(review)
    print(f"Execução analisada: {review['run_id']}")
    print(f"Status da revisão: {review['review_status']}")
    print(f"Publicação liberada: {review['publication_ready']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

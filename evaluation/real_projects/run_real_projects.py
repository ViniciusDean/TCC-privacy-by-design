"""Executa e documenta a avaliação externa sem apagar a revisão manual."""

from __future__ import annotations

import csv
import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVALUATION_DIR = Path(__file__).resolve().parent
PROJECTS_PATH = EVALUATION_DIR / "projects.json"
RESULTS_DIR = EVALUATION_DIR / "results"
RUNS_DIR = RESULTS_DIR / "runs"
ADJUDICATION_PATH = RESULTS_DIR / "manual_adjudication.csv"
FALSE_NEGATIVES_PATH = EVALUATION_DIR / "manual_false_negatives.csv"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from code_analyzer import analisar_arquivo, analisar_diretorio  # noqa: E402
from db_analyzer import analisar_banco  # noqa: E402
from analysis_profile import apply_profile, parse_profile  # noqa: E402


ADJUDICATION_FIELDS = [
    "finding_id",
    "manual_classification",
    "reviewer_notes",
    "suggested_fix",
    "reviewed_at",
]
FINDING_FIELDS = [
    "finding_id",
    "project_id",
    "project_name",
    "project_type",
    "evaluation_role",
    "artifact_path",
    "line",
    "category",
    "risk",
    "base_risk",
    "confidence",
    "lgpd_article",
    "description",
    "safe_evidence",
    "manual_classification",
    "reviewer_notes",
    "suggested_fix",
    "reviewed_at",
]
FALSE_NEGATIVE_FIELDS = [
    "false_negative_id",
    "project_id",
    "artifact_path",
    "line",
    "evidence_locator",
    "category",
    "description",
    "reviewer_notes",
    "status",
    "reviewed_at",
    "resolved_in_version",
]


def load_projects() -> list[dict]:
    if not PROJECTS_PATH.exists():
        raise FileNotFoundError(
            "Arquivo projects.json nao encontrado. Copie "
            "evaluation/real_projects/projects.example.json para "
            "evaluation/real_projects/projects.json e ajuste os caminhos."
        )
    data = json.loads(PROJECTS_PATH.read_text(encoding="utf-8"))
    projects = data.get("projects", [])
    if not projects:
        raise ValueError("projects.json nao contem projetos cadastrados.")
    return projects


def count_artifacts(path: Path, project_type: str) -> dict:
    if project_type == "sqlite":
        return {"sqlite_files": 1 if path.is_file() else 0}
    if path.is_file():
        suffix = path.suffix.lower()
        return {"python_files": int(suffix == ".py"), "java_files": int(suffix == ".java")}
    return {"python_files": len(list(path.rglob("*.py"))), "java_files": len(list(path.rglob("*.java")))}


def source_artifacts(path: Path, project_type: str) -> list[Path]:
    if path.is_file():
        return [path]
    suffixes = {".db", ".sqlite", ".sqlite3"} if project_type == "sqlite" else {".py", ".java"}
    return sorted((item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in suffixes), key=lambda item: item.as_posix())


def artifact_fingerprint(path: Path, project_type: str) -> str:
    """Return a reproducible SHA-256 for the files in the evaluated scope."""
    digest = hashlib.sha256()
    root = path if path.is_dir() else path.parent
    for artifact in source_artifacts(path, project_type):
        digest.update(relative_artifact_path(str(artifact), root).encode("utf-8"))
        digest.update(b"\0")
        with artifact.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


def verify_project_commit(project: dict, path: Path) -> str:
    """Falha antes da analise quando o checkout nao corresponde ao pre-registro."""
    expected = str(project.get("commit", "")).strip()
    if not expected or expected == "PENDING_FREEZE":
        raise ValueError(f"Commit nao fixado para {project['id']}.")
    start = path if path.is_dir() else path.parent
    repository = next((candidate for candidate in (start, *start.parents) if (candidate / ".git").exists()), None)
    if repository is None:
        raise ValueError(f"Checkout Git nao localizado para {project['id']}.")
    actual = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if len(expected) < 7 or not actual.lower().startswith(expected.lower()):
        raise ValueError(
            f"Commit divergente em {project['id']}: esperado {expected}, atual {actual}."
        )
    return actual


def analyze_project(project: dict) -> tuple[list, list, dict, Path]:
    project_type = project.get("type", "source")
    path = Path(project["path"]).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Caminho nao encontrado: {path}")
    checked_commit = verify_project_commit(project, path)

    started = time.perf_counter()
    if project_type == "sqlite":
        raw_findings = analisar_banco(str(path))
    elif path.is_dir():
        raw_findings = analisar_diretorio(str(path))
    else:
        raw_findings = analisar_arquivo(str(path))
    elapsed = time.perf_counter() - started

    profile = parse_profile(
        project.get("profile"),
        source="projects.json" if project.get("profile") is not None else "padrao",
    )
    findings = apply_profile(raw_findings, profile)

    metadata = count_artifacts(path, project_type)
    metadata.update({
        "elapsed_seconds": round(elapsed, 4),
        "finding_count": len(findings),
        "raw_finding_count": len(raw_findings),
        "perfil_analise": profile.public_metadata(),
        "input_sha256": artifact_fingerprint(path, project_type),
        "project_commit": checked_commit,
    })
    return raw_findings, findings, metadata, path


def relative_artifact_path(artifact_path: str, project_path: Path) -> str:
    artifact = Path(artifact_path)
    try:
        return artifact.resolve().relative_to(project_path if project_path.is_dir() else project_path.parent).as_posix()
    except (OSError, ValueError):
        return artifact.as_posix()


def stable_finding_id(
    project_id: str,
    artifact_path: str,
    line: int,
    category: str,
    discriminator: str = "",
) -> str:
    parts = [project_id, artifact_path.replace("\\", "/").lower(), str(line), category]
    if discriminator:
        parts.append(" ".join(discriminator.lower().split()))
    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def stable_false_negative_id(
    project_id: str,
    artifact_path: str,
    line: int,
    category: str,
    discriminator: str = "",
) -> str:
    return "fn-" + stable_finding_id(
        project_id, artifact_path, line, category, discriminator
    )


def safe_evidence(finding) -> str:
    value = getattr(finding, "evidencia_segura", None)
    if value:
        return str(value)
    return "Evidência técnica disponível pela categoria e localização; conteúdo bruto não é exportado."


def serialize_finding(project: dict, project_path: Path, finding) -> dict:
    artifact_path = relative_artifact_path(finding.arquivo, project_path)
    line = int(finding.linha or 0)
    category = str(finding.categoria)
    return {
        "finding_id": stable_finding_id(
            project["id"],
            artifact_path,
            line,
            category,
            getattr(finding, "trecho", "") if line == 0 else "",
        ),
        "project_id": project["id"],
        "project_name": project.get("name", project["id"]),
        "project_type": project.get("type", "source"),
        "evaluation_role": project.get("evaluation_role", "validation"),
        "artifact_path": artifact_path,
        "line": line,
        "category": category,
        "risk": finding.risco,
        "base_risk": getattr(finding, "risco_base", None) or finding.risco,
        "confidence": getattr(finding, "confianca", "ALTA"),
        "lgpd_article": finding.artigo_lgpd,
        "description": finding.descricao,
        "safe_evidence": safe_evidence(finding),
    }


def read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def write_csv_rows(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ensure_manual_review_files() -> None:
    if not ADJUDICATION_PATH.exists():
        write_csv_rows(ADJUDICATION_PATH, ADJUDICATION_FIELDS, [])
    if not FALSE_NEGATIVES_PATH.exists():
        write_csv_rows(FALSE_NEGATIVES_PATH, FALSE_NEGATIVE_FIELDS, [])


def load_adjudications() -> dict[str, dict]:
    return {row["finding_id"]: row for row in read_csv_rows(ADJUDICATION_PATH) if row.get("finding_id")}


def merge_adjudications(rows: list[dict], adjudications: dict[str, dict]) -> list[dict]:
    merged = []
    for row in rows:
        review = adjudications.get(row["finding_id"], {})
        merged.append({
            **row,
            "manual_classification": review.get("manual_classification", "").upper(),
            "reviewer_notes": review.get("reviewer_notes", ""),
            "suggested_fix": review.get("suggested_fix", ""),
            "reviewed_at": review.get("reviewed_at", ""),
        })
    return merged


def git_metadata() -> dict:
    def command(*args: str) -> str:
        try:
            return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return "indisponivel"

    return {
        "scanner_version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        "git_commit": command("git", "rev-parse", "HEAD"),
        "working_tree": "dirty" if command("git", "status", "--porcelain") not in {"", "indisponivel"} else "clean",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }


def active_false_negatives(project_ids: set[str] | None = None) -> list[dict]:
    active = []
    for row in read_csv_rows(FALSE_NEGATIVES_PATH):
        if not row.get("category"):
            continue
        if project_ids is not None and row.get("project_id") not in project_ids:
            continue
        if row.get("status", "OPEN").upper() in {"RESOLVED", "INVALID", "DUPLICATE"}:
            continue
        active.append(row)
    return active


def external_metrics(
    rows: list[dict],
    project_ids: set[str] | None = None,
    fn_review_complete: bool = True,
) -> dict:
    classifications = Counter(row["manual_classification"] for row in rows if row["manual_classification"] in {"TP", "FP"})
    unclassified = len(rows) - classifications["TP"] - classifications["FP"]
    false_negatives = len(active_false_negatives(project_ids))
    result = {
        "reviewed_tp": classifications["TP"],
        "reviewed_fp": classifications["FP"],
        "registered_fn": false_negatives,
        "unclassified": unclassified,
        "fn_review_complete": fn_review_complete,
        "ready": unclassified == 0 and fn_review_complete,
    }
    if result["ready"]:
        denominator = classifications["TP"] + classifications["FP"]
        result["precision"] = classifications["TP"] / denominator if denominator else None
        recall_denominator = classifications["TP"] + false_negatives
        result["recall"] = classifications["TP"] / recall_denominator if recall_denominator else None
        precision = result["precision"]
        recall = result["recall"]
        result["f1"] = (
            2 * precision * recall / (precision + recall)
            if precision is not None and recall is not None and precision + recall
            else None
        )
    return result


def render_summary(results: dict) -> str:
    lines = [
        "# Validação externa - achados técnicos",
        "",
        f"Gerado em: `{results['generated_at']}`",
        f"Execução: `{results['run_id']}`",
        f"Commit: `{results['provenance']['git_commit']}` ({results['provenance']['working_tree']})",
        "",
        "## Projetos analisados",
        "",
        "| Projeto | Papel | Tipo | Perfil | Brutos | Exibidos | Python | Java | SQLite | Tempo (s) | Hash do escopo |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for project in results["projects"]:
        meta = project["metadata"]
        lines.append(
            f"| {project['id']} | {project['evaluation_role']} | {project['type']} | "
            f"{meta.get('perfil_analise', {}).get('preset', 'n/a')} | {meta.get('raw_finding_count', meta['finding_count'])} | "
            f"{meta['finding_count']} | {meta.get('python_files', 0)} | "
            f"{meta.get('java_files', 0)} | {meta.get('sqlite_files', 0)} | {meta['elapsed_seconds']:.4f} | "
            f"{str(meta.get('input_sha256', 'n/a'))[:12]} |"
        )

    lines.extend([
        "",
        "## Revisão manual por projeto",
        "",
        "| Projeto | Papel | TP | FP | FN | Sem classificação | Precisão | Recall | F1 | Pronto |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for project in results["projects"]:
        metrics = results["manual_review_by_project"][project["id"]]
        precision = "n/a" if metrics.get("precision") is None else f"{metrics['precision']:.2%}"
        recall = "n/a" if metrics.get("recall") is None else f"{metrics['recall']:.2%}"
        f1 = "n/a" if metrics.get("f1") is None else f"{metrics['f1']:.2%}"
        ready = "sim" if metrics["ready"] else "não"
        lines.append(
            f"| {project['id']} | {project['evaluation_role']} | {metrics['reviewed_tp']} | "
            f"{metrics['reviewed_fp']} | {metrics['registered_fn']} | {metrics['unclassified']} | "
            f"{precision} | {recall} | {f1} | {ready} |"
        )

    lines.extend(["", "## Síntese por papel", ""])
    for role, metrics in results["manual_review_by_role"].items():
        if metrics["ready"]:
            precision = "n/a" if metrics.get("precision") is None else f"{metrics['precision']:.2%}"
            recall = "n/a" if metrics.get("recall") is None else f"{metrics['recall']:.2%}"
            f1 = "n/a" if metrics.get("f1") is None else f"{metrics['f1']:.2%}"
            lines.append(f"- `{role}`: precisão **{precision}**, recall **{recall}**, F1 **{f1}**.")
        else:
            lines.append(f"- `{role}`: revisão incompleta; métricas ainda não publicadas.")
    lines.append("")
    if results["manual_review"]["ready"]:
        lines.append(
            "A revisão manual foi concluída para os escopos registrados. As métricas descrevem somente "
            "estes projetos e commits; não devem ser generalizadas para outros sistemas."
        )
    else:
        lines.append(
            "A execução externa é exploratória até que a revisão manual esteja completa; ela não deve "
            "ser usada como estimativa de precisão em projetos reais antes disso."
        )
    lines.append("")
    return "\n".join(lines)


def write_results(
    rows: list[dict],
    project_summaries: list[dict],
    errors: dict[str, str],
    raw_rows: list[dict] | None = None,
) -> dict:
    ensure_manual_review_files()
    merged_rows = merge_adjudications(rows, load_adjudications())
    now = datetime.now(timezone.utc)
    run_id = f"{now.strftime('%Y%m%dT%H%M%SZ')}-{hashlib.sha256(str(now.timestamp()).encode()).hexdigest()[:8]}"
    project_metrics = {}
    role_metrics = {}
    for project in project_summaries:
        project_rows = [row for row in merged_rows if row["project_id"] == project["id"]]
        project_metrics[project["id"]] = external_metrics(
            project_rows,
            {project["id"]},
            bool(project.get("fn_review_complete", False)),
        )
    for role in sorted({project.get("evaluation_role", "validation") for project in project_summaries}):
        role_projects = [
            project for project in project_summaries
            if project.get("evaluation_role", "validation") == role
        ]
        role_ids = {project["id"] for project in role_projects}
        role_rows = [row for row in merged_rows if row["project_id"] in role_ids]
        role_metrics[role] = external_metrics(
            role_rows,
            role_ids,
            bool(role_projects) and all(project.get("fn_review_complete", False) for project in role_projects),
        )
    results = {
        "run_id": run_id,
        "generated_at": now.isoformat(),
        "provenance": git_metadata(),
        "projects": project_summaries,
        "errors": errors,
        "category_counts": dict(Counter(row["category"] for row in merged_rows)),
        "manual_review": external_metrics(
            merged_rows,
            {project["id"] for project in project_summaries},
            bool(project_summaries) and all(project.get("fn_review_complete", False) for project in project_summaries),
        ),
        "manual_review_by_project": project_metrics,
        "manual_review_by_role": role_metrics,
        "findings": merged_rows,
        "unfiltered_findings": raw_rows if raw_rows is not None else rows,
    }
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    summary = render_summary(results)
    for directory in (run_dir, RESULTS_DIR):
        (directory / "findings.json" if directory == run_dir else directory / "latest_raw_findings.json").write_text(
            json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        write_csv_rows(
            directory / "findings.csv" if directory == run_dir else directory / "latest_raw_findings.csv",
            FINDING_FIELDS,
            merged_rows,
        )
        raw_output = directory / "unfiltered_findings.json" if directory == run_dir else directory / "latest_unfiltered_findings.json"
        raw_output.write_text(
            json.dumps(raw_rows if raw_rows is not None else rows, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (directory / "summary.md" if directory == run_dir else directory / "latest_summary.md").write_text(summary, encoding="utf-8")
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Executa corpus externo versionado.")
    parser.add_argument("--role", help="Executa somente projetos com este evaluation_role.")
    parser.add_argument("--project", action="append", help="ID de projeto; pode repetir.")
    args = parser.parse_args()
    try:
        projects = load_projects()
    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        return 2

    projects = [project for project in projects if project.get("enabled", True)]
    if args.role:
        projects = [project for project in projects if project.get("evaluation_role") == args.role]
    if args.project:
        selected = set(args.project)
        projects = [project for project in projects if project.get("id") in selected]
    if not projects:
        print("Nenhum projeto corresponde aos filtros informados.")
        return 2

    rows: list[dict] = []
    raw_rows: list[dict] = []
    project_summaries: list[dict] = []
    errors: dict[str, str] = {}
    for project in projects:
        try:
            raw_findings, findings, metadata, project_path = analyze_project(project)
        except Exception as exc:
            errors[project["id"]] = str(exc)
            raw_findings, findings, project_path = [], [], Path(project["path"]).expanduser()
            metadata = {"elapsed_seconds": 0.0, "finding_count": 0, "raw_finding_count": 0, "error": str(exc)}
        project_summaries.append({
            "id": project["id"],
            "name": project.get("name", project["id"]),
            "type": project.get("type", "source"),
            "evaluation_role": project.get("evaluation_role", "validation"),
            "path": project["path"],
            "fn_review_complete": bool(project.get("fn_review_complete", False)),
            "metadata": metadata,
        })
        rows.extend(serialize_finding(project, project_path, finding) for finding in findings)
        raw_rows.extend(serialize_finding(project, project_path, finding) for finding in raw_findings)

    results = write_results(rows, project_summaries, errors, raw_rows)
    print(f"Projetos: {len(projects)}")
    print(f"Achados: {len(rows)}")
    print(f"Execução: {results['run_id']}")
    print(f"Resumo: {RESULTS_DIR / 'latest_summary.md'}")
    if errors:
        print("Projetos com erro:")
        for project_id, error in errors.items():
            print(f"- {project_id}: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

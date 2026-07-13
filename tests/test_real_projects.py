"""Regression tests for the persistent external-evaluation workflow."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = Path(__file__).resolve().parents[1] / "evaluation" / "real_projects" / "run_real_projects.py"
SPEC = importlib.util.spec_from_file_location("real_projects_runner", MODULE_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_holdout_v1_1_is_pinned_and_disabled_before_freeze():
    holdout = [
        project for project in runner.load_projects()
        if project.get("evaluation_role") == "holdout_v1_1"
    ]
    assert {project["id"] for project in holdout} == {
        "django_oscar_v1_1",
        "spring_petclinic_v1_1",
        "northwind_sqlite_v1_1",
    }
    assert all(project.get("enabled") is False for project in holdout)
    assert all(project.get("commit") not in {"", "PENDING_FREEZE"} for project in holdout)


def configure_results_dir(monkeypatch, tmp_path):
    results_dir = tmp_path / "results"
    monkeypatch.setattr(runner, "RESULTS_DIR", results_dir)
    monkeypatch.setattr(runner, "RUNS_DIR", results_dir / "runs")
    monkeypatch.setattr(runner, "ADJUDICATION_PATH", results_dir / "manual_adjudication.csv")
    monkeypatch.setattr(runner, "FALSE_NEGATIVES_PATH", tmp_path / "manual_false_negatives.csv")
    return results_dir


def test_finding_id_is_stable_for_the_same_location():
    first = runner.stable_finding_id("sample", "src/User.py", 17, "DADO_EM_LOG")
    second = runner.stable_finding_id("sample", "src\\user.py", 17, "DADO_EM_LOG")

    assert first == second


def test_database_findings_on_line_zero_use_a_stable_discriminator():
    first = runner.stable_finding_id(
        "sample", "data.sqlite", 0, "CAMPO_SEM_HASH", "Customer.Email : TEXT"
    )
    second = runner.stable_finding_id(
        "sample", "data.sqlite", 0, "CAMPO_SEM_HASH", "Employee.Email : TEXT"
    )

    assert first != second


def test_false_negative_id_is_stable_for_the_same_location():
    first = runner.stable_false_negative_id("sample", "src/User.py", 17, "DADO_EM_LOG")
    second = runner.stable_false_negative_id("sample", "src\\user.py", 17, "DADO_EM_LOG")

    assert first == second


def test_database_false_negative_ids_accept_column_discriminator():
    first = runner.stable_false_negative_id(
        "sample", "data.sqlite", 0, "CAMPO_SEM_HASH", "Customer.City"
    )
    second = runner.stable_false_negative_id(
        "sample", "data.sqlite", 0, "CAMPO_SEM_HASH", "Employee.City"
    )

    assert first != second


def test_verify_project_commit_accepts_safe_abbreviation(monkeypatch, tmp_path):
    (tmp_path / ".git").mkdir()
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout="7503f50c8d785f1ef60a557a4cb780d004108f3a\n"
        ),
    )

    actual = runner.verify_project_commit(
        {"id": "sample", "commit": "7503f50"}, tmp_path
    )

    assert actual == "7503f50c8d785f1ef60a557a4cb780d004108f3a"


def test_safe_evidence_never_falls_back_to_raw_source_text():
    finding = type("Finding", (), {"trecho": 'senha = "sentinela"'})()

    assert "sentinela" not in runner.safe_evidence(finding)


def test_reexecution_preserves_manual_adjudication(monkeypatch, tmp_path):
    results_dir = configure_results_dir(monkeypatch, tmp_path)
    runner.ensure_manual_review_files()
    finding_id = runner.stable_finding_id("sample", "src/model.py", 42, "DADO_EM_LOG")
    runner.write_csv_rows(
        runner.ADJUDICATION_PATH,
        runner.ADJUDICATION_FIELDS,
        [{
            "finding_id": finding_id,
            "manual_classification": "TP",
            "reviewer_notes": "Confirmado pela revisão manual.",
            "suggested_fix": "Remover dado pessoal do log.",
            "reviewed_at": "2026-07-09T12:00:00Z",
        }],
    )
    manual_before = runner.ADJUDICATION_PATH.read_bytes()
    row = {
        "finding_id": finding_id,
        "project_id": "sample",
        "project_name": "Sample",
        "project_type": "source",
        "evaluation_role": "tuning",
        "artifact_path": "src/model.py",
        "line": 42,
        "category": "DADO_EM_LOG",
        "risk": "ALTO",
        "lgpd_article": "Art. 46",
        "description": "Possível dado pessoal em log.",
        "safe_evidence": "Registro de log com identificador potencial.",
    }

    project = {
        "id": "sample",
        "name": "Sample",
        "type": "source",
        "evaluation_role": "tuning",
        "path": "src",
        "fn_review_complete": True,
        "metadata": {
            "python_files": 1,
            "java_files": 0,
            "sqlite_files": 0,
            "finding_count": 1,
            "elapsed_seconds": 0.01,
            "input_sha256": "abc",
        },
    }
    first = runner.write_results([row], [project], {})
    second = runner.write_results([row], [project], {})

    latest = runner.read_csv_rows(results_dir / "latest_raw_findings.csv")
    assert latest[0]["manual_classification"] == "TP"
    assert latest[0]["reviewer_notes"] == "Confirmado pela revisão manual."
    assert runner.ADJUDICATION_PATH.read_bytes() == manual_before
    assert first["manual_review"]["ready"] is True
    assert second["manual_review"]["reviewed_tp"] == 1
    assert second["manual_review"]["f1"] == 1.0
    assert second["manual_review_by_role"]["tuning"]["ready"] is True
    assert len(list((results_dir / "runs").iterdir())) == 2


def test_metrics_include_only_open_false_negatives(monkeypatch, tmp_path):
    configure_results_dir(monkeypatch, tmp_path)
    runner.ensure_manual_review_files()
    runner.write_csv_rows(
        runner.FALSE_NEGATIVES_PATH,
        runner.FALSE_NEGATIVE_FIELDS,
        [
            {
                "false_negative_id": "fn-open",
                "project_id": "sample",
                "artifact_path": "src/model.py",
                "line": 10,
                "category": "DADO_EM_LOG",
                "description": "Não detectado.",
                "reviewer_notes": "Confirmado manualmente.",
                "status": "OPEN",
            },
            {
                "false_negative_id": "fn-resolved",
                "project_id": "sample",
                "artifact_path": "src/dto.py",
                "line": 20,
                "category": "COLETA_EXCESSIVA",
                "description": "Resolvido pelo scanner.",
                "status": "RESOLVED",
            },
        ],
    )
    rows = [
        {"manual_classification": "TP"},
        {"manual_classification": "TP"},
        {"manual_classification": "FP"},
    ]

    metrics = runner.external_metrics(rows, {"sample"}, fn_review_complete=True)

    assert metrics["registered_fn"] == 1
    assert metrics["precision"] == 2 / 3
    assert metrics["recall"] == 2 / 3
    assert metrics["f1"] == 2 / 3

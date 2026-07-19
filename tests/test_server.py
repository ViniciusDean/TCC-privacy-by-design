"""Testes de integração dos endpoints principais do servidor Flask."""

import json
import sqlite3

from server import app


def criar_banco_vulneravel(caminho):
    with sqlite3.connect(caminho) as conexao:
        conexao.execute(
            "CREATE TABLE usuarios (cpf TEXT PRIMARY KEY, email TEXT)"
        )


def test_analyze_directory_combines_code_and_database(tmp_path):
    (tmp_path / "app.py").write_text(
        'cpf = "123.456.789-00"\n',
        encoding="utf-8",
    )
    criar_banco_vulneravel(tmp_path / "dados.db")

    response = app.test_client().post(
        "/api/analyze-directory",
        json={"directory": str(tmp_path)},
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["achados"] == data["vulnerabilities"]
    assert "indicador_tecnico" in data["summary"]
    assert "score_conformidade" in data["summary"]
    arquivos = {item["arquivo"] for item in data["achados"]}
    assert any(arquivo.endswith("app.py") for arquivo in arquivos)
    assert any(arquivo.endswith("dados.db") for arquivo in arquivos)


def test_analyze_directory_respects_privacyignore_for_code_and_database(tmp_path):
    (tmp_path / ".privacyignore").write_text(
        "fixtures/\nignorado.db\n",
        encoding="utf-8",
    )
    fixture = tmp_path / "fixtures" / "vulneravel.py"
    fixture.parent.mkdir()
    fixture.write_text('password = "secret123"\n', encoding="utf-8")
    criar_banco_vulneravel(tmp_path / "ignorado.db")

    response = app.test_client().post(
        "/api/analyze-directory",
        json={"directory": str(tmp_path)},
    )
    data = response.get_json()

    assert response.status_code == 422
    assert data["success"] is False
    assert data["status"] == "empty"
    assert data["achados"] == []
    assert data["vulnerabilities"] == []
    assert data["summary"]["total"] == 0
    assert data["summary"]["indicador_tecnico"] is None


def test_health_exposes_backend_identity():
    response = app.test_client().get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "service": "privacy-scanner",
        "version": "1.2.0",
        "api_version": 1,
    }


def test_analyze_file_has_canonical_contract_and_safe_aliases(tmp_path):
    arquivo = tmp_path / "entrada.py"
    arquivo.write_text('senha = "SENTINEL_SECRET_123"\n', encoding="utf-8")

    response = app.test_client().post(
        "/api/analyze-file",
        json={"filepath": str(arquivo)},
    )
    data = response.get_json()
    serialized = json.dumps(data, ensure_ascii=False)

    assert response.status_code == 200
    assert data["success"] is True
    assert data["status"] == "complete"
    assert data["achados"] == data["vulnerabilities"] == data["vulnerabilidades"]
    assert data["resumo"] == data["summary"] == data["sumario"]
    assert data["criterio_indicador"] == data["resumo"]["criterio_indicador"]
    assert data["escopo"]["arquivos_elegiveis"] == 1
    assert data["escopo"]["arquivos_analisados"] == 1
    assert data["achados"][0]["trecho"] == data["achados"][0]["evidencia_segura"]
    assert "SENTINEL_SECRET_123" not in serialized


def test_invalid_json_and_missing_fields_return_structured_400():
    client = app.test_client()
    responses = [
        client.post("/api/analyze-file", data="{", content_type="application/json"),
        client.post("/api/analyze-file", json=[]),
        client.post("/api/analyze-file", json={}),
    ]

    for response in responses:
        data = response.get_json()
        assert response.status_code == 400
        assert data["success"] is False
        assert isinstance(data["error"], dict)
        assert data["indicador_tecnico"] is None


def test_missing_target_is_404_without_technical_indicator(tmp_path):
    response = app.test_client().post(
        "/api/analyze-file",
        json={"filepath": str(tmp_path / "ausente.py")},
    )
    data = response.get_json()

    assert response.status_code == 404
    assert data["success"] is False
    assert data["status"] == "invalid"
    assert data["resumo"]["indicador_tecnico"] is None


def test_empty_directory_is_not_reported_as_clean(tmp_path):
    response = app.test_client().post(
        "/api/analyze-directory",
        json={"directory": str(tmp_path)},
    )
    data = response.get_json()

    assert response.status_code == 422
    assert data["status"] == "empty"
    assert data["resumo"]["indicador_tecnico"] is None
    assert data["escopo"]["arquivos_elegiveis"] == 0


def test_directory_keeps_valid_findings_when_some_files_fail(tmp_path):
    (tmp_path / "valido.py").write_text(
        'cpf = "111.222.333-44"\n',
        encoding="utf-8",
    )
    (tmp_path / "invalido.py").write_text("def quebrado(:\n", encoding="utf-8")
    (tmp_path / "corrompido.db").write_bytes(b"not a sqlite database")

    response = app.test_client().post(
        "/api/analyze-directory",
        json={"directory": str(tmp_path)},
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert data["status"] == "partial"
    assert data["escopo"]["arquivos_elegiveis"] == 3
    assert data["escopo"]["arquivos_analisados"] == 1
    assert data["escopo"]["arquivos_falhos"] == 2
    assert len(data["escopo"]["erros"]) == 2
    assert any(item["arquivo"].endswith("valido.py") for item in data["achados"])


def test_database_endpoint_rejects_corrupt_sqlite_with_422(tmp_path):
    database = tmp_path / "corrompido.db"
    database.write_bytes(b"invalid sqlite")

    response = app.test_client().post(
        "/api/analyze-database",
        json={"database": str(database)},
    )
    data = response.get_json()

    assert response.status_code == 422
    assert data["success"] is False
    assert data["error"]["codigo"] == "ANALISE_SEM_RESULTADO"
    assert data["escopo"]["erros"][0]["codigo"] == "BANCO_INVALIDO"


def test_export_json_is_sanitized(tmp_path):
    (tmp_path / "vulneravel.py").write_text(
        'token = "SENTINEL_TOKEN_987"\n',
        encoding="utf-8",
    )

    response = app.test_client().post(
        "/api/export",
        json={"directory": str(tmp_path), "format": "json"},
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["success"] is True
    assert "SENTINEL_TOKEN_987" not in data["content"]
    exported = json.loads(data["content"])
    assert exported["achados"] == exported["vulnerabilities"]
    assert exported["achados"][0]["trecho"] == exported["achados"][0]["evidencia_segura"]


def test_analysis_applies_profile_and_exposes_audit_metadata(tmp_path):
    source = tmp_path / "entrada.py"
    source.write_text('senha = "segredo"\n', encoding="utf-8")
    response = app.test_client().post(
        "/api/analyze-file",
        json={
            "filepath": str(source),
            "profile": {
                "schemaVersion": 1,
                "preset": "conservador",
                "categories": {"DADO_HARDCODED": {"severity": "BAIXO"}},
            },
        },
    )
    data = response.get_json()
    assert response.status_code == 200
    assert data["perfil_analise"]["preset"] == "conservador"
    assert data["achados"][0]["risco"] == "BAIXO"
    assert data["achados"][0]["risco_base"] == "ALTO"
    assert data["achados"][0]["confianca"] == "ALTA"


def test_invalid_profile_blocks_analysis(tmp_path):
    source = tmp_path / "entrada.py"
    source.write_text('senha = "segredo"\n', encoding="utf-8")
    response = app.test_client().post(
        "/api/analyze-file",
        json={"filepath": str(source), "profile": {"preset": "desconhecido"}},
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["codigo"] == "PERFIL_INVALIDO"


def test_profile_summary_distinguishes_raw_and_displayed_findings(tmp_path):
    source = tmp_path / "fixture.py"
    source.write_text('email = "fixture"\n', encoding="utf-8")

    response = app.test_client().post(
        "/api/analyze-file",
        json={"filepath": str(source), "profile": {"preset": "conservador"}},
    )
    data = response.get_json()

    assert response.status_code == 200
    assert data["resumo"]["total_bruto"] == 1
    assert data["resumo"]["total_exibido"] == 0
    assert data["resumo"]["ocultos_por_perfil"] == 1
    assert data["resumo"]["indicador_tecnico_bruto"] == 90
    assert data["resumo"]["indicador_tecnico_exibido"] == 100
    assert data["indicador_tecnico"] == 100
    assert data["achados"] == []

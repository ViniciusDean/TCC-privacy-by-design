"""Testes de integração dos endpoints principais do servidor Flask."""

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
    arquivos = {item["arquivo"] for item in data["vulnerabilities"]}
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

    assert response.status_code == 200
    assert data["success"] is True
    assert data["vulnerabilities"] == []
    assert data["summary"]["total"] == 0

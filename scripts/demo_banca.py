"""Gera uma demonstração antes/depois sem alterar as fixtures de avaliação."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server import VERSION, app  # noqa: E402


def main() -> None:
    output = ROOT / "output" / "demo-banca"
    workspace = output / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    source = ROOT / "evaluation/benchmark/cases/python/py_hardcoded_log.py"
    target = workspace / "app.py"
    profile = {"preset": "conservador"}
    client = app.test_client()
    steps = []

    # A correção retira identificador e saída desnecessários deste exemplo
    # mínimo; não simula proteção criptográfica nem altera o corpus original.
    for name, code, expected in (
        ("antes", source.read_text(encoding="utf-8"), {"DADO_HARDCODED", "DADO_EM_LOG"}),
        ("depois", 'print("Operação concluída")\n', set()),
    ):
        target.write_text(code, encoding="utf-8")
        (output / f"{name}.py").write_text(code, encoding="utf-8")
        response = client.post("/api/analyze-file", json={
            "filepath": str(target), "profile": profile,
        })
        assert response.status_code == 200
        analysis = response.get_json()
        assert {item["categoria"] for item in analysis["achados"]} == expected
        for report_format in ("html", "json", "pdf"):
            exported = client.post("/api/export", json={
                "directory": str(workspace), "profile": profile, "format": report_format,
            })
            assert exported.status_code == 200
            data = exported.get_json()
            assert data["resumo"] == analysis["resumo"]
            artifact = output / f"{name}.{report_format}"
            if data["encoding"] == "base64":
                artifact.write_bytes(base64.b64decode(data["content"]))
            else:
                artifact.write_text(data["content"], encoding="utf-8")
            if report_format == "json":
                assert json.loads(data["content"])["resumo"] == analysis["resumo"]
        steps.append({
            "etapa": name, "resumo": analysis["resumo"],
            "categorias": sorted(expected),
            "sha256_codigo": hashlib.sha256(code.encode("utf-8")).hexdigest(),
        })
    receipt = {
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "versao": VERSION,
        "fixture_original": source.relative_to(ROOT).as_posix(),
        "perfil": profile,
        "metodo": "API Flask real via test_client; relatórios renderizados pelo Reporter",
        "limite": "Demonstração sintética; não é avaliação externa nem prova de conformidade.",
        "sha256_backend": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ("server.py", "reporter.py", "analysis_profile.py", "code_analyzer.py")
        },
        "etapas": steps,
    }
    (output / "verificacao.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    print(f"Demonstração verificada em {output}: antes=2 achados; depois=0.")


if __name__ == "__main__":
    main()

"""Keep the CLI/API/extension version contract synchronized."""

import json
from pathlib import Path

from reporter import VERSAO_FERRAMENTA
from server import app


ROOT = Path(__file__).resolve().parents[1]


def test_version_is_shared_by_backend_extension_and_health_endpoint():
    expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    extension = json.loads((ROOT / "vscode-extension" / "package.json").read_text(encoding="utf-8"))
    health = app.test_client().get("/health").get_json()

    assert VERSAO_FERRAMENTA == expected
    assert extension["version"] == expected
    assert health["status"] == "ok"
    assert health["service"] == "privacy-scanner"
    assert health["version"] == expected

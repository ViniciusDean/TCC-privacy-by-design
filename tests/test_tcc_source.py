"""Guardrails for the canonical dissertation source."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "latex_tcc" / "main.tex"


def test_canonical_tcc_has_required_defense_sections():
    content = SOURCE.read_text(encoding="utf-8")

    assert "\\section{Privacy by Design e Cobertura do Artefato}" in content
    assert "\\section{Posicionamento da Revisão de Privacidade no SDLC}" in content
    assert "\\subsection{Rastreabilidade e Ameaças à Validade}" in content
    assert "\\chapter{CONCLUSÃO}" in content
    assert "caso--categoria" in content


def test_canonical_tcc_does_not_restore_obsolete_delivery_text():
    content = SOURCE.read_text(encoding="utf-8")

    assert "(DOMO, 2023)" not in content
    assert "\\chapter{CRONOGRAMA}" not in content
    assert "RESULTADOS ESPERADOS" not in content
    assert "relatório de conformidade" not in content.lower()


def test_canonical_tcc_contains_missing_foundational_references():
    content = SOURCE.read_text(encoding="utf-8")

    for citation in ("HEVNER, Alan R.", "PRESSMAN, Roger S.", "Constituição da República Federativa"):
        assert citation in content


def test_canonical_tcc_reports_reproduced_external_results():
    content = SOURCE.read_text(encoding="utf-8")

    assert "\\section{Validação Externa}" in content
    assert "Validação Externa Inicial" not in content
    assert "135 testes com sucesso" in content
    assert "precisão foi de 39,58\\%" in content
    assert "recall de 48,72\\%" in content
    assert "F1 de 43,68\\%" in content

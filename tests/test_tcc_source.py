"""Guardrails for the canonical dissertation source."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "latex_tcc" / "main.tex"


def test_canonical_tcc_has_required_defense_sections():
    content = SOURCE.read_text(encoding="utf-8")

    assert "\\section{Privacy by Design e Cobertura do Artefato}" in content
    assert "\\section{Posicionamento da Revisão de Privacidade no SDLC}" in content
    assert "\\subsection{Rastreabilidade e Ameaças à Validade}" in content
    assert "\\chapter{CONSIDERAÇÕES FINAIS}" in content
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


def test_canonical_tcc_answers_advisor_task_b():
    content = SOURCE.read_text(encoding="utf-8")

    for section in (
        "\\subsection{Modelo Preditivo ou em Cascata}",
        "\\subsection{Modelo Espiral e Desenvolvimento Iterativo}",
        "\\subsection{Desenvolvimento Ágil e Scrum}",
        "\\subsection{DevOps, DevSecOps e SSDF}",
        "\\section{Definição da Etapa do SDLC para Aplicação da Ferramenta}",
    ):
        assert section in content

    for source in (
        "BECK, Kent et al.",
        "A spiral model of software development and enhancement",
        "SCHWABER, Ken; SUTHERLAND, Jeff",
        "OWASP Software Assurance Maturity Model",
        "SOUPPAYA, Murugiah; SCARFONE, Karen; DODSON, Donna",
    ):
        assert source in content

    assert "\\label{qua:modelos-aplicacao}" in content
    assert "não compara metodologias de desenvolvimento" not in content


def test_canonical_tcc_reports_current_and_historical_evidence():
    content = SOURCE.read_text(encoding="utf-8")

    assert "\\section{Validação Externa}" in content
    assert "Validação Externa Inicial" not in content
    assert "135 testes com sucesso" in content
    assert "Privacy Scanner LGPD 1.2.0" in content
    assert "181 testes Python" in content
    assert "24 positivos corretos, 96 negativos corretos" in content
    assert "conjunto de retenção" in content
    assert "não como validação externa independente da versão 1.2.0" in content
    for metric in ("39,58\\%", "48,72\\%", "43,68\\%"):
        assert metric in content
    assert "164 testes" not in content
    assert "29 verificações TypeScript" not in content


def test_canonical_tcc_keeps_abnt_structure_and_sources():
    content = SOURCE.read_text(encoding="utf-8")
    document_body = content.split("\\begin{document}", maxsplit=1)[1]

    assert document_body.index("\\paginaCapa") < document_body.index("\\pagenumbering{arabic}")
    assert document_body.index("\\pagenumbering{arabic}") < document_body.index("\\paginaFolhaRosto")
    assert content.count("\\captionquadro{") == 11
    assert content.count("\\fonte{") == 26
    assert "\\listadequadros" in content
    assert "\\listadetabelas" in content
    assert "\\captiontabela{Resultados da validação externa por projeto}" in content
    assert "\\resizebox{\\textwidth}{!}" not in content


def test_canonical_tcc_does_not_restore_unsupported_claims():
    content = SOURCE.read_text(encoding="utf-8")

    for unsupported in (
        "processo irreversível pelo qual os dados perdem qualquer possibilidade",
        "por natureza, lidam com dados pessoais sensíveis",
        "custos são sistematicamente maiores",
        "área ainda incipiente no contexto brasileiro",
        "Relatório de atividades 2023",
        "(CAVOUKIAN, 2009)",
    ):
        assert unsupported not in content

    for required in (
        "Westin, 1967, p. 7",
        "Brasil, 2018, arts. 5º, XI, e 12",
        "Relatório de Ciclo de Monitoramento}: 1º semestre de 2023",
        "evaluation/real_projects/projects.json",
    ):
        assert required in content


def test_canonical_tcc_follows_advisor_review_october_2026():
    content = SOURCE.read_text(encoding="utf-8")

    assert "\\chapter*{INTRODUÇÃO}" in content
    assert "\\chapter{INTRODUÇÃO}" not in content
    assert "\\chapter{METODOLOGIA}" not in content
    assert "\\secaointro{Metodologia}" in content
    assert "segurança de software." in content
    assert "a pesquisa foi orientada pela seguinte pergunta-problema" in content
    assert "\\item foram revisados os fundamentos teóricos" in content
    assert "label=\\alph*)" in content
    for chapter in ("\\chapter{TECNOLOGIAS}", "\\chapter{REQUISITOS}", "\\chapter{RESULTADOS}"):
        assert chapter in content
    assert content.index("\\chapter{TECNOLOGIAS}") < content.index("\\chapter{REQUISITOS}") < content.index("\\chapter{RESULTADOS}")
    for label in ("qua:rf", "qua:rnf", "qua:regras-deteccao", "qua:atendimento"):
        assert "\\label{%s}" % label in content

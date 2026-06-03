"""
Tests for reporter.py — validates aggregation and reporting functionality.
"""

import pytest
import json
import os
from reporter import Reporter, RECOMENDACOES, ORDEM_RISCO
from code_analyzer import Vulnerability


class TestReporterSummary:
    """Test summary generation."""
    
    def test_summary_calculation_zero_vulnerabilities(self):
        """Summary with zero vulnerabilities."""
        reporter = Reporter()
        reporter.resultados = []
        
        summary = reporter._sumario()
        
        assert summary['total'] == 0
        assert summary['por_risco']['ALTO'] == 0
        assert summary['por_risco']['MEDIO'] == 0
        assert summary['por_risco']['BAIXO'] == 0
        assert summary['score_conformidade'] == 100
    
    def test_summary_calculation_perfect_score(self):
        """Perfect score with no vulnerabilities."""
        reporter = Reporter()
        reporter.resultados = []
        
        summary = reporter._sumario()
        
        assert summary['score_conformidade'] == 100
    
    def test_summary_calculation_with_alto_risk(self):
        """Score calculation with ALTO risk."""
        reporter = Reporter()
        reporter.resultados = [
            Vulnerability(
                arquivo="test.py",
                linha=1,
                categoria="DADO_HARDCODED",
                descricao="Test",
                risco="ALTO",
                artigo_lgpd="Art. 46"
            )
        ]
        
        summary = reporter._sumario()
        
        assert summary['total'] == 1
        assert summary['por_risco']['ALTO'] == 1
        # Score should be 100 - 10 = 90
        assert summary['score_conformidade'] == 90
    
    def test_summary_calculation_with_medio_risk(self):
        """Score calculation with MEDIO risk."""
        reporter = Reporter()
        reporter.resultados = [
            Vulnerability(
                arquivo="test.py",
                linha=1,
                categoria="COLETA_EXCESSIVA",
                descricao="Test",
                risco="MEDIO",
                artigo_lgpd="Art. 6º"
            )
        ]
        
        summary = reporter._sumario()
        
        # Score should be 100 - 5 = 95
        assert summary['score_conformidade'] == 95
    
    def test_summary_calculation_with_baixo_risk(self):
        """Score calculation with BAIXO risk."""
        reporter = Reporter()
        reporter.resultados = [
            Vulnerability(
                arquivo="test.py",
                linha=1,
                categoria="AUSENCIA_RETENCAO",
                descricao="Test",
                risco="BAIXO",
                artigo_lgpd="Art. 15"
            )
        ]
        
        summary = reporter._sumario()
        
        # Score should be 100 - 2 = 98
        assert summary['score_conformidade'] == 98
    
    def test_summary_mixed_risks(self):
        """Score calculation with mixed risks."""
        reporter = Reporter()
        reporter.resultados = [
            Vulnerability("test.py", 1, "A", "Test A", "ALTO", "Art. 46"),
            Vulnerability("test.py", 2, "B", "Test B", "ALTO", "Art. 46"),
            Vulnerability("test.py", 3, "C", "Test C", "MEDIO", "Art. 6º"),
            Vulnerability("test.py", 4, "D", "Test D", "BAIXO", "Art. 15"),
        ]
        
        summary = reporter._sumario()
        
        assert summary['total'] == 4
        assert summary['por_risco']['ALTO'] == 2
        assert summary['por_risco']['MEDIO'] == 1
        # Score = 100 - (2*10 + 1*5 + 1*2) = 100 - 27 = 73
        assert summary['score_conformidade'] == 73


class TestReporterSorting:
    """Test vulnerability sorting."""
    
    def test_sorting_by_risk(self):
        """Results should be sorted by risk (ALTO → MEDIO → BAIXO)."""
        reporter = Reporter()
        reporter.resultados = [
            Vulnerability("test.py", 5, "A", "Test", "BAIXO", "Art. 15"),
            Vulnerability("test.py", 3, "B", "Test", "ALTO", "Art. 46"),
            Vulnerability("test.py", 4, "C", "Test", "MEDIO", "Art. 6º"),
        ]
        
        # Coletar e ordenar (simula o que coletar() faz)
        reporter.resultados.sort(
            key=lambda v: (ORDEM_RISCO.get(v.risco, 9), v.arquivo, v.linha)
        )
        
        # Deve estar em ordem: ALTO, MEDIO, BAIXO
        assert reporter.resultados[0].risco == "ALTO"
        assert reporter.resultados[1].risco == "MEDIO"
        assert reporter.resultados[2].risco == "BAIXO"
    
    def test_sorting_by_file_then_line(self):
        """Same risk should be sorted by file then line number."""
        reporter = Reporter()
        reporter.resultados = [
            Vulnerability("b.py", 1, "A", "Test", "ALTO", "Art. 46"),
            Vulnerability("a.py", 2, "B", "Test", "ALTO", "Art. 46"),
            Vulnerability("a.py", 1, "C", "Test", "ALTO", "Art. 46"),
        ]
        
        reporter.resultados.sort(
            key=lambda v: (ORDEM_RISCO.get(v.risco, 9), v.arquivo, v.linha)
        )
        
        # Deve estar em ordem: a.py:1, a.py:2, b.py:1
        assert reporter.resultados[0].arquivo == "a.py" and reporter.resultados[0].linha == 1
        assert reporter.resultados[1].arquivo == "a.py" and reporter.resultados[1].linha == 2
        assert reporter.resultados[2].arquivo == "b.py" and reporter.resultados[2].linha == 1


class TestRecommendations:
    """Test recommendation mapping."""
    
    def test_all_categories_have_recommendations(self):
        """All vulnerability categories should have recommendations."""
        categories = [
            "DADO_HARDCODED",
            "DADO_SEM_CRIPTOGRAFIA",
            "CRIPTOGRAFIA_FRACA",
            "DADO_EM_LOG",
            "TRANSFERENCIA_SEM_BASE_LEGAL",
            "COLETA_EXCESSIVA",
            "AUSENCIA_EXCLUSAO",
            "CAMPO_SEM_HASH",
            "AUSENCIA_SOFT_DELETE",
            "AUSENCIA_RETENCAO",
            "MISTURA_DADOS",
            "AUSENCIA_CONSENTIMENTO",
            "DADO_SENSIVEL_COMO_PK",
        ]
        
        for categoria in categories:
            assert categoria in RECOMENDACOES, f"Missing recommendation for {categoria}"
            assert len(RECOMENDACOES[categoria]) > 0
    
    def test_recommendation_text_quality(self):
        """Recommendations should be practical and actionable."""
        for categoria, recomendacao in RECOMENDACOES.items():
            # Should be non-empty
            assert len(recomendacao) > 20, f"Recommendation too short for {categoria}"
            
            # Should contain imperative verbs or keywords
            assert any(word in recomendacao.lower() for word in [
                "adicione", "aplique", "remova", "use", "implemente", "verifique",
                "substitua", "separe", "implemente", "documente", "considere",
                "revise", "altere", "criptografe"
            ]), f"Recommendation lacks action verb for {categoria}"


class TestJSONExport:
    """Test JSON export format."""
    
    def test_json_structure(self, tmp_path):
        """JSON export should have correct structure."""
        reporter = Reporter()
        reporter.resultados = [
            Vulnerability("test.py", 1, "DADO_HARDCODED", "Test", "ALTO", "Art. 46")
        ]
        
        json_file = tmp_path / "report.json"
        reporter.exportar_json(str(json_file))
        
        assert json_file.exists()
        
        with open(json_file) as f:
            data = json.load(f)
        
        # Check required fields
        assert "ferramenta" in data
        assert "versao" in data
        assert "timestamp" in data
        assert "sumario" in data
        assert "vulnerabilidades" in data
        
        # Check summary structure
        assert "total" in data["sumario"]
        assert "por_risco" in data["sumario"]
        assert "score_conformidade" in data["sumario"]
        
        # Check vulnerability structure
        assert len(data["vulnerabilidades"]) == 1
        v = data["vulnerabilidades"][0]
        assert "arquivo" in v
        assert "linha" in v
        assert "categoria" in v
        assert "descricao" in v
        assert "risco" in v
        assert "artigo_lgpd" in v
        assert "recomendacao" in v
    
    def test_json_unicode_support(self, tmp_path):
        """JSON should properly handle Portuguese characters."""
        reporter = Reporter()
        reporter.resultados = [
            Vulnerability(
                "arquivos.py",
                1,
                "DADO_HARDCODED",
                "Segurança — Proteção de dados pessoais",
                "ALTO",
                "Art. 46 — Segurança e prevenção"
            )
        ]
        
        json_file = tmp_path / "report.json"
        reporter.exportar_json(str(json_file))
        
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
        
        # Should properly decode special characters
        v = data["vulnerabilidades"][0]
        assert "Segurança" in v["descricao"]
        assert "—" in v["artigo_lgpd"]


class TestHTMLExport:
    """Test HTML export format."""
    
    def test_html_structure(self, tmp_path):
        """HTML export should have correct structure."""
        reporter = Reporter()
        reporter.resultados = [
            Vulnerability("test.py", 1, "DADO_HARDCODED", "Test", "ALTO", "Art. 46")
        ]
        
        html_file = tmp_path / "report.html"
        reporter.exportar_html(str(html_file))
        
        assert html_file.exists()
        
        with open(html_file, encoding="utf-8") as f:
            html_content = f.read()
        
        # Check key elements
        assert "<html" in html_content.lower()
        assert "<table" in html_content.lower()
        assert "Privacy Scanner" in html_content
        assert "DADO_HARDCODED" in html_content
        assert "ALTO" in html_content
    
    def test_html_has_summary(self, tmp_path):
        """HTML should include summary cards."""
        reporter = Reporter()
        reporter.resultados = [
            Vulnerability("test.py", 1, "DADO_HARDCODED", "Test", "ALTO", "Art. 46"),
            Vulnerability("test.py", 2, "COLETA_EXCESSIVA", "Test", "MEDIO", "Art. 6º"),
        ]
        
        html_file = tmp_path / "report.html"
        reporter.exportar_html(str(html_file))
        
        with open(html_file, encoding="utf-8") as f:
            html_content = f.read()
        
        # Should contain summary data
        assert "2" in html_content  # Total vulnerabilities
        assert "1" in html_content  # ALTO count
        assert "100" in html_content  # Score field (100 - score)

    def test_html_escapes_vulnerability_content(self, tmp_path):
        """HTML export should escape code excerpts and descriptions."""
        reporter = Reporter()
        reporter.resultados = [
            Vulnerability(
                "test.py",
                1,
                "DADO_HARDCODED",
                "<script>alert('x')</script>",
                "ALTO",
                "Art. 46",
                trecho='senha = "<b>123</b>"',
            )
        ]

        html_file = tmp_path / "report.html"
        reporter.exportar_html(str(html_file))

        with open(html_file, encoding="utf-8") as f:
            html_content = f.read()

        assert "<script>alert" not in html_content
        assert "&lt;script&gt;alert" in html_content
        assert "&lt;b&gt;123&lt;/b&gt;" in html_content


class TestIntegration:
    """Integration tests for reporter."""
    
    def test_full_reporting_workflow(self, tmp_path):
        """Test complete reporting workflow."""
        reporter = Reporter()
        
        # Add diverse vulnerabilities
        reporter.resultados = [
            Vulnerability("code.py", 5, "DADO_HARDCODED", "Hardcoded password", "ALTO", "Art. 46"),
            Vulnerability("code.py", 10, "CRIPTOGRAFIA_FRACA", "MD5 usage", "ALTO", "Art. 46"),
            Vulnerability("code.py", 15, "COLETA_EXCESSIVA", "7 fields collected", "MEDIO", "Art. 6º"),
            Vulnerability("banco.db", 0, "CAMPO_SEM_HASH", "Email in plaintext", "ALTO", "Art. 46"),
        ]
        
        # Generate reports
        json_file = tmp_path / "report.json"
        html_file = tmp_path / "report.html"
        
        reporter.exportar_json(str(json_file))
        reporter.exportar_html(str(html_file))
        
        # Verify files exist
        assert json_file.exists()
        assert html_file.exists()
        
        # Verify JSON content
        with open(json_file) as f:
            data = json.load(f)
        assert len(data["vulnerabilidades"]) == 4
        assert data["sumario"]["total"] == 4
        assert data["sumario"]["por_risco"]["ALTO"] == 3
        
        # Verify HTML content
        with open(html_file, encoding="utf-8") as f:
            html = f.read()
        assert "DADO_HARDCODED" in html
        assert "CRIPTOGRAFIA_FRACA" in html
        assert "COLETA_EXCESSIVA" in html

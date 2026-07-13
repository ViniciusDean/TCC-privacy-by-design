"""
Tests for db_analyzer.py — detects privacy vulnerabilities in SQLite schemas.
"""

import os
import pytest
import sqlite3
from db_analyzer import DBAnalyzer, analisar_banco, analisar_banco_com_escopo
from analysis_profile import apply_profile, parse_profile


def test_sqlite_presets_filter_contextual_medium_confidence(tmp_path):
    database = tmp_path / "profile.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE usuarios (id INTEGER, cidade TEXT)")
    connection.commit()
    connection.close()
    raw = analisar_banco(str(database))
    medium = [item for item in raw if item.confianca == "MEDIA"]

    assert medium
    assert not apply_profile(medium, parse_profile())
    assert apply_profile(medium, parse_profile({"preset": "equilibrado"}))


class TestDBAnalyzerBasic:
    """Test basic database vulnerability detection."""
    
    def test_detects_sensitive_field_plaintext(self, temp_db_file):
        """Should detect sensitive field in plaintext (CAMPO_SEM_HASH)."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        # Create table with sensitive field in plaintext
        cur.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                email TEXT,
                senha TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        assert any(v.categoria == "CAMPO_SEM_HASH" for v in results)
        assert any(v.risco in ["ALTO", "MEDIO"] for v in results)
    
    def test_detects_missing_soft_delete(self, temp_db_file):
        """Should detect missing soft-delete column (AUSENCIA_SOFT_DELETE)."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        # Create table without deleted_at or is_deleted
        cur.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                email TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        soft_delete_findings = [
            v for v in results if v.categoria == "AUSENCIA_SOFT_DELETE"
        ]
        assert soft_delete_findings
        assert all(v.risco == "MEDIO" for v in soft_delete_findings)
        assert any("Art. 18" in v.artigo_lgpd for v in soft_delete_findings)
        assert any("Tabela: usuarios" == v.trecho for v in soft_delete_findings)
    
    def test_detects_missing_retention_policy(self, temp_db_file):
        """Should detect missing retention column (AUSENCIA_RETENCAO)."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        # Create table with personal data but without retention column
        cur.execute('''
            CREATE TABLE logs_acesso (
                id INTEGER PRIMARY KEY,
                email TEXT,
                ip_address TEXT,
                deleted_at TIMESTAMP,
                consentimento BOOLEAN
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        retention_findings = [
            v for v in results if v.categoria == "AUSENCIA_RETENCAO"
        ]
        assert retention_findings
        assert all(v.risco == "BAIXO" for v in retention_findings)
        assert any("Art. 15" in v.artigo_lgpd for v in retention_findings)
        assert any("logs_acesso" in v.trecho for v in retention_findings)
    
    def test_detects_missing_consent_column(self, temp_db_file):
        """Should detect missing consent column (AUSENCIA_CONSENTIMENTO)."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        # Create table with personal data but no consent column
        cur.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                email TEXT,
                cpf TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        # Sem coluna de consentimento, deve alertar
        consent_findings = [
            v for v in results if v.categoria == "AUSENCIA_CONSENTIMENTO"
        ]
        assert consent_findings
        assert any("base legal" in v.descricao.lower() for v in consent_findings)
    
    def test_detects_sensitive_as_primary_key(self, temp_db_file):
        """Should detect sensitive field as primary key (DADO_SENSIVEL_COMO_PK)."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        # Create table with CPF as PK (wrong!)
        cur.execute('''
            CREATE TABLE usuarios (
                cpf TEXT PRIMARY KEY,
                nome TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        assert any(v.categoria == "DADO_SENSIVEL_COMO_PK" for v in results)


class TestCorrectSchema:
    """Test that correct schemas don't trigger alerts."""
    
    def test_correct_schema_no_alerts(self, temp_db_file):
        """Correctly designed schema should have minimal/no alerts."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        # Create correct schema
        cur.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                email_hash TEXT,
                created_at TIMESTAMP,
                deleted_at TIMESTAMP,
                lgpd_aceito BOOLEAN,
                lgpd_aceito_em TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        # Não deve ter alertas graves
        high_risk = [v for v in results if v.risco == "ALTO"]
        assert len(high_risk) == 0
    
    def test_mixed_data_separation_correct(self, temp_db_file):
        """Properly separated personal data should not trigger MISTURA_DADOS."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        # Create separated tables
        cur.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                deleted_at TIMESTAMP
            )
        ''')
        
        cur.execute('''
            CREATE TABLE usuarios_dados_pessoais (
                usuario_id INTEGER PRIMARY KEY,
                email_hash TEXT,
                cpf_hash TEXT,
                lgpd_aceito BOOLEAN
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        # Dados separados não devem gerar MISTURA_DADOS
        assert not any(v.categoria == "MISTURA_DADOS" for v in results)

    def test_hashed_personal_data_still_requires_retention_control(
        self,
        temp_db_file,
    ):
        """Hash protects storage but does not remove governance obligations."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE contatos (
                id INTEGER PRIMARY KEY,
                email_hash TEXT,
                deleted_at TIMESTAMP,
                consentimento BOOLEAN
            )
        ''')
        conn.commit()
        conn.close()

        results = analisar_banco(temp_db_file)

        assert not any(v.categoria == "CAMPO_SEM_HASH" for v in results)
        assert any(v.categoria == "AUSENCIA_RETENCAO" for v in results)


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_empty_database(self, temp_db_file):
        """Should handle empty database gracefully."""
        conn = sqlite3.connect(temp_db_file)
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        # Should not crash
        assert isinstance(results, list)
    
    def test_multiple_tables(self, temp_db_file):
        """Should analyze all tables in database."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        # Create multiple tables
        cur.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                email TEXT
            )
        ''')
        
        cur.execute('''
            CREATE TABLE pedidos (
                id INTEGER PRIMARY KEY,
                cpf TEXT
            )
        ''')
        
        cur.execute('''
            CREATE TABLE configuracoes (
                chave TEXT,
                valor TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        # Should detect vulnerabilities in multiple tables
        assert len(results) > 0
    
    def test_special_characters_in_columns(self, temp_db_file):
        """Should handle columns with special characters."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                "e_mail" TEXT,
                "CPF" TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        plaintext_fields = [
            v for v in results if v.categoria == "CAMPO_SEM_HASH"
        ]
        assert {v.trecho for v in plaintext_fields} >= {
            "usuarios.e_mail : TEXT",
            "usuarios.CPF : TEXT",
        }

    def test_sqlite_is_opened_read_only_without_mutating_file(self, temp_db_file):
        with sqlite3.connect(temp_db_file) as conn:
            conn.execute("CREATE TABLE contatos (id INTEGER PRIMARY KEY, email TEXT)")

        antes = os.stat(temp_db_file)
        analisar_banco(temp_db_file)
        depois = os.stat(temp_db_file)

        assert depois.st_size == antes.st_size
        assert depois.st_mtime_ns == antes.st_mtime_ns
        assert not os.path.exists(f"{temp_db_file}-journal")

    def test_identifier_tokens_support_camel_case_and_quoted_names(self, temp_db_file):
        with sqlite3.connect(temp_db_file) as conn:
            conn.execute(
                'CREATE TABLE "usuarios""auditoria" ('
                'id INTEGER PRIMARY KEY, "userEmail" TEXT, "base_legal" TEXT)'
            )

        resultados = analisar_banco(temp_db_file)
        categorias = {resultado.categoria for resultado in resultados}

        assert "CAMPO_SEM_HASH" in categorias
        assert "AUSENCIA_CONSENTIMENTO" not in categorias

    def test_tokenization_does_not_match_partial_identifier(self, temp_db_file):
        with sqlite3.connect(temp_db_file) as conn:
            conn.execute("CREATE TABLE metadados (id INTEGER PRIMARY KEY, agent TEXT)")

        resultados = analisar_banco(temp_db_file)

        assert resultados == []

    def test_corrupt_database_is_auditable_failure(self, tmp_path):
        database = tmp_path / "corrompido.db"
        database.write_bytes(b"not a sqlite database")

        resultados, escopo = analisar_banco_com_escopo(str(database))

        assert resultados == []
        assert escopo["status"] == "failed"
        assert escopo["arquivos_falhos"] == 1
        assert escopo["erros"][0]["codigo"] == "BANCO_INVALIDO"


class TestArtigos:
    """Test LGPD article mapping for database."""
    
    def test_sensitive_field_references_art_46(self, temp_db_file):
        """Sensitive field in plaintext should reference Art. 46."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                cpf TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        assert any("Art. 46" in v.artigo_lgpd for v in results)
    
    def test_missing_deletion_references_art_18(self, temp_db_file):
        """Missing soft-delete should reference Art. 18 IV."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                email TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        soft_delete_missing = [v for v in results if v.categoria == "AUSENCIA_SOFT_DELETE"]
        assert soft_delete_missing
        assert any("Art. 18" in v.artigo_lgpd for v in soft_delete_missing)
        assert any("schema" in v.descricao.lower() for v in soft_delete_missing)
    
    def test_missing_consent_references_art_7(self, temp_db_file):
        """Missing consent should reference Art. 7º."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                nome TEXT,
                email TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        consent_missing = [v for v in results if v.categoria == "AUSENCIA_CONSENTIMENTO"]
        assert consent_missing
        assert any("Art. 7º" in v.artigo_lgpd for v in consent_missing)
        assert any("bases legais" in v.artigo_lgpd.lower() for v in consent_missing)


class TestIntegration:
    """Integration tests for database analysis."""
    
    def test_complete_database_audit(self, temp_db_file):
        """Test complete audit of a database."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        # Create realistic but vulnerable schema
        cur.execute('''
            CREATE TABLE usuarios (
                cpf TEXT PRIMARY KEY,
                nome TEXT,
                email TEXT,
                telefone TEXT,
                endereco TEXT,
                senha_md5 TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        cur.execute('''
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY,
                usuario_cpf TEXT,
                acao TEXT,
                data TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        # Should detect multiple vulnerabilities
        assert len(results) > 0
        
        # Check for expected issues
        categories = {v.categoria for v in results}
        
        # CPF como PK é problema
        assert "DADO_SENSIVEL_COMO_PK" in categories
        
        # Todos devem ter artigos LGPD
        assert all(v.artigo_lgpd for v in results)


def test_generic_name_requires_personal_table_context(tmp_path):
    database = tmp_path / "context.db"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE Artist (ArtistId INTEGER PRIMARY KEY, Name TEXT);
        CREATE TABLE Customer (
            CustomerId INTEGER PRIMARY KEY,
            Name TEXT,
            Address TEXT,
            Email TEXT
        );
        """
    )
    connection.close()

    results = analisar_banco(str(database))
    descriptions = [item.descricao for item in results]
    assert not any("Artist" in description for description in descriptions)
    assert any("Customer" in description for description in descriptions)

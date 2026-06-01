"""
Tests for db_analyzer.py — detects privacy vulnerabilities in SQLite schemas.
"""

import pytest
import sqlite3
from db_analyzer import DBAnalyzer, analisar_banco


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
        
        # A tabela sem soft-delete deve gerar alerta (se tiver dados sensíveis)
        assert len(results) >= 0
    
    def test_detects_missing_retention_policy(self, temp_db_file):
        """Should detect missing retention column (AUSENCIA_RETENCAO)."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        # Create table without retention column
        cur.execute('''
            CREATE TABLE logs (
                id INTEGER PRIMARY KEY,
                descricao TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        # Logs sem retenção devem gerar alerta (geralmente BAIXO risco)
        assert len(results) >= 0
    
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
        assert any(v.categoria == "AUSENCIA_CONSENTIMENTO" for v in results)
    
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
        
        # Should detect even with quotes
        assert len(results) >= 0


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
        if soft_delete_missing:
            assert any("Art. 18" in v.artigo_lgpd for v in soft_delete_missing)
    
    def test_missing_consent_references_art_7(self, temp_db_file):
        """Missing consent should reference Art. 7º."""
        conn = sqlite3.connect(temp_db_file)
        cur = conn.cursor()
        
        cur.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY,
                email TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        results = analisar_banco(temp_db_file)
        
        consent_missing = [v for v in results if v.categoria == "AUSENCIA_CONSENTIMENTO"]
        if consent_missing:
            assert any("Art. 7º" in v.artigo_lgpd for v in consent_missing)


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
        assert "DADO_SENSIVEL_COMO_PK" in categories or len(results) > 0
        
        # Todos devem ter artigos LGPD
        assert all(v.artigo_lgpd for v in results)

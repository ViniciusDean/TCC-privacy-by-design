"""
Tests for code_analyzer.py — detects privacy vulnerabilities in Python code.
"""

import pytest
from code_analyzer import CodeAnalyzer, analisar_arquivo, analisar_diretorio


class TestCodeAnalyzerBasic:
    """Test basic vulnerability detection."""
    
    def test_detects_hardcoded_password(self, temp_py_file):
        """Should detect hardcoded password (DADO_HARDCODED)."""
        code = 'senha = "minhasenha123"\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert len(results) > 0
        assert any(v.categoria == "DADO_HARDCODED" for v in results)
        assert any(v.risco == "ALTO" for v in results)
    
    def test_detects_hardcoded_cpf(self, temp_py_file):
        """Should detect hardcoded CPF."""
        code = 'cpf = "123.456.789-00"\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert any(v.categoria == "DADO_HARDCODED" for v in results)
    
    def test_ignores_empty_initialization(self, temp_py_file):
        """Should NOT flag empty string initialization (Bug 1 fix)."""
        code = '''
class Usuario:
    nome = ""
    email = ""
    cpf = ""
'''
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        # Não deve ter DADO_HARDCODED para inicializações vazias
        hardcoded = [v for v in results if v.categoria == "DADO_HARDCODED"]
        assert len(hardcoded) == 0
    
    def test_detects_weak_crypto_md5(self, temp_py_file):
        """Should detect MD5 (weak cryptography)."""
        code = 'import hashlib\nhash_passwd = hashlib.md5(password.encode()).hexdigest()\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert any(v.categoria == "CRIPTOGRAFIA_FRACA" for v in results)
        assert any(v.risco == "ALTO" for v in results)
    
    def test_detects_weak_crypto_sha1(self, temp_py_file):
        """Should detect SHA1 (weak cryptography)."""
        code = 'import hashlib\nhash = hashlib.sha1(data.encode()).hexdigest()\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert any(v.categoria == "CRIPTOGRAFIA_FRACA" for v in results)
    
    def test_detects_data_in_log(self, temp_py_file):
        """Should detect personal data in logs (DADO_EM_LOG)."""
        code = 'import logging\nlogging.info(f"CPF: {cpf}")\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert any(v.categoria == "DADO_EM_LOG" for v in results)
        assert any(v.risco == "ALTO" for v in results)
    
    def test_detects_print_with_data(self, temp_py_file):
        """Should detect personal data in print statements."""
        code = 'print(f"Email: {email}")\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert any(v.categoria == "DADO_EM_LOG" for v in results)
    
    def test_detects_data_transfer_without_legal_basis(self, temp_py_file):
        """Should detect personal data transfer to third-party."""
        code = 'import requests\nrequests.post("https://api.com", json={"cpf": cpf})\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert any(v.categoria == "TRANSFERENCIA_SEM_BASE_LEGAL" for v in results)
        assert any(v.risco == "ALTO" for v in results)
    
    def test_detects_excessive_collection(self, temp_py_file):
        """Should detect excessive data collection (4+ fields)."""
        code = 'def cadastro(nome, email, cpf, telefone, nascimento):\n    pass\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert any(v.categoria == "COLETA_EXCESSIVA" for v in results)
        assert any(v.risco == "MEDIO" for v in results)
    
    def test_detects_missing_deletion_method(self, temp_py_file):
        """Should detect class with sensitive data but no delete method."""
        code = '''
class Usuario:
    nome = "João"
    email = "joao@test.com"
    cpf = "123.456.789-00"
    
    def salvar(self):
        pass
'''
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert any(v.categoria == "AUSENCIA_EXCLUSAO" for v in results)
        assert any(v.risco == "MEDIO" for v in results)


class TestWordBoundary:
    """Test word boundary fix (Bug 2)."""
    
    def test_word_boundary_age_in_user_agent(self, temp_py_file):
        """Should NOT flag 'age' when it's part of 'user_agent'."""
        code = 'user_agent = "Mozilla/5.0"\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        # Não deve detectar nada, pois 'age' é parte de 'user_agent', não isolado
        assert len(results) == 0
    
    def test_word_boundary_age_in_message(self, temp_py_file):
        """Should NOT flag 'age' in 'message_age'."""
        code = 'message_age = "Mensagem"\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert len(results) == 0
    
    def test_word_boundary_age_isolated(self, temp_py_file):
        """Should flag 'age' when it's an isolated field."""
        code = 'age = input("Digite a idade: ")\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        # Deve detectar 'age' como campo sensível
        assert any(v.categoria == "DADO_SEM_CRIPTOGRAFIA" for v in results)
    
    def test_word_boundary_average_age(self, temp_py_file):
        """Should NOT flag 'age' in 'average_age'."""
        code = 'average_age = 35\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert len(results) == 0

    def test_constructor_parameter_assignment_no_alert(self, temp_py_file):
        """Should not flag model fields assigned from constructor parameters."""
        code = '''
class Usuario:
    nome = ""
    email = ""
    cpf = ""

    def __init__(self, nome: str, email: str, cpf: str):
        self.nome = nome
        self.email = email
        self.cpf = cpf

    def anonimizar(self):
        self.nome = "Anonimo"
        self.email = "anonimo@anon.com"
        self.cpf = "000.000.000-00"
'''
        temp_py_file.write(code)
        temp_py_file.flush()

        results = analisar_arquivo(temp_py_file.name)

        assert len(results) == 0

    def test_technical_ip_address_log_no_alert(self, temp_py_file):
        """Should not flag technical user_agent/ip_address logging."""
        code = '''
import logging
def registrar_acesso(user_agent: str, ip_address: str):
    logging.info(f"Novo acesso: user_agent={user_agent}, ip={ip_address}")
'''
        temp_py_file.write(code)
        temp_py_file.flush()

        results = analisar_arquivo(temp_py_file.name)

        assert len(results) == 0

    def test_detects_sensitive_snake_case_prefixes(self, temp_py_file):
        """Should detect sensitive fields embedded as snake_case tokens."""
        code = '''
cpf_usuario = input("CPF: ")
email_cliente = input("Email: ")
'''
        temp_py_file.write(code)
        temp_py_file.flush()

        results = analisar_arquivo(temp_py_file.name)

        assert sum(1 for v in results if v.categoria == "DADO_SEM_CRIPTOGRAFIA") == 2

    def test_detects_personal_context_for_ambiguous_name(self, temp_py_file):
        """Should flag ambiguous fields when the variable context is personal."""
        code = 'user_name = input("Nome: ")\n'
        temp_py_file.write(code)
        temp_py_file.flush()

        results = analisar_arquivo(temp_py_file.name)

        assert any(v.categoria == "DADO_SEM_CRIPTOGRAFIA" for v in results)

    def test_ignores_ambiguous_internal_metadata_assignments(self, temp_py_file):
        """Should not treat variables that manipulate identifiers as personal data."""
        code = '''
def normalizar(nome):
    nome_lower = nome.lower()
    nome = None
    nome = target.id
    nome_chamada = obter_nome_chamada()
'''
        temp_py_file.write(code)
        temp_py_file.flush()

        results = analisar_arquivo(temp_py_file.name)

        assert not any(v.categoria == "DADO_SEM_CRIPTOGRAFIA" for v in results)

    def test_ignores_generic_name_literal_and_log(self, temp_py_file):
        """Generic metadata called name is not necessarily personal data."""
        code = '''
name = "bash"
print("NAMEMATCH", name)
'''
        temp_py_file.write(code)
        temp_py_file.flush()

        results = analisar_arquivo(temp_py_file.name)

        assert results == []

    def test_ignores_generic_class_with_name_field(self, temp_py_file):
        """Technical classes should not require personal-data deletion methods."""
        code = '''
class Lexer:
    name = "Python"

    def compile(self):
        self.name = obter_nome()
'''
        temp_py_file.write(code)
        temp_py_file.flush()

        results = analisar_arquivo(temp_py_file.name)

        assert results == []

    def test_detects_ambiguous_model_attribute_assignment(self, temp_py_file):
        """Should keep detecting ambiguous fields stored on model attributes."""
        code = '''
class Usuario:
    def carregar(self):
        self.nome = buscar_valor()
'''
        temp_py_file.write(code)
        temp_py_file.flush()

        results = analisar_arquivo(temp_py_file.name)

        assert any(v.categoria == "DADO_SEM_CRIPTOGRAFIA" for v in results)


class TestNoFalsePositives:
    """Test that correct code doesn't trigger false positives."""
    
    def test_bcrypt_no_alert(self, temp_py_file):
        """Should NOT flag bcrypt usage."""
        code = '''
import bcrypt
hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
'''
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        # Não deve detectar vulnerabilidades
        assert len(results) == 0
    
    def test_delete_method_no_alert(self, temp_py_file):
        """Should NOT flag class with delete method."""
        code = '''
class Usuario:
    nome = "João"
    
    def delete(self):
        pass
'''
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        # Não deve detectar AUSENCIA_EXCLUSAO
        assert not any(v.categoria == "AUSENCIA_EXCLUSAO" for v in results)
    
    def test_generic_logging_no_alert(self, temp_py_file):
        """Should NOT flag generic logging without personal data."""
        code = '''
import logging
logging.info("Operacao concluida com sucesso")
'''
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        # Não deve detectar DADO_EM_LOG
        assert not any(v.categoria == "DADO_EM_LOG" for v in results)
    
    def test_technical_ids_no_alert(self, temp_py_file):
        """Should NOT flag technical IDs without personal data."""
        code = '''
import logging
logging.info(f"User ID: {user_id}")
requests.post("https://api.com", json={"user_id": user_id})
'''
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        # Não deve detectar vulnerabilidades
        assert len(results) == 0


class TestArtigos:
    """Test LGPD article mapping."""
    
    def test_hardcoded_references_art_46(self, temp_py_file):
        """Hardcoded data should reference Art. 46."""
        code = 'senha = "123"\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert any("Art. 46" in v.artigo_lgpd for v in results)
    
    def test_data_in_log_references_multiple_articles(self, temp_py_file):
        """Data in logs should reference Art. 46 and Art. 6º III."""
        code = 'import logging\nlogging.info(f"CPF: {cpf}")\n'
        temp_py_file.write(code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        assert any(v.categoria == "DADO_EM_LOG" for v in results)
        v = [v for v in results if v.categoria == "DADO_EM_LOG"][0]
        assert "Art. 46" in v.artigo_lgpd
        assert "Art. 6º" in v.artigo_lgpd


class TestDirectory:
    """Test directory analysis."""
    
    def test_analyze_multiple_files(self, tmp_path):
        """Should analyze all .py files in directory."""
        # Create test files
        file1 = tmp_path / "vulnerable.py"
        file1.write_text('senha = "123"\n')
        
        file2 = tmp_path / "correct.py"
        file2.write_text('import bcrypt\n')
        
        results = analisar_diretorio(str(tmp_path))
        
        # Should detect vulnerability in file1
        assert len(results) > 0
        assert any("vulnerable.py" in v.arquivo for v in results)

    def test_ignores_dependencies_builds_and_packaged_backend(self, tmp_path):
        """Project analysis must not scan generated or third-party source."""
        (tmp_path / "app.py").write_text(
            'cpf = "123.456.789-00"\n',
            encoding="utf-8",
        )
        ignored_files = [
            tmp_path / ".venv" / "Lib" / "site-packages" / "dependency.py",
            tmp_path / "venv" / "dependency.py",
            tmp_path / "node_modules" / "package.py",
            tmp_path / "build" / "generated.py",
            tmp_path / "dist" / "generated.py",
            tmp_path / "vscode-extension" / "python_backend" / "code_analyzer.py",
        ]
        for path in ignored_files:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('password = "secret123"\n', encoding="utf-8")

        results = analisar_diretorio(str(tmp_path))

        assert len(results) == 1
        assert results[0].arquivo.endswith("app.py")

    def test_respects_privacyignore_file_and_directory_patterns(self, tmp_path):
        """Projects can exclude intentional fixtures from full scans."""
        (tmp_path / ".privacyignore").write_text(
            "fixtures/\nexemplo_vulneravel.py\n",
            encoding="utf-8",
        )
        (tmp_path / "app.py").write_text(
            'cpf = "123.456.789-00"\n',
            encoding="utf-8",
        )
        (tmp_path / "exemplo_vulneravel.py").write_text(
            'password = "secret123"\n',
            encoding="utf-8",
        )
        fixture = tmp_path / "fixtures" / "dados.py"
        fixture.parent.mkdir()
        fixture.write_text('email = "teste@exemplo.com"\n', encoding="utf-8")

        results = analisar_diretorio(str(tmp_path))

        assert len(results) == 1
        assert results[0].arquivo.endswith("app.py")

    def test_privacyignore_does_not_block_individual_analysis(self, tmp_path):
        """Ignored files remain available for deliberate single-file demos."""
        arquivo = tmp_path / "exemplo_vulneravel.py"
        arquivo.write_text('password = "secret123"\n', encoding="utf-8")
        (tmp_path / ".privacyignore").write_text(
            "exemplo_vulneravel.py\n",
            encoding="utf-8",
        )

        results = analisar_arquivo(str(arquivo))

        assert any(v.categoria == "DADO_HARDCODED" for v in results)


class TestIntegration:
    """Integration tests."""

    def test_analyzer_does_not_flag_its_own_internal_assignments(self):
        """The analyzer implementation should not trigger its assignment rule."""
        results = analisar_arquivo("code_analyzer.py")

        assert not any(v.categoria == "DADO_SEM_CRIPTOGRAFIA" for v in results)
    
    def test_full_analysis_flow(self, sample_vulnerable_code, temp_py_file):
        """Test full analysis from code to results."""
        temp_py_file.write(sample_vulnerable_code)
        temp_py_file.flush()
        
        results = analisar_arquivo(temp_py_file.name)
        
        # Should detect multiple vulnerabilities
        assert len(results) >= 5
        
        # Check for key vulnerabilities
        categories = {v.categoria for v in results}
        assert "DADO_HARDCODED" in categories
        assert "CRIPTOGRAFIA_FRACA" in categories
        assert "DADO_EM_LOG" in categories
        assert "TRANSFERENCIA_SEM_BASE_LEGAL" in categories
        
        # All should have articles
        assert all(v.artigo_lgpd for v in results)
        
        # All should have descriptions
        assert all(v.descricao for v in results)

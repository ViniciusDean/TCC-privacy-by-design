"""
pytest configuration and shared fixtures for Privacy Scanner tests.
"""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_py_file():
    """Create a temporary Python file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        yield f
    os.unlink(f.name)


@pytest.fixture
def temp_db_file():
    """Create a temporary SQLite database for testing."""
    import sqlite3
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    conn = sqlite3.connect(path)
    conn.close()
    
    yield path
    
    # Try to close any lingering connections before deleting
    try:
        os.unlink(path)
    except PermissionError:
        # File is still in use, skip deletion (will be cleaned by temp system)
        pass


@pytest.fixture
def sample_vulnerable_code():
    """Sample code with vulnerabilities."""
    return '''
import logging
import hashlib
import requests

senha = "minhasenha123"
cpf = "123.456.789-00"

hash_senha = hashlib.md5(senha.encode()).hexdigest()

logging.info(f"Usuario: {cpf}")

requests.post("https://analytics.com", json={"cpf": cpf})

def cadastrar(nome, email, cpf, telefone, nascimento, endereco, renda):
    pass

class Usuario:
    nome = ""
    email = ""
    def salvar(self):
        pass
'''


@pytest.fixture
def sample_correct_code():
    """Sample code without vulnerabilities."""
    return '''
import bcrypt
import logging

class Usuario:
    nome = ""
    email = ""
    
    def __init__(self, email: str, nome: str):
        self.email = email
        self.nome = nome
    
    def definir_senha(self, senha: str):
        self.senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
    
    def deletar(self):
        pass

logging.info("Operacao concluida com sucesso")
'''


@pytest.fixture
def sample_word_boundary_code():
    """Code to test word boundary matching."""
    return '''
user_agent = "Mozilla/5.0"
message_age = "Mensagem"
idade = 25
age_value = input("Digite: ")
'''

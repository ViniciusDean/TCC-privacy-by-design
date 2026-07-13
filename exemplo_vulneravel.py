"""
exemplo_vulneravel.py
Arquivo de teste com vulnerabilidades de privacidade propositais.
NÃO usar em produção — apenas para demonstrar o analisador.
"""
import hashlib
import logging
import requests


class Model:
    """Marcador local para manter o exemplo executável sem depender de um ORM."""


# ── Vulnerabilidade 1: dado hardcoded ───────────────────────────────────────
senha = "minhasenha123"         # ALTO — dado pessoal fixo no código
cpf   = "123.456.789-00"        # ALTO — CPF hardcoded

# ── Vulnerabilidade 2: criptografia fraca ───────────────────────────────────
hash_senha = hashlib.md5(senha.encode()).hexdigest()   # ALTO — md5 é fraco

# ── Vulnerabilidade 3: dado pessoal em log ──────────────────────────────────
logging.info(f"Usuário autenticado: {cpf}")            # ALTO — CPF no log

# ── Vulnerabilidade 4: transferência sem base legal ─────────────────────────
requests.post(
    "https://analytics.exemplo.com/track",
    json={"cpf": cpf, "email": "user@mail.com"}        # ALTO — dado enviado
)


# ── Vulnerabilidade 5: coleta excessiva ─────────────────────────────────────
def cadastrar_usuario(nome, email, cpf, telefone, nascimento, endereco, renda):
    pass   # MEDIO — 7 campos sensíveis, provável coleta excessiva


# ── Vulnerabilidade 6: classe sem método de exclusão ───────────────────────
class Usuario(Model):
    nome      = ""
    email     = ""
    cpf       = ""
    senha     = ""

    def salvar(self):
        pass

    def buscar(self):
        pass
    # Sem delete(), excluir() ou anonimizar() → MEDIO

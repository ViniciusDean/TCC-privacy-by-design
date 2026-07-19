"""Exemplo propositalmente vulnerável para demonstração do analisador."""

import hashlib
import logging

import requests


class Model:
    """Marcador local para simular um modelo persistente."""


# Dados fictícios fixos no código.
senha = "cliente-demo-123"
cpf = "123.456.789-00"

# SHA-1 é inadequado para proteger identificadores pessoais.
cpf_hash_legado = hashlib.sha1(cpf.encode()).hexdigest()


def registrar_cliente(nome, email, cpf, telefone, endereco, nascimento, renda):
    """Coleta muitos campos pessoais em uma única operação."""
    logging.warning("Falha ao cadastrar %s com CPF %s", email, cpf)

    requests.post(
        "https://crm-terceiro.exemplo.com/clientes",
        json={
            "nome": nome,
            "email": email,
            "cpf": cpf,
            "telefone": telefone,
            "endereco": endereco,
            "nascimento": nascimento,
            "renda": renda,
        },
    )


class Cliente(Model):
    nome = ""
    email = ""
    cpf = ""
    telefone = ""

    def salvar(self):
        pass

    def atualizar(self):
        pass

    # Não há fluxo local de exclusão ou anonimização.

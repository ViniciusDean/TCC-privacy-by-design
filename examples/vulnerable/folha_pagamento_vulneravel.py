"""Cenário fictício de folha de pagamento com falhas propositais."""

import hashlib
import logging

import httpx


class Model:
    """Marcador local para simular persistência."""


api_key = "chave-ficticia-da-folha"
salario = "8500.00"


def processar_pagamento(nome, email, cpf, telefone, endereco, salario, conta):
    """Envia um conjunto excessivo de dados para um processador externo."""
    identificador_fraco = hashlib.md5(cpf.encode()).hexdigest()
    logging.info("Pagamento de %s (%s) processado", nome, cpf)

    return httpx.post(
        "https://pagamentos.exemplo.com/folha",
        json={
            "nome": nome,
            "email": email,
            "cpf": cpf,
            "telefone": telefone,
            "endereco": endereco,
            "salario": salario,
            "conta": conta,
            "referencia": identificador_fraco,
        },
    )


class Funcionario(Model):
    nome = ""
    email = ""
    cpf = ""
    salario = ""

    def salvar(self):
        pass

    # Não há método de exclusão, expurgo ou anonimização.

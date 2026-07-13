"""
db_analyzer.py
Módulo de análise de esquemas de banco de dados SQLite orientado à detecção
de indícios técnicos de risco à privacidade conforme os princípios do
Privacy by Design e os requisitos da Lei Geral de Proteção de Dados Pessoais
(LGPD).
"""

import sqlite3
import os
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from code_analyzer import (
    codigo_erro_analise,
    finalizar_escopo_varredura,
    mensagem_erro_analise,
    novo_escopo_varredura,
    registrar_erro_escopo,
)


# ─────────────────────────────────────────────────────────────────────────────
# Estrutura de vulnerabilidade (mesma do code_analyzer para compatibilidade)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Vulnerability:
    arquivo:     str
    linha:       int             # usamos 0 para banco (não há linha)
    categoria:   str
    descricao:   str
    risco:       str             # "ALTO" | "MEDIO" | "BAIXO"
    artigo_lgpd: str
    trecho:      Optional[str] = None  # "tabela.coluna : TIPO"
    confianca:   str = "ALTA"
    risco_base:  Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Palavras-chave que indicam dado pessoal sensível em nomes de coluna/tabela
# ─────────────────────────────────────────────────────────────────────────────
CAMPOS_SENSIVEIS = [
    "senha", "password", "passwd", "pwd", "hash",
    "cpf", "rg", "cnpj", "passaporte", "documento",
    "email", "e_mail", "telefone", "celular", "phone", "contato",
    "nome", "name", "sobrenome", "lastname",
    "endereco", "address", "logradouro", "cep", "bairro", "cidade",
    "nascimento", "birth", "idade", "age",
    "cartao", "card", "credit", "credito", "cvv", "pan",
    "token", "secret", "api_key", "apikey", "chave",
    "saude", "health", "diagnostico", "cid", "prescricao",
    "salario", "salary", "renda", "income", "banco",
    "religiao", "etnia", "raca", "orientacao", "biometria",
    "ip_address", "ip_addr", "user_agent", "geolocal",
    "foto", "imagem", "avatar", "selfie",
]

# Tipos de coluna que indicam dado em texto puro (suspeito para campos sensíveis)
TIPOS_TEXTO = ["TEXT", "VARCHAR", "CHAR", "CLOB", "STRING", "NVARCHAR"]

# Sufixos que indicam hash/criptografia aplicada (OK)
SUFIXOS_HASH = ["_hash", "_encrypted", "_hashed", "_cifrado", "_digest"]

# Colunas que indicam controle de exclusão / soft delete
COLUNAS_EXCLUSAO = [
    "deleted_at", "deletado_em", "excluido_em",
    "removed_at", "is_deleted", "ativo", "active",
    "anonymized", "anonimizado",
]

# Colunas que indicam controle de retenção / validade
COLUNAS_RETENCAO = [
    "expires_at", "expira_em", "validade", "valid_until",
    "retention_date", "data_retencao", "purge_at",
]

# Colunas de consentimento (ausência em tabelas com dados pessoais é suspeita)
COLUNAS_CONSENTIMENTO = [
    "consentimento", "consent", "aceite", "aceito",
    "lgpd_aceito", "privacy_accepted", "optin",
]

COLUNAS_BASE_LEGAL = [
    "base_legal", "baselegal", "legal_basis", "legalbasis",
    "fundamento_legal", "fundamentolegal", "hipotese_legal",
]

MARCADORES_PROTECAO = {
    "hash", "hashed", "encrypt", "encrypted", "cipher", "cifrado",
    "criptografado", "tokenized", "tokenizado", "pseudonymized",
    "pseudonimizado",
}

TABELAS_PESSOAIS = {
    "user", "usuario", "customer", "cliente", "client", "employee",
    "funcionario", "person", "pessoa", "owner", "patient", "paciente",
    "contact", "contato", "account", "conta", "member", "membro",
    "users", "usuarios", "customers", "clientes", "clients", "employees",
    "funcionarios", "people", "pessoas", "owners", "patients", "pacientes",
    "contacts", "contatos", "accounts", "contas", "members", "membros",
}
CAMPOS_DEPENDENTES_CONTEXTO = {
    "name", "nome", "lastname", "sobrenome", "address", "endereco",
    "city", "cidade", "postal", "postalcode", "cep", "phone", "telefone",
    "birth", "birthdate", "nascimento", "age", "idade",
}


def _tokens_identificador(nome: str) -> list[str]:
    """Normaliza snake_case e camelCase para evitar correspondência parcial."""
    separado = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", nome)
    separado = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", separado)
    return [
        token for token in re.split(r"[^a-z0-9]+|_", separado.lower()) if token
    ]


def _identificador_sql_seguro(nome: str) -> str:
    """Escapa identificadores SQLite para PRAGMA sem interpolar SQL bruto."""
    if not isinstance(nome, str) or not nome or "\x00" in nome:
        raise ValueError("Identificador SQLite inválido.")
    return '"' + nome.replace('"', '""') + '"'


# ─────────────────────────────────────────────────────────────────────────────
# Analisador principal
# ─────────────────────────────────────────────────────────────────────────────
class DBAnalyzer:

    def __init__(self, caminho_db: str):
        self.caminho    = caminho_db
        self.resultados: list[Vulnerability] = []
        # O modo `ro` impede criação de banco, journal ou qualquer alteração
        # acidental durante a inspeção do schema.
        uri_ro = f"{Path(caminho_db).resolve().as_uri()}?mode=ro"
        self.conn       = sqlite3.connect(uri_ro, uri=True)
        self.conn.execute("PRAGMA query_only = ON")
        self.cur        = self.conn.cursor()

    def _adicionar(self, categoria, descricao, risco, artigo, trecho="", confianca="ALTA"):
        self.resultados.append(Vulnerability(
            arquivo=self.caminho,
            linha=0,
            categoria=categoria,
            descricao=descricao,
            risco=risco,
            artigo_lgpd=artigo,
            trecho=trecho,
            confianca=confianca,
        ))

    def _tabela_pessoal(self, tabela: str) -> bool:
        return any(token in TABELAS_PESSOAIS for token in _tokens_identificador(tabela))

    def _campo_pessoal(self, nome: str, tabela: str | None = None) -> Optional[str]:
        nome_lower = nome.lower()
        tokens = _tokens_identificador(nome)
        normalizado = "_".join(tokens)
        for campo in CAMPOS_SENSIVEIS:
            campo_tokens = _tokens_identificador(campo)
            campo_normalizado = "_".join(campo_tokens)
            if nome_lower == campo or normalizado == campo_normalizado:
                if (
                    tabela is not None
                    and campo_normalizado in CAMPOS_DEPENDENTES_CONTEXTO
                    and not self._tabela_pessoal(tabela)
                ):
                    continue
                return campo
            if campo in tokens:
                if (
                    tabela is not None
                    and campo_normalizado in CAMPOS_DEPENDENTES_CONTEXTO
                    and not self._tabela_pessoal(tabela)
                ):
                    continue
                return campo
        return None

    def _campo_sensivel(self, nome: str, tabela: str | None = None) -> Optional[str]:
        tokens = _tokens_identificador(nome)
        if (
            any(nome.lower().endswith(s) for s in SUFIXOS_HASH)
            or any(token in MARCADORES_PROTECAO for token in tokens)
        ):
            return None
        return self._campo_pessoal(nome, tabela)

    def _tabelas(self) -> list[str]:
        self.cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [r[0] for r in self.cur.fetchall()]

    def _colunas(self, tabela: str) -> list[dict]:
        self.cur.execute(f"PRAGMA table_info({_identificador_sql_seguro(tabela)})")
        rows = self.cur.fetchall()
        # cid, name, type, notnull, dflt_value, pk
        return [
            {"cid": r[0], "name": r[1], "type": r[2].upper(),
             "notnull": r[3], "pk": r[5]}
            for r in rows
        ]

    def _indices(self, tabela: str) -> list[str]:
        self.cur.execute(f"PRAGMA index_list({_identificador_sql_seguro(tabela)})")
        indices = self.cur.fetchall()
        nomes = []
        for idx in indices:
            self.cur.execute(f"PRAGMA index_info({_identificador_sql_seguro(idx[1])})")
            for col in self.cur.fetchall():
                nomes.append(col[2])
        return nomes

    # ── Regra 1: campo sensível em texto puro sem hash ───────────────────────
    def _verificar_criptografia(self, tabela: str, colunas: list[dict]):
        for col in colunas:
            campo = self._campo_sensivel(col["name"], tabela)
            if not campo:
                continue
            tipo = col["type"]
            eh_texto = any(tipo.startswith(t) for t in TIPOS_TEXTO)
            if eh_texto:
                # Casos especialmente graves: senha, cpf, cartão
                graves = ["senha", "password", "passwd", "pwd",
                          "cpf", "cartao", "card", "cvv"]
                risco = "ALTO" if campo in graves else "MEDIO"
                confianca = "ALTA" if campo in graves else "MEDIA"
                self._adicionar(
                    "CAMPO_SEM_HASH",
                    f"Coluna '{col['name']}' (campo sensível: '{campo}') "
                    f"armazenada como {tipo} sem indicação, no schema, de "
                    f"hash, criptografia ou pseudonimização. Se a proteção já "
                    f"existir em outra camada, documente-a ou use nomenclatura "
                    f"que evidencie o controle aplicado.",
                    risco,
                    "Art. 46 — Segurança e prevenção",
                    f"{tabela}.{col['name']} : {tipo}",
                    confianca,
                )

    # ── Regra 2: tabela com dados pessoais sem coluna de exclusão ────────────
    def _verificar_exclusao(self, tabela: str, colunas: list[dict]):
        nomes_colunas = [c["name"].lower() for c in colunas]
        tem_sensivel  = any(self._campo_pessoal(n, tabela) for n in nomes_colunas)
        tem_exclusao  = any(ex in nomes_colunas for ex in COLUNAS_EXCLUSAO)

        if tem_sensivel and not tem_exclusao:
            self._adicionar(
                "AUSENCIA_SOFT_DELETE",
                f"Tabela '{tabela}' contém dados pessoais, mas o schema não "
                f"evidencia coluna de exclusão lógica ou anonimização "
                f"(ex: deleted_at, is_deleted, anonimizado). Verifique se o "
                f"atendimento ao direito de eliminação existe em outra camada.",
                "MEDIO",
                "Art. 18, IV — Direito à eliminação dos dados",
                f"Tabela: {tabela}",
                "MEDIA",
            )

    # ── Regra 3: tabela com dados pessoais sem controle de retenção ──────────
    def _verificar_retencao(self, tabela: str, colunas: list[dict]):
        nomes_colunas = [c["name"].lower() for c in colunas]
        tem_sensivel  = any(self._campo_pessoal(n, tabela) for n in nomes_colunas)
        tem_retencao  = any(r in nomes_colunas for r in COLUNAS_RETENCAO)

        if tem_sensivel and not tem_retencao:
            self._adicionar(
                "AUSENCIA_RETENCAO",
                f"Tabela '{tabela}' contém dados pessoais, mas o schema não "
                f"evidencia controle de retenção ou expurgo "
                f"(ex: expires_at, data_retencao). Verifique se a política de "
                f"retenção é aplicada por rotina externa ou regra de negócio.",
                "BAIXO",
                "Art. 15 — Término do tratamento | Art. 6º, I — Finalidade",
                f"Tabela: {tabela}",
                "BAIXA",
            )

    # ── Regra 4: mistura de dados pessoais com dados operacionais ────────────
    def _verificar_separacao(self, tabela: str, colunas: list[dict]):
        """
        Detecta tabelas que misturam muitos campos sensíveis com campos
        operacionais (status, created_at, updated_at etc.), indicando
        ausência de separação de dados.
        """
        campos_sensiveis  = [c for c in colunas if self._campo_pessoal(c["name"], tabela)]
        campos_operacionais = [
            c for c in colunas
            if any(op in c["name"].lower()
                   for op in ["status", "created", "updated", "flag",
                               "tipo", "type", "code", "codigo"])
        ]

        if len(campos_sensiveis) >= 3 and len(campos_operacionais) >= 3:
            nomes_sens = ", ".join(c["name"] for c in campos_sensiveis[:4])
            self._adicionar(
                "MISTURA_DADOS",
                f"Tabela '{tabela}' mistura {len(campos_sensiveis)} campos "
                f"sensíveis ({nomes_sens}...) com dados operacionais. "
                f"Considere separar dados pessoais em tabela dedicada para "
                f"facilitar controle de acesso e exclusão.",
                "BAIXO",
                "Art. 46 — Segurança | Princípio Privacy by Design — Separação",
                f"Tabela: {tabela}",
                "MEDIA",
            )

    # ── Regra 5: ausência de consentimento em tabela de usuários ─────────────
    def _verificar_consentimento(self, tabela: str, colunas: list[dict]):
        """
        Em tabelas que parecem ser de usuários/clientes (contêm email, cpf,
        nome), verifica se há coluna que registre consentimento ou outra base
        legal operacionalizada no schema.
        """
        nomes_colunas = [c["name"].lower() for c in colunas]
        indicadores_usuario = ["email", "cpf", "nome", "name", "usuario", "user"]
        eh_tabela_usuario = sum(
            1 for ind in indicadores_usuario if any(ind in n for n in nomes_colunas)
        ) >= 2

        tem_base_legal = any(
            nome in COLUNAS_CONSENTIMENTO or nome in COLUNAS_BASE_LEGAL
            for nome in nomes_colunas
        )

        if eh_tabela_usuario and not tem_base_legal:
            self._adicionar(
                "AUSENCIA_CONSENTIMENTO",
                f"Tabela '{tabela}' parece armazenar dados de usuários/clientes, "
                f"mas o schema não evidencia consentimento ou outra base legal "
                f"operacionalizada (ex: lgpd_aceito, base_legal, optin). "
                f"O Art. 7º prevê diferentes bases legais; confirme qual se "
                f"aplica à finalidade do tratamento.",
                "MEDIO",
                "Art. 7º — Bases legais para tratamento de dados pessoais",
                f"Tabela: {tabela}",
                "BAIXA",
            )

    # ── Regra 6: campo sensível exposto sem índice de controle ───────────────
    def _verificar_exposicao_indice(self, tabela: str, colunas: list[dict]):
        """
        CPF, email e similares usados como chave primária ou índice único
        podem facilitar correlação entre sistemas (linkability).
        """
        for col in colunas:
            campo = self._campo_pessoal(col["name"], tabela)
            if not campo:
                continue
            if col["pk"] == 1:
                self._adicionar(
                    "DADO_SENSIVEL_COMO_PK",
                    f"Coluna '{col['name']}' (campo: '{campo}') usada como "
                    f"chave primária. Dados pessoais como PK facilitam "
                    f"correlação entre tabelas (linkability). "
                    f"Prefira um ID técnico (UUID ou inteiro autoincrement).",
                    "MEDIO",
                    "Art. 46 — Segurança | Princípio Privacy by Design — Linkability",
                    f"{tabela}.{col['name']} : PK",
                )

    # ── Execução de todas as regras ──────────────────────────────────────────
    def analisar(self) -> list[Vulnerability]:
        try:
            tabelas = self._tabelas()

            for tabela in tabelas:
                colunas = self._colunas(tabela)
                self._verificar_criptografia(tabela, colunas)
                self._verificar_exclusao(tabela, colunas)
                self._verificar_retencao(tabela, colunas)
                self._verificar_separacao(tabela, colunas)
                self._verificar_consentimento(tabela, colunas)
                self._verificar_exposicao_indice(tabela, colunas)

            return self.resultados
        finally:
            self.conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Função pública de entrada
# ─────────────────────────────────────────────────────────────────────────────
def analisar_banco(caminho: str) -> list[Vulnerability]:
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Banco não encontrado: {caminho}")
    return DBAnalyzer(caminho).analisar()


def analisar_banco_com_escopo(caminho: str) -> tuple[list[Vulnerability], dict]:
    """Analisa um SQLite em modo somente leitura e registra falhas seguras."""
    if not isinstance(caminho, (str, os.PathLike)) or not str(caminho).strip():
        raise ValueError("O caminho do banco é obrigatório.")
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Banco não encontrado: {caminho}")

    escopo = novo_escopo_varredura(caminho, "banco")
    escopo["arquivos_elegiveis"] = 1
    if os.path.getsize(caminho) == 0:
        return [], finalizar_escopo_varredura(escopo)

    try:
        resultados = analisar_banco(caminho)
    except (OSError, ValueError, sqlite3.Error) as erro:
        registrar_erro_escopo(escopo, caminho, erro)
        if isinstance(erro, sqlite3.Error):
            escopo["erros"][-1].update({
                "codigo": "BANCO_INVALIDO",
                "mensagem": "O arquivo não contém um banco SQLite analisável.",
            })
        return [], finalizar_escopo_varredura(escopo)

    escopo["arquivos_analisados"] = 1
    return resultados, finalizar_escopo_varredura(escopo)


# ─────────────────────────────────────────────────────────────────────────────
# Execução direta
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import json

    alvo = sys.argv[1] if len(sys.argv) > 1 else "exemplo.db"
    try:
        resultados, escopo = analisar_banco_com_escopo(alvo)
    except (FileNotFoundError, ValueError) as erro:
        codigo = codigo_erro_analise(erro)
        print(json.dumps({
            "success": False,
            "status": "invalid",
            "error": {"codigo": codigo, "mensagem": mensagem_erro_analise(codigo)},
            "indicador_tecnico": None,
        }, ensure_ascii=False))
        sys.exit(2)

    if escopo["status"] not in {"complete", "partial"}:
        print(json.dumps({
            "success": False,
            "status": escopo["status"],
            "escopo": escopo,
            "indicador_tecnico": None,
        }, ensure_ascii=False))
        sys.exit(2)

    print(json.dumps({
        "success": True,
        "status": escopo["status"],
        "escopo": escopo,
        "achados": [
            {
                "arquivo": v.arquivo,
                "linha": v.linha,
                "categoria": v.categoria,
                "risco": v.risco,
                "evidencia_segura": "Regra de schema acionada; detalhes originais ocultados.",
            }
            for v in resultados
        ],
    }, ensure_ascii=False, indent=2))

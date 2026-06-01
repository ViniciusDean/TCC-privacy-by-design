"""
db_analyzer.py
Módulo de análise de esquemas de banco de dados SQLite orientado à detecção
de vulnerabilidades de privacidade conforme os princípios do Privacy by Design
e os requisitos da Lei Geral de Proteção de Dados Pessoais (LGPD).
"""

import sqlite3
import os
import re
from dataclasses import dataclass
from typing import Optional


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


# ─────────────────────────────────────────────────────────────────────────────
# Analisador principal
# ─────────────────────────────────────────────────────────────────────────────
class DBAnalyzer:

    def __init__(self, caminho_db: str):
        self.caminho    = caminho_db
        self.resultados: list[Vulnerability] = []
        self.conn       = sqlite3.connect(caminho_db)
        self.cur        = self.conn.cursor()

    def _adicionar(self, categoria, descricao, risco, artigo, trecho=""):
        self.resultados.append(Vulnerability(
            arquivo=self.caminho,
            linha=0,
            categoria=categoria,
            descricao=descricao,
            risco=risco,
            artigo_lgpd=artigo,
            trecho=trecho,
        ))

    def _campo_sensivel(self, nome: str) -> Optional[str]:
        nome_lower = nome.lower()
        # Ignora se já tem sufixo de hash/criptografia
        if any(nome_lower.endswith(s) for s in SUFIXOS_HASH):
            return None
        for campo in CAMPOS_SENSIVEIS:
            if campo in nome_lower:
                return campo
        return None

    def _tabelas(self) -> list[str]:
        self.cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [r[0] for r in self.cur.fetchall()]

    def _colunas(self, tabela: str) -> list[dict]:
        self.cur.execute(f"PRAGMA table_info('{tabela}')")
        rows = self.cur.fetchall()
        # cid, name, type, notnull, dflt_value, pk
        return [
            {"cid": r[0], "name": r[1], "type": r[2].upper(),
             "notnull": r[3], "pk": r[5]}
            for r in rows
        ]

    def _indices(self, tabela: str) -> list[str]:
        self.cur.execute(f"PRAGMA index_list('{tabela}')")
        indices = self.cur.fetchall()
        nomes = []
        for idx in indices:
            self.cur.execute(f"PRAGMA index_info('{idx[1]}')")
            for col in self.cur.fetchall():
                nomes.append(col[2])
        return nomes

    # ── Regra 1: campo sensível em texto puro sem hash ───────────────────────
    def _verificar_criptografia(self, tabela: str, colunas: list[dict]):
        for col in colunas:
            campo = self._campo_sensivel(col["name"])
            if not campo:
                continue
            tipo = col["type"]
            eh_texto = any(tipo.startswith(t) for t in TIPOS_TEXTO)
            if eh_texto:
                # Casos especialmente graves: senha, cpf, cartão
                graves = ["senha", "password", "passwd", "pwd",
                          "cpf", "cartao", "card", "cvv"]
                risco = "ALTO" if campo in graves else "MEDIO"
                self._adicionar(
                    "CAMPO_SEM_HASH",
                    f"Coluna '{col['name']}' (campo sensível: '{campo}') "
                    f"armazenada como {tipo} sem indicação de hash/criptografia. "
                    f"Renomeie para '{col['name']}_hash' se já houver hash, "
                    f"ou aplique bcrypt/sha256 antes de persistir.",
                    risco,
                    "Art. 46 — Segurança e prevenção",
                    f"{tabela}.{col['name']} : {tipo}",
                )

    # ── Regra 2: tabela com dados pessoais sem coluna de exclusão ────────────
    def _verificar_exclusao(self, tabela: str, colunas: list[dict]):
        nomes_colunas = [c["name"].lower() for c in colunas]
        tem_sensivel  = any(self._campo_sensivel(n) for n in nomes_colunas)
        tem_exclusao  = any(ex in nomes_colunas for ex in COLUNAS_EXCLUSAO)

        if tem_sensivel and not tem_exclusao:
            self._adicionar(
                "AUSENCIA_SOFT_DELETE",
                f"Tabela '{tabela}' contém dados pessoais mas não possui coluna "
                f"de exclusão lógica (ex: deleted_at, is_deleted, anonimizado). "
                f"Sem esse controle, não é possível atender ao direito de "
                f"eliminação do titular.",
                "MEDIO",
                "Art. 18, IV — Direito à eliminação dos dados",
                f"Tabela: {tabela}",
            )

    # ── Regra 3: tabela com dados pessoais sem controle de retenção ──────────
    def _verificar_retencao(self, tabela: str, colunas: list[dict]):
        nomes_colunas = [c["name"].lower() for c in colunas]
        tem_sensivel  = any(self._campo_sensivel(n) for n in nomes_colunas)
        tem_retencao  = any(r in nomes_colunas for r in COLUNAS_RETENCAO)

        if tem_sensivel and not tem_retencao:
            self._adicionar(
                "AUSENCIA_RETENCAO",
                f"Tabela '{tabela}' contém dados pessoais mas não possui coluna "
                f"de controle de retenção (ex: expires_at, data_retencao). "
                f"Dados pessoais devem ser eliminados após o prazo necessário.",
                "BAIXO",
                "Art. 15 — Término do tratamento | Art. 6º, I — Finalidade",
                f"Tabela: {tabela}",
            )

    # ── Regra 4: mistura de dados pessoais com dados operacionais ────────────
    def _verificar_separacao(self, tabela: str, colunas: list[dict]):
        """
        Detecta tabelas que misturam muitos campos sensíveis com campos
        operacionais (status, created_at, updated_at etc.), indicando
        ausência de separação de dados.
        """
        campos_sensiveis  = [c for c in colunas if self._campo_sensivel(c["name"])]
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
            )

    # ── Regra 5: ausência de consentimento em tabela de usuários ─────────────
    def _verificar_consentimento(self, tabela: str, colunas: list[dict]):
        """
        Em tabelas que parecem ser de usuários/clientes (contêm email, cpf, nome),
        verifica se há coluna de consentimento LGPD.
        """
        nomes_colunas = [c["name"].lower() for c in colunas]
        indicadores_usuario = ["email", "cpf", "nome", "name", "usuario", "user"]
        eh_tabela_usuario = sum(
            1 for ind in indicadores_usuario if any(ind in n for n in nomes_colunas)
        ) >= 2

        tem_consentimento = any(c in nomes_colunas for c in COLUNAS_CONSENTIMENTO)

        if eh_tabela_usuario and not tem_consentimento:
            self._adicionar(
                "AUSENCIA_CONSENTIMENTO",
                f"Tabela '{tabela}' parece armazenar dados de usuários/clientes "
                f"mas não possui coluna de consentimento LGPD "
                f"(ex: lgpd_aceito, consentimento, optin). "
                f"O consentimento é uma das bases legais previstas no Art. 7º.",
                "MEDIO",
                "Art. 7º, I — Consentimento do titular",
                f"Tabela: {tabela}",
            )

    # ── Regra 6: campo sensível exposto sem índice de controle ───────────────
    def _verificar_exposicao_indice(self, tabela: str, colunas: list[dict]):
        """
        CPF, email e similares usados como chave primária ou índice único
        podem facilitar correlação entre sistemas (linkability).
        """
        for col in colunas:
            campo = self._campo_sensivel(col["name"])
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
        tabelas = self._tabelas()

        if not tabelas:
            return []

        for tabela in tabelas:
            colunas = self._colunas(tabela)
            self._verificar_criptografia(tabela, colunas)
            self._verificar_exclusao(tabela, colunas)
            self._verificar_retencao(tabela, colunas)
            self._verificar_separacao(tabela, colunas)
            self._verificar_consentimento(tabela, colunas)
            self._verificar_exposicao_indice(tabela, colunas)

        self.conn.close()
        return self.resultados


# ─────────────────────────────────────────────────────────────────────────────
# Função pública de entrada
# ─────────────────────────────────────────────────────────────────────────────
def analisar_banco(caminho: str) -> list[Vulnerability]:
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Banco não encontrado: {caminho}")
    return DBAnalyzer(caminho).analisar()


# ─────────────────────────────────────────────────────────────────────────────
# Execução direta
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    alvo = sys.argv[1] if len(sys.argv) > 1 else "exemplo.db"
    resultados = analisar_banco(alvo)

    if not resultados:
        print("✅  Nenhuma vulnerabilidade de privacidade encontrada.")
    else:
        print(f"\n⚠️  {len(resultados)} vulnerabilidade(s) encontrada(s):\n")
        for v in resultados:
            print(f"  [{v.risco}] {v.categoria}")
            print(f"  Banco   : {v.arquivo}")
            print(f"  LGPD    : {v.artigo_lgpd}")
            print(f"  Detalhe : {v.descricao}")
            if v.trecho:
                print(f"  Trecho  : {v.trecho}")
            print()

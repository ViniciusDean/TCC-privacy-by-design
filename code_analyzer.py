"""
code_analyzer.py
Módulo de análise estática de código-fonte orientado à detecção de
vulnerabilidades de privacidade conforme os princípios do Privacy by Design
e os requisitos da Lei Geral de Proteção de Dados Pessoais (LGPD).
"""

import ast
import re
import os
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Estrutura de uma vulnerabilidade encontrada
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Vulnerability:
    arquivo:    str
    linha:      int
    categoria:  str          # ex: "DADO_SEM_CRIPTOGRAFIA"
    descricao:  str          # mensagem legível
    risco:      str          # "ALTO" | "MEDIO" | "BAIXO"
    artigo_lgpd: str         # ex: "Art. 46 — Segurança"
    trecho:     Optional[str] = None   # linha do código original


# ─────────────────────────────────────────────────────────────────────────────
# Palavras-chave indicativas de dados pessoais sensíveis
# ─────────────────────────────────────────────────────────────────────────────
CAMPOS_SENSIVEIS = [
    "senha", "password", "passwd", "pwd",
    "cpf", "rg", "cnpj", "passaporte",
    "email", "e_mail", "telefone", "celular", "phone",
    "nome", "name", "endereco", "address",
    "nascimento", "birth", "idade", "age",
    "cartao", "card", "credit", "credito",
    "token", "secret", "api_key", "apikey",
    "saude", "health", "diagnostico", "diagnosis",
    "salario", "salary", "renda", "income",
    "religiao", "religion", "etnia", "ethnicity",
]

CAMPOS_AMBIGUOS = {"nome", "name", "idade", "age"}
CONTEXTO_PESSOAL = {
    "usuario", "user", "cliente", "customer", "pessoa", "person", "titular",
    "paciente", "patient", "funcionario", "employee",
}
CAMPOS_TECNICOS = {
    "ip_address", "ip_addr", "user_agent", "user_id", "session_id",
    "request_id", "trace_id",
}
METODOS_EXCLUSAO_ANONIMIZACAO = (
    "delete", "delet", "remov", "exclu", "anonimiz", "anonymiz", "purge",
)

# Funções de log mais comuns em Python
FUNCOES_LOG = [
    "print", "logging.debug", "logging.info",
    "logging.warning", "logging.error", "logging.critical",
    "logger.debug", "logger.info", "logger.warning",
    "logger.error", "logger.critical",
]

# Funções/padrões indicativos de criptografia (presença = OK)
FUNCOES_CRIPTOGRAFIA = [
    "hashlib", "bcrypt", "argon2", "pbkdf2",
    "sha256", "sha512", "md5",   # md5 é fraco, vai gerar aviso separado
    "encrypt", "cifrar", "AES", "RSA", "fernet",
    "make_password", "check_password",
]

CRIPTOGRAFIA_FRACA = ["md5", "sha1"]

# Serviços de terceiros que recebem dados
SERVICOS_TERCEIROS = [
    "requests.post", "requests.get", "requests.put",
    "httpx.post", "httpx.get",
    "urllib.request", "http.client",
    "boto3",       # AWS
    "firebase",
    "analytics",
    "mixpanel", "segment", "amplitude",
    "sendgrid", "mailchimp",
]


# ─────────────────────────────────────────────────────────────────────────────
# Analisador principal
# ─────────────────────────────────────────────────────────────────────────────
class CodeAnalyzer(ast.NodeVisitor):
    """
    Percorre a AST do Python em busca de padrões de vulnerabilidade de privacidade.
    Cada método visit_* trata um tipo de nó da árvore sintática.
    """

    def __init__(self, caminho_arquivo: str, codigo_fonte: str):
        self.caminho    = caminho_arquivo
        self.linhas     = codigo_fonte.splitlines()
        self.resultados: list[Vulnerability] = []
        self._pilha_funcoes: list[ast.FunctionDef] = []

    def visit(self, node):
        if isinstance(node, ast.FunctionDef):
            self._pilha_funcoes.append(node)
            try:
                return super().visit(node)
            finally:
                self._pilha_funcoes.pop()
        return super().visit(node)

    # ── Utilitários ──────────────────────────────────────────────────────────

    def _trecho(self, linha: int) -> str:
        """Retorna o texto da linha (1-indexado), truncado a 120 chars."""
        if 1 <= linha <= len(self.linhas):
            return self.linhas[linha - 1].strip()[:120]
        return ""

    def _adicionar(self, linha, categoria, descricao, risco, artigo):
        self.resultados.append(Vulnerability(
            arquivo=self.caminho,
            linha=linha,
            categoria=categoria,
            descricao=descricao,
            risco=risco,
            artigo_lgpd=artigo,
            trecho=self._trecho(linha),
        ))

    def _nome_contem_campo_sensivel(self, nome: str) -> Optional[str]:
        """Verifica se um nome de variável/atributo contém campo sensível.
        Usa tokens para evitar falsos positivos (ex: 'age' em 'user_agent').
        """
        nome_lower = nome.lower()
        if nome_lower in CAMPOS_TECNICOS:
            return None

        tokens = [t for t in re.split(r"[^a-z0-9]+|_", nome_lower) if t]
        if tokens and tokens[0] == "ip":
            return None

        for campo in CAMPOS_SENSIVEIS:
            if nome_lower == campo:
                return campo

            if campo not in CAMPOS_AMBIGUOS and campo in tokens:
                return campo

            if campo in CAMPOS_AMBIGUOS and campo in tokens:
                if tokens[0] == campo:
                    return campo
                if tokens[-1] == campo and any(t in CONTEXTO_PESSOAL for t in tokens[:-1]):
                    return campo
        return None

    def _funcao_atual(self) -> Optional[ast.FunctionDef]:
        return self._pilha_funcoes[-1] if self._pilha_funcoes else None

    def _em_funcao_exclusao_anonimizacao(self) -> bool:
        funcao = self._funcao_atual()
        if not funcao:
            return False
        nome = funcao.name.lower()
        return any(p in nome for p in METODOS_EXCLUSAO_ANONIMIZACAO)

    def _valor_e_parametro(self, nome: str, node: ast.Assign) -> bool:
        funcao = self._funcao_atual()
        if not funcao or not isinstance(node.value, ast.Name):
            return False
        parametros = {arg.arg for arg in funcao.args.args}
        return node.value.id == nome and node.value.id in parametros

    # ── Regra 1: variável com dado sensível atribuída como string simples ────

    def visit_Assign(self, node: ast.Assign):
        """
        Detecta padrões como:
            senha = "123456"
            cpf   = input(...)
        → dado pessoal armazenado sem criptografia aparente.
        """
        for target in node.targets:
            nome = None
            if isinstance(target, ast.Name):
                nome = target.id
            elif isinstance(target, ast.Attribute):
                nome = target.attr

            if nome:
                campo = self._nome_contem_campo_sensivel(nome)
                if campo:
                    if self._em_funcao_exclusao_anonimizacao():
                        continue
                    # Verifica se o valor é string literal (dado hardcoded)
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        # Ignora atribuições vazias (inicializações) — não é dado real
                        if node.value.value == "":
                            pass
                        else:
                            self._adicionar(
                                node.lineno,
                                "DADO_HARDCODED",
                                f"Campo sensível '{campo}' recebe valor literal "
                                f"(dado pessoal fixo no código).",
                                "ALTO",
                                "Art. 46 — Segurança e prevenção"
                            )
                    else:
                        if self._valor_e_parametro(nome, node):
                            continue
                        # Atribuição normal — verifica se há criptografia na mesma linha
                        trecho = self._trecho(node.lineno).lower()
                        tem_cripto = any(c in trecho for c in FUNCOES_CRIPTOGRAFIA)
                        if not tem_cripto:
                            self._adicionar(
                                node.lineno,
                                "DADO_SEM_CRIPTOGRAFIA",
                                f"Campo '{campo}' recebe dado pessoal sem indício "
                                f"de criptografia ou hash.",
                                "MEDIO",
                                "Art. 46 — Segurança e prevenção"
                            )

        self.generic_visit(node)

    # ── Regra 2: uso de criptografia fraca ───────────────────────────────────

    def visit_Attribute(self, node: ast.Attribute):
        """
        Detecta: hashlib.md5(...), hashlib.sha1(...)
        """
        if isinstance(node.value, ast.Name) and node.value.id == "hashlib":
            if node.attr in CRIPTOGRAFIA_FRACA:
                self._adicionar(
                    node.lineno,
                    "CRIPTOGRAFIA_FRACA",
                    f"Uso de algoritmo fraco: hashlib.{node.attr}(). "
                    f"Para senhas use bcrypt ou argon2; para integridade use sha256+.",
                    "ALTO",
                    "Art. 46 — Segurança e prevenção"
                )
        self.generic_visit(node)

    # ── Regra 3: dados pessoais em logs ──────────────────────────────────────

    def visit_Call(self, node: ast.Call):
        """
        Detecta chamadas de log/print com variáveis de campos sensíveis:
            logging.info(f"usuário: {cpf}")
            print(senha)
        """
        # Monta o nome completo da chamada (ex: "logging.info")
        nome_chamada = self._nome_call(node)

        # ── 3a: dado sensível passado diretamente para log ──
        if any(nome_chamada.startswith(log) for log in FUNCOES_LOG):
            for arg in node.args:
                variaveis = self._extrair_nomes(arg)
                for var in variaveis:
                    campo = self._nome_contem_campo_sensivel(var)
                    if campo:
                        self._adicionar(
                            node.lineno,
                            "DADO_EM_LOG",
                            f"Dado pessoal '{campo}' registrado em log/print. "
                            f"Logs com dados identificáveis violam o princípio "
                            f"da minimização.",
                            "ALTO",
                            "Art. 46 — Segurança | Art. 6º, III — Necessidade"
                        )
                        break  # um aviso por chamada é suficiente

        # ── 3b: transferência de dados para serviço externo ──
        if any(nome_chamada.startswith(svc) for svc in SERVICOS_TERCEIROS):
            # Verifica se há campos sensíveis nos kwargs (json=, data=, params=)
            for kw in node.keywords:
                if kw.arg in ("json", "data", "params", "body"):
                    variaveis = self._extrair_nomes(kw.value)
                    for var in variaveis:
                        campo = self._nome_contem_campo_sensivel(var)
                        if campo:
                            self._adicionar(
                                node.lineno,
                                "TRANSFERENCIA_SEM_BASE_LEGAL",
                                f"Campo '{campo}' enviado para serviço externo "
                                f"({nome_chamada}). Verifique se há base legal "
                                f"documentada para esta transferência.",
                                "ALTO",
                                "Art. 7º — Hipóteses de tratamento | "
                                "Art. 33 — Transferência internacional"
                            )
                            break

        self.generic_visit(node)

    # ── Regra 4: coleta excessiva via input / formulário ─────────────────────

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Detecta funções cujos parâmetros acumulam muitos campos sensíveis,
        indicando possível coleta excessiva.
        """
        campos_encontrados = []
        for arg in node.args.args:
            campo = self._nome_contem_campo_sensivel(arg.arg)
            if campo:
                campos_encontrados.append(campo)

        if len(campos_encontrados) >= 4:
            self._adicionar(
                node.lineno,
                "COLETA_EXCESSIVA",
                f"Função '{node.name}' recebe {len(campos_encontrados)} campos "
                f"sensíveis ({', '.join(campos_encontrados)}). Verifique se todos "
                f"são estritamente necessários para a finalidade.",
                "MEDIO",
                "Art. 6º, III — Necessidade | Art. 6º, I — Finalidade"
            )

        self.generic_visit(node)

    # ── Regra 5: ausência de mecanismo de exclusão ───────────────────────────

    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Em classes que parecem modelos de dados (contêm campos sensíveis),
        verifica se há algum método de exclusão/anonimização definido.
        """
        campos_na_classe = []
        metodos = []

        for item in node.body:
            if isinstance(item, ast.Assign):
                for t in item.targets:
                    nome = t.id if isinstance(t, ast.Name) else (
                        t.attr if isinstance(t, ast.Attribute) else "")
                    if self._nome_contem_campo_sensivel(nome):
                        campos_na_classe.append(nome)
            if isinstance(item, ast.FunctionDef):
                metodos.append(item.name.lower())

        if campos_na_classe:
            tem_exclusao = any(
                p in m for m in metodos
                for p in ["delete", "remov", "exclu", "anonimiz", "anonymiz", "purge"]
            )
            if not tem_exclusao:
                self._adicionar(
                    node.lineno,
                    "AUSENCIA_EXCLUSAO",
                    f"Classe '{node.name}' contém campos sensíveis "
                    f"({', '.join(campos_na_classe[:3])}) mas não define "
                    f"método de exclusão ou anonimização.",
                    "MEDIO",
                    "Art. 18, IV — Direito à eliminação dos dados"
                )

        self.generic_visit(node)

    # ── Auxiliares ───────────────────────────────────────────────────────────

    def _nome_call(self, node: ast.Call) -> str:
        """Retorna o nome completo de uma chamada como string."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            partes = []
            atual = node.func
            while isinstance(atual, ast.Attribute):
                partes.append(atual.attr)
                atual = atual.value
            if isinstance(atual, ast.Name):
                partes.append(atual.id)
            return ".".join(reversed(partes))
        return ""

    def _extrair_nomes(self, node) -> list[str]:
        """Extrai nomes de variáveis de um nó AST (Name, JoinedStr, etc.)."""
        nomes = []
        if isinstance(node, ast.Name):
            nomes.append(node.id)
        elif isinstance(node, ast.JoinedStr):   # f-string
            for v in ast.walk(node):
                if isinstance(v, ast.Name):
                    nomes.append(v.id)
        elif isinstance(node, ast.Dict):
            for k in node.keys:
                if isinstance(k, ast.Constant):
                    nomes.append(str(k.value))
        return nomes


# ─────────────────────────────────────────────────────────────────────────────
# Função pública de entrada
# ─────────────────────────────────────────────────────────────────────────────
def analisar_arquivo(caminho: str) -> list[Vulnerability]:
    """
    Recebe o caminho de um arquivo .py e retorna a lista de vulnerabilidades.
    """
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    with open(caminho, encoding="utf-8") as f:
        codigo = f.read()

    try:
        arvore = ast.parse(codigo, filename=caminho)
    except SyntaxError as e:
        raise SyntaxError(f"Erro de sintaxe em {caminho}: {e}") from e

    analisador = CodeAnalyzer(caminho, codigo)
    analisador.visit(arvore)
    return analisador.resultados


def analisar_diretorio(diretorio: str) -> list[Vulnerability]:
    """
    Varre recursivamente um diretório e analisa todos os arquivos .py.
    """
    todos: list[Vulnerability] = []
    for raiz, _, arquivos in os.walk(diretorio):
        for arquivo in arquivos:
            if arquivo.endswith(".py"):
                caminho = os.path.join(raiz, arquivo)
                todos.extend(analisar_arquivo(caminho))
    return todos


# ─────────────────────────────────────────────────────────────────────────────
# Execução direta (teste rápido no terminal)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import json

    alvo = sys.argv[1] if len(sys.argv) > 1 else "."
    resultados = (
        analisar_arquivo(alvo) if alvo.endswith(".py")
        else analisar_diretorio(alvo)
    )

    if not resultados:
        print("✅  Nenhuma vulnerabilidade de privacidade encontrada.")
    else:
        print(f"\n⚠️  {len(resultados)} vulnerabilidade(s) encontrada(s):\n")
        for v in resultados:
            print(f"  [{v.risco}] {v.categoria}")
            print(f"  Arquivo : {v.arquivo}:{v.linha}")
            print(f"  LGPD    : {v.artigo_lgpd}")
            print(f"  Detalhe : {v.descricao}")
            if v.trecho:
                print(f"  Trecho  : {v.trecho}")
            print()

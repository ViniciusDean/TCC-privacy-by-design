"""
code_analyzer.py
Módulo de análise estática de código-fonte orientado à detecção de
vulnerabilidades de privacidade conforme os princípios do Privacy by Design
e os requisitos da Lei Geral de Proteção de Dados Pessoais (LGPD).
"""

import ast
import fnmatch
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
    confianca:  str = "ALTA"
    risco_base: Optional[str] = None
    localizador_interno: Optional[str] = None


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
CAMPOS_PROTEGIDOS = {
    "hash", "hashed", "sha256", "sha512", "encrypt", "encrypted",
    "cipher", "cifrado", "criptografado", "anonimizado", "anon",
    "mask", "masked", "mascar", "mascarado", "mascarada", "redact", "redacted",
}
TOKENS_FINALIDADE_TECNICA = {
    "template", "templates", "file", "filename", "path", "subject", "body",
    "event", "evento", "code", "codigo", "status", "type", "tipo", "label",
    "slug", "module", "modulo",
}
TOKENS_CONFIGURACAO_TECNICA = {
    "default", "defaults", "config", "configuration", "sender", "remetente",
    "from", "system", "sistema",
}
TOKENS_CONTEXTO_TESTE = {
    "test", "tests", "teste", "testes", "fixture", "fixtures", "factory",
    "factories", "mock", "mocks", "seed", "seeder",
}
METODOS_EXCLUSAO_ANONIMIZACAO = (
    "delete", "delet", "remov", "exclu", "anonimiz", "anonymiz", "purge",
)

DIRETORIOS_IGNORADOS = {
    ".git", ".github", ".idea", ".mypy_cache", ".nox", ".pytest_cache",
    ".ruff_cache", ".tox", ".venv", ".vscode", "__pycache__", "build",
    "coverage", "dist", "env", "htmlcov", "node_modules", "out",
    "python_backend", "site-packages", "third_party", "vendor", "venv",
}
PADROES_DIRETORIOS_IGNORADOS = {
    ".pytest-tmp-*", ".test-tmp-*", ".tmp-*", "pytest-*", "tmp-*",
}
ARQUIVO_IGNORADOS = ".privacyignore"
EXTENSOES_CODIGO = (".py", ".java")


def novo_escopo_varredura(alvo: str, tipo: str) -> dict:
    """Cria metadados auditáveis para uma execução de análise.

    O escopo é separado dos achados para que a ausência de achados nunca seja
    interpretada como sucesso quando nenhum arquivo pôde ser analisado.
    """
    return {
        "tipo": tipo,
        "alvo": os.path.abspath(os.fspath(alvo)),
        "status": "pending",
        "arquivos_elegiveis": 0,
        "arquivos_analisados": 0,
        "arquivos_ignorados": 0,
        "arquivos_falhos": 0,
        "erros": [],
    }


def codigo_erro_analise(erro: BaseException) -> str:
    """Normaliza erros sem expor mensagem, conteúdo ou caminho interno."""
    if isinstance(erro, SyntaxError):
        return "SINTAXE_INVALIDA"
    if isinstance(erro, UnicodeDecodeError):
        return "CODIFICACAO_NAO_SUPORTADA"
    if isinstance(erro, PermissionError):
        return "ACESSO_NEGADO"
    if isinstance(erro, FileNotFoundError):
        return "ARQUIVO_NAO_ENCONTRADO"
    if isinstance(erro, ValueError):
        return "TIPO_NAO_SUPORTADO"
    return "FALHA_DE_ANALISE"


def mensagem_erro_analise(codigo: str) -> str:
    mensagens = {
        "SINTAXE_INVALIDA": "O arquivo não possui sintaxe válida para análise estática.",
        "CODIFICACAO_NAO_SUPORTADA": "O arquivo não pôde ser lido com a codificação esperada.",
        "ACESSO_NEGADO": "O arquivo não pôde ser acessado para análise.",
        "ARQUIVO_NAO_ENCONTRADO": "O arquivo deixou de estar disponível durante a varredura.",
        "TIPO_NAO_SUPORTADO": "O tipo de arquivo não é suportado pela análise.",
        "FALHA_DE_ANALISE": "O arquivo não pôde ser analisado; revise-o localmente.",
    }
    return mensagens.get(codigo, mensagens["FALHA_DE_ANALISE"])


def registrar_erro_escopo(escopo: dict, caminho: str, erro: BaseException) -> None:
    codigo = codigo_erro_analise(erro)
    escopo["arquivos_falhos"] += 1
    escopo["erros"].append({
        "arquivo": os.path.abspath(caminho),
        "codigo": codigo,
        "mensagem": mensagem_erro_analise(codigo),
    })


def finalizar_escopo_varredura(escopo: dict) -> dict:
    if escopo["arquivos_analisados"] > 0:
        escopo["status"] = (
            "partial" if escopo["arquivos_falhos"] else "complete"
        )
    elif escopo["arquivos_falhos"] > 0:
        escopo["status"] = "failed"
    else:
        escopo["status"] = "empty"
    return escopo


def _contar_arquivos_analisaveis(diretorio: str, extensoes: tuple[str, ...]) -> int:
    """Conta somente candidatos de análise em uma árvore ignorada."""
    total = 0
    try:
        for _, _, arquivos in os.walk(diretorio):
            total += sum(nome.lower().endswith(extensoes) for nome in arquivos)
    except OSError:
        # O diretório já foi removido ou não pode ser enumerado; não deve
        # impedir a análise dos demais alvos.
        return total
    return total


def carregar_padroes_ignorados(diretorio: str) -> list[str]:
    caminho = os.path.join(diretorio, ARQUIVO_IGNORADOS)
    if not os.path.isfile(caminho):
        return []
    with open(caminho, encoding="utf-8-sig") as arquivo:
        return [
            linha.strip().replace("\\", "/")
            for linha in arquivo
            if linha.strip() and not linha.lstrip().startswith("#")
        ]


def caminho_deve_ser_ignorado(
    caminho_relativo: str,
    padroes: list[str],
    diretorio: bool = False,
) -> bool:
    relativo = caminho_relativo.replace("\\", "/").strip("/")
    for padrao_original in padroes:
        padrao = padrao_original.strip().lstrip("./").strip("/")
        if not padrao:
            continue
        if padrao_original.rstrip().endswith("/"):
            if relativo == padrao or relativo.startswith(f"{padrao}/"):
                return True
            continue
        if fnmatch.fnmatch(relativo, padrao):
            return True
        if "/" not in padrao and fnmatch.fnmatch(os.path.basename(relativo), padrao):
            return True
        if diretorio and relativo == padrao:
            return True
    return False

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
    "generate_password_hash", "set_password", "make_password",
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
        self._pilha_funcoes: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        self._pilha_classes: list[ast.ClassDef] = []
        self._chaves_adicionadas: set[tuple[int, str, str]] = set()

    def visit(self, node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._pilha_funcoes.append(node)
            try:
                return super().visit(node)
            finally:
                self._pilha_funcoes.pop()
        if isinstance(node, ast.ClassDef):
            self._pilha_classes.append(node)
            try:
                return super().visit(node)
            finally:
                self._pilha_classes.pop()
        return super().visit(node)

    # ── Utilitários ──────────────────────────────────────────────────────────

    def _trecho(self, linha: int) -> str:
        """Retorna o texto da linha (1-indexado), truncado a 120 chars."""
        if 1 <= linha <= len(self.linhas):
            return self.linhas[linha - 1].strip()[:120]
        return ""

    def _adicionar(
        self,
        linha,
        categoria,
        descricao,
        risco,
        artigo,
        confianca="ALTA",
        localizador_interno="",
    ):
        chave = (int(linha or 0), str(categoria), str(localizador_interno))
        if chave in self._chaves_adicionadas:
            return
        self._chaves_adicionadas.add(chave)
        self.resultados.append(Vulnerability(
            arquivo=self.caminho,
            linha=linha,
            categoria=categoria,
            descricao=descricao,
            risco=risco,
            artigo_lgpd=artigo,
            trecho=self._trecho(linha),
            confianca=confianca,
            localizador_interno=localizador_interno or None,
        ))

    def _nome_tem_finalidade_tecnica(self, nome: str) -> bool:
        return any(
            token in TOKENS_FINALIDADE_TECNICA
            for token in self._tokens_nome(nome)
        )

    def _arquivo_em_contexto_de_teste(self) -> bool:
        partes = [
            parte.lower()
            for parte in re.split(r"[\\/]+", os.path.abspath(self.caminho))
            if parte
        ]
        nome = os.path.basename(self.caminho).lower()
        return (
            any(parte in {"test", "tests", "fixture", "fixtures"} for parte in partes)
            or nome.startswith(("test_", "fixture_"))
        )

    def _classe_atual_e_configuracao(self) -> bool:
        if not self._pilha_classes:
            return False
        classe = self._pilha_classes[-1]
        tokens = self._tokens_nome(classe.name)
        if tokens and tokens[-1] in {"config", "configuration", "settings"}:
            return True
        bases = {self._nome_expr(base).lower() for base in classe.bases}
        return any(
            base.endswith(("appconfig", "config", "configuration"))
            for base in bases
        )

    @staticmethod
    def _literal_parece_identificador_tecnico(valor: str) -> bool:
        texto = valor.strip()
        return bool(
            re.fullmatch(r"[A-Z][A-Z0-9_:-]{2,}", texto)
            or re.fullmatch(
                r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.%{}-]+)+",
                texto,
            )
        )

    def _confianca_literal_pessoal(
        self,
        nome: str,
        campo: str,
        valor: str,
    ) -> str | None:
        tokens = self._tokens_nome(nome)
        texto = valor.strip()
        if not texto or self._nome_tem_finalidade_tecnica(nome):
            return None
        if self._classe_atual_e_configuracao() and campo in CAMPOS_AMBIGUOS:
            return None
        if campo in CAMPOS_AMBIGUOS and self._literal_parece_identificador_tecnico(texto):
            return None

        if set(tokens) & TOKENS_CONFIGURACAO_TECNICA:
            return "MEDIA"
        if self._arquivo_em_contexto_de_teste():
            return "MEDIA"
        if campo in {
            "senha", "password", "passwd", "pwd", "secret", "token",
            "api_key", "apikey",
        }:
            return "ALTA"
        if campo in {"cpf", "rg", "cnpj", "passaporte"}:
            return "ALTA" if sum(char.isdigit() for char in texto) >= 7 else "MEDIA"
        if campo in {"email", "e_mail"}:
            return "ALTA" if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", texto) else "MEDIA"
        if campo in {"telefone", "celular", "phone"}:
            return "ALTA" if sum(char.isdigit() for char in texto) >= 8 else "MEDIA"
        if campo in {"cartao", "card", "credit", "credito"}:
            return "ALTA" if sum(char.isdigit() for char in texto) >= 12 else None
        if campo in CAMPOS_AMBIGUOS:
            return "ALTA" if self._contexto_atual_pessoal() else "MEDIA"
        return "MEDIA"

    def _nome_contem_campo_sensivel(self, nome: str) -> Optional[str]:
        """Verifica se um nome de variável/atributo contém campo sensível.
        Usa tokens para evitar falsos positivos (ex: 'age' em 'user_agent').
        """
        nome_lower = nome.lower()
        if nome_lower in CAMPOS_TECNICOS:
            return None
        if self._nome_tem_finalidade_tecnica(nome):
            return None

        tokens = self._tokens_nome(nome)
        if tokens and tokens[0] == "ip":
            return None
        if any(token in CAMPOS_PROTEGIDOS for token in tokens):
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

    @staticmethod
    def _tokens_nome(nome: str) -> list[str]:
        """Quebra snake_case e camelCase sem usar correspondência parcial."""
        separado = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", nome)
        separado = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", separado)
        return [
            token for token in re.split(r"[^a-z0-9]+|_", separado.lower()) if token
        ]

    def _funcao_atual(self) -> Optional[ast.FunctionDef | ast.AsyncFunctionDef]:
        return self._pilha_funcoes[-1] if self._pilha_funcoes else None

    def _em_funcao_exclusao_anonimizacao(self) -> bool:
        funcao = self._funcao_atual()
        if not funcao:
            return False
        nome = funcao.name.lower()
        return any(p in nome for p in METODOS_EXCLUSAO_ANONIMIZACAO)

    def _valor_e_parametro(self, nome: str, valor: ast.expr) -> bool:
        funcao = self._funcao_atual()
        if not funcao or not isinstance(valor, ast.Name):
            return False
        parametros = {
            arg.arg
            for arg in (
                list(funcao.args.posonlyargs)
                + list(funcao.args.args)
                + list(funcao.args.kwonlyargs)
            )
        }
        if funcao.args.vararg:
            parametros.add(funcao.args.vararg.arg)
        if funcao.args.kwarg:
            parametros.add(funcao.args.kwarg.arg)
        return valor.id == nome and valor.id in parametros

    def _valor_e_declaracao_de_campo(self, valor: ast.expr) -> bool:
        if not isinstance(valor, ast.Call):
            return False

        nome_chamada = self._nome_call(valor).lower()
        if nome_chamada in {"field", "column", "mapped_column", "relationship"}:
            return True
        return nome_chamada.endswith(("field", ".field", "column", ".column"))

    def _atribuicao_local_temporaria(self, target: ast.expr, valor: ast.expr) -> bool:
        if not self._funcao_atual() or not isinstance(target, ast.Name):
            return False
        return not (isinstance(valor, ast.Call) and self._nome_call(valor) == "input")

    def _atribuicao_ambigua_tem_contexto_pessoal(
        self,
        nome: str,
        target: ast.expr,
        valor: ast.expr,
    ) -> bool:
        """Exige contexto adicional para campos ambiguos como nome/name/idade."""
        tokens = self._tokens_nome(nome)
        if any(token in CONTEXTO_PESSOAL for token in tokens):
            return True

        if self._contexto_atual_pessoal():
            return True

        # Entrada explicita do usuario e um sinal forte de coleta de dado pessoal.
        return isinstance(valor, ast.Call) and self._nome_call(valor) == "input"

    def _contexto_atual_pessoal(self) -> bool:
        nomes = [node.name for node in self._pilha_classes + self._pilha_funcoes]
        return any(
            token in CONTEXTO_PESSOAL
            for nome in nomes
            for token in self._tokens_nome(nome)
            if token
        )

    def _campo_ambiguo_tem_contexto(self, nome: str) -> bool:
        tokens = self._tokens_nome(nome)
        return (
            any(token in CONTEXTO_PESSOAL for token in tokens)
            or self._contexto_atual_pessoal()
        )

    # ── Regra 1: variável com dado sensível atribuída como string simples ────

    def _processar_atribuicao(
        self,
        targets: list[ast.expr],
        valor: ast.expr,
        linha: int,
    ) -> None:
        """Aplica a regra de armazenamento a atribuições comuns e anotadas."""
        for target in targets:
            nome = None
            if isinstance(target, ast.Name):
                nome = target.id
            elif isinstance(target, ast.Attribute):
                nome = target.attr

            if not nome:
                continue

            campo = self._nome_contem_campo_sensivel(nome)
            if not campo or self._em_funcao_exclusao_anonimizacao():
                continue
            if (
                campo in CAMPOS_AMBIGUOS
                and not self._atribuicao_ambigua_tem_contexto_pessoal(nome, target, valor)
            ):
                continue

            # Valor literal não vazio é o caso de maior risco. O conteúdo não
            # é publicado pelos relatórios; apenas a categoria e a localização.
            if isinstance(valor, ast.Constant) and isinstance(valor.value, str):
                confianca = self._confianca_literal_pessoal(nome, campo, valor.value)
                if confianca:
                    self._adicionar(
                        linha,
                        "DADO_HARDCODED",
                        f"Campo sensível '{campo}' recebe valor literal "
                        f"(dado pessoal fixo no código).",
                        "ALTO",
                        "Art. 46 — Segurança e prevenção",
                        confianca,
                        f"atribuicao:{nome}",
                    )
                continue

            if isinstance(valor, ast.Constant) and valor.value is None:
                continue
            if isinstance(valor, ast.Constant) and isinstance(valor.value, bool):
                continue
            if self._valor_e_declaracao_de_campo(valor):
                continue
            if self._valor_e_parametro(nome, valor):
                continue
            if self._atribuicao_local_temporaria(target, valor):
                continue

            # A criptografia é inferida apenas da instrução local; a saída
            # pública permanece uma evidência segura e não inclui a linha.
            trecho = self._trecho(linha).lower()
            tem_cripto = any(c.lower() in trecho for c in FUNCOES_CRIPTOGRAFIA)
            if not tem_cripto:
                self._adicionar(
                    linha,
                    "DADO_SEM_CRIPTOGRAFIA",
                    f"Campo '{campo}' recebe dado pessoal sem indício "
                    f"de criptografia ou hash.",
                    "MEDIO",
                    "Art. 46 — Segurança e prevenção",
                    "MEDIA",
                )

    def visit_Assign(self, node: ast.Assign):
        """Detecta atribuições convencionais de dados pessoais."""
        self._processar_atribuicao(node.targets, node.value, node.lineno)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        """Detecta atribuições anotadas, por exemplo ``self.email: str = ...``."""
        if node.value is not None:
            self._processar_atribuicao([node.target], node.value, node.lineno)
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
        partes_chamada = nome_chamada.lower().split(".")
        eh_log = nome_chamada == "print" or (
            len(partes_chamada) >= 2
            and partes_chamada[-1]
            in {"debug", "info", "warning", "warn", "error", "critical"}
            and partes_chamada[-2] in {"logging", "logger"}
        )
        if eh_log:
            argumentos_log = [*node.args, *(kw.value for kw in node.keywords)]
            campos_log: set[str] = set()
            for arg in argumentos_log:
                variaveis = self._extrair_nomes(arg)
                for var in variaveis:
                    campo = self._nome_contem_campo_sensivel(var)
                    if campo and (
                        campo not in CAMPOS_AMBIGUOS
                        or self._campo_ambiguo_tem_contexto(var)
                    ):
                        campos_log.add(campo)
            if campos_log:
                campos_texto = ", ".join(sorted(campos_log))
                self._adicionar(
                    node.lineno,
                    "DADO_EM_LOG",
                    f"Dados pessoais ({campos_texto}) registrados em log/print. "
                    f"Logs com dados identificáveis violam o princípio "
                    f"da minimização.",
                    "ALTO",
                    "Art. 46 — Segurança | Art. 6º, III — Necessidade",
                    localizador_interno=(
                        f"chamada-log:{node.lineno}:{node.col_offset}"
                    ),
                )

        # ── 3b: transferência de dados para serviço externo ──
        eh_servico = any(
            nome_chamada == svc or nome_chamada.startswith(f"{svc}.")
            for svc in SERVICOS_TERCEIROS
        )
        if eh_servico:
            # Verifica se há campos sensíveis nos kwargs (json=, data=, params=)
            campos_transferidos: set[str] = set()
            for kw in node.keywords:
                if kw.arg in ("json", "data", "params", "body"):
                    variaveis = self._extrair_nomes(kw.value)
                    for var in variaveis:
                        campo = self._nome_contem_campo_sensivel(var)
                        if campo:
                            campos_transferidos.add(campo)
            if campos_transferidos:
                campos_texto = ", ".join(sorted(campos_transferidos))
                self._adicionar(
                    node.lineno,
                    "TRANSFERENCIA_SEM_BASE_LEGAL",
                    f"Campos ({campos_texto}) enviados para serviço externo "
                    f"({nome_chamada}). Verifique se há base legal "
                    f"documentada para esta transferência.",
                    "ALTO",
                    "Art. 7º — Hipóteses de tratamento | "
                    "Art. 33 — Transferência internacional",
                    localizador_interno=(
                        f"chamada-transferencia:{node.lineno}:{node.col_offset}"
                    ),
                )

        self.generic_visit(node)

    # ── Regra 4: coleta excessiva via input / formulário ─────────────────────

    def _visitar_definicao_funcao(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        """
        Detecta funções cujos parâmetros acumulam muitos campos sensíveis,
        indicando possível coleta excessiva.
        """
        campos_encontrados = []
        campos_fortes = []
        for arg in node.args.args:
            campo = self._nome_contem_campo_sensivel(arg.arg)
            if campo:
                campos_encontrados.append(campo)
                if campo not in CAMPOS_AMBIGUOS:
                    campos_fortes.append(campo)

        if (
            len(campos_encontrados) >= 4
            and (campos_fortes or self._contexto_atual_pessoal())
        ):
            self._adicionar(
                node.lineno,
                "COLETA_EXCESSIVA",
                f"Função '{node.name}' recebe {len(campos_encontrados)} campos "
                f"sensíveis ({', '.join(campos_encontrados)}). Verifique se todos "
                f"são estritamente necessários para a finalidade.",
                "MEDIO",
                "Art. 6º, III — Necessidade | Art. 6º, I — Finalidade",
                "MEDIA",
            )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._visitar_definicao_funcao(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._visitar_definicao_funcao(node)

    # ── Regra 5: ausência de mecanismo de exclusão ───────────────────────────

    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Em classes que parecem modelos de dados (contêm campos sensíveis),
        verifica se há algum método de exclusão/anonimização definido.
        """
        # Regras de ausencia de exclusao so fazem sentido para estruturas que
        # representam persistencia. Formularios e classes de configuracao eram
        # a principal fonte de falsos positivos na validacao externa.
        nome_lower = node.name.lower()
        if nome_lower == "config" or nome_lower.endswith((
            "form", "schema", "serializer", "table", "config",
            "configuration", "seeder",
        )):
            self.generic_visit(node)
            return

        bases = {
            self._nome_expr(base).lower()
            for base in node.bases
            if self._nome_expr(base)
        }
        marcadores_persistencia = {"model", "document", "entity", "basemodel"}
        herda_persistencia = any(
            base.split(".")[-1] in marcadores_persistencia
            or base.endswith((".model", ".document", ".entity"))
            for base in bases
        )
        chamadas_persistentes = {
            "column", "mapped_column", "relationship",
            "models.field", "models.charfield", "models.textfield",
            "models.emailfield", "models.datefield", "models.datetimefield",
            "models.foreignkey", "models.onetoonefield", "models.manytomanyfield",
            "db.column", "db.relationship",
        }
        declara_campo_persistente = any(
            isinstance(item, (ast.Assign, ast.AnnAssign))
            and isinstance(
                item.value if isinstance(item, ast.Assign) else item.value,
                ast.Call,
            )
            and self._nome_call(
                item.value if isinstance(item, ast.Assign) else item.value
            ).lower() in chamadas_persistentes
            for item in node.body
        )
        if not (herda_persistencia or declara_campo_persistente):
            self.generic_visit(node)
            return

        campos_na_classe = []
        metodos = []

        for item in node.body:
            if isinstance(item, (ast.Assign, ast.AnnAssign)):
                targets = item.targets if isinstance(item, ast.Assign) else [item.target]
                for t in targets:
                    nome = t.id if isinstance(t, ast.Name) else (
                        t.attr if isinstance(t, ast.Attribute) else "")
                    if self._nome_contem_campo_sensivel(nome):
                        campos_na_classe.append(nome)
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metodos.append(item.name.lower())

        if campos_na_classe:
            campos_fortes = [
                nome for nome in campos_na_classe
                if self._nome_contem_campo_sensivel(nome) not in CAMPOS_AMBIGUOS
            ]
            if not campos_fortes and not self._contexto_atual_pessoal():
                self.generic_visit(node)
                return
            verbos_exclusao = {
                "delete", "remove", "remover", "excluir", "anonimizar",
                "anonymize", "purge",
            }
            alvos_exclusao = {
                "user", "usuario", "account", "conta", "profile", "perfil",
                "data", "dados", "personal", "pessoal", "record", "registro",
            }
            tem_exclusao = any(
                tokens
                and tokens[0] in verbos_exclusao
                and (len(tokens) == 1 or tokens[1] in alvos_exclusao)
                for metodo in metodos
                if (tokens := self._tokens_nome(metodo))
            )
            tem_cascata = any(
                isinstance(item, (ast.Assign, ast.AnnAssign))
                and isinstance(item.value, ast.Call)
                and any(
                    kw.arg == "on_delete"
                    and self._nome_expr(kw.value).lower().endswith("cascade")
                    for kw in item.value.keywords
                )
                for item in node.body
            )
            if not tem_exclusao and not tem_cascata:
                self._adicionar(
                    node.lineno,
                    "AUSENCIA_EXCLUSAO",
                    f"Classe '{node.name}' contém campos sensíveis "
                    f"({', '.join(campos_na_classe[:3])}) mas não define "
                    f"método de exclusão ou anonimização.",
                    "MEDIO",
                    "Art. 18, IV — Direito à eliminação dos dados",
                    "ALTA" if herda_persistencia else "MEDIA",
                    f"classe:{node.name}:ausencia-exclusao",
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

    def _nome_expr(self, node: ast.expr) -> str:
        """Retorna nome pontuado de uma expressao simples."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            prefix = self._nome_expr(node.value)
            return f"{prefix}.{node.attr}" if prefix else node.attr
        return ""

    def _extrair_nomes(self, node: ast.AST) -> list[str]:
        """Extrai identificadores inclusive atributos, sem seguir valores mascarados."""
        nomes: list[str] = []

        def coletar(atual: ast.AST) -> None:
            if isinstance(atual, ast.Call):
                chamada = self._nome_call(atual).lower()
                if any(marcador in chamada for marcador in CAMPOS_PROTEGIDOS):
                    # `mascarar(cpf)` e `hash(email)` não representam exposição
                    # do valor original no log.
                    return
            if isinstance(atual, ast.Name):
                nomes.append(atual.id)
            elif isinstance(atual, ast.Attribute):
                nomes.append(atual.attr)
            elif isinstance(atual, ast.Dict):
                for chave in atual.keys:
                    if isinstance(chave, ast.Constant) and isinstance(chave.value, str):
                        nomes.append(chave.value)
            for filho in ast.iter_child_nodes(atual):
                coletar(filho)

        coletar(node)
        return nomes


# ─────────────────────────────────────────────────────────────────────────────
# Função pública de entrada
# ─────────────────────────────────────────────────────────────────────────────
def analisar_arquivo(caminho: str) -> list[Vulnerability]:
    """
    Recebe o caminho de um arquivo Python ou Java e retorna vulnerabilidades.
    """
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    if caminho.lower().endswith(".java"):
        from java_analyzer import analisar_java
        return analisar_java(caminho)

    if not caminho.lower().endswith(".py"):
        raise ValueError(f"Tipo de arquivo não suportado: {caminho}")

    with open(caminho, encoding="utf-8") as f:
        codigo = f.read()

    try:
        arvore = ast.parse(codigo, filename=caminho)
    except SyntaxError as e:
        raise SyntaxError(f"Erro de sintaxe em {caminho}: {e}") from e

    analisador = CodeAnalyzer(caminho, codigo)
    analisador.visit(arvore)
    return analisador.resultados


def analisar_arquivo_com_escopo(caminho: str) -> tuple[list[Vulnerability], dict]:
    """Analisa um arquivo isolado sem converter falha em um falso resultado limpo."""
    if not isinstance(caminho, (str, os.PathLike)) or not str(caminho).strip():
        raise ValueError("O caminho do arquivo é obrigatório.")
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    escopo = novo_escopo_varredura(caminho, "arquivo")
    escopo["arquivos_elegiveis"] = 1
    try:
        if os.path.getsize(caminho) == 0:
            registrar_erro_escopo(escopo, caminho, ValueError("arquivo vazio"))
            return [], finalizar_escopo_varredura(escopo)
        resultados = analisar_arquivo(caminho)
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError) as erro:
        registrar_erro_escopo(escopo, caminho, erro)
        return [], finalizar_escopo_varredura(escopo)

    escopo["arquivos_analisados"] = 1
    return resultados, finalizar_escopo_varredura(escopo)


def analisar_diretorio_com_escopo(diretorio: str) -> tuple[list[Vulnerability], dict]:
    """Varre um diretório preservando achados dos arquivos válidos.

    Erros de leitura, codificação e sintaxe são registrados por arquivo. Assim,
    um candidato defeituoso não oculta os indícios encontrados nos demais.
    """
    if not isinstance(diretorio, (str, os.PathLike)) or not str(diretorio).strip():
        raise ValueError("O diretório é obrigatório.")
    if not os.path.isdir(diretorio):
        raise FileNotFoundError(f"Diretório não encontrado: {diretorio}")

    todos: list[Vulnerability] = []
    diretorio_raiz = os.path.realpath(os.path.abspath(diretorio))
    escopo = novo_escopo_varredura(diretorio_raiz, "diretorio")
    padroes_ignorados = carregar_padroes_ignorados(diretorio_raiz)

    def registrar_erro_walk(erro: OSError) -> None:
        registrar_erro_escopo(
            escopo,
            getattr(erro, "filename", None) or diretorio_raiz,
            erro,
        )

    for raiz, diretorios, arquivos in os.walk(
        diretorio_raiz,
        onerror=registrar_erro_walk,
    ):
        diretorios_mantidos = []
        for nome in diretorios:
            caminho_diretorio = os.path.join(raiz, nome)
            relativo = os.path.relpath(caminho_diretorio, diretorio_raiz)
            ignorado = (
                nome.lower() in DIRETORIOS_IGNORADOS
                or any(
                    fnmatch.fnmatch(nome.lower(), padrao)
                    for padrao in PADROES_DIRETORIOS_IGNORADOS
                )
                or caminho_deve_ser_ignorado(relativo, padroes_ignorados, diretorio=True)
            )
            if ignorado:
                escopo["arquivos_ignorados"] += _contar_arquivos_analisaveis(
                    caminho_diretorio,
                    EXTENSOES_CODIGO,
                )
            else:
                diretorios_mantidos.append(nome)
        diretorios[:] = diretorios_mantidos

        for arquivo in arquivos:
            if not arquivo.lower().endswith(EXTENSOES_CODIGO):
                continue
            caminho = os.path.join(raiz, arquivo)
            relativo = os.path.relpath(caminho, diretorio_raiz)
            if caminho_deve_ser_ignorado(relativo, padroes_ignorados):
                escopo["arquivos_ignorados"] += 1
                continue

            try:
                caminho_real = os.path.realpath(caminho)
                raiz_comum = os.path.commonpath([diretorio_raiz, caminho_real])
                if os.path.normcase(raiz_comum) != os.path.normcase(diretorio_raiz):
                    escopo["arquivos_ignorados"] += 1
                    continue
                escopo["arquivos_elegiveis"] += 1
                if os.path.getsize(caminho) == 0:
                    registrar_erro_escopo(
                        escopo,
                        caminho,
                        ValueError("arquivo vazio"),
                    )
                    continue
                todos.extend(analisar_arquivo(caminho))
            except (OSError, SyntaxError, UnicodeDecodeError, ValueError) as erro:
                registrar_erro_escopo(escopo, caminho, erro)
                continue
            escopo["arquivos_analisados"] += 1

    return todos, finalizar_escopo_varredura(escopo)


def analisar_diretorio(diretorio: str) -> list[Vulnerability]:
    """
    Varre recursivamente um diretório e analisa arquivos .py e .java.
    """
    resultados, _ = analisar_diretorio_com_escopo(diretorio)
    return resultados


# ─────────────────────────────────────────────────────────────────────────────
# Execução direta (teste rápido no terminal)
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import json

    alvo = sys.argv[1] if len(sys.argv) > 1 else "."
    try:
        resultados, escopo = (
            analisar_arquivo_com_escopo(alvo)
            if alvo.lower().endswith(EXTENSOES_CODIGO)
            else analisar_diretorio_com_escopo(alvo)
        )
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
                "evidencia_segura": "Regra estática acionada; conteúdo original ocultado.",
            }
            for v in resultados
        ],
    }, ensure_ascii=False, indent=2))

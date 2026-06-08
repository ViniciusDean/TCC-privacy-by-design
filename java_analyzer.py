"""
Análise estática inicial de arquivos Java.

Esta versão usa regras textuais conservadoras para detectar três padrões:
- dados pessoais hardcoded;
- criptografia fraca com MD5 ou SHA-1;
- dados pessoais enviados para logs ou saída padrão.

O analisador não compila nem executa o código Java.
"""

import os
import re


CAMPOS_SENSIVEIS = {
    "senha", "password", "passwd", "pwd",
    "cpf", "rg", "cnpj", "passaporte",
    "email", "telefone", "celular", "phone",
    "nome", "name", "endereco", "address",
    "nascimento", "birth", "idade", "age",
    "cartao", "card", "token", "secret", "apikey",
    "saude", "health", "salario", "salary", "renda", "income",
}

CAMPOS_AMBIGUOS = {"nome", "name", "idade", "age"}
CONTEXTO_PESSOAL = {
    "usuario", "user", "cliente", "customer", "pessoa", "person",
    "paciente", "patient", "funcionario", "employee",
}
CAMPOS_TECNICOS = {
    "user_agent", "user_id", "session_id", "request_id", "trace_id",
    "ip_address", "ip_addr",
}

PADRAO_ATRIBUICAO_STRING = re.compile(
    r"(?:\bString\b|\bvar\b)?\s*"
    r"(?P<nome>[A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*"
    r'"(?P<valor>(?:\\.|[^"\\])*)"\s*;'
)
PADRAO_CRIPTOGRAFIA_FRACA = re.compile(
    r'MessageDigest\s*\.\s*getInstance\s*\(\s*"(?P<alg>MD5|SHA-?1)"\s*\)',
    re.IGNORECASE,
)
PADRAO_LOG = re.compile(
    r"(?:System\.(?:out|err)\.(?:print|println|printf)|"
    r"(?:log|logger)\.(?:trace|debug|info|warn|error))\s*\((?P<args>.*)\)\s*;?",
    re.IGNORECASE,
)


def _tokens(nome: str) -> list[str]:
    separado = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", nome)
    return [token for token in re.split(r"[^a-z0-9]+", separado.lower()) if token]


def _campo_sensivel(nome: str):
    nome_lower = nome.lower()
    if nome_lower in CAMPOS_TECNICOS:
        return None

    tokens = _tokens(nome)
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


def _linha_sem_comentario(linha: str) -> str:
    return linha.split("//", 1)[0]


def analisar_java(caminho: str):
    """Analisa um arquivo .java e retorna Vulnerability objects."""
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    # Importação local evita dependência circular com code_analyzer.
    from code_analyzer import Vulnerability

    with open(caminho, encoding="utf-8") as arquivo:
        linhas = arquivo.read().splitlines()

    resultados = []

    def adicionar(numero, categoria, descricao, risco, artigo):
        resultados.append(Vulnerability(
            arquivo=caminho,
            linha=numero,
            categoria=categoria,
            descricao=descricao,
            risco=risco,
            artigo_lgpd=artigo,
            trecho=linhas[numero - 1].strip()[:120],
        ))

    for numero, original in enumerate(linhas, start=1):
        linha = _linha_sem_comentario(original).strip()
        if not linha:
            continue

        atribuicao = PADRAO_ATRIBUICAO_STRING.search(linha)
        if atribuicao:
            nome = atribuicao.group("nome")
            valor = atribuicao.group("valor")
            campo = _campo_sensivel(nome)
            if campo and valor:
                adicionar(
                    numero,
                    "DADO_HARDCODED",
                    f"Campo sensível '{campo}' recebe valor literal no código Java.",
                    "ALTO",
                    "Art. 46 — Segurança e prevenção",
                )

        cripto = PADRAO_CRIPTOGRAFIA_FRACA.search(linha)
        if cripto:
            algoritmo = cripto.group("alg").upper()
            adicionar(
                numero,
                "CRIPTOGRAFIA_FRACA",
                f"Uso de algoritmo criptográfico fraco no Java: {algoritmo}.",
                "ALTO",
                "Art. 46 — Segurança e prevenção",
            )

        log = PADRAO_LOG.search(linha)
        if log:
            argumentos = log.group("args")
            argumentos_sem_strings = re.sub(r'"(?:\\.|[^"\\])*"', "", argumentos)
            campos = sorted({
                campo
                for identificador in re.findall(r"[A-Za-z_$][A-Za-z0-9_$]*", argumentos_sem_strings)
                if (campo := _campo_sensivel(identificador))
            })
            if campos:
                adicionar(
                    numero,
                    "DADO_EM_LOG",
                    f"Dado pessoal pode estar sendo registrado em log Java: {', '.join(campos)}.",
                    "ALTO",
                    "Art. 46 — Segurança; Art. 6º, III — Necessidade",
                )

    return resultados

"""
Análise estática conservadora de arquivos Java.

O módulo não compila nem executa o código. Ele faz uma leitura léxica leve para
reconhecer atribuições, chamadas, métodos e classes, preservando o contrato de
resultados usado pelos analisadores Python e SQLite.
"""

import bisect
import os
import re
from dataclasses import dataclass


CAMPOS_SENSIVEIS = {
    "senha", "password", "passwd", "pwd",
    "cpf", "rg", "cnpj", "passaporte", "passport",
    "email", "telefone", "celular", "phone",
    "nome", "name", "endereco", "address",
    "nascimento", "birth", "idade", "age",
    "cartao", "card", "credit", "credito",
    "token", "secret", "apikey", "api_key",
    "saude", "health", "diagnostico", "diagnosis",
    "salario", "salary", "renda", "income",
    "religiao", "religion", "etnia", "ethnicity",
}
CAMPOS_AMBIGUOS = {"nome", "name", "idade", "age"}
CONTEXTO_PESSOAL = {
    "usuario", "user", "cliente", "customer", "pessoa", "person", "titular",
    "paciente", "patient", "funcionario", "employee",
}
CAMPOS_TECNICOS = {
    "user_agent", "user_id", "session_id", "request_id", "trace_id",
    "ip_address", "ip_addr",
}
METODOS_EXCLUSAO = (
    "delete", "delet", "remove", "remov", "exclu", "anonimiz", "anonymiz",
    "purge", "erase", "apagar",
)
MARCADORES_CRIPTOGRAFIA = (
    "bcrypt", "argon2", "pbkdf2", "scrypt", "sha-256", "sha-512",
    "sha256", "sha512", "aes", "cipher", "encrypt", "criptograf",
    "hashpassword", "passwordencoder", "messagedigest",
)
MARCADORES_TRANSFERENCIA = (
    "resttemplate.", "webclient.", "httpclient.", "client.send(",
    "client.sendasync(", "okhttpclient", ".newcall(", "httpurlconnection",
    "urlconnection", "retrofit", "feign", "postforentity(", "postforobject(",
    ".exchange(", ".retrieve(", ".bodyvalue(", ".body(",
)
MARCADORES_BASE_LEGAL = (
    "consentimento", "consent", "baselegal", "base_legal", "legitimateinterest",
    "legitimo_interesse", "dadosanonimizados", "dados_anonimizados",
    "anonymizeddata", "anonymiseddata",
)

PADRAO_IDENTIFICADOR = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
PADRAO_STRING = re.compile(r'"(?:\\.|[^"\\])*"')
PADRAO_ATRIBUICAO = re.compile(
    r"(?:(?:this|super)\s*\.\s*)?(?P<nome>[A-Za-z_$][A-Za-z0-9_$]*)"
    r"\s*=\s*(?!=)(?P<valor>.+?)\s*;\s*$",
    re.DOTALL,
)
PADRAO_LITERAL_STRING = re.compile(r'^\s*"(?P<valor>(?:\\.|[^"\\])*)"\s*$',
                                   re.DOTALL)
PADRAO_CRIPTOGRAFIA_FRACA = re.compile(
    r"(?:MessageDigest\s*\.\s*getInstance\s*\(\s*\"(?:MD5|SHA-?1)\"\s*\)|"
    r"DigestUtils\s*\.\s*(?:md5|md5Hex|sha1|sha1Hex)\s*\(|"
    r"Hashing\s*\.\s*(?:md5|sha1)\s*\()",
    re.IGNORECASE,
)
PADRAO_LOG = re.compile(
    r"(?:System\s*\.\s*(?:out|err)\s*\.\s*(?:print|println|printf)|"
    r"(?:log|logger)\s*\.\s*(?:trace|debug|info|warn|warning|error|fatal))"
    r"\s*\((?P<args>.*)\)\s*;?\s*$",
    re.IGNORECASE | re.DOTALL,
)
PADRAO_CLASSE = re.compile(
    r"\b(?:class|record)\s+(?P<nome>[A-Za-z_$][A-Za-z0-9_$]*)[^{]*\{",
    re.MULTILINE,
)
PADRAO_METODO = re.compile(
    r"(?:^|[;{}])\s*"
    r"(?:@[A-Za-z0-9_$.]+(?:\s*\([^)]*\))?\s*)*"
    r"(?:(?:public|protected|private|static|final|abstract|synchronized|native|"
    r"default|strictfp)\s+)*"
    r"(?:<[^>{};]+>\s*)?"
    r"(?:(?:[A-Za-z_$][A-Za-z0-9_$.<>\[\],?]*\s+)+)?"
    r"(?P<nome>[A-Za-z_$][A-Za-z0-9_$]*)\s*"
    r"\((?P<parametros>[^()]*)\)\s*"
    r"(?:throws\s+[^{]+)?\{",
    re.MULTILINE,
)
PADRAO_CAMPO = re.compile(
    r"(?:@[A-Za-z0-9_$.]+(?:\s*\([^)]*\))?\s*)*"
    r"(?:(?:public|protected|private|static|final|transient|volatile)\s+)*"
    r"[A-Za-z_$][A-Za-z0-9_$.<>\[\],?]*\s+"
    r"(?P<nome>[A-Za-z_$][A-Za-z0-9_$]*)"
    r"(?:\s*=\s*.+)?\s*;\s*$",
    re.DOTALL,
)


@dataclass
class Bloco:
    nome: str
    inicio: int
    abertura: int
    fim: int
    parametros: tuple[str, ...] = ()


def _tokens(nome: str) -> list[str]:
    separado = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", nome)
    return [token for token in re.split(r"[^a-z0-9]+", separado.lower()) if token]


def _campo_sensivel(nome: str):
    nome_lower = nome.lower()
    if nome_lower in CAMPOS_TECNICOS:
        return None

    tokens = _tokens(nome)
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
            if tokens[-1] == campo and any(
                token in CONTEXTO_PESSOAL for token in tokens[:-1]
            ):
                return campo
    return None


def _mascarar_comentarios(codigo: str) -> str:
    """Remove comentários preservando strings, tamanho e quebras de linha."""
    resultado = list(codigo)
    i = 0
    estado = "codigo"

    while i < len(codigo):
        atual = codigo[i]
        proximo = codigo[i + 1] if i + 1 < len(codigo) else ""

        if estado == "codigo":
            if atual == '"':
                estado = "string"
            elif atual == "'":
                estado = "char"
            elif atual == "/" and proximo == "/":
                resultado[i] = resultado[i + 1] = " "
                estado = "linha"
                i += 1
            elif atual == "/" and proximo == "*":
                resultado[i] = resultado[i + 1] = " "
                estado = "bloco"
                i += 1
        elif estado == "string":
            if atual == "\\":
                i += 1
            elif atual == '"':
                estado = "codigo"
        elif estado == "char":
            if atual == "\\":
                i += 1
            elif atual == "'":
                estado = "codigo"
        elif estado == "linha":
            if atual == "\n":
                estado = "codigo"
            else:
                resultado[i] = " "
        elif estado == "bloco":
            if atual == "*" and proximo == "/":
                resultado[i] = resultado[i + 1] = " "
                estado = "codigo"
                i += 1
            elif atual != "\n":
                resultado[i] = " "
        i += 1

    return "".join(resultado)


def _mascarar_strings(codigo: str) -> str:
    resultado = list(codigo)
    i = 0
    while i < len(codigo):
        if codigo[i] not in {'"', "'"}:
            i += 1
            continue
        delimitador = codigo[i]
        i += 1
        while i < len(codigo):
            if codigo[i] == "\\":
                if codigo[i] != "\n":
                    resultado[i] = " "
                if i + 1 < len(codigo) and codigo[i + 1] != "\n":
                    resultado[i + 1] = " "
                i += 2
                continue
            if codigo[i] == delimitador:
                break
            if codigo[i] != "\n":
                resultado[i] = " "
            i += 1
        i += 1
    return "".join(resultado)


def _linha_de(posicao: int, quebras: list[int]) -> int:
    return bisect.bisect_right(quebras, posicao) + 1


def _fim_bloco(estrutura: str, abertura: int) -> int:
    profundidade = 0
    for posicao in range(abertura, len(estrutura)):
        if estrutura[posicao] == "{":
            profundidade += 1
        elif estrutura[posicao] == "}":
            profundidade -= 1
            if profundidade == 0:
                return posicao
    return len(estrutura) - 1


def _profundidade(estrutura: str, abertura: int, posicao: int) -> int:
    trecho = estrutura[abertura:posicao]
    return trecho.count("{") - trecho.count("}")


def _parametros_java(texto: str) -> tuple[str, ...]:
    nomes = []
    for parametro in texto.split(","):
        sem_anotacoes = re.sub(
            r"@[A-Za-z0-9_$.]+(?:\s*\([^)]*\))?", " ", parametro
        )
        identificadores = PADRAO_IDENTIFICADOR.findall(sem_anotacoes)
        if identificadores:
            nomes.append(identificadores[-1])
    return tuple(nomes)


def _encontrar_classes(estrutura: str) -> list[Bloco]:
    classes = []
    for match in PADRAO_CLASSE.finditer(estrutura):
        abertura = estrutura.find("{", match.start(), match.end())
        classes.append(Bloco(
            nome=match.group("nome"),
            inicio=match.start(),
            abertura=abertura,
            fim=_fim_bloco(estrutura, abertura),
        ))
    return classes


def _encontrar_metodos(estrutura: str, classes: list[Bloco]) -> list[Bloco]:
    metodos = []
    for classe in classes:
        corpo = estrutura[classe.abertura + 1:classe.fim]
        deslocamento = classe.abertura + 1
        for match in PADRAO_METODO.finditer(corpo):
            inicio = deslocamento + match.start("nome")
            if _profundidade(estrutura, classe.abertura, inicio) != 1:
                continue
            abertura = estrutura.find(
                "{", deslocamento + match.start(), deslocamento + match.end()
            )
            metodos.append(Bloco(
                nome=match.group("nome"),
                inicio=inicio,
                abertura=abertura,
                fim=_fim_bloco(estrutura, abertura),
                parametros=_parametros_java(match.group("parametros")),
            ))
    return metodos


def _instrucoes(codigo: str):
    """Retorna instruções terminadas em ponto e vírgula com sua posição."""
    inicio = 0
    parenteses = 0
    for posicao, caractere in enumerate(codigo):
        if caractere == "(":
            parenteses += 1
        elif caractere == ")":
            parenteses = max(0, parenteses - 1)
        elif caractere == ";" and parenteses == 0:
            trecho = codigo[inicio:posicao + 1]
            trecho_antes_do_final = trecho[:-1]
            ultimo_delimitador = max(
                trecho_antes_do_final.rfind("{"),
                trecho_antes_do_final.rfind("}"),
                trecho_antes_do_final.rfind(";"),
            )
            if ultimo_delimitador >= 0:
                inicio_real = inicio + ultimo_delimitador + 1
                trecho = codigo[inicio_real:posicao + 1]
            else:
                inicio_real = inicio
            if trecho.strip():
                espacos_iniciais = len(trecho) - len(trecho.lstrip())
                yield inicio_real + espacos_iniciais, trecho.strip()
            inicio = posicao + 1


def _identificadores_fora_de_strings(texto: str) -> list[str]:
    return PADRAO_IDENTIFICADOR.findall(PADRAO_STRING.sub(" ", texto))


def _campos_no_texto(texto: str) -> list[str]:
    return sorted({
        campo
        for identificador in _identificadores_fora_de_strings(texto)
        if (campo := _campo_sensivel(identificador))
    })


def _metodo_em(posicao: int, metodos: list[Bloco]):
    return next(
        (metodo for metodo in metodos if metodo.abertura < posicao < metodo.fim),
        None,
    )


def _tem_protecao(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(marcador in texto_lower for marcador in MARCADORES_CRIPTOGRAFIA)


def analisar_java(caminho: str):
    """Analisa um arquivo .java e retorna objetos Vulnerability."""
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    from code_analyzer import Vulnerability

    with open(caminho, encoding="utf-8") as arquivo:
        codigo = arquivo.read()

    linhas = codigo.splitlines()
    quebras = [pos for pos, caractere in enumerate(codigo) if caractere == "\n"]
    sem_comentarios = _mascarar_comentarios(codigo)
    estrutura = _mascarar_strings(sem_comentarios)
    classes = _encontrar_classes(estrutura)
    metodos = _encontrar_metodos(estrutura, classes)
    resultados = []
    chaves_adicionadas = set()

    def adicionar(posicao, categoria, descricao, risco, artigo):
        numero = _linha_de(posicao, quebras)
        chave = (numero, categoria)
        if chave in chaves_adicionadas:
            return
        chaves_adicionadas.add(chave)
        trecho = linhas[numero - 1].strip()[:120] if linhas else ""
        resultados.append(Vulnerability(
            arquivo=caminho,
            linha=numero,
            categoria=categoria,
            descricao=descricao,
            risco=risco,
            artigo_lgpd=artigo,
            trecho=trecho,
        ))

    # Regras por instrução: atribuições, criptografia, logs e transferências.
    for posicao, instrucao in _instrucoes(sem_comentarios):
        cripto = PADRAO_CRIPTOGRAFIA_FRACA.search(instrucao)
        if cripto:
            algoritmo = (
                "SHA-1"
                if re.search(r"sha-?1", cripto.group(0), re.IGNORECASE)
                else "MD5"
            )
            adicionar(
                posicao + cripto.start(),
                "CRIPTOGRAFIA_FRACA",
                f"Uso de algoritmo criptográfico fraco no Java: "
                f"{algoritmo}.",
                "ALTO",
                "Art. 46 — Segurança e prevenção",
            )

        log = PADRAO_LOG.search(instrucao)
        if log:
            campos = _campos_no_texto(log.group("args"))
            if campos:
                adicionar(
                    posicao + log.start(),
                    "DADO_EM_LOG",
                    "Dado pessoal pode estar sendo registrado em log Java: "
                    f"{', '.join(campos)}.",
                    "ALTO",
                    "Art. 46 — Segurança; Art. 6º, III — Necessidade",
                )

        instrucao_lower = re.sub(r"\s+", "", instrucao.lower())
        if (
            any(marcador in instrucao_lower for marcador in MARCADORES_TRANSFERENCIA)
            and not any(marcador in instrucao_lower for marcador in MARCADORES_BASE_LEGAL)
        ):
            campos = _campos_no_texto(instrucao)
            if campos:
                adicionar(
                    posicao,
                    "TRANSFERENCIA_SEM_BASE_LEGAL",
                    "Possível envio de dado pessoal para serviço externo no Java: "
                    f"{', '.join(campos)}. Verifique e documente a base legal.",
                    "ALTO",
                    "Art. 7º — Hipóteses de tratamento; "
                    "Art. 33 — Transferência internacional",
                )

        atribuicao = PADRAO_ATRIBUICAO.search(instrucao)
        if not atribuicao:
            continue

        nome = atribuicao.group("nome")
        valor = atribuicao.group("valor").strip()
        campo = _campo_sensivel(nome)
        if not campo:
            continue

        metodo = _metodo_em(posicao, metodos)
        if metodo and any(parte in metodo.nome.lower() for parte in METODOS_EXCLUSAO):
            continue

        literal = PADRAO_LITERAL_STRING.match(valor)
        if literal:
            if literal.group("valor"):
                adicionar(
                    posicao + atribuicao.start("nome"),
                    "DADO_HARDCODED",
                    f"Campo sensível '{campo}' recebe valor literal no código Java.",
                    "ALTO",
                    "Art. 46 — Segurança e prevenção",
                )
            continue

        valor_identificadores = PADRAO_IDENTIFICADOR.findall(valor)
        atribuicao_direta_parametro = (
            metodo
            and len(valor_identificadores) == 1
            and valor_identificadores[0] == nome
            and nome in metodo.parametros
        )
        nome_protegido = any(
            marcador in nome.lower()
            for marcador in ("hash", "hashed", "encrypt", "encrypted", "cipher")
        )
        if (
            valor.lower() not in {"null", "optional.empty()"}
            and not atribuicao_direta_parametro
            and not nome_protegido
            and not _tem_protecao(valor)
        ):
            adicionar(
                posicao + atribuicao.start("nome"),
                "DADO_SEM_CRIPTOGRAFIA",
                f"Campo '{campo}' recebe dado pessoal sem indício de "
                "criptografia ou hash no código Java.",
                "MEDIO",
                "Art. 46 — Segurança e prevenção",
            )

    # Coleta excessiva em métodos e construtores.
    for metodo in metodos:
        campos = [
            campo for parametro in metodo.parametros
            if (campo := _campo_sensivel(parametro))
        ]
        if len(campos) >= 4:
            adicionar(
                metodo.inicio,
                "COLETA_EXCESSIVA",
                f"Método '{metodo.nome}' recebe {len(campos)} campos sensíveis "
                f"({', '.join(campos)}). Verifique se todos são necessários.",
                "MEDIO",
                "Art. 6º, III — Necessidade; Art. 6º, I — Finalidade",
            )

    # Classes-modelo com dados pessoais devem oferecer exclusão ou anonimização.
    for classe in classes:
        campos = []
        metodos_classe = [
            metodo for metodo in metodos
            if classe.abertura < metodo.inicio < classe.fim
        ]
        for posicao, instrucao in _instrucoes(
            sem_comentarios[classe.abertura + 1:classe.fim]
        ):
            posicao_absoluta = classe.abertura + 1 + posicao
            if _profundidade(estrutura, classe.abertura, posicao_absoluta) != 1:
                continue
            campo_match = PADRAO_CAMPO.search(instrucao)
            if campo_match and (campo := _campo_sensivel(campo_match.group("nome"))):
                campos.append(campo_match.group("nome"))

        tem_exclusao = any(
            parte in metodo.nome.lower()
            for metodo in metodos_classe
            for parte in METODOS_EXCLUSAO
        )
        if campos and not tem_exclusao:
            adicionar(
                classe.inicio,
                "AUSENCIA_EXCLUSAO",
                f"Classe '{classe.nome}' contém campos sensíveis "
                f"({', '.join(campos[:3])}) mas não define método de exclusão "
                "ou anonimização.",
                "MEDIO",
                "Art. 18, IV — Direito à eliminação dos dados",
            )

    return sorted(resultados, key=lambda item: (item.linha, item.categoria))

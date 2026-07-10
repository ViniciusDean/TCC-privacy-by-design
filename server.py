"""API HTTP do Privacy Scanner.

O contrato público deliberadamente não inclui linhas de código, valores de
campos ou trechos de schema. Os detalhes necessários para revisão ficam no
arquivo local analisado; a API retorna apenas evidência segura e metadados de
escopo auditáveis.
"""

import base64
import json
import os
import sys
import tempfile

from flask import Flask, jsonify, request

from code_analyzer import (
    DIRETORIOS_IGNORADOS,
    analisar_arquivo_com_escopo,
    analisar_diretorio_com_escopo,
    caminho_deve_ser_ignorado,
    carregar_padroes_ignorados,
    finalizar_escopo_varredura,
    novo_escopo_varredura,
)
from db_analyzer import analisar_banco_com_escopo
from reporter import (
    AVISO_ESCOPO_ANALISE,
    CRITERIO_INDICADOR_TECNICO,
    Reporter,
    VERSAO_FERRAMENTA,
    combinar_escopos,
    construir_resumo,
    serializar_achados,
)


app = Flask(__name__)
port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 5000

SERVICE = "privacy-scanner"
VERSION = VERSAO_FERRAMENTA
DB_EXTENSIONS = (".db", ".sqlite", ".sqlite3")


def _escopo_indisponivel(status: str = "invalid") -> dict:
    return {
        "tipo": "desconhecido",
        "alvo": None,
        "status": status,
        "arquivos_elegiveis": 0,
        "arquivos_analisados": 0,
        "arquivos_ignorados": 0,
        "arquivos_falhos": 0,
        "erros": [],
    }


def _indicador_disponivel(escopo: dict) -> bool:
    return (
        escopo.get("status") in {"complete", "partial"}
        and escopo.get("arquivos_analisados", 0) > 0
    )


def _envelope(
    resultados,
    escopo: dict,
    *,
    success: bool,
    error: dict | None = None,
) -> dict:
    """Monta um único contrato para todos os endpoints de análise."""
    resumo = construir_resumo(
        resultados,
        indicador_disponivel=_indicador_disponivel(escopo),
    )
    achados = serializar_achados(resultados)
    payload = {
        "success": success,
        "status": escopo["status"],
        "service": SERVICE,
        "version": VERSION,
        "aviso_escopo": AVISO_ESCOPO_ANALISE,
        "criterio_indicador": CRITERIO_INDICADOR_TECNICO,
        "escopo": escopo,
        "achados": achados,
        "resumo": resumo,
        # Aliases de transição para consumidores anteriores.
        "vulnerabilities": achados,
        "vulnerabilidades": achados,
        "summary": resumo,
        "sumario": resumo,
        "count": len(achados),
        "indicador_tecnico": resumo["indicador_tecnico"],
        "score_conformidade": resumo["score_conformidade"],
    }
    if error is not None:
        payload["error"] = error
        payload["message"] = error["mensagem"]
    return payload


def _erro(
    http_status: int,
    codigo: str,
    mensagem: str,
    escopo: dict | None = None,
) -> tuple:
    escopo = escopo or _escopo_indisponivel()
    return jsonify(_envelope(
        [],
        escopo,
        success=False,
        error={"codigo": codigo, "mensagem": mensagem},
    )), http_status


def _json_object() -> tuple[dict | None, tuple[str, str] | None]:
    """Lê JSON de forma previsível, sem propagar 415/400 como erro interno."""
    if not request.is_json:
        return None, (
            "JSON_OBRIGATORIO",
            "Envie um objeto JSON com Content-Type application/json.",
        )
    data = request.get_json(silent=True)
    if data is None:
        return None, ("JSON_INVALIDO", "O corpo da requisição não contém JSON válido.")
    if not isinstance(data, dict):
        return None, ("JSON_ESTRUTURA_INVALIDA", "O corpo JSON deve ser um objeto.")
    return data, None


def _alvo(
    data: dict,
    campo: str,
    tipo_esperado: str,
) -> tuple[str | None, tuple[int, str, str] | None]:
    valor = data.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        return None, (400, "CAMPO_OBRIGATORIO", f"O campo '{campo}' é obrigatório.")

    caminho = os.path.abspath(valor)
    if not os.path.exists(caminho):
        return None, (404, "ALVO_NAO_ENCONTRADO", "O alvo informado não foi encontrado.")
    if tipo_esperado == "arquivo" and not os.path.isfile(caminho):
        return None, (422, "TIPO_DE_ALVO_INVALIDO", "O alvo informado deve ser um arquivo.")
    if tipo_esperado == "diretorio" and not os.path.isdir(caminho):
        return None, (422, "TIPO_DE_ALVO_INVALIDO", "O alvo informado deve ser um diretório.")
    return caminho, None


def _contar_bancos(diretorio: str) -> int:
    total = 0
    try:
        for _, _, arquivos in os.walk(diretorio):
            total += sum(nome.lower().endswith(DB_EXTENSIONS) for nome in arquivos)
    except OSError:
        pass
    return total


def analisar_bancos_diretorio_com_escopo(directory: str) -> tuple[list, dict]:
    """Analisa SQLite por arquivo e mantém resultados válidos em falhas parciais."""
    raiz = os.path.abspath(directory)
    escopo = novo_escopo_varredura(raiz, "diretorio")
    resultados = []
    padroes_ignorados = carregar_padroes_ignorados(raiz)

    for root, dirs, files in os.walk(raiz):
        dirs_mantidos = []
        for nome in dirs:
            caminho_dir = os.path.join(root, nome)
            relativo = os.path.relpath(caminho_dir, raiz)
            ignorado = (
                nome.lower() in DIRETORIOS_IGNORADOS
                or caminho_deve_ser_ignorado(relativo, padroes_ignorados, diretorio=True)
            )
            if ignorado:
                escopo["arquivos_ignorados"] += _contar_bancos(caminho_dir)
            else:
                dirs_mantidos.append(nome)
        dirs[:] = dirs_mantidos

        for nome in files:
            if not nome.lower().endswith(DB_EXTENSIONS):
                continue
            caminho = os.path.join(root, nome)
            relativo = os.path.relpath(caminho, raiz)
            if caminho_deve_ser_ignorado(relativo, padroes_ignorados):
                escopo["arquivos_ignorados"] += 1
                continue

            achados_arquivo, escopo_arquivo = analisar_banco_com_escopo(caminho)
            resultados.extend(achados_arquivo)
            for chave in (
                "arquivos_elegiveis",
                "arquivos_analisados",
                "arquivos_ignorados",
                "arquivos_falhos",
            ):
                escopo[chave] += escopo_arquivo[chave]
            escopo["erros"].extend(escopo_arquivo["erros"])

    return resultados, finalizar_escopo_varredura(escopo)


def _analisar_diretorio(directory: str) -> tuple[list, dict]:
    achados_codigo, escopo_codigo = analisar_diretorio_com_escopo(directory)
    achados_banco, escopo_banco = analisar_bancos_diretorio_com_escopo(directory)
    escopo = combinar_escopos([escopo_codigo, escopo_banco], directory)
    escopo["tipo"] = "diretorio"
    return achados_codigo + achados_banco, escopo


def _resposta_varredura(resultados, escopo: dict):
    if escopo["status"] in {"complete", "partial"}:
        return jsonify(_envelope(resultados, escopo, success=True))

    codigo = "ESCOPO_VAZIO" if escopo["status"] == "empty" else "ANALISE_SEM_RESULTADO"
    mensagem = (
        "Nenhum arquivo elegível foi analisado; o indicador técnico não foi calculado."
        if codigo == "ESCOPO_VAZIO"
        else "Nenhum arquivo pôde ser analisado; corrija os erros de escopo e tente novamente."
    )
    return _erro(422, codigo, mensagem, escopo)


@app.route("/health", methods=["GET"])
def health():
    """Identidade estável consumida pela extensão antes de cada análise."""
    return jsonify({"status": "ok", "service": SERVICE, "version": VERSION})


@app.route("/api/analyze-file", methods=["POST"])
def analyze_file():
    data, erro_json = _json_object()
    if erro_json:
        return _erro(400, *erro_json)
    filepath, erro_alvo = _alvo(data, "filepath", "arquivo")
    if erro_alvo:
        return _erro(*erro_alvo)
    if not filepath.lower().endswith((".py", ".java")):
        return _erro(422, "TIPO_NAO_SUPORTADO", "O arquivo deve possuir extensão .py ou .java.")

    try:
        resultados, escopo = analisar_arquivo_com_escopo(filepath)
    except OSError:
        return _erro(422, "ALVO_INACESSIVEL", "O arquivo não pôde ser acessado para análise.")
    return _resposta_varredura(resultados, escopo)


@app.route("/api/analyze-directory", methods=["POST"])
def analyze_directory():
    data, erro_json = _json_object()
    if erro_json:
        return _erro(400, *erro_json)
    directory, erro_alvo = _alvo(data, "directory", "diretorio")
    if erro_alvo:
        return _erro(*erro_alvo)

    try:
        resultados, escopo = _analisar_diretorio(directory)
    except OSError:
        return _erro(422, "ALVO_INACESSIVEL", "O diretório não pôde ser percorrido para análise.")
    return _resposta_varredura(resultados, escopo)


@app.route("/api/analyze-database", methods=["POST"])
def analyze_database():
    data, erro_json = _json_object()
    if erro_json:
        return _erro(400, *erro_json)
    database, erro_alvo = _alvo(data, "database", "arquivo")
    if erro_alvo:
        return _erro(*erro_alvo)

    try:
        resultados, escopo = analisar_banco_com_escopo(database)
    except OSError:
        return _erro(422, "ALVO_INACESSIVEL", "O banco não pôde ser acessado para análise.")
    return _resposta_varredura(resultados, escopo)


@app.route("/api/export", methods=["POST"])
def export_report():
    data, erro_json = _json_object()
    if erro_json:
        return _erro(400, *erro_json)
    directory, erro_alvo = _alvo(data, "directory", "diretorio")
    if erro_alvo:
        return _erro(*erro_alvo)

    format_type = data.get("format", "html")
    if not isinstance(format_type, str) or format_type.lower() not in {"html", "json", "pdf"}:
        return _erro(400, "FORMATO_INVALIDO", "O formato deve ser html, json ou pdf.")
    format_type = format_type.lower()

    try:
        resultados, escopo = _analisar_diretorio(directory)
    except OSError:
        return _erro(422, "ALVO_INACESSIVEL", "O diretório não pôde ser percorrido para análise.")
    if escopo["status"] not in {"complete", "partial"}:
        return _resposta_varredura(resultados, escopo)

    reporter = Reporter(alvo_codigo=directory)
    reporter.resultados = resultados
    reporter.escopo = escopo
    reporter.resultados.sort(key=lambda v: (v.risco, v.arquivo, v.linha))

    try:
        if format_type == "json":
            content = json.dumps(reporter.dados_publicos(), ensure_ascii=False, indent=2)
            encoding = "utf-8"
        elif format_type == "pdf":
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                temp_path = tmp.name
            try:
                reporter.exportar_pdf(temp_path)
                with open(temp_path, "rb") as arquivo_pdf:
                    content = base64.b64encode(arquivo_pdf.read()).decode("ascii")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            encoding = "base64"
        else:
            content = reporter.gerar_html()
            encoding = "utf-8"
    except (OSError, RuntimeError, ValueError):
        return _erro(500, "EXPORTACAO_INDISPONIVEL", "Não foi possível gerar o relatório solicitado.", escopo)

    payload = _envelope(resultados, escopo, success=True)
    payload.update({"content": content, "format": format_type, "encoding": encoding})
    return jsonify(payload)


def generate_html_report(reporter: Reporter) -> str:
    """Mantido para compatibilidade com consumidores que chamam esta função."""
    return reporter.gerar_html()


if __name__ == "__main__":
    print(f"Privacy Scanner Server v{VERSION} iniciando na porta {port}...")
    print("Endpoints:")
    print("   GET  /health")
    print("   POST /api/analyze-file")
    print("   POST /api/analyze-directory")
    print("   POST /api/analyze-database")
    print("   POST /api/export")
    app.run(host="localhost", port=port, debug=False)

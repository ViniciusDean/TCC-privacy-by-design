"""
reporter.py
Agrega os resultados do code_analyzer e do db_analyzer,
classifica por risco e gera relatório em JSON e HTML.
"""

import json
import os
import html as html_lib
import hashlib
from datetime import datetime
from code_analyzer import (
    analisar_arquivo_com_escopo,
    analisar_diretorio_com_escopo,
    finalizar_escopo_varredura,
)
from db_analyzer import analisar_banco_com_escopo


# ─────────────────────────────────────────────────────────────────────────────
# Mapeamento de categoria → recomendação de correção
# ─────────────────────────────────────────────────────────────────────────────
RECOMENDACOES = {
    "DADO_HARDCODED": (
        "Remova valores literais de dados pessoais do código-fonte. "
        "Use variáveis de ambiente ou cofres de segredos (ex: .env, AWS Secrets Manager)."
    ),
    "DADO_SEM_CRIPTOGRAFIA": (
        "Aplique hash ou criptografia antes de armazenar o dado. "
        "Para senhas use bcrypt, argon2 ou um PasswordEncoder seguro. "
        "Para outros dados use AES-256 com gerenciamento adequado de chaves."
    ),
    "CRIPTOGRAFIA_FRACA": (
        "Substitua MD5/SHA1 por algoritmos modernos. "
        "Para senhas: bcrypt, argon2 ou PBKDF2. "
        "Para integridade: SHA-256 ou SHA-512."
    ),
    "DADO_EM_LOG": (
        "Remova dados pessoais de logs. Use IDs técnicos (UUID) no lugar de CPF/email. "
        "Se necessário logar, aplique mascaramento: '***.***.789-**'."
    ),
    "TRANSFERENCIA_SEM_BASE_LEGAL": (
        "Documente a base legal para cada transferência de dados a terceiros "
        "(Art. 7º LGPD). Considere anonimizar ou pseudonimizar antes de enviar."
    ),
    "COLETA_EXCESSIVA": (
        "Revise os parâmetros da função e colete apenas o mínimo necessário "
        "para a finalidade declarada (princípio da minimização — Art. 6º, III)."
    ),
    "AUSENCIA_EXCLUSAO": (
        "Verifique como o sistema atende pedidos de anonimização, bloqueio ou "
        "eliminação de dados desnecessários, excessivos ou tratados em desconformidade "
        "(Art. 18, IV). Para dados tratados com consentimento, revise os pedidos de "
        "eliminação conforme o Art. 18, VI, e as hipóteses de conservação do Art. 16. "
        "O controle pode existir em outra camada; um método na classe, isoladamente, "
        "não comprova o atendimento."
    ),
    "CAMPO_SEM_HASH": (
        "Verifique se o dado é realmente armazenado em texto puro. Quando "
        "necessário, aplique hash, criptografia ou pseudonimização conforme a "
        "finalidade; se a proteção já existir em outra camada, documente-a ou "
        "use nomenclatura que evidencie o controle."
    ),
    "AUSENCIA_SOFT_DELETE": (
        "Revise o fluxo de atendimento aos pedidos previstos no Art. 18, IV e VI, "
        "considerando a hipótese aplicável e a conservação autorizada pelo Art. 16. "
        "Uma coluna 'deleted_at' ou 'is_deleted' apenas marca exclusão lógica; "
        "por si só, não elimina os dados. Verifique a execução efetiva da medida "
        "solicitada e os controles existentes nas demais camadas."
    ),
    "AUSENCIA_RETENCAO": (
        "Documente a política de retenção e verifique se há rotina externa de "
        "expurgo. Se o controle ficar no schema, adicione coluna 'expires_at' "
        "ou campo equivalente e implemente a purga conforme a finalidade."
    ),
    "MISTURA_DADOS": (
        "Separe dados pessoais em tabela dedicada (ex: usuarios_dados_pessoais) "
        "vinculada por ID técnico. Facilita controle de acesso e exclusão seletiva."
    ),
    "AUSENCIA_CONSENTIMENTO": (
        "Verifique qual base legal do Art. 7º justifica o tratamento. Se for "
        "consentimento, registre aceite, data e versão da política; se for "
        "outra base legal, documente essa base no fluxo ou no modelo de dados."
    ),
    "DADO_SENSIVEL_COMO_PK": (
        "Substitua a PK por ID técnico (INTEGER AUTOINCREMENT ou UUID). "
        "Evite expor o identificador pessoal como chave entre contextos."
    ),
    "DADO_SENSIVEL_COMO_INDICE_UNICO": (
        "Avalie usar um ID técnico e proteger o identificador pessoal. "
        "Se a unicidade for necessária, documente a finalidade e restrinja o acesso."
    ),
}

ORDEM_RISCO = {"ALTO": 0, "MEDIO": 1, "BAIXO": 2}
VERSAO_FERRAMENTA = "1.2.3"

AVISO_ESCOPO_ANALISE = (
    "Os resultados representam indícios técnicos identificados por análise "
    "estática. Eles apoiam revisão de privacidade, mas não comprovam, sozinhos, "
    "conformidade ou desconformidade jurídica com a LGPD."
)

CRITERIO_INDICADOR_TECNICO = (
    "Indicador operacional: 100 - (ALTO * 10 + MEDIO * 5 + BAIXO * 2). "
    "Os pesos priorizam revisão por severidade e não representam métrica "
    "jurídica, estatística ou regulatória de conformidade."
)

EVIDENCIAS_SEGURAS = {
    "DADO_HARDCODED": "A regra identificou uma atribuição literal a um identificador classificado; o conteúdo foi ocultado.",
    "DADO_SEM_CRIPTOGRAFIA": "A regra não encontrou indício local de proteção no fluxo de armazenamento; o conteúdo foi ocultado.",
    "CRIPTOGRAFIA_FRACA": "A regra identificou uso de algoritmo criptográfico classificado como fraco.",
    "DADO_EM_LOG": "A regra identificou possível registro de dado pessoal em mecanismo de log; o conteúdo foi ocultado.",
    "TRANSFERENCIA_SEM_BASE_LEGAL": "A regra identificou possível envio a serviço externo sem marcador técnico de base legal.",
    "COLETA_EXCESSIVA": "A regra identificou concentração de campos classificados em uma mesma entrada.",
    "AUSENCIA_EXCLUSAO": "A regra não encontrou método de exclusão ou anonimização no modelo analisado.",
    "CAMPO_SEM_HASH": "O schema não evidenciou proteção no nome ou tipo do campo classificado; detalhes foram ocultados.",
    "AUSENCIA_SOFT_DELETE": "O schema não evidenciou mecanismo de exclusão lógica ou anonimização.",
    "AUSENCIA_RETENCAO": "O schema não evidenciou controle de retenção ou expurgo.",
    "MISTURA_DADOS": "O schema concentrou campos classificados e operacionais na mesma estrutura.",
    "AUSENCIA_CONSENTIMENTO": "O schema não evidenciou consentimento nem outro registro técnico de base legal.",
    "DADO_SENSIVEL_COMO_PK": "O schema usa um campo classificado como identificador primário.",
    "DADO_SENSIVEL_COMO_INDICE_UNICO": "O schema usa um identificador pessoal em índice único.",
}

DESCRICOES_SEGURAS = {
    "DADO_HARDCODED": "Possível dado pessoal literal identificado por análise estática.",
    "DADO_SEM_CRIPTOGRAFIA": "Possível armazenamento sem proteção evidenciada localmente.",
    "CRIPTOGRAFIA_FRACA": "Algoritmo criptográfico potencialmente fraco identificado.",
    "DADO_EM_LOG": "Possível exposição de dado pessoal em log identificada.",
    "TRANSFERENCIA_SEM_BASE_LEGAL": "Possível transferência para terceiro sem marcador técnico de base legal.",
    "COLETA_EXCESSIVA": "Possível coleta acima do mínimo necessário identificada.",
    "AUSENCIA_EXCLUSAO": "Mecanismo de exclusão ou anonimização não evidenciado na estrutura analisada.",
    "CAMPO_SEM_HASH": "Proteção do campo não evidenciada pelo schema analisado.",
    "AUSENCIA_SOFT_DELETE": "Controle de exclusão lógica ou anonimização não evidenciado pelo schema.",
    "AUSENCIA_RETENCAO": "Controle de retenção ou expurgo não evidenciado pelo schema.",
    "MISTURA_DADOS": "Separação entre dados classificados e operacionais deve ser revisada.",
    "AUSENCIA_CONSENTIMENTO": "Proteção/base legal não evidenciada pelo schema; requer revisão humana.",
    "DADO_SENSIVEL_COMO_PK": "Uso de identificador pessoal como chave primária deve ser revisado.",
    "DADO_SENSIVEL_COMO_INDICE_UNICO": "Uso de identificador pessoal em índice único deve ser revisado.",
}

REFERENCIAS_POTENCIAIS = {
    "DADO_HARDCODED": "Art. 46 — Segurança e prevenção",
    "DADO_SEM_CRIPTOGRAFIA": "Art. 46 — Segurança e prevenção",
    "CRIPTOGRAFIA_FRACA": "Art. 46 — Segurança e prevenção",
    "DADO_EM_LOG": "Art. 46 — Segurança | Art. 6º, III — Necessidade",
    "TRANSFERENCIA_SEM_BASE_LEGAL": "Art. 7º — Hipóteses de tratamento | Art. 33 — Transferência internacional",
    "COLETA_EXCESSIVA": "Art. 6º, I e III — Finalidade e necessidade",
    "AUSENCIA_EXCLUSAO": "Art. 18, IV e VI — Direitos conforme hipótese aplicável | Art. 16 — Conservação",
    "CAMPO_SEM_HASH": "Art. 46 — Segurança e prevenção",
    "AUSENCIA_SOFT_DELETE": "Art. 18, IV e VI — Direitos conforme hipótese aplicável | Art. 16 — Conservação",
    "AUSENCIA_RETENCAO": "Art. 15 — Término do tratamento | Art. 6º, I — Finalidade",
    "MISTURA_DADOS": "Art. 46 — Segurança | Privacy by Design — Separação",
    "AUSENCIA_CONSENTIMENTO": "Art. 7º — Bases legais para tratamento de dados pessoais",
    "DADO_SENSIVEL_COMO_PK": "Art. 46 — Segurança | Privacy by Design — Linkability",
    "DADO_SENSIVEL_COMO_INDICE_UNICO": "Art. 46 — Segurança | Privacy by Design — Linkability",
}

CATEGORIAS_PUBLICAS = {
    "AUSENCIA_CONSENTIMENTO": "PROTEÇÃO/BASE LEGAL NÃO EVIDENCIADA",
    "DADO_SENSIVEL_COMO_INDICE_UNICO": "IDENTIFICADOR PESSOAL EM ÍNDICE ÚNICO",
}


def status_score_tecnico(score: int) -> str:
    if score >= 80:
        return "Baixo risco técnico"
    if score >= 50:
        return "Revisar controles"
    return "Risco técnico crítico"


def _indicador_disponivel(escopo: dict | None) -> bool:
    if escopo is None:
        # Mantém compatibilidade para relatórios criados programaticamente com
        # resultados já validados pelo chamador.
        return True
    return (
        escopo.get("status") in {"complete", "partial"}
        and escopo.get("arquivos_analisados", 0) > 0
    )


def construir_resumo(resultados, indicador_disponivel: bool = True) -> dict:
    """Calcula o resumo bruto sem depender de filtros de interface."""
    por_risco = {"ALTO": 0, "MEDIO": 0, "BAIXO": 0}
    por_categoria = {}
    for achado in resultados:
        por_risco[achado.risco] = por_risco.get(achado.risco, 0) + 1
        por_categoria[achado.categoria] = por_categoria.get(achado.categoria, 0) + 1

    indicador = None
    if indicador_disponivel:
        indicador = max(0, 100 - (
            por_risco["ALTO"] * 10 +
            por_risco["MEDIO"] * 5 +
            por_risco["BAIXO"] * 2
        ))

    return {
        "total": len(resultados),
        "por_risco": por_risco,
        "por_categoria": por_categoria,
        "indicador_tecnico": indicador,
        "score_conformidade": indicador,
        "criterio_indicador": CRITERIO_INDICADOR_TECNICO,
        "aviso_escopo": AVISO_ESCOPO_ANALISE,
    }


def deduplicar_achados(resultados) -> list:
    """Remove duplicatas sem confundir regras distintas na mesma linha."""
    unicos = []
    vistos = set()
    for achado in resultados:
        arquivo = os.path.normcase(os.path.realpath(os.fspath(achado.arquivo)))
        localizador = str(
            getattr(achado, "localizador_interno", None)
            or getattr(achado, "trecho", "")
        )
        chave = (
            arquivo,
            int(getattr(achado, "linha", 0) or 0),
            str(achado.categoria),
            " ".join(localizador.lower().split()),
        )
        if chave in vistos:
            continue
        vistos.add(chave)
        unicos.append(achado)
    return unicos


def enriquecer_resumo_exibido(resumo_exibido: dict, resumo_bruto: dict) -> dict:
    """Explicita o efeito do perfil preservando os nomes legados exibidos."""
    resumo = dict(resumo_exibido)
    resumo.update({
        "total_exibido": resumo_exibido["total"],
        "total_bruto": resumo_bruto["total"],
        "ocultos_por_perfil": max(0, resumo_bruto["total"] - resumo_exibido["total"]),
        "por_risco_exibido": resumo_exibido["por_risco"],
        "por_risco_bruto": resumo_bruto["por_risco"],
        "indicador_tecnico_exibido": resumo_exibido["indicador_tecnico"],
        "indicador_tecnico_bruto": resumo_bruto["indicador_tecnico"],
    })
    return resumo


def combinar_escopos(escopos: list[dict], alvo: str | None = None) -> dict:
    """Combina escopos de código e banco em um único registro auditável."""
    if not escopos:
        return {
            "tipo": "misto",
            "alvo": os.path.abspath(alvo) if alvo else None,
            "status": "empty",
            "arquivos_elegiveis": 0,
            "arquivos_analisados": 0,
            "arquivos_ignorados": 0,
            "arquivos_falhos": 0,
            "erros": [],
        }

    combinado = {
        "tipo": escopos[0]["tipo"] if len(escopos) == 1 else "misto",
        "alvo": os.path.abspath(alvo) if alvo else None,
        "status": "pending",
        "arquivos_elegiveis": 0,
        "arquivos_analisados": 0,
        "arquivos_ignorados": 0,
        "arquivos_falhos": 0,
        "erros": [],
    }
    for escopo in escopos:
        for chave in (
            "arquivos_elegiveis",
            "arquivos_analisados",
            "arquivos_ignorados",
            "arquivos_falhos",
        ):
            combinado[chave] += escopo.get(chave, 0)
        combinado["erros"].extend(escopo.get("erros", []))

    return finalizar_escopo_varredura(combinado)


def _caminho_identidade(arquivo: str, scope_root: str | None) -> str:
    """Normaliza a localizacao sem incorporar o caminho absoluto da maquina."""
    arquivo_absoluto = os.path.abspath(arquivo)
    if scope_root:
        raiz = os.path.abspath(scope_root)
        if os.path.isfile(raiz):
            raiz = os.path.dirname(raiz)
        try:
            relativo = os.path.relpath(arquivo_absoluto, raiz)
            if relativo != os.pardir and not relativo.startswith(os.pardir + os.sep):
                return relativo.replace("\\", "/").lower()
        except ValueError:
            pass
    return os.path.basename(arquivo_absoluto).lower()


def serializar_achado(achado, scope_root: str | None = None) -> dict:
    """Converte um achado interno em contrato público sem trecho bruto.

    O campo legado ``trecho`` é mantido somente como alias da evidência segura;
    nenhum serializador deve usar o atributo interno de mesmo nome.
    """
    categoria = str(achado.categoria)
    risco = str(achado.risco) if achado.risco in ORDEM_RISCO else "NAO_CLASSIFICADO"
    risco_base = str(getattr(achado, "risco_base", None) or risco)
    confianca = str(getattr(achado, "confianca", "ALTA"))
    evidencia = EVIDENCIAS_SEGURAS.get(
        categoria,
        "Regra estática acionada; detalhes originais foram ocultados para revisão local.",
    )
    arquivo = os.fspath(achado.arquivo)
    linha = int(achado.linha or 0)
    caminho_identidade = _caminho_identidade(arquivo, scope_root)
    localizador = str(
        getattr(achado, "localizador_interno", None)
        or getattr(achado, "trecho", "")
    )
    localizador = " ".join(localizador.lower().split())
    localizador_hash = hashlib.sha256(localizador.encode("utf-8")).hexdigest()[:16]
    finding_id = hashlib.sha256(
        f"v2\0{caminho_identidade}\0{linha}\0{categoria}\0{localizador_hash}".encode("utf-8")
    ).hexdigest()[:20]
    finding_id_legacy = hashlib.sha256(
        f"{arquivo}\0{linha}\0{categoria}\0{risco}".encode("utf-8")
    ).hexdigest()[:20]
    suppression_id = hashlib.sha256(
        f"s1\0{caminho_identidade}\0{linha}\0{categoria}\0{localizador_hash}".encode("utf-8")
    ).hexdigest()[:24]
    return {
        "finding_id": finding_id,
        "finding_id_legacy": finding_id_legacy,
        "suppression_id": suppression_id,
        "arquivo": arquivo,
        "linha": linha,
        "categoria": categoria,
        "categoria_publica": CATEGORIAS_PUBLICAS.get(categoria, categoria),
        "risco": risco,
        "risco_base": risco_base,
        "confianca": confianca,
        "descricao": DESCRICOES_SEGURAS.get(
            categoria,
            "Indício técnico identificado por análise estática; requer revisão humana.",
        ),
        "artigo_lgpd": REFERENCIAS_POTENCIAIS.get(
            categoria,
            "Referência normativa potencial; requer revisão humana.",
        ),
        "recomendacao": RECOMENDACOES.get(
            categoria,
            "Revise o achado localmente e documente o controle técnico aplicável.",
        ),
        "evidencia_segura": evidencia,
        "trecho": evidencia,
    }


def serializar_achados(resultados, scope_root: str | None = None) -> list[dict]:
    return [serializar_achado(achado, scope_root) for achado in resultados]


# ─────────────────────────────────────────────────────────────────────────────
# Gerador de relatório
# ─────────────────────────────────────────────────────────────────────────────
class Reporter:

    def __init__(self, alvo_codigo: str = None, alvo_banco: str = None):
        self.alvo_codigo = alvo_codigo
        self.alvo_banco  = alvo_banco
        self.timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.resultados  = []
        self.resultados_brutos: list | None = None
        self.escopo: dict | None = None
        self.perfil_analise: dict | None = None

    def _scope_root(self) -> str | None:
        alvo = self.alvo_codigo or self.alvo_banco
        if not alvo:
            return None
        return alvo if os.path.isdir(alvo) else os.path.dirname(os.path.abspath(alvo))

    def coletar(self):
        if not self.alvo_codigo and not self.alvo_banco:
            raise ValueError("Informe ao menos um alvo de código ou banco SQLite.")

        self.resultados = []
        self.resultados_brutos = None
        escopos = []
        if self.alvo_codigo:
            if os.path.isfile(self.alvo_codigo):
                resultados, escopo = analisar_arquivo_com_escopo(self.alvo_codigo)
            elif os.path.isdir(self.alvo_codigo):
                resultados, escopo = analisar_diretorio_com_escopo(self.alvo_codigo)
            else:
                raise FileNotFoundError(f"Alvo de código não encontrado: {self.alvo_codigo}")
            self.resultados += resultados
            escopos.append(escopo)

        if self.alvo_banco:
            resultados, escopo = analisar_banco_com_escopo(self.alvo_banco)
            self.resultados += resultados
            escopos.append(escopo)

        self.resultados = deduplicar_achados(self.resultados)
        self.escopo = combinar_escopos(escopos)

        # Ordena: ALTO → MEDIO → BAIXO, depois por arquivo e linha
        self.resultados.sort(
            key=lambda v: (ORDEM_RISCO.get(v.risco, 9), v.arquivo, v.linha)
        )
        return self

    # ── Sumário em texto para o terminal ─────────────────────────────────────
    def _sumario(self) -> dict:
        return construir_resumo(
            self.resultados,
            indicador_disponivel=_indicador_disponivel(self.escopo),
        )

    def dados_publicos(self) -> dict:
        """Retorna o contrato serializável usado em JSON e pela API."""
        resultados_brutos = deduplicar_achados(
            self.resultados_brutos if self.resultados_brutos is not None else self.resultados
        )
        self.resultados = deduplicar_achados(self.resultados)
        resumo_exibido = self._sumario()
        resumo_bruto = construir_resumo(
            resultados_brutos,
            indicador_disponivel=_indicador_disponivel(self.escopo),
        )
        resumo = enriquecer_resumo_exibido(resumo_exibido, resumo_bruto)
        achados = serializar_achados(self.resultados, self._scope_root())
        return {
            "ferramenta": "Privacy Scanner — TCC FATEC",
            "versao": VERSAO_FERRAMENTA,
            "timestamp": self.timestamp,
            "status": self.escopo.get("status") if self.escopo else "complete",
            "aviso_escopo": AVISO_ESCOPO_ANALISE,
            "criterio_indicador": CRITERIO_INDICADOR_TECNICO,
            "escopo": self.escopo,
            "perfil_analise": self.perfil_analise,
            "resumo": resumo,
            "sumario": resumo,
            "summary": resumo,
            "achados": achados,
            "vulnerabilidades": achados,
            "vulnerabilities": achados,
        }

    # ── Exportar JSON ─────────────────────────────────────────────────────────
    def exportar_json(self, caminho: str):
        payload = self.dados_publicos()
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"JSON gerado: {caminho}")

    # ── Exportar HTML ─────────────────────────────────────────────────────────
    def gerar_html(self) -> str:
        """Retorna o relatorio HTML em memoria."""
        sumario = self.dados_publicos()["resumo"]
        score = sumario["indicador_tecnico"]
        if score is None:
            raise ValueError("Não é possível gerar relatório para escopo vazio, inválido ou sem análise concluída.")
        cor_score = "#15803d" if score >= 80 else "#b45309" if score >= 50 else "#b91c1c"
        status_score = status_score_tecnico(score)

        arquivos = sorted({v.arquivo for v in self.resultados if v.arquivo})
        arquivos_python = sum(1 for a in arquivos if a.lower().endswith(".py"))
        arquivos_java = sum(1 for a in arquivos if a.lower().endswith(".java"))
        bancos_sqlite = sum(1 for a in arquivos if a.lower().endswith((".db", ".sqlite", ".sqlite3")))

        def esc(valor) -> str:
            return html_lib.escape(str(valor)) if valor is not None else ""

        def barra(label, count, cor):
            total = max(sumario["total"], 1)
            largura = int((count / total) * 100)
            return f"""
            <div class="risk-row">
              <div class="risk-label">{label}</div>
              <div class="risk-track">
                <div class="risk-fill" style="width:{largura}%;background:{cor}"></div>
              </div>
              <div class="risk-count">{count}</div>
            </div>"""

        linhas_tabela = ""
        for idx, v in enumerate(self.resultados, start=1):
            achado = serializar_achado(v, self._scope_root())
            badge_risco = {
                "ALTO": '<span class="badge alto">ALTO</span>',
                "MEDIO": '<span class="badge medio">MEDIO</span>',
                "BAIXO": '<span class="badge baixo">BAIXO</span>',
            }.get(achado["risco"], esc(achado["risco"]))

            local = (
                f"{os.path.basename(achado['arquivo'])}:{achado['linha']}"
                if achado["linha"] > 0 else os.path.basename(achado["arquivo"])
            )
            evidencia = f"<span>{esc(achado['evidencia_segura'])}</span>"

            risco_ordem = {"ALTO": 3, "MEDIO": 2, "BAIXO": 1}.get(achado["risco"], 0)
            linhas_tabela += f"""
            <tr data-risk="{esc(achado['risco'])}" data-risk-order="{risco_ordem}">
              <td class="index">{idx}</td>
              <td>{badge_risco}</td>
              <td><strong>{esc(achado['categoria_publica'])}</strong></td>
              <td>{esc(local)}</td>
              <td>{esc(achado['artigo_lgpd'])}</td>
              <td>{esc(achado['descricao'])}</td>
              <td>{esc(achado['recomendacao'])}</td>
              <td>{evidencia}</td>
            </tr>"""

        if not linhas_tabela:
            linhas_tabela = """
            <tr>
              <td colspan="8" class="empty-state">
                Nenhum achado tecnico encontrado nos alvos analisados.
              </td>
            </tr>"""

        barras = (
            barra("ALTO", sumario["por_risco"]["ALTO"], "#dc2626") +
            barra("MEDIO", sumario["por_risco"]["MEDIO"], "#d97706") +
            barra("BAIXO", sumario["por_risco"]["BAIXO"], "#2563eb")
        )

        alvo_codigo = esc(self.alvo_codigo or "Nao informado")
        alvo_banco = esc(self.alvo_banco or "Nao informado")
        timestamp = esc(self.timestamp)
        aviso_escopo = esc(AVISO_ESCOPO_ANALISE)
        perfil_nome = esc((self.perfil_analise or {}).get("preset", "nao informado"))

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Privacy Scanner LGPD - Relatorio Tecnico de Privacidade</title>
  <style>
    :root {{
      --bg: #f5f7fb;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #64748b;
      --line: #e2e8f0;
      --navy: #18233f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Segoe UI", Arial, sans-serif;
      font-size: 14px;
      line-height: 1.45;
    }}
    header {{
      background: var(--navy);
      color: #fff;
      padding: 28px 40px;
    }}
    .header-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 24px;
      align-items: end;
      max-width: 1280px;
      margin: 0 auto;
    }}
    h1 {{ margin: 0 0 6px; font-size: 24px; font-weight: 700; letter-spacing: 0; }}
    .subtitle, .meta, .muted {{ color: var(--muted); }}
    header .subtitle, header .meta {{ color: rgba(255,255,255,.76); }}
    .score-pill {{
      min-width: 150px;
      text-align: center;
      background: rgba(255,255,255,.1);
      border: 1px solid rgba(255,255,255,.18);
      border-radius: 8px;
      padding: 12px 16px;
    }}
    .score-pill strong {{ display: block; font-size: 30px; line-height: 1; color: #fff; }}
    main {{ max-width: 1280px; margin: 0 auto; padding: 28px 40px 40px; }}
    .section {{ margin-bottom: 24px; }}
    .section h2 {{ margin: 0 0 12px; font-size: 16px; font-weight: 700; }}
    .cards {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }}
    .card, .panel, .table-wrap {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .card {{ padding: 16px; min-height: 94px; }}
    .card .num {{ font-size: 30px; font-weight: 800; line-height: 1; color: var(--ink); }}
    .card .lbl {{ margin-top: 8px; font-size: 12px; color: var(--muted); }}
    .card.score {{ border-top: 4px solid {cor_score}; }}
    .card.score .num {{ color: {cor_score}; }}
    .panel {{ padding: 18px; }}
    .notice {{
      background: #fffbeb;
      border: 1px solid #fcd34d;
      border-left: 4px solid #d97706;
      border-radius: 8px;
      padding: 12px 14px;
      color: #78350f;
      font-size: 13px;
    }}
    .notice strong {{ display: block; margin-bottom: 4px; color: #78350f; }}
    .targets {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .target-box {{ border: 1px solid var(--line); border-radius: 8px; padding: 12px; background: #fbfdff; }}
    .target-box span {{ display: block; color: var(--muted); font-size: 12px; margin-bottom: 4px; }}
    .target-box code {{ word-break: break-all; }}
    .risk-row {{ display: grid; grid-template-columns: 72px minmax(0, 1fr) 36px; gap: 12px; align-items: center; margin: 10px 0; }}
    .risk-label, .risk-count {{ font-size: 12px; font-weight: 700; }}
    .risk-count {{ text-align: right; }}
    .risk-track {{ height: 12px; background: #edf2f7; border-radius: 999px; overflow: hidden; }}
    .risk-fill {{ height: 100%; min-width: 3px; border-radius: 999px; }}
    .table-wrap {{ overflow: hidden; }}
    .table-toolbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      padding: 12px;
      border-bottom: 1px solid var(--line);
      background: #fbfdff;
    }}
    .filter-group {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .filter-btn {{
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
    }}
    .filter-btn.active {{
      background: #18233f;
      border-color: #18233f;
      color: #fff;
    }}
    .table-count {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .table-scroll {{ overflow-x: auto; }}
    table {{ width: 100%; min-width: 1080px; border-collapse: collapse; }}
    th, td {{ padding: 11px 12px; border-bottom: 1px solid var(--line); vertical-align: top; text-align: left; }}
    th {{ background: #f8fafc; color: #334155; font-size: 12px; font-weight: 700; white-space: nowrap; }}
    th.sortable {{ cursor: pointer; user-select: none; }}
    th.sortable::after {{ content: "  sort"; color: #94a3b8; font-weight: 400; }}
    th.sortable.sort-asc::after {{ content: "  asc"; color: #18233f; }}
    th.sortable.sort-desc::after {{ content: "  desc"; color: #18233f; }}
    td {{ font-size: 12px; }}
    tr:last-child td {{ border-bottom: 0; }}
    .index {{ width: 44px; color: var(--muted); text-align: right; }}
    .badge {{ display: inline-block; border-radius: 999px; padding: 3px 9px; font-size: 11px; font-weight: 800; white-space: nowrap; }}
    .badge.alto {{ color: #991b1b; background: #fee2e2; }}
    .badge.medio {{ color: #92400e; background: #fef3c7; }}
    .badge.baixo {{ color: #1e40af; background: #dbeafe; }}
    code {{
      display: inline-block;
      max-width: 360px;
      background: #f1f5f9;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 2px 6px;
      color: #0f172a;
      font-family: Consolas, "Courier New", monospace;
      font-size: 11px;
      word-break: break-word;
    }}
    .empty-state {{ padding: 28px; text-align: center; color: #15803d; font-weight: 700; }}
    footer {{ max-width: 1280px; margin: 0 auto; padding: 0 40px 28px; color: var(--muted); font-size: 12px; }}
    @media print {{
      body {{ background: #fff; }}
      header {{ padding: 22px 28px; }}
      main {{ padding: 22px 28px; }}
      .table-scroll {{ overflow: visible; }}
      table {{ min-width: 0; }}
    }}
    @media (max-width: 900px) {{
      header, main, footer {{ padding-left: 18px; padding-right: 18px; }}
      .header-grid, .targets {{ grid-template-columns: 1fr; }}
      .cards {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="header-grid">
      <div>
        <h1>Privacy Scanner LGPD</h1>
        <div class="subtitle">Relatorio tecnico de indicios de risco a privacidade em codigo Python, Java e SQLite.</div>
        <div class="meta">Gerado em {timestamp} | Perfil: {perfil_nome} | Privacy by Design no ciclo de desenvolvimento</div>
      </div>
      <div class="score-pill"><strong>{score}/100</strong><span>{status_score}</span></div>
    </div>
  </header>
  <main>
    <section class="section">
      <div class="notice"><strong>Limite da analise</strong>{aviso_escopo}</div>
    </section>
    <section class="section">
      <div class="cards">
        <div class="card"><div class="num">{sumario['total_exibido']}</div><div class="lbl">Achados exibidos pelo perfil</div></div>
        <div class="card"><div class="num">{sumario['total_bruto']}</div><div class="lbl">Achados brutos</div></div>
        <div class="card"><div class="num">{sumario['ocultos_por_perfil']}</div><div class="lbl">Ocultos pelo perfil</div></div>
        <div class="card"><div class="num" style="color:#dc2626">{sumario['por_risco']['ALTO']}</div><div class="lbl">Risco alto</div></div>
        <div class="card"><div class="num" style="color:#d97706">{sumario['por_risco']['MEDIO']}</div><div class="lbl">Risco medio</div></div>
        <div class="card"><div class="num" style="color:#2563eb">{sumario['por_risco']['BAIXO']}</div><div class="lbl">Risco baixo</div></div>
        <div class="card score"><div class="num">{score}</div><div class="lbl">Indicador tecnico ({status_score})</div></div>
      </div>
    </section>
    <section class="section">
      <h2>Escopo analisado</h2>
      <div class="panel targets">
        <div class="target-box"><span>Codigo-fonte</span><code>{alvo_codigo}</code></div>
        <div class="target-box"><span>Banco SQLite</span><code>{alvo_banco}</code></div>
      </div>
    </section>
    <section class="section">
      <h2>Resumo tecnico</h2>
      <div class="panel">
        <div class="risk-row">
          <div class="risk-label">Arquivos</div>
          <div class="muted">{arquivos_python} arquivo(s) Python, {arquivos_java} arquivo(s) Java e {bancos_sqlite} banco(s) SQLite com achados.</div>
          <div class="risk-count">{len(arquivos)}</div>
        </div>
          {barras.lstrip()}
      </div>
    </section>
    <section class="section">
      <h2>Achados tecnicos e recomendacoes</h2>
      <div class="table-wrap">
        <div class="table-toolbar">
          <div class="filter-group" aria-label="Filtrar por risco">
            <button class="filter-btn active" type="button" data-filter-risk="TODOS">Todos</button>
            <button class="filter-btn" type="button" data-filter-risk="ALTO">Alto</button>
            <button class="filter-btn" type="button" data-filter-risk="MEDIO">Medio</button>
            <button class="filter-btn" type="button" data-filter-risk="BAIXO">Baixo</button>
          </div>
          <div class="table-count" id="table-count">{sumario['total']} item(ns)</div>
        </div>
        <div class="table-scroll">
          <table id="vulnerabilities-table">
            <thead>
              <tr>
                <th class="sortable" data-sort="number">#</th>
                <th class="sortable" data-sort="risk">Risco</th>
                <th class="sortable" data-sort="text">Categoria</th>
                <th class="sortable" data-sort="text">Local</th>
                <th class="sortable" data-sort="text">LGPD</th>
                <th class="sortable" data-sort="text">Descricao</th>
                <th>Recomendacao</th>
                <th>Evidencia segura</th>
              </tr>
            </thead>
            <tbody>{linhas_tabela}</tbody>
          </table>
        </div>
      </div>
    </section>
  </main>
  <script>
    (function () {{
      const table = document.getElementById('vulnerabilities-table');
      if (!table) return;

      const tbody = table.querySelector('tbody');
      const headers = table.querySelectorAll('th.sortable');
      const filterButtons = document.querySelectorAll('[data-filter-risk]');
      const countEl = document.getElementById('table-count');
      let currentRisk = 'TODOS';
      let sortState = {{ index: 1, direction: 'desc', type: 'risk' }};

      function getRows() {{
        return Array.from(tbody.querySelectorAll('tr')).filter(row => row.dataset.risk);
      }}

      function cellText(row, index) {{
        return (row.children[index]?.textContent || '').trim().toLowerCase();
      }}

      function sortRows() {{
        const rows = getRows();
        rows.sort((a, b) => {{
          let av;
          let bv;

          if (sortState.type === 'risk') {{
            av = Number(a.dataset.riskOrder || 0);
            bv = Number(b.dataset.riskOrder || 0);
          }} else if (sortState.type === 'number') {{
            av = Number(cellText(a, sortState.index)) || 0;
            bv = Number(cellText(b, sortState.index)) || 0;
          }} else {{
            av = cellText(a, sortState.index);
            bv = cellText(b, sortState.index);
          }}

          if (av < bv) return sortState.direction === 'asc' ? -1 : 1;
          if (av > bv) return sortState.direction === 'asc' ? 1 : -1;
          return 0;
        }});

        rows.forEach(row => tbody.appendChild(row));
      }}

      function applyFilter() {{
        let visible = 0;
        getRows().forEach(row => {{
          const show = currentRisk === 'TODOS' || row.dataset.risk === currentRisk;
          row.style.display = show ? '' : 'none';
          if (show) visible += 1;
        }});
        if (countEl) {{
          countEl.textContent = visible + ' item(ns)';
        }}
      }}

      headers.forEach((header, index) => {{
        header.addEventListener('click', () => {{
          const type = header.dataset.sort || 'text';
          if (sortState.index === index) {{
            sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
          }} else {{
            sortState = {{
              index,
              type,
              direction: type === 'risk' ? 'desc' : 'asc'
            }};
          }}

          headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
          header.classList.add(sortState.direction === 'asc' ? 'sort-asc' : 'sort-desc');
          sortRows();
          applyFilter();
        }});
      }});

      filterButtons.forEach(button => {{
        button.addEventListener('click', () => {{
          currentRisk = button.dataset.filterRisk || 'TODOS';
          filterButtons.forEach(btn => btn.classList.remove('active'));
          button.classList.add('active');
          applyFilter();
        }});
      }});

      sortRows();
      applyFilter();
    }})();
  </script>
  <footer>Privacy Scanner LGPD v{VERSAO_FERRAMENTA} | TCC FATEC | Relatorio gerado automaticamente.</footer>
</body>
</html>"""

    def exportar_html(self, caminho: str):
        html = self.gerar_html()
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML gerado: {caminho}")

    # ── Imprimir no terminal ──────────────────────────────────────────────────
    def exportar_pdf(self, caminho: str):
        """Exporta relatorio PDF formal e estatico."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                SimpleDocTemplate,
                Paragraph,
                Spacer,
                Table,
                TableStyle,
                PageBreak,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Dependencia ausente: instale com 'python -m pip install -r requirements.txt'"
            ) from exc

        def esc(valor) -> str:
            return html_lib.escape(str(valor)) if valor is not None else ""

        sumario = self._sumario()
        score = sumario["indicador_tecnico"]
        if score is None:
            raise ValueError("Não é possível gerar relatório para escopo vazio, inválido ou sem análise concluída.")
        status_score = status_score_tecnico(score)
        score_color = colors.HexColor("#15803d" if score >= 80 else "#b45309" if score >= 50 else "#b91c1c")
        risk_colors = {
            "ALTO": colors.HexColor("#dc2626"),
            "MEDIO": colors.HexColor("#d97706"),
            "BAIXO": colors.HexColor("#2563eb"),
        }

        doc = SimpleDocTemplate(
            caminho,
            pagesize=A4,
            rightMargin=1.4 * cm,
            leftMargin=1.4 * cm,
            topMargin=1.2 * cm,
            bottomMargin=1.2 * cm,
            title="Privacy Scanner LGPD - Relatorio Tecnico de Privacidade",
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="TitleCenter",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#172033"),
            fontSize=20,
            leading=24,
            spaceAfter=8,
        ))
        styles.add(ParagraphStyle(
            name="SubtitleCenter",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#64748b"),
            fontSize=9,
            leading=12,
            spaceAfter=18,
        ))
        styles.add(ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#172033"),
            fontSize=13,
            leading=16,
            spaceBefore=12,
            spaceAfter=8,
        ))
        styles.add(ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontSize=7,
            leading=9,
        ))
        styles.add(ParagraphStyle(
            name="Notice",
            parent=styles["Normal"],
            textColor=colors.HexColor("#78350f"),
            backColor=colors.HexColor("#fffbeb"),
            borderColor=colors.HexColor("#fcd34d"),
            borderWidth=0.5,
            borderPadding=6,
            fontSize=8,
            leading=11,
            spaceAfter=12,
        ))
        styles.add(ParagraphStyle(
            name="Cell",
            parent=styles["Normal"],
            fontSize=7,
            leading=9,
            wordWrap="CJK",
        ))

        story = [
            Paragraph("Privacy Scanner LGPD", styles["TitleCenter"]),
            Paragraph(
                f"Relatorio tecnico de privacidade gerado em {esc(self.timestamp)} | Privacy by Design no ciclo de desenvolvimento",
                styles["SubtitleCenter"],
            ),
            Paragraph(f"<b>Limite da analise:</b> {esc(AVISO_ESCOPO_ANALISE)}", styles["Notice"]),
        ]

        summary_table = Table(
            [
                ["Indicador tecnico", "Status", "Total", "ALTO", "MEDIO", "BAIXO"],
                [
                    f"{score}/100",
                    status_score,
                    str(sumario["total"]),
                    str(sumario["por_risco"]["ALTO"]),
                    str(sumario["por_risco"]["MEDIO"]),
                    str(sumario["por_risco"]["BAIXO"]),
                ],
            ],
            colWidths=[3.0 * cm, 3.0 * cm, 2.4 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm],
        )
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#18233f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8fafc")),
            ("TEXTCOLOR", (0, 1), (0, 1), score_color),
            ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 12))

        story.append(Paragraph("Escopo analisado", styles["Section"]))
        scope_table = Table(
            [
                ["Codigo-fonte", Paragraph(esc(self.alvo_codigo or "Nao informado"), styles["Small"])],
                ["Banco SQLite", Paragraph(esc(self.alvo_banco or "Nao informado"), styles["Small"])],
            ],
            colWidths=[3.4 * cm, 13.4 * cm],
        )
        scope_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(scope_table)
        story.append(Spacer(1, 8))

        if not self.resultados:
            story.append(Paragraph("Nenhum achado tecnico encontrado nos alvos analisados.", styles["Section"]))
        else:
            for risco in ["ALTO", "MEDIO", "BAIXO"]:
                vulns = [v for v in self.resultados if v.risco == risco]
                if not vulns:
                    continue

                story.append(Paragraph(f"Achados técnicos de risco {risco}", styles["Section"]))
                table_data = [["#", "Categoria", "Local", "LGPD", "Descricao", "Recomendacao"]]

                for idx, v in enumerate(vulns, start=1):
                    achado = serializar_achado(v, self._scope_root())
                    local = (
                        f"{os.path.basename(achado['arquivo'])}:{achado['linha']}"
                        if achado["linha"] > 0 else os.path.basename(achado["arquivo"])
                    )
                    table_data.append([
                        str(idx),
                        Paragraph(esc(achado["categoria_publica"]), styles["Cell"]),
                        Paragraph(esc(local), styles["Cell"]),
                        Paragraph(esc(achado["artigo_lgpd"]), styles["Cell"]),
                        Paragraph(esc(achado["descricao"]), styles["Cell"]),
                        Paragraph(esc(achado["recomendacao"]), styles["Cell"]),
                    ])

                findings_table = Table(
                    table_data,
                    colWidths=[0.7 * cm, 3.0 * cm, 2.8 * cm, 2.5 * cm, 5.0 * cm, 5.0 * cm],
                    repeatRows=1,
                )
                findings_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), risk_colors.get(risco, colors.HexColor("#334155"))),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]))
                story.append(findings_table)
                story.append(Spacer(1, 10))

            story.append(PageBreak())
            story.append(Paragraph("Evidencias tecnicas", styles["Section"]))
            evidence_data = [["Risco", "Categoria", "Local", "Evidencia segura"]]
            for v in self.resultados:
                achado = serializar_achado(v, self._scope_root())
                local = (
                    f"{os.path.basename(achado['arquivo'])}:{achado['linha']}"
                    if achado["linha"] > 0 else os.path.basename(achado["arquivo"])
                )
                evidence_data.append([
                    achado["risco"],
                    Paragraph(esc(achado["categoria_publica"]), styles["Cell"]),
                    Paragraph(esc(local), styles["Cell"]),
                    Paragraph(esc(achado["evidencia_segura"]), styles["Cell"]),
                ])
            evidence_table = Table(
                evidence_data,
                colWidths=[1.6 * cm, 3.2 * cm, 3.2 * cm, 10.0 * cm],
                repeatRows=1,
            )
            evidence_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#18233f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(evidence_table)

        def footer(canvas, doc_obj):
            canvas.saveState()
            canvas.setFont("Helvetica", 8)
            canvas.setFillColor(colors.HexColor("#64748b"))
            canvas.drawString(1.4 * cm, 0.8 * cm, f"Privacy Scanner LGPD v{VERSAO_FERRAMENTA} - TCC FATEC")
            canvas.drawRightString(19.6 * cm, 0.8 * cm, f"Pagina {doc_obj.page}")
            canvas.restoreState()

        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        print(f"PDF gerado: {caminho}")

    def imprimir(self):
        sumario = self._sumario()
        print("\n" + "═" * 60)
        print("  🔒 PRIVACY SCANNER — Relatório Técnico de Privacidade")
        print("═" * 60)
        print(f"  Gerado em  : {self.timestamp}")
        print(f"  Código     : {self.alvo_codigo or '—'}")
        print(f"  Banco      : {self.alvo_banco  or '—'}")
        print(f"  Total      : {sumario['total']} achado(s)")
        print(f"  ALTO       : {sumario['por_risco']['ALTO']}")
        print(f"  MÉDIO      : {sumario['por_risco']['MEDIO']}")
        print(f"  BAIXO      : {sumario['por_risco']['BAIXO']}")
        print(f"  Indicador  : {sumario['indicador_tecnico']}/100")
        print(f"  Aviso      : {AVISO_ESCOPO_ANALISE}")
        print("═" * 60 + "\n")

        if not self.resultados:
            print("  ✅  Nenhum achado técnico encontrado.\n")
            return

        for v in self.resultados:
            achado = serializar_achado(v, self._scope_root())
            local = (
                f"{achado['arquivo']}:{achado['linha']}"
                if achado["linha"] > 0 else achado["arquivo"]
            )
            print(f"  [{achado['risco']}] {achado['categoria_publica']}")
            print(f"  Local    : {local}")
            print(f"  LGPD     : {achado['artigo_lgpd']}")
            print(f"  Detalhe  : {achado['descricao']}")
            print(f"  Correção : {achado['recomendacao']}")
            print(f"  Evidência: {achado['evidencia_segura']}")
            print()


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def _imprimir_ascii(self):
    """Imprime resumo ASCII, compativel com terminal Windows."""
    sumario = self._sumario()
    print("\n" + "=" * 60)
    print("  PRIVACY SCANNER - Relatorio Tecnico de Privacidade")
    print("=" * 60)
    print(f"  Gerado em  : {self.timestamp}")
    print(f"  Codigo     : {self.alvo_codigo or '-'}")
    print(f"  Banco      : {self.alvo_banco or '-'}")
    print(f"  Total      : {sumario['total']} achado(s)")
    print(f"  ALTO       : {sumario['por_risco']['ALTO']}")
    print(f"  MEDIO      : {sumario['por_risco']['MEDIO']}")
    print(f"  BAIXO      : {sumario['por_risco']['BAIXO']}")
    print(f"  Indicador  : {sumario['indicador_tecnico']}/100")
    print(f"  Aviso      : {AVISO_ESCOPO_ANALISE}")
    print("=" * 60 + "\n")

    if not self.resultados:
        print("  Nenhum achado tecnico encontrado.\n")
        return

    for v in self.resultados:
        achado = serializar_achado(v, self._scope_root())
        local = (
            f"{achado['arquivo']}:{achado['linha']}"
            if achado["linha"] > 0 else achado["arquivo"]
        )
        print(f"  [{achado['risco']}] {achado['categoria_publica']}")
        print(f"  Local    : {local}")
        print(f"  LGPD     : {achado['artigo_lgpd']}")
        print(f"  Detalhe  : {achado['descricao']}")
        print(f"  Correcao : {achado['recomendacao']}")
        print(f"  Evidencia: {achado['evidencia_segura']}")
        print()


Reporter.imprimir = _imprimir_ascii


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Privacy Scanner — verifica indicios tecnicos de risco a privacidade"
    )
    parser.add_argument("--codigo", "-c", help="Arquivo .py ou diretório")
    parser.add_argument("--banco",  "-b", help="Arquivo .db (SQLite)")
    parser.add_argument("--json",   "-j", help="Exportar relatório JSON")
    parser.add_argument("--html",   "-H", help="Exportar relatório HTML")
    parser.add_argument("--pdf",    "-P", help="Exportar relatório PDF")
    args = parser.parse_args()

    if not args.codigo and not args.banco:
        parser.print_help()
        sys.exit(1)

    try:
        reporter = Reporter(
            alvo_codigo=args.codigo,
            alvo_banco=args.banco,
        ).coletar()
    except (FileNotFoundError, ValueError):
        print(json.dumps({
            "success": False,
            "status": "invalid",
            "indicador_tecnico": None,
            "mensagem": "O alvo informado é inválido ou não está disponível para análise.",
        }, ensure_ascii=False))
        sys.exit(2)

    if not _indicador_disponivel(reporter.escopo):
        print(json.dumps({
            "success": False,
            "status": reporter.escopo["status"],
            "escopo": reporter.escopo,
            "indicador_tecnico": None,
        }, ensure_ascii=False))
        sys.exit(2)

    reporter.imprimir()

    if args.json:
        reporter.exportar_json(args.json)
    if args.html:
        reporter.exportar_html(args.html)
    if args.pdf:
        reporter.exportar_pdf(args.pdf)

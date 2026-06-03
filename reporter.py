"""
reporter.py
Agrega os resultados do code_analyzer e do db_analyzer,
classifica por risco e gera relatório em JSON e HTML.
"""

import json
import os
import html as html_lib
from datetime import datetime
from dataclasses import asdict
from code_analyzer import analisar_arquivo, analisar_diretorio
from db_analyzer   import analisar_banco


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
        "Para senhas use bcrypt ou argon2. Para outros dados use AES-256 ou Fernet."
    ),
    "CRIPTOGRAFIA_FRACA": (
        "Substitua MD5/SHA1 por algoritmos modernos. "
        "Para senhas: bcrypt, argon2 ou pbkdf2. Para integridade: SHA-256 ou SHA-512."
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
        "Implemente método de exclusão ou anonimização na classe. "
        "O titular tem direito à eliminação dos dados (Art. 18, IV LGPD)."
    ),
    "CAMPO_SEM_HASH": (
        "Aplique hash/criptografia antes de persistir. Renomeie a coluna com "
        "sufixo '_hash' após aplicar (ex: senha → senha_hash com bcrypt)."
    ),
    "AUSENCIA_SOFT_DELETE": (
        "Adicione coluna 'deleted_at TIMESTAMP' ou 'is_deleted BOOLEAN' "
        "para suportar exclusão lógica sem perda de integridade referencial."
    ),
    "AUSENCIA_RETENCAO": (
        "Adicione coluna 'expires_at TIMESTAMP' e implemente rotina de purga "
        "automática. Defina o prazo de retenção conforme a finalidade do dado."
    ),
    "MISTURA_DADOS": (
        "Separe dados pessoais em tabela dedicada (ex: usuarios_dados_pessoais) "
        "vinculada por ID técnico. Facilita controle de acesso e exclusão seletiva."
    ),
    "AUSENCIA_CONSENTIMENTO": (
        "Adicione coluna 'lgpd_aceito BOOLEAN' e 'lgpd_aceito_em TIMESTAMP'. "
        "Registre data e versão da política aceita pelo titular."
    ),
    "DADO_SENSIVEL_COMO_PK": (
        "Substitua a PK por ID técnico (INTEGER AUTOINCREMENT ou UUID). "
        "Mantenha CPF/email como campo único (UNIQUE) mas não como PK."
    ),
}

ORDEM_RISCO = {"ALTO": 0, "MEDIO": 1, "BAIXO": 2}


# ─────────────────────────────────────────────────────────────────────────────
# Gerador de relatório
# ─────────────────────────────────────────────────────────────────────────────
class Reporter:

    def __init__(self, alvo_codigo: str = None, alvo_banco: str = None):
        self.alvo_codigo = alvo_codigo
        self.alvo_banco  = alvo_banco
        self.timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.resultados  = []

    def coletar(self):
        if self.alvo_codigo:
            if os.path.isfile(self.alvo_codigo):
                self.resultados += analisar_arquivo(self.alvo_codigo)
            elif os.path.isdir(self.alvo_codigo):
                self.resultados += analisar_diretorio(self.alvo_codigo)

        if self.alvo_banco and os.path.isfile(self.alvo_banco):
            self.resultados += analisar_banco(self.alvo_banco)

        # Ordena: ALTO → MEDIO → BAIXO, depois por arquivo e linha
        self.resultados.sort(
            key=lambda v: (ORDEM_RISCO.get(v.risco, 9), v.arquivo, v.linha)
        )
        return self

    # ── Sumário em texto para o terminal ─────────────────────────────────────
    def _sumario(self) -> dict:
        total = len(self.resultados)
        por_risco = {"ALTO": 0, "MEDIO": 0, "BAIXO": 0}
        por_categoria = {}
        for v in self.resultados:
            por_risco[v.risco] = por_risco.get(v.risco, 0) + 1
            por_categoria[v.categoria] = por_categoria.get(v.categoria, 0) + 1
        return {
            "total": total,
            "por_risco": por_risco,
            "por_categoria": por_categoria,
            "score_conformidade": max(0, 100 - (
                por_risco["ALTO"]  * 10 +
                por_risco["MEDIO"] *  5 +
                por_risco["BAIXO"] *  2
            )),
        }

    # ── Exportar JSON ─────────────────────────────────────────────────────────
    def exportar_json(self, caminho: str):
        sumario = self._sumario()
        payload = {
            "ferramenta": "Privacy Scanner — TCC FATEC",
            "versao":     "1.0.0",
            "timestamp":  self.timestamp,
            "sumario":    sumario,
            "vulnerabilidades": [
                {**asdict(v), "recomendacao": RECOMENDACOES.get(v.categoria, "")}
                for v in self.resultados
            ],
        }
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"📄 JSON gerado: {caminho}")

    # ── Exportar HTML ─────────────────────────────────────────────────────────
    def exportar_html(self, caminho: str):
        sumario = self._sumario()
        score   = sumario["score_conformidade"]
        cor_score = (
            "#27ae60" if score >= 80 else
            "#f39c12" if score >= 50 else
            "#e74c3c"
        )

        # ── Linhas da tabela ──
        linhas_tabela = ""
        for v in self.resultados:
            badge_risco = {
                "ALTO":  '<span class="badge alto">ALTO</span>',
                "MEDIO": '<span class="badge medio">MÉDIO</span>',
                "BAIXO": '<span class="badge baixo">BAIXO</span>',
            }.get(v.risco, v.risco)

            rec = html_lib.escape(RECOMENDACOES.get(v.categoria, "—"))
            trecho_html = (
                f'<code>{html_lib.escape(v.trecho)}</code>' if v.trecho else "—"
            )
            local = (
                f"{os.path.basename(v.arquivo)}:{v.linha}"
                if v.linha > 0 else os.path.basename(v.arquivo)
            )
            local = html_lib.escape(local)
            categoria = html_lib.escape(v.categoria)
            artigo_lgpd = html_lib.escape(v.artigo_lgpd)
            descricao = html_lib.escape(v.descricao)

            linhas_tabela += f"""
            <tr>
              <td>{badge_risco}</td>
              <td><strong>{categoria}</strong></td>
              <td>{local}</td>
              <td>{artigo_lgpd}</td>
              <td>{descricao}</td>
              <td>{rec}</td>
              <td>{trecho_html}</td>
            </tr>"""

        # ── Barras do sumário ──
        def barra(label, count, cor):
            return f"""
            <div class="barra-item">
              <span class="barra-label">{label}</span>
              <div class="barra-fundo">
                <div class="barra-fill" style="width:{min(count*8,100)}%;background:{cor}"></div>
              </div>
              <span class="barra-num">{count}</span>
            </div>"""

        barras = (
            barra("ALTO",  sumario["por_risco"]["ALTO"],  "#e74c3c") +
            barra("MÉDIO", sumario["por_risco"]["MEDIO"], "#f39c12") +
            barra("BAIXO", sumario["por_risco"]["BAIXO"], "#3498db")
        )

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Privacy Scanner — Relatório de Conformidade LGPD</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body      {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9;
                color: #2c3e50; font-size: 14px; }}
    header    {{ background: #1a2744; color: #fff; padding: 24px 40px;
                display: flex; justify-content: space-between; align-items: center; }}
    header h1 {{ font-size: 20px; font-weight: 600; }}
    header p  {{ font-size: 12px; opacity: .7; margin-top: 4px; }}
    .main     {{ padding: 32px 40px; }}

    /* Cartões do sumário */
    .cards    {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 16px;
                margin-bottom: 32px; }}
    .card     {{ background: #fff; border-radius: 10px; padding: 20px 24px;
                box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
    .card .num  {{ font-size: 36px; font-weight: 700; }}
    .card .lbl  {{ font-size: 12px; color: #888; margin-top: 4px; }}
    .card.score .num {{ color: {cor_score}; }}

    /* Barras */
    .barras   {{ background:#fff; border-radius:10px; padding:20px 24px;
                box-shadow:0 1px 4px rgba(0,0,0,.08); margin-bottom:32px; }}
    .barras h2 {{ font-size:14px; font-weight:600; margin-bottom:16px; }}
    .barra-item {{ display:flex; align-items:center; gap:12px; margin-bottom:10px; }}
    .barra-label {{ width:50px; font-size:12px; font-weight:600; }}
    .barra-fundo {{ flex:1; background:#eee; border-radius:4px; height:12px; }}
    .barra-fill  {{ height:12px; border-radius:4px; transition:width .4s; }}
    .barra-num   {{ width:30px; text-align:right; font-size:12px; font-weight:700; }}

    /* Tabela */
    .tabela-wrap {{ background:#fff; border-radius:10px;
                   box-shadow:0 1px 4px rgba(0,0,0,.08); overflow:hidden; }}
    .tabela-wrap h2 {{ font-size:14px; font-weight:600; padding:16px 24px;
                      border-bottom:1px solid #f0f0f0; }}
    table      {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th         {{ background:#f8f9fb; padding:10px 12px; text-align:left;
                font-weight:600; font-size:12px; color:#555;
                border-bottom:1px solid #e8e8e8; }}
    td         {{ padding:10px 12px; border-bottom:1px solid #f0f0f0;
                vertical-align:top; }}
    tr:last-child td {{ border-bottom:none; }}
    tr:hover td {{ background:#fafbfc; }}
    code       {{ background:#f0f0f0; padding:2px 6px; border-radius:4px;
                font-size:11px; font-family:monospace; word-break:break-all; }}

    /* Badges de risco */
    .badge     {{ display:inline-block; padding:2px 8px; border-radius:12px;
                font-size:11px; font-weight:700; }}
    .badge.alto  {{ background:#fde8e8; color:#c0392b; }}
    .badge.medio {{ background:#fef3cd; color:#856404; }}
    .badge.baixo {{ background:#d1ecf1; color:#0c5460; }}

    footer {{ text-align:center; padding:24px; color:#aaa; font-size:12px; }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>🔒 Privacy Scanner — Relatório de Conformidade LGPD</h1>
      <p>Gerado em {self.timestamp} &nbsp;|&nbsp; TCC FATEC &nbsp;|&nbsp;
         Privacy by Design no Ciclo de Desenvolvimento de Software</p>
    </div>
  </header>

  <div class="main">

    <!-- Cartões -->
    <div class="cards">
      <div class="card">
        <div class="num">{sumario['total']}</div>
        <div class="lbl">Total de vulnerabilidades</div>
      </div>
      <div class="card" style="border-top:3px solid #e74c3c">
        <div class="num" style="color:#e74c3c">{sumario['por_risco']['ALTO']}</div>
        <div class="lbl">Risco ALTO</div>
      </div>
      <div class="card" style="border-top:3px solid #f39c12">
        <div class="num" style="color:#f39c12">{sumario['por_risco']['MEDIO']}</div>
        <div class="lbl">Risco MÉDIO</div>
      </div>
      <div class="card score" style="border-top:3px solid {cor_score}">
        <div class="num">{score}/100</div>
        <div class="lbl">Score de conformidade LGPD</div>
      </div>
    </div>

    <!-- Barras -->
    <div class="barras">
      <h2>Distribuição por nível de risco</h2>
      {barras}
    </div>

    <!-- Tabela -->
    <div class="tabela-wrap">
      <h2>Vulnerabilidades encontradas</h2>
      <table>
        <thead>
          <tr>
            <th>Risco</th>
            <th>Categoria</th>
            <th>Local</th>
            <th>Artigo LGPD</th>
            <th>Descrição</th>
            <th>Recomendação</th>
            <th>Trecho</th>
          </tr>
        </thead>
        <tbody>
          {linhas_tabela}
        </tbody>
      </table>
    </div>
  </div>

  <footer>Privacy Scanner v1.0.0 — TCC FATEC — Privacy by Design no SDLC</footer>
</body>
</html>"""

        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"🌐 HTML gerado: {caminho}")

    # ── Imprimir no terminal ──────────────────────────────────────────────────
    def imprimir(self):
        sumario = self._sumario()
        print("\n" + "═" * 60)
        print("  🔒 PRIVACY SCANNER — Relatório de Conformidade LGPD")
        print("═" * 60)
        print(f"  Gerado em  : {self.timestamp}")
        print(f"  Código     : {self.alvo_codigo or '—'}")
        print(f"  Banco      : {self.alvo_banco  or '—'}")
        print(f"  Total      : {sumario['total']} vulnerabilidade(s)")
        print(f"  ALTO       : {sumario['por_risco']['ALTO']}")
        print(f"  MÉDIO      : {sumario['por_risco']['MEDIO']}")
        print(f"  BAIXO      : {sumario['por_risco']['BAIXO']}")
        print(f"  Score LGPD : {sumario['score_conformidade']}/100")
        print("═" * 60 + "\n")

        if not self.resultados:
            print("  ✅  Nenhuma vulnerabilidade encontrada.\n")
            return

        for v in self.resultados:
            local = f"{v.arquivo}:{v.linha}" if v.linha > 0 else v.arquivo
            print(f"  [{v.risco}] {v.categoria}")
            print(f"  Local    : {local}")
            print(f"  LGPD     : {v.artigo_lgpd}")
            print(f"  Detalhe  : {v.descricao}")
            rec = RECOMENDACOES.get(v.categoria)
            if rec:
                print(f"  Correção : {rec}")
            if v.trecho:
                print(f"  Trecho   : {v.trecho}")
            print()


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Privacy Scanner — verifica vulnerabilidades de privacidade"
    )
    parser.add_argument("--codigo", "-c", help="Arquivo .py ou diretório")
    parser.add_argument("--banco",  "-b", help="Arquivo .db (SQLite)")
    parser.add_argument("--json",   "-j", help="Exportar relatório JSON")
    parser.add_argument("--html",   "-H", help="Exportar relatório HTML")
    args = parser.parse_args()

    if not args.codigo and not args.banco:
        parser.print_help()
        sys.exit(1)

    reporter = Reporter(
        alvo_codigo=args.codigo,
        alvo_banco=args.banco,
    ).coletar()

    reporter.imprimir()

    if args.json:
        reporter.exportar_json(args.json)
    if args.html:
        reporter.exportar_html(args.html)

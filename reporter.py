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
    def gerar_html(self) -> str:
        """Retorna o relatorio HTML em memoria."""
        sumario = self._sumario()
        score = sumario["score_conformidade"]
        cor_score = "#15803d" if score >= 80 else "#b45309" if score >= 50 else "#b91c1c"
        status_score = "Conforme" if score >= 80 else "Atencao" if score >= 50 else "Critico"

        arquivos = sorted({v.arquivo for v in self.resultados if v.arquivo})
        arquivos_python = sum(1 for a in arquivos if a.lower().endswith(".py"))
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
            badge_risco = {
                "ALTO": '<span class="badge alto">ALTO</span>',
                "MEDIO": '<span class="badge medio">MEDIO</span>',
                "BAIXO": '<span class="badge baixo">BAIXO</span>',
            }.get(v.risco, esc(v.risco))

            local = f"{os.path.basename(v.arquivo)}:{v.linha}" if v.linha > 0 else os.path.basename(v.arquivo)
            recomendacao = RECOMENDACOES.get(v.categoria, "Sem recomendacao cadastrada.")
            trecho = f"<code>{esc(v.trecho)}</code>" if v.trecho else '<span class="muted">Nao informado</span>'

            risco_ordem = {"ALTO": 3, "MEDIO": 2, "BAIXO": 1}.get(v.risco, 0)
            linhas_tabela += f"""
            <tr data-risk="{esc(v.risco)}" data-risk-order="{risco_ordem}">
              <td class="index">{idx}</td>
              <td>{badge_risco}</td>
              <td><strong>{esc(v.categoria)}</strong></td>
              <td>{esc(local)}</td>
              <td>{esc(v.artigo_lgpd)}</td>
              <td>{esc(v.descricao)}</td>
              <td>{esc(recomendacao)}</td>
              <td>{trecho}</td>
            </tr>"""

        if not linhas_tabela:
            linhas_tabela = """
            <tr>
              <td colspan="8" class="empty-state">
                Nenhuma vulnerabilidade encontrada nos alvos analisados.
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

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Privacy Scanner LGPD - Relatorio de Conformidade</title>
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
        <div class="subtitle">Relatorio de conformidade e evidencias de privacidade em codigo Python e SQLite.</div>
        <div class="meta">Gerado em {timestamp} | Privacy by Design no ciclo de desenvolvimento</div>
      </div>
      <div class="score-pill"><strong>{score}/100</strong><span>{status_score}</span></div>
    </div>
  </header>
  <main>
    <section class="section">
      <div class="cards">
        <div class="card"><div class="num">{sumario['total']}</div><div class="lbl">Total de vulnerabilidades</div></div>
        <div class="card"><div class="num" style="color:#dc2626">{sumario['por_risco']['ALTO']}</div><div class="lbl">Risco alto</div></div>
        <div class="card"><div class="num" style="color:#d97706">{sumario['por_risco']['MEDIO']}</div><div class="lbl">Risco medio</div></div>
        <div class="card"><div class="num" style="color:#2563eb">{sumario['por_risco']['BAIXO']}</div><div class="lbl">Risco baixo</div></div>
        <div class="card score"><div class="num">{score}</div><div class="lbl">Score LGPD ({status_score})</div></div>
      </div>
    </section>
    <section class="section">
      <h2>Escopo analisado</h2>
      <div class="panel targets">
        <div class="target-box"><span>Codigo Python</span><code>{alvo_codigo}</code></div>
        <div class="target-box"><span>Banco SQLite</span><code>{alvo_banco}</code></div>
      </div>
    </section>
    <section class="section">
      <h2>Resumo tecnico</h2>
      <div class="panel">
        <div class="risk-row">
          <div class="risk-label">Arquivos</div>
          <div class="muted">{arquivos_python} arquivo(s) Python com achados e {bancos_sqlite} banco(s) SQLite com achados.</div>
          <div class="risk-count">{len(arquivos)}</div>
        </div>
        {barras}
      </div>
    </section>
    <section class="section">
      <h2>Vulnerabilidades e recomendacoes</h2>
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
                <th>Trecho</th>
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
  <footer>Privacy Scanner LGPD v1.0.0 | TCC FATEC | Relatorio gerado automaticamente.</footer>
</body>
</html>"""

    def exportar_html(self, caminho: str):
        html = self.gerar_html()
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML gerado: {caminho}")
        return

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
        score = sumario["score_conformidade"]
        status_score = "Conforme" if score >= 80 else "Atencao" if score >= 50 else "Critico"
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
            title="Privacy Scanner LGPD - Relatorio de Conformidade",
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
            name="Cell",
            parent=styles["Normal"],
            fontSize=7,
            leading=9,
            wordWrap="CJK",
        ))

        story = [
            Paragraph("Privacy Scanner LGPD", styles["TitleCenter"]),
            Paragraph(
                f"Relatorio de conformidade gerado em {esc(self.timestamp)} | Privacy by Design no ciclo de desenvolvimento",
                styles["SubtitleCenter"],
            ),
        ]

        summary_table = Table(
            [
                ["Score LGPD", "Status", "Total", "ALTO", "MEDIO", "BAIXO"],
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
                ["Codigo Python", Paragraph(esc(self.alvo_codigo or "Nao informado"), styles["Small"])],
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
            story.append(Paragraph("Nenhuma vulnerabilidade encontrada nos alvos analisados.", styles["Section"]))
        else:
            for risco in ["ALTO", "MEDIO", "BAIXO"]:
                vulns = [v for v in self.resultados if v.risco == risco]
                if not vulns:
                    continue

                story.append(Paragraph(f"Vulnerabilidades de risco {risco}", styles["Section"]))
                table_data = [["#", "Categoria", "Local", "LGPD", "Descricao", "Recomendacao"]]

                for idx, v in enumerate(vulns, start=1):
                    local = f"{os.path.basename(v.arquivo)}:{v.linha}" if v.linha > 0 else os.path.basename(v.arquivo)
                    recomendacao = RECOMENDACOES.get(v.categoria, "Sem recomendacao cadastrada.")
                    table_data.append([
                        str(idx),
                        Paragraph(esc(v.categoria), styles["Cell"]),
                        Paragraph(esc(local), styles["Cell"]),
                        Paragraph(esc(v.artigo_lgpd), styles["Cell"]),
                        Paragraph(esc(v.descricao), styles["Cell"]),
                        Paragraph(esc(recomendacao), styles["Cell"]),
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
            evidence_data = [["Risco", "Categoria", "Local", "Trecho"]]
            for v in self.resultados:
                local = f"{os.path.basename(v.arquivo)}:{v.linha}" if v.linha > 0 else os.path.basename(v.arquivo)
                evidence_data.append([
                    v.risco,
                    Paragraph(esc(v.categoria), styles["Cell"]),
                    Paragraph(esc(local), styles["Cell"]),
                    Paragraph(esc(v.trecho or "Nao informado"), styles["Cell"]),
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
            canvas.drawString(1.4 * cm, 0.8 * cm, "Privacy Scanner LGPD v1.0.0 - TCC FATEC")
            canvas.drawRightString(19.6 * cm, 0.8 * cm, f"Pagina {doc_obj.page}")
            canvas.restoreState()

        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        print(f"PDF gerado: {caminho}")

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
def _imprimir_ascii(self):
    """Imprime resumo ASCII, compativel com terminal Windows."""
    sumario = self._sumario()
    print("\n" + "=" * 60)
    print("  PRIVACY SCANNER - Relatorio de Conformidade LGPD")
    print("=" * 60)
    print(f"  Gerado em  : {self.timestamp}")
    print(f"  Codigo     : {self.alvo_codigo or '-'}")
    print(f"  Banco      : {self.alvo_banco or '-'}")
    print(f"  Total      : {sumario['total']} vulnerabilidade(s)")
    print(f"  ALTO       : {sumario['por_risco']['ALTO']}")
    print(f"  MEDIO      : {sumario['por_risco']['MEDIO']}")
    print(f"  BAIXO      : {sumario['por_risco']['BAIXO']}")
    print(f"  Score LGPD : {sumario['score_conformidade']}/100")
    print("=" * 60 + "\n")

    if not self.resultados:
        print("  Nenhuma vulnerabilidade encontrada.\n")
        return

    for v in self.resultados:
        local = f"{v.arquivo}:{v.linha}" if v.linha > 0 else v.arquivo
        print(f"  [{v.risco}] {v.categoria}")
        print(f"  Local    : {local}")
        print(f"  LGPD     : {v.artigo_lgpd}")
        print(f"  Detalhe  : {v.descricao}")
        rec = RECOMENDACOES.get(v.categoria)
        if rec:
            print(f"  Correcao : {rec}")
        if v.trecho:
            print(f"  Trecho   : {v.trecho}")
        print()


Reporter.imprimir = _imprimir_ascii


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
    parser.add_argument("--pdf",    "-P", help="Exportar relatório PDF")
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
    if args.pdf:
        reporter.exportar_pdf(args.pdf)

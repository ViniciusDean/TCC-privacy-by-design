"""
server.py
Servidor Flask que expõe os analisadores (code_analyzer, db_analyzer) via HTTP API.
Usado pela extensão VS Code para fazer requisições remotas.

Uso:
    python server.py 5000
"""

import sys
import os
import json
import html as html_lib
from flask import Flask, request, jsonify
from code_analyzer import analisar_arquivo, analisar_diretorio
from db_analyzer import analisar_banco
from reporter import Reporter, RECOMENDACOES
from dataclasses import asdict


app = Flask(__name__)
port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint para verificar se o servidor está rodando."""
    return jsonify({'status': 'ok', 'version': '1.0.0'})


# ─────────────────────────────────────────────────────────────────────────────
# Análise de arquivo individual
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/analyze-file', methods=['POST'])
def analyze_file():
    """
    Analisa um arquivo Python individual.
    Payload: {"filepath": "/caminho/para/arquivo.py"}
    """
    try:
        data = request.get_json()
        filepath = data.get('filepath')

        if not filepath:
            return jsonify({'success': False, 'error': 'filepath é obrigatório'}), 400

        if not os.path.isfile(filepath):
            return jsonify({'success': False, 'error': f'Arquivo não encontrado: {filepath}'}), 404

        vulnerabilities = analisar_arquivo(filepath)

        # Adicionar recomendações
        vulns_dict = []
        for v in vulnerabilities:
            v_dict = asdict(v)
            v_dict['recomendacao'] = RECOMENDACOES.get(v.categoria, '')
            vulns_dict.append(v_dict)

        return jsonify({
            'success': True,
            'vulnerabilities': vulns_dict,
            'count': len(vulnerabilities)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# Análise de diretório
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/analyze-directory', methods=['POST'])
def analyze_directory():
    """
    Analisa todos os arquivos .py de um diretório (recursivamente).
    Payload: {"directory": "/caminho/para/pasta"}
    """
    try:
        data = request.get_json()
        directory = data.get('directory')

        if not directory:
            return jsonify({'success': False, 'error': 'directory é obrigatório'}), 400

        if not os.path.isdir(directory):
            return jsonify({'success': False, 'error': f'Diretório não encontrado: {directory}'}), 404

        vulnerabilities = analisar_diretorio(directory)

        # Adicionar recomendações
        vulns_dict = []
        for v in vulnerabilities:
            v_dict = asdict(v)
            v_dict['recomendacao'] = RECOMENDACOES.get(v.categoria, '')
            vulns_dict.append(v_dict)

        # Calcular sumário
        total = len(vulnerabilities)
        por_risco = {'ALTO': 0, 'MEDIO': 0, 'BAIXO': 0}
        for v in vulnerabilities:
            por_risco[v.risco] = por_risco.get(v.risco, 0) + 1

        score = max(0, 100 - (
            por_risco.get('ALTO', 0) * 10 +
            por_risco.get('MEDIO', 0) * 5 +
            por_risco.get('BAIXO', 0) * 2
        ))

        return jsonify({
            'success': True,
            'vulnerabilities': vulns_dict,
            'summary': {
                'total': total,
                'por_risco': por_risco,
                'score_conformidade': score
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# Análise de banco de dados
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/analyze-database', methods=['POST'])
def analyze_database():
    """
    Analisa um banco de dados SQLite.
    Payload: {"database": "/caminho/para/banco.db"}
    """
    try:
        data = request.get_json()
        database = data.get('database')

        if not database:
            return jsonify({'success': False, 'error': 'database é obrigatório'}), 400

        if not os.path.isfile(database):
            return jsonify({'success': False, 'error': f'Banco não encontrado: {database}'}), 404

        vulnerabilities = analisar_banco(database)

        # Adicionar recomendações
        vulns_dict = []
        for v in vulnerabilities:
            v_dict = asdict(v)
            v_dict['recomendacao'] = RECOMENDACOES.get(v.categoria, '')
            vulns_dict.append(v_dict)

        return jsonify({
            'success': True,
            'vulnerabilities': vulns_dict,
            'count': len(vulnerabilities)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# Exportação de relatórios
# ─────────────────────────────────────────────────────────────────────────────
@app.route('/api/export', methods=['POST'])
def export_report():
    """
    Gera relatório em formato HTML ou JSON.
    Payload: {"directory": "/caminho", "format": "html" | "json"}
    """
    try:
        data = request.get_json()
        directory = data.get('directory')
        format_type = data.get('format', 'html')

        if not directory:
            return jsonify({'success': False, 'error': 'directory é obrigatório'}), 400

        if format_type not in ['html', 'json']:
            return jsonify({'success': False, 'error': 'format deve ser html ou json'}), 400

        reporter = Reporter(alvo_codigo=directory).coletar()

        if format_type == 'json':
            # Gerar JSON em memória
            sumario = reporter._sumario()
            payload = {
                'ferramenta': 'Privacy Scanner — TCC FATEC',
                'versao': '1.0.0',
                'timestamp': reporter.timestamp,
                'sumario': sumario,
                'vulnerabilidades': [
                    {**asdict(v), 'recomendacao': RECOMENDACOES.get(v.categoria, '')}
                    for v in reporter.resultados
                ]
            }
            content = json.dumps(payload, ensure_ascii=False, indent=2)
        else:
            # Gerar HTML — usar método interno (precisa ser ajustado para retornar string)
            content = generate_html_report(reporter)

        return jsonify({
            'success': True,
            'content': content,
            'format': format_type
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_html_report(reporter):
    """Gera HTML do relatório (adaptação do reporter.exportar_html)."""
    sumario = reporter._sumario()
    score = sumario['score_conformidade']
    cor_score = (
        '#27ae60' if score >= 80 else
        '#f39c12' if score >= 50 else
        '#e74c3c'
    )

    linhas_tabela = ""
    for v in reporter.resultados:
        badge_risco = {
            'ALTO': '<span class="badge alto">ALTO</span>',
            'MEDIO': '<span class="badge medio">MÉDIO</span>',
            'BAIXO': '<span class="badge baixo">BAIXO</span>',
        }.get(v.risco, v.risco)

        rec = html_lib.escape(RECOMENDACOES.get(v.categoria, '—'))
        trecho_html = f'<code>{html_lib.escape(v.trecho)}</code>' if v.trecho else '—'
        local = f"{os.path.basename(v.arquivo)}:{v.linha}" if v.linha > 0 else os.path.basename(v.arquivo)
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
        barra('ALTO', sumario['por_risco']['ALTO'], '#e74c3c') +
        barra('MÉDIO', sumario['por_risco']['MEDIO'], '#f39c12') +
        barra('BAIXO', sumario['por_risco']['BAIXO'], '#3498db')
    )

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <title>Privacy Scanner — Relatório LGPD</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body      {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; color: #2c3e50; }}
    header    {{ background: #1a2744; color: #fff; padding: 24px 40px; }}
    header h1 {{ font-size: 20px; font-weight: 600; }}
    .main     {{ padding: 32px 40px; }}
    .cards    {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; margin-bottom: 32px; }}
    .card     {{ background: #fff; border-radius: 10px; padding: 20px 24px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }}
    .card .num  {{ font-size: 36px; font-weight: 700; }}
    .card .lbl  {{ font-size: 12px; color: #888; margin-top: 4px; }}
    table     {{ width:100%; border-collapse:collapse; font-size:13px; }}
    th        {{ background:#f8f9fb; padding:10px 12px; text-align:left; font-weight:600; }}
    td        {{ padding:10px 12px; border-bottom:1px solid #f0f0f0; }}
    .badge.alto  {{ background:#fde8e8; color:#c0392b; padding:2px 8px; border-radius:12px; }}
    .badge.medio {{ background:#fef3cd; color:#856404; padding:2px 8px; border-radius:12px; }}
    .badge.baixo {{ background:#d1ecf1; color:#0c5460; padding:2px 8px; border-radius:12px; }}
    code {{ background:#f0f0f0; padding:2px 6px; border-radius:4px; }}
  </style>
</head>
<body>
  <header>
    <h1>🔒 Privacy Scanner — Relatório LGPD</h1>
  </header>
  <div class="main">
    <div class="cards">
      <div class="card">
        <div class="num">{sumario['total']}</div>
        <div class="lbl">Vulnerabilidades</div>
      </div>
      <div class="card">
        <div class="num" style="color:#e74c3c">{sumario['por_risco']['ALTO']}</div>
        <div class="lbl">Risco ALTO</div>
      </div>
      <div class="card">
        <div class="num" style="color:#f39c12">{sumario['por_risco']['MEDIO']}</div>
        <div class="lbl">Risco MÉDIO</div>
      </div>
      <div class="card" style="color:{cor_score}">
        <div class="num">{score}/100</div>
        <div class="lbl">Score LGPD</div>
      </div>
    </div>
    <table>
      <thead>
        <tr><th>Risco</th><th>Categoria</th><th>Local</th><th>LGPD</th><th>Descrição</th><th>Correção</th></tr>
      </thead>
      <tbody>{linhas_tabela}</tbody>
    </table>
  </div>
</body>
</html>"""

    return html


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(f'🚀 Privacy Scanner Server iniciando na porta {port}...')
    print(f'📡 Endpoints:')
    print(f'   GET  /health')
    print(f'   POST /api/analyze-file')
    print(f'   POST /api/analyze-directory')
    print(f'   POST /api/analyze-database')
    print(f'   POST /api/export')
    app.run(host='localhost', port=port, debug=False)

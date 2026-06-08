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
import base64
import tempfile
from flask import Flask, request, jsonify
from code_analyzer import analisar_arquivo, analisar_diretorio
from db_analyzer import analisar_banco
from reporter import Reporter, RECOMENDACOES
from dataclasses import asdict


app = Flask(__name__)
port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
DB_EXTENSIONS = ('.db', '.sqlite', '.sqlite3')


def analisar_bancos_diretorio(directory):
    resultados = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [
            d for d in dirs
            if d not in {'node_modules', '.git', '__pycache__', 'htmlcov', '.pytest_cache'}
        ]
        for filename in files:
            if filename.lower().endswith(DB_EXTENSIONS):
                resultados.extend(analisar_banco(os.path.join(root, filename)))
    return resultados


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
    Analisa um arquivo Python ou Java individual.
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

        if format_type not in ['html', 'json', 'pdf']:
            return jsonify({'success': False, 'error': 'format deve ser html, json ou pdf'}), 400

        reporter = Reporter(alvo_codigo=directory).coletar()
        reporter.resultados += analisar_bancos_diretorio(directory)

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
        elif format_type == 'pdf':
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                temp_path = tmp.name
            try:
                reporter.exportar_pdf(temp_path)
                with open(temp_path, 'rb') as f:
                    content = base64.b64encode(f.read()).decode('ascii')
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            # Gerar HTML — usar método interno (precisa ser ajustado para retornar string)
            content = generate_html_report(reporter)

        return jsonify({
            'success': True,
            'content': content,
            'format': format_type,
            'encoding': 'base64' if format_type == 'pdf' else 'utf-8'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def generate_html_report(reporter):
    """Gera HTML do relatório (adaptação do reporter.exportar_html)."""
    return reporter.gerar_html()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(f'Privacy Scanner Server iniciando na porta {port}...')
    print('Endpoints:')
    print(f'   GET  /health')
    print(f'   POST /api/analyze-file')
    print(f'   POST /api/analyze-directory')
    print(f'   POST /api/analyze-database')
    print(f'   POST /api/export')
    app.run(host='localhost', port=port, debug=False)

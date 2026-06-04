# Privacy Scanner LGPD - TCC FATEC

Ferramenta de analise estatica para detectar vulnerabilidades de privacidade em codigo Python e bancos SQLite, com mapeamento das ocorrencias para artigos da Lei Geral de Protecao de Dados Pessoais (LGPD).

Projeto desenvolvido no contexto de TCC sobre **Privacy by Design no Ciclo de Desenvolvimento de Software**.

## Visao Geral

O Privacy Scanner LGPD ajuda desenvolvedores a identificar riscos de privacidade ainda durante o desenvolvimento, sem executar o codigo analisado.

Principais recursos:

- Analise estatica de codigo Python usando AST.
- Analise de schema SQLite.
- Mapeamento automatico para artigos da LGPD.
- Score de conformidade de 0 a 100.
- Extensao VS Code com diagnosticos no editor.
- Sidebar com resumo e agrupamento por risco.
- Code Actions com recomendacoes LGPD.
- Exportacao de relatorio HTML interativo.
- Exportacao JSON estruturada.
- Preparacao para exportacao PDF.

## Estrutura do Projeto

```text
TCC/
|-- code_analyzer.py              # Analise de codigo Python via AST
|-- db_analyzer.py                # Analise de schema SQLite
|-- reporter.py                   # Agregacao e relatorios JSON/HTML
|-- server.py                     # API Flask usada pela extensao VS Code
|-- requirements.txt              # Dependencias Python
|-- pytest.ini                    # Configuracao dos testes
|-- push_github.bat               # Script local para commit/push
|-- setup_windows.bat             # Setup inicial no Windows
|-- validate_project.bat          # Validacao local do projeto
|
|-- exemplo_vulneravel.py         # Exemplo com vulnerabilidades propositais
|-- exemplo_correto.py            # Exemplo sem falsos positivos esperados
|-- exemplo_parcial.py            # Exemplo intermediario/realista
|
|-- tests/
|   |-- test_code_analyzer.py
|   |-- test_db_analyzer.py
|   |-- test_reporter.py
|
|-- vscode-extension/
|   |-- src/extension.ts          # Codigo principal da extensao
|   |-- package.json              # Manifesto da extensao
|   |-- tsconfig.json             # Configuracao TypeScript
|   |-- resources/icon.svg        # Icone da extensao
|
|-- scripts/
|   |-- create_test_workspace.py  # Recria workspace externo de testes
|
|-- docs/
|   |-- DEMO.md
|   |-- FASE_1_ESTABILIZACAO.md
```

## Quick Start

### 1. Instalar dependencias Python

```powershell
python -m pip install -r requirements.txt
```

### 2. Instalar e compilar a extensao

```powershell
cd vscode-extension
npm install
npm run compile
cd ..
```

### 3. Rodar testes

```powershell
python -m pytest
```

Resultado esperado:

```text
56 passed
```

### 4. Testar a extensao no VS Code

1. Abra a pasta `TCC` no VS Code.
2. Pressione `F5`.
3. Uma nova janela `[Extension Development Host]` sera aberta.
4. Abra a pasta de teste ou um arquivo Python.
5. Use a sidebar `Privacy Scanner`.

Se precisar recriar a pasta externa de testes:

```powershell
python scripts/create_test_workspace.py
```

## Uso pela CLI

Analisar um arquivo Python:

```powershell
python code_analyzer.py exemplo_vulneravel.py
```

Gerar relatorio HTML:

```powershell
python reporter.py --codigo exemplo_vulneravel.py --html relatorio.html
```

Gerar relatorio JSON:

```powershell
python reporter.py --codigo exemplo_vulneravel.py --json relatorio.json
```

Analisar banco SQLite:

```powershell
python reporter.py --banco banco_vulneravel.db --html relatorio_banco.html
```

Analisar projeto inteiro:

```powershell
python reporter.py --codigo . --html relatorio_projeto.html
```

## Uso pela Extensao VS Code

Comandos disponiveis na Paleta de Comandos (`Ctrl+Shift+P`):

- `Privacy Scanner: Analisar agora`
- `Privacy Scanner: Analisar arquivo atual`
- `Privacy Scanner: Analisar projeto inteiro`
- `Privacy Scanner: Analisar banco SQLite`
- `Privacy Scanner: Limpar resultados`
- `Privacy Scanner: Exportar relatorio`
- `Privacy Scanner: Exportar relatorio HTML`
- `Privacy Scanner: Exportar relatorio JSON`

A extensao tambem analisa arquivos Python automaticamente ao abrir, trocar de aba ou salvar.

## Sidebar da Extensao

A sidebar mostra:

- vulnerabilidades agrupadas por risco;
- arquivos afetados;
- score LGPD;
- total de vulnerabilidades;
- contagem por risco;
- quantidade de arquivos Python e bancos SQLite com achados.

Enquanto a analise esta em andamento, a sidebar mostra estado de carregamento em vez de exibir `100/100` antes da hora.

## Code Actions

Quando uma vulnerabilidade aparece sublinhada no editor, use a lampada/Quick Fix para:

- ver a recomendacao LGPD da regra;
- copiar a recomendacao para a area de transferencia.

## Relatorios

### HTML

O relatorio HTML inclui:

- score LGPD;
- cards por risco;
- escopo analisado;
- resumo tecnico;
- tabela de vulnerabilidades;
- recomendacoes;
- trecho de codigo/schema;
- filtro por risco;
- ordenacao ao clicar nos cabecalhos da tabela.

Na extensao, ao exportar HTML, o VS Code abre a janela do Windows para escolher nome e destino do arquivo.

### JSON

O JSON contem:

- metadados da ferramenta;
- timestamp;
- sumario;
- lista estruturada de vulnerabilidades;
- recomendacao de correcao por categoria.

### PDF

A opcao PDF ja aparece no fluxo de exportacao, mas ainda esta reservada para a proxima etapa. A recomendacao do projeto e manter:

- HTML como relatorio interativo;
- PDF como relatorio formal e estatico para entrega/compliance.

## Regras Detectadas

### Codigo Python

| Categoria | Risco | Artigo LGPD | Descricao |
|---|---|---|---|
| DADO_HARDCODED | ALTO | Art. 46 | Dado pessoal fixo no codigo |
| CRIPTOGRAFIA_FRACA | ALTO | Art. 46 | Uso de MD5 ou SHA1 |
| DADO_EM_LOG | ALTO | Art. 46 | Dado pessoal em print/logging |
| TRANSFERENCIA_SEM_BASE_LEGAL | ALTO | Art. 7 / Art. 33 | Envio a terceiros sem base legal documentada |
| COLETA_EXCESSIVA | MEDIO | Art. 6 | Coleta de muitos campos sensiveis |
| AUSENCIA_EXCLUSAO | MEDIO | Art. 18 | Classe sem metodo de exclusao/anonimizacao |
| DADO_SEM_CRIPTOGRAFIA | MEDIO | Art. 46 | Campo sensivel sem protecao esperada |

### Banco SQLite

| Categoria | Risco | Artigo LGPD | Descricao |
|---|---|---|---|
| CAMPO_SEM_HASH | ALTO | Art. 46 | Campo sensivel armazenado em texto puro |
| AUSENCIA_SOFT_DELETE | MEDIO | Art. 18 | Ausencia de `deleted_at` ou `is_deleted` |
| AUSENCIA_CONSENTIMENTO | MEDIO | Art. 7 | Ausencia de controle de consentimento |
| DADO_SENSIVEL_COMO_PK | MEDIO | Art. 46 | CPF/email usado como chave primaria |
| AUSENCIA_RETENCAO | BAIXO | Art. 15 | Ausencia de politica de retencao |
| MISTURA_DADOS | BAIXO | Art. 6 | Dados pessoais e nao pessoais misturados |

## Score LGPD

Formula:

```text
100 - (ALTO * 10 + MEDIO * 5 + BAIXO * 2)
```

Interpretacao:

| Score | Situacao |
|---|---|
| 80-100 | Boa conformidade |
| 50-79 | Atencao |
| 0-49 | Critico |

## API Flask

Servidor local:

```text
http://localhost:5000
```

Endpoints:

| Metodo | Endpoint | Funcao |
|---|---|---|
| GET | `/health` | Verifica se o servidor esta ativo |
| POST | `/api/analyze-file` | Analisa um arquivo Python |
| POST | `/api/analyze-directory` | Analisa um diretorio |
| POST | `/api/analyze-database` | Analisa um banco SQLite |
| POST | `/api/export` | Exporta relatorio HTML/JSON |

## Configuracoes da Extensao

Exemplo em `settings.json`:

```json
{
  "privacy-scanner.serverPort": 5000,
  "privacy-scanner.autoAnalyzeOnSave": true,
  "privacy-scanner.pythonPath": "python",
  "privacy-scanner.enableSidebar": true,
  "privacy-scanner.showDiagnostics": true
}
```

## Testes

Executar tudo:

```powershell
python -m pytest
```

Executar com cobertura:

```powershell
python -m pytest --cov=code_analyzer --cov=db_analyzer --cov=reporter --cov-report=html
```

Suite atual:

- `test_code_analyzer.py`: regras de codigo, falsos positivos, word boundary e artigos LGPD.
- `test_db_analyzer.py`: regras SQLite, schemas corretos, edge cases e erros.
- `test_reporter.py`: score, ordenacao, recomendacoes, JSON e HTML.

## Scripts Uteis

Setup no Windows:

```powershell
setup_windows.bat
```

Validacao geral:

```powershell
validate_project.bat
```

Commit e push:

```powershell
push_github.bat
```

## Status

Implementado:

- analise Python;
- analise SQLite;
- mapeamento LGPD;
- score de conformidade;
- relatorio terminal;
- export JSON;
- export HTML interativo;
- servidor Flask;
- extensao VS Code;
- sidebar;
- botao de analise;
- botao de exportacao;
- Code Actions;
- workspace de teste;
- suite automatizada com 56 testes.

Proximas etapas:

- exportacao PDF;
- melhoria do relatorio PDF formal;
- CI/CD com GitHub Actions;
- empacotamento da extensao VS Code.

## Autor

Desenvolvido por Dean V. como TCC na FATEC.

## Licenca

MIT

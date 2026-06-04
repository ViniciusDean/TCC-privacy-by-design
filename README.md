# Privacy Scanner LGPD - TCC FATEC

Ferramenta de análise estática para detectar vulnerabilidades de privacidade em código Python e bancos SQLite, com mapeamento das ocorrências para artigos da Lei Geral de Proteção de Dados Pessoais (LGPD).

Projeto desenvolvido no contexto de TCC sobre **Privacy by Design no Ciclo de Desenvolvimento de Software**.

## Visão Geral

O Privacy Scanner LGPD ajuda desenvolvedores a identificar riscos de privacidade ainda durante o desenvolvimento, sem executar o código analisado.

Principais recursos:

- Análise estática de código Python usando AST.
- Análise de schema SQLite.
- Mapeamento automático para artigos da LGPD.
- Score de conformidade de 0 a 100.
- Extensão VS Code com diagnósticos no editor.
- Sidebar com resumo e agrupamento por risco.
- Code Actions com recomendações LGPD.
- Exportação de relatório HTML interativo.
- Exportação JSON estruturada.
- Preparação para exportação PDF.

## Estrutura do Projeto

```text
TCC/
|-- code_analyzer.py              # Análise de código Python via AST
|-- db_analyzer.py                # Análise de schema SQLite
|-- reporter.py                   # Agregação e relatórios JSON/HTML
|-- server.py                     # API Flask usada pela extensão VS Code
|-- requirements.txt              # Dependências Python
|-- pytest.ini                    # Configuração dos testes
|-- push_github.bat               # Script local para commit/push
|-- setup_windows.bat             # Setup inicial no Windows
|-- validate_project.bat          # Validação local do projeto
|
|-- exemplo_vulneravel.py         # Exemplo com vulnerabilidades propositais
|-- exemplo_correto.py            # Exemplo sem falsos positivos esperados
|-- exemplo_parcial.py            # Exemplo intermediário/realista
|
|-- tests/
|   |-- test_code_analyzer.py
|   |-- test_db_analyzer.py
|   |-- test_reporter.py
|
|-- vscode-extension/
|   |-- src/extension.ts          # Código principal da extensão
|   |-- package.json              # Manifesto da extensão
|   |-- tsconfig.json             # Configuração TypeScript
|   |-- resources/icon.svg        # Ícone da extensão
|
|-- scripts/
|   |-- create_test_workspace.py  # Recria workspace externo de testes
|
|-- docs/
|   |-- DEMO.md
|   |-- FASE_1_ESTABILIZACAO.md
```

## Quick Start

### 1. Instalar dependências Python

```powershell
python -m pip install -r requirements.txt
```

### 2. Instalar e compilar a extensão

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

### 4. Testar a extensão no VS Code

1. Abra a pasta `TCC` no VS Code.
2. Pressione `F5`.
3. Uma nova janela `[Extension Development Host]` será aberta.
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

Gerar relatório HTML:

```powershell
python reporter.py --codigo exemplo_vulneravel.py --html relatorio.html
```

Gerar relatório JSON:

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

## Uso pela Extensão VS Code

Comandos disponíveis na Paleta de Comandos (`Ctrl+Shift+P`):

- `Privacy Scanner: Analisar agora`
- `Privacy Scanner: Analisar arquivo atual`
- `Privacy Scanner: Analisar projeto inteiro`
- `Privacy Scanner: Analisar banco SQLite`
- `Privacy Scanner: Limpar resultados`
- `Privacy Scanner: Exportar relatorio`
- `Privacy Scanner: Exportar relatório HTML`
- `Privacy Scanner: Exportar relatório JSON`

A extensão também analisa arquivos Python automaticamente ao abrir, trocar de aba ou salvar.

## Sidebar da Extensão

A sidebar mostra:

- vulnerabilidades agrupadas por risco;
- arquivos afetados;
- score LGPD;
- total de vulnerabilidades;
- contagem por risco;
- quantidade de arquivos Python e bancos SQLite com achados.

Enquanto a análise está em andamento, a sidebar mostra estado de carregamento em vez de exibir `100/100` antes da hora.

## Code Actions

Quando uma vulnerabilidade aparece sublinhada no editor, use a lâmpada/Quick Fix para:

- ver a recomendação LGPD da regra;
- copiar a recomendação para a área de transferência.

## Relatórios

### HTML

O relatório HTML inclui:

- score LGPD;
- cards por risco;
- escopo analisado;
- resumo técnico;
- tabela de vulnerabilidades;
- recomendações;
- trecho de código/schema;
- filtro por risco;
- ordenação ao clicar nos cabeçalhos da tabela.

Na extensão, ao exportar HTML, o VS Code abre a janela do Windows para escolher nome e destino do arquivo.

### JSON

O JSON contém:

- metadados da ferramenta;
- timestamp;
- sumário;
- lista estruturada de vulnerabilidades;
- recomendação de correção por categoria.

### PDF

A opção PDF já aparece no fluxo de exportação, mas ainda está reservada para a próxima etapa. A recomendação do projeto é manter:

- HTML como relatório interativo;
- PDF como relatório formal e estático para entrega/compliance.

## Regras Detectadas

### Código Python

| Categoria | Risco | Artigo LGPD | Descrição |
|---|---|---|---|
| DADO_HARDCODED | ALTO | Art. 46 | Dado pessoal fixo no código |
| CRIPTOGRAFIA_FRACA | ALTO | Art. 46 | Uso de MD5 ou SHA1 |
| DADO_EM_LOG | ALTO | Art. 46 | Dado pessoal em print/logging |
| TRANSFERENCIA_SEM_BASE_LEGAL | ALTO | Art. 7 / Art. 33 | Envio a terceiros sem base legal documentada |
| COLETA_EXCESSIVA | MÉDIO | Art. 6 | Coleta de muitos campos sensíveis |
| AUSENCIA_EXCLUSAO | MÉDIO | Art. 18 | Classe sem método de exclusão/anonimização |
| DADO_SEM_CRIPTOGRAFIA | MÉDIO | Art. 46 | Campo sensível sem proteção esperada |

### Banco SQLite

| Categoria | Risco | Artigo LGPD | Descrição |
|---|---|---|---|
| CAMPO_SEM_HASH | ALTO | Art. 46 | Campo sensível armazenado em texto puro |
| AUSENCIA_SOFT_DELETE | MÉDIO | Art. 18 | Ausência de `deleted_at` ou `is_deleted` |
| AUSENCIA_CONSENTIMENTO | MÉDIO | Art. 7 | Ausência de controle de consentimento |
| DADO_SENSIVEL_COMO_PK | MÉDIO | Art. 46 | CPF/email usado como chave primária |
| AUSENCIA_RETENCAO | BAIXO | Art. 15 | Ausência de política de retenção |
| MISTURA_DADOS | BAIXO | Art. 6 | Dados pessoais e não pessoais misturados |

## Score LGPD

Fórmula:

```text
100 - (ALTO * 10 + MÉDIO * 5 + BAIXO * 2)
```

Interpretação:

| Score | Situação |
|---|---|
| 80-100 | Boa conformidade |
| 50-79 | Atenção |
| 0-49 | Crítico |

## API Flask

Servidor local:

```text
http://localhost:5000
```

Endpoints:

| Método | Endpoint | Função |
|---|---|---|
| GET | `/health` | Verifica se o servidor está ativo |
| POST | `/api/analyze-file` | Analisa um arquivo Python |
| POST | `/api/analyze-directory` | Analisa um diretório |
| POST | `/api/analyze-database` | Analisa um banco SQLite |
| POST | `/api/export` | Exporta relatório HTML/JSON |

## Configurações da Extensão

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

Suíte atual:

- `test_code_analyzer.py`: regras de código, falsos positivos, word boundary e artigos LGPD.
- `test_db_analyzer.py`: regras SQLite, schemas corretos, edge cases e erros.
- `test_reporter.py`: score, ordenação, recomendações, JSON e HTML.

## Scripts Úteis

Setup no Windows:

```powershell
setup_windows.bat
```

Validação geral:

```powershell
validate_project.bat
```

Commit e push:

```powershell
push_github.bat
```

## Status

Implementado:

- análise Python;
- análise SQLite;
- mapeamento LGPD;
- score de conformidade;
- relatório terminal;
- exportação JSON;
- exportação HTML interativa;
- servidor Flask;
- extensão VS Code;
- sidebar;
- botão de análise;
- botão de exportação;
- Code Actions;
- workspace de teste;
- suíte automatizada com 56 testes.

Próximas etapas:

- exportação PDF;
- melhoria do relatório PDF formal;
- CI/CD com GitHub Actions;
- empacotamento da extensão VS Code.

## Autor

Desenvolvido por Dean V. como TCC na FATEC.

## Licença

MIT

# ðŸ”’ Privacy Scanner LGPD â€” TCC FATEC

**Privacy by Design no Ciclo de Desenvolvimento de Software**

Ferramenta de anÃ¡lise estÃ¡tica para detectar vulnerabilidades de privacidade em cÃ³digo Python e bancos SQLite conforme a Lei Geral de ProteÃ§Ã£o de Dados Pessoais (LGPD).

## ðŸ“Š VisÃ£o Geral

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Privacy Scanner LGPD (VersÃ£o 1.0.0)                        â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚                                                             â”‚
â”‚  ðŸ” AnÃ¡lise EstÃ¡tica de CÃ³digo Python                      â”‚
â”‚     â”œâ”€ Dados pessoais hardcoded                           â”‚
â”‚     â”œâ”€ AusÃªncia/fraqueza de criptografia                  â”‚
â”‚     â”œâ”€ Dados em logs                                      â”‚
â”‚     â”œâ”€ TransferÃªncias sem base legal                      â”‚
â”‚     â”œâ”€ Coleta excessiva                                   â”‚
â”‚     â””â”€ AusÃªncia de mÃ©todos de exclusÃ£o                    â”‚
â”‚                                                             â”‚
â”‚  ðŸ—„ï¸  AnÃ¡lise de Banco SQLite                               â”‚
â”‚     â”œâ”€ Campos sensÃ­veis em texto puro                     â”‚
â”‚     â”œâ”€ AusÃªncia de soft-delete                            â”‚
â”‚     â”œâ”€ AusÃªncia de retenÃ§Ã£o                               â”‚
â”‚     â”œâ”€ AusÃªncia de consentimento                          â”‚
â”‚     â”œâ”€ Mistura de dados                                   â”‚
â”‚     â””â”€ Chaves primÃ¡rias sensÃ­veis                         â”‚
â”‚                                                             â”‚
â”‚  ðŸŽ¨ Interface VS Code                                       â”‚
â”‚     â”œâ”€ AnÃ¡lise em tempo real                              â”‚
â”‚     â”œâ”€ Gutter icons + Diagnostics API                     â”‚
â”‚     â”œâ”€ Comando manual                                     â”‚
â”‚     â”œâ”€ ExportaÃ§Ã£o de relatÃ³rios                           â”‚
â”‚     â””â”€ ConfiguraÃ§Ãµes personalizÃ¡veis                      â”‚
â”‚                                                             â”‚
â”‚  ðŸ“Š RelatÃ³rios                                             â”‚
â”‚     â”œâ”€ Terminal (sumÃ¡rio + detalhes)                      â”‚
â”‚     â”œâ”€ JSON (estrutura completa)                          â”‚
â”‚     â”œâ”€ HTML (visual com score)                            â”‚
â”‚     â””â”€ (PDF â€” prÃ³ximo)                                    â”‚
â”‚                                                             â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## ðŸ—‚ï¸ Estrutura de Arquivos

```
TCC/
â”œâ”€â”€ ðŸ“„ code_analyzer.py              â† AnÃ¡lise de cÃ³digo Python (AST)
â”œâ”€â”€ ðŸ“„ db_analyzer.py                â† AnÃ¡lise de banco SQLite
â”œâ”€â”€ ðŸ“„ reporter.py                   â† GeraÃ§Ã£o de relatÃ³rios
â”œâ”€â”€ ðŸ“„ server.py                     â† Servidor Flask (NEW)
â”‚
â”œâ”€â”€ ðŸ“š Exemplos & Testes
â”‚   â”œâ”€â”€ exemplo_vulneravel.py        â† 6 vulnerabilidades propositais
â”‚   â”œâ”€â”€ exemplo_correto.py           â† Sem falsos positivos
â”‚   â”œâ”€â”€ exemplo_parcial.py           â† Boas prÃ¡ticas parciais (NEW)
â”‚   â””â”€â”€ teste_word_boundary.py       â† Teste de word boundary
â”‚
â”œâ”€â”€ ðŸŽ¨ vscode-extension/             â† ExtensÃ£o VS Code (NEW)
â”‚   â”œâ”€â”€ src/
â”‚   â”‚   â””â”€â”€ extension.ts             â† CÃ³digo TypeScript principal
â”‚   â”œâ”€â”€ package.json                 â† Metadados & dependÃªncias
â”‚   â”œâ”€â”€ tsconfig.json                â† ConfiguraÃ§Ã£o TypeScript
â”‚   â”œâ”€â”€ .vscodeignore                â† Empacotamento
â”‚   â”œâ”€â”€ .gitignore
â”‚   â””â”€â”€ README.md                    â† DocumentaÃ§Ã£o da extensÃ£o
â”‚
â”œâ”€â”€ ðŸ“‹ SETUP.md                      â† Guia de instalaÃ§Ã£o (NEW)
â””â”€â”€ ðŸ“‹ README.md                     â† Este arquivo
```

## ðŸš€ Quick Start

### OpÃ§Ã£o rÃ¡pida no Windows

```bat
setup_windows.bat
validate_project.bat
```

Depois abra o VS Code na pasta do projeto e pressione `F5`.

### 1ï¸âƒ£ InstalaÃ§Ã£o Python

```bash
python -m pip install -r requirements.txt
```

### 2ï¸âƒ£ Compilar extensÃ£o

```bash
cd vscode-extension
npm install
npm run compile
```

### 3ï¸âƒ£ Testar no VS Code

- Abra VS Code nesta pasta
- Pressione `F5` ou `Ctrl+Shift+D` â†’ "Run Extension"
- Uma nova janela VS Code abre com a extensÃ£o ativa no workspace de teste

### 4ï¸âƒ£ Testar anÃ¡lise

- Se necessario, gere o workspace de teste:
  ```bash
  python scripts/create_test_workspace.py
  ```
- Abra `exemplo_vulneravel.py` na janela de teste
- Salve o arquivo (`Ctrl+S`)
- Vulnerabilidades aparecem em **vermelho** no editor âœ¨

## ðŸ“– Uso

### CLI

```bash
# Analisar arquivo Ãºnico
python code_analyzer.py exemplo_vulneravel.py

# Analisar projeto inteiro
python reporter.py --codigo . --json resultado.json --html resultado.html
```

### VS Code Extension

Paleta de Comandos (`Ctrl+Shift+P`):
- `Privacy Scanner: Analisar arquivo atual`
- `Privacy Scanner: Analisar projeto inteiro`
- `Privacy Scanner: Analisar banco SQLite`
- `Privacy Scanner: Limpar resultados`
- `Privacy Scanner: Exportar relatÃ³rio HTML`
- `Privacy Scanner: Exportar relatÃ³rio JSON`

A extensÃ£o tambÃ©m analisa automaticamente arquivos Python quando vocÃª abre, troca para a aba ou salva o arquivo.
Nas vulnerabilidades exibidas no editor, use a lampada/Quick Fix para ver ou copiar a recomendacao LGPD da regra.

## ðŸ“Š Vulnerabilidades Detectadas

### CÃ³digo Python (7 regras)

| # | Categoria | Risco | DescriÃ§Ã£o |
|---|-----------|-------|-----------|
| 1 | DADO_HARDCODED | ðŸ”´ ALTO | Dado pessoal fixo no cÃ³digo |
| 2 | DADO_SEM_CRIPTOGRAFIA | ðŸŸ¡ MÃ‰DIO | Sem hash ou criptografia |
| 3 | CRIPTOGRAFIA_FRACA | ðŸ”´ ALTO | MD5, SHA1 (algoritmos fracos) |
| 4 | DADO_EM_LOG | ðŸ”´ ALTO | Dado pessoal em print/logging |
| 5 | TRANSFERENCIA_SEM_BASE_LEGAL | ðŸ”´ ALTO | Envio a terceiros sem justificaÃ§Ã£o |
| 6 | COLETA_EXCESSIVA | ðŸŸ¡ MÃ‰DIO | Mais de 4 campos sensÃ­veis |
| 7 | AUSENCIA_EXCLUSAO | ðŸŸ¡ MÃ‰DIO | Classe sem mÃ©todo delete/anonimizar |

### Banco SQLite (6 regras)

| # | Categoria | Risco | DescriÃ§Ã£o |
|---|-----------|-------|-----------|
| 1 | CAMPO_SEM_HASH | ðŸ”´ ALTO | Campo sensÃ­vel em TEXT puro |
| 2 | AUSENCIA_SOFT_DELETE | ðŸŸ¡ MÃ‰DIO | Sem coluna deleted_at |
| 3 | AUSENCIA_RETENCAO | ðŸ”µ BAIXO | Sem polÃ­tica de retenÃ§Ã£o |
| 4 | AUSENCIA_CONSENTIMENTO | ðŸŸ¡ MÃ‰DIO | Sem coluna lgpd_aceito |
| 5 | MISTURA_DADOS | ðŸ”µ BAIXO | Dados pessoais nÃ£o segregados |
| 6 | DADO_SENSIVEL_COMO_PK | ðŸŸ¡ MÃ‰DIO | CPF/Email como chave primÃ¡ria |

## ðŸ“ˆ Score de Conformidade

Score LGPD = `100 - (ALTOÃ—10 + MÃ‰DIOÃ—5 + BAIXOÃ—2)`

- âœ… 80-100: Excelente conformidade
- âš ï¸ 50-79: Conformidade aceitÃ¡vel
- ðŸ”´ 0-49: CrÃ­tico â€” correÃ§Ãµes necessÃ¡rias

## ðŸ§ª Exemplos

### exemplo_vulneravel.py
âœ— 7 vulnerabilidades detectadas
```python
senha = "minhasenha123"        # DADO_HARDCODED (ALTO)
cpf = "123.456.789-00"         # DADO_HARDCODED (ALTO)
hash = hashlib.md5(...)        # CRIPTOGRAFIA_FRACA (ALTO)
logging.info(f"CPF: {cpf}")    # DADO_EM_LOG (ALTO)
requests.post(..., json={"cpf": cpf})  # TRANSFERENCIA (ALTO)
```

### exemplo_correto.py
âœ“ Sem falsos positivos
```python
nome = ""              # InicializaÃ§Ã£o vazia (OK)
user_agent = "..."    # NÃ£o Ã© 'age' isolado (OK)
bcrypt.hashpw(...)    # Criptografia forte (OK)
Usuario.deletar()     # MÃ©todo de exclusÃ£o (OK)
```

### exemplo_parcial.py
âš¡ Boas prÃ¡ticas parciais
```python
bcrypt.hashpw(...)         # âœ“ Forte
logging.info(email)        # âœ— Ainda expÃµe email
soft_delete()              # âœ“ Implementado
exportar_usuario_json()    # âœ— Serializa tudo
```

## ðŸ”§ ConfiguraÃ§Ã£o

### VS Code Settings

```json
{
  "privacy-scanner.serverPort": 5000,
  "privacy-scanner.autoAnalyzeOnSave": true,
  "privacy-scanner.pythonPath": "python",
  "privacy-scanner.enableSidebar": true,
  "privacy-scanner.showDiagnostics": true
}
```

## ðŸ“¦ DependÃªncias

- **Python**: 3.8+
- **Flask**: 2.0+
- **Node.js**: 14+
- **TypeScript**: 4.0+
- **VS Code**: 1.60+

## ðŸš¨ Troubleshooting

### âŒ Flask not found
```bash
python -m pip install -r requirements.txt
```

### âŒ npm not found
Instale Node.js: https://nodejs.org/

### âŒ Porta 5000 em uso
Mude em VS Code Settings:
```json
"privacy-scanner.serverPort": 5001
```

## ðŸ“š DocumentaÃ§Ã£o

- [SETUP.md](SETUP.md) â€” InstalaÃ§Ã£o detalhada
- [docs/DEMO.md](docs/DEMO.md) â€” Roteiro de demonstraÃ§Ã£o
- [docs/FASE_1_ESTABILIZACAO.md](docs/FASE_1_ESTABILIZACAO.md) â€” Checklist da Fase 1
- [vscode-extension/README.md](vscode-extension/README.md) â€” Docs da extensÃ£o
- [code_analyzer.py](code_analyzer.py) â€” Docstrings
- [db_analyzer.py](db_analyzer.py) â€” Docstrings

## ðŸ§ª Testes UnitÃ¡rios

**Suite completa com 56 testes** â€” Todas as funcionalidades validadas âœ…

### Executar Testes
```bash
pytest tests/ -v                    # Todos os testes
pytest tests/ --cov=. --cov-report=html  # Com cobertura (gera HTML)
```

### Cobertura Atual
```
code_analyzer.py:   86% (167 linhas, 23 nÃ£o cobertas)
db_analyzer.py:     80% (128 linhas, 25 nÃ£o cobertas)
reporter.py:        48% (103 linhas, 54 nÃ£o cobertas)
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
TOTAL:              74% (398 linhas, 102 nÃ£o cobertas)
```

### Testes por Componente
- **code_analyzer.py**: 22 testes (detecÃ§Ã£o, word boundary, falsos positivos, LGPD)
- **db_analyzer.py**: 16 testes (schema, edge cases, artigos)
- **reporter.py**: 13 testes (sumÃ¡rio, score, export JSON/HTML)

Detalhes em [TESTS.md](TESTS.md)

## ðŸŽ“ Para o TCC

### Componentes Completados
- [x] AnÃ¡lise estÃ¡tica de Python
- [x] AnÃ¡lise de banco SQLite  
- [x] Mapeamento de artigos LGPD
- [x] RelatÃ³rios (terminal, JSON, HTML)
- [x] ExtensÃ£o VS Code
- [x] Servidor Flask
- [x] Casos de teste (vulnerÃ¡vel, correto, parcial)
- [x] ConfiguraÃ§Ãµes
- [x] Testes unitÃ¡rios (56 testes, 74% cobertura) âœ…
- [x] Sidebar com resumo na extensÃ£o

### PrÃ³ximos Passos (no escopo)
- [ ] Code actions (sugestÃµes inline)
- [ ] ExportaÃ§Ã£o PDF
- [ ] CI/CD (GitHub Actions)

### Fora do Escopo (futuro)
- [ ] Suporte a outras linguagens
- [ ] Suporte a MySQL, PostgreSQL
- [ ] AnÃ¡lise dinÃ¢mica (runtime)
- [ ] Dashboard web
- [ ] PublicaÃ§Ã£o no Marketplace

## ðŸ“Š MÃ©tricas

| Componente | Linhas | Status | Completude | Cobertura |
|-----------|--------|--------|-----------|-----------|
| code_analyzer.py | ~350 | âœ… | 70% | **86%** |
| db_analyzer.py | ~250 | âœ… | 65% | **80%** |
| reporter.py | ~350 | âœ… | 60% | **48%** |
| server.py | ~250 | âœ… NEW | 100% | - |
| extension.ts | ~400 | âœ… NEW | 100% | - |
| **Testes** | **~1600** | âœ… NEW | **100%** | **56/56** âœ… |
| **Total** | **~3450** | âœ… | **76%** | **74%** |

## ðŸ‘¥ Autor

Desenvolvido como **TCC** na **FATEC** sob metodologia **DSR** (Design Science Research).

## ðŸ“„ LicenÃ§a

MIT

---

**Status**: VersÃ£o 1.0.0 â€” Funcional âœ…  
**Ãšltima atualizaÃ§Ã£o**: 2026-06-01  

**PrÃ³xima release**: Code Actions + PDF Export


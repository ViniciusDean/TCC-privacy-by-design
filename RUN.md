# â–¶ï¸ RUN.md â€” Como Executar Privacy Scanner

Guia passo a passo para rodar a ferramenta completa.

---

## ðŸš€ OpÃ§Ã£o 1: Testes (Quick Validation)

### ValidaÃ§Ã£o completa no Windows
```bat
validate_project.bat
```

Esse script recria o workspace de teste, roda `pytest` e compila a extensÃ£o.

### Rodar todos os testes
```bash
cd c:\Users\deanv\OneDrive\Documents\TCC
pytest tests/ -v
```

**SaÃ­da esperada**:
```
===== 56 passed in 0.17s =====
```

### Gerar relatÃ³rio de cobertura
```bash
pytest tests/ --cov=code_analyzer --cov=db_analyzer --cov=reporter --cov-report=html
```

Abre relatÃ³rio em: `htmlcov/index.html`

---

## ðŸŽ¨ OpÃ§Ã£o 2: VS Code Extension (Recomendado)

### PrÃ©-requisitos
```bash
# Windows/PowerShell
python -m pip install -r requirements.txt
npm install -g typescript  # Se nÃ£o tiver
```

Para preparar a pasta externa usada no teste da extensÃ£o:

```bash
python scripts/create_test_workspace.py
```

### Abrir extensÃ£o no VS Code
```bash
cd c:\Users\deanv\OneDrive\Documents\TCC
code .
```

### Rodar no modo debug
1. Pressione `F5` ou `Ctrl+Shift+D`
2. Selecione **"Run Extension"**
3. Nova janela VS Code abre com extensÃ£o ativa

### Testar anÃ¡lise
1. Abra arquivo: `exemplo_vulneravel.py`
2. Pressione `Ctrl+S` (salvar)
3. Vulnerabilidades aparecem em **vermelho** âœ¨

### Comandos disponÃ­veis
Pressione `Ctrl+Shift+P` e escolha:
- `Privacy Scanner: Analisar arquivo atual`
- `Privacy Scanner: Analisar projeto inteiro`
- `Privacy Scanner: Analisar banco SQLite`
- `Privacy Scanner: Exportar relatÃ³rio HTML`
- `Privacy Scanner: Exportar relatÃ³rio JSON`

---

## ðŸ–¥ï¸ OpÃ§Ã£o 3: Server Flask + CLI

### Iniciar servidor Flask
```bash
cd c:\Users\deanv\OneDrive\Documents\TCC
python server.py
```

**SaÃ­da**:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### Analisar arquivo (em outro terminal)
```bash
curl -X POST http://localhost:5000/api/analyze-file \
  -H "Content-Type: application/json" \
  -d '{"filepath": "exemplo_vulneravel.py"}'
```

### Analisar projeto
```bash
curl -X POST http://localhost:5000/api/analyze-directory \
  -H "Content-Type: application/json" \
  -d '{"dirpath": "."}'
```

---

## ðŸ“Š OpÃ§Ã£o 4: CLI Python Direto

### Analisar um arquivo
```bash
python code_analyzer.py exemplo_vulneravel.py
```

**SaÃ­da**:
```
ðŸ” Analisando: exemplo_vulneravel.py
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

Vulnerabilidade: DADO_HARDCODED
  Arquivo: exemplo_vulneravel.py, Linha: 1
  DescriÃ§Ã£o: Dado pessoal encontrado hardcoded
  Risco: ALTO
  LGPD: Art. 46

Vulnerabilidade: CRIPTOGRAFIA_FRACA
  ...
```

### Analisar banco de dados
```bash
python db_analyzer.py seu_banco.db
```

### Exportar relatÃ³rio
```bash
python reporter.py --codigo . --json resultado.json --html resultado.html
```

---

## ðŸ“‹ ValidaÃ§Ã£o Passo a Passo

### 1ï¸âƒ£ Verificar instalaÃ§Ã£o
```bash
python --version  # Deve ser 3.8+
flask --version   # Deve estar instalado
pytest --version  # Deve estar instalado
```

### 2ï¸âƒ£ Rodar testes
```bash
pytest tests/ -v --tb=short
# Esperado: 56 passed
```

### 3ï¸âƒ£ Testar anÃ¡lise manual
```bash
python code_analyzer.py exemplo_vulneravel.py
# Esperado: 6 vulnerabilidades detectadas
```

### 4ï¸âƒ£ Testar anÃ¡lise correto (falsos positivos)
```bash
python code_analyzer.py exemplo_correto.py
# Esperado: 0 vulnerabilidades
```

### 5ï¸âƒ£ Rodar extensÃ£o
```bash
# VS Code: F5 â†’ Run Extension
# Em nova janela, abra exemplo_vulneravel.py
# Salve: Ctrl+S
# Esperado: Gutter icons vermelhos aparecem
```

---

## ðŸ” Analisando Seu CÃ³digo

### Arquivo Ãºnico
```bash
python code_analyzer.py seu_arquivo.py
```

### DiretÃ³rio inteiro
```bash
python reporter.py --codigo ./meu_projeto --json relatorio.json
```

### Banco SQLite
```bash
python db_analyzer.py ./database.db
```

---

## ðŸ“Š Visualizar RelatÃ³rios

### HTML (recomendado)
```bash
# ApÃ³s gerar:
start resultado.html  # Windows
open resultado.html   # Mac
xdg-open resultado.html  # Linux
```

### JSON
```bash
# Visualizar em editor:
code resultado.json
```

### Terminal
```bash
python reporter.py --codigo . --imprimir
```

---

## ðŸ”§ Troubleshooting

### âŒ Erro: "ModuleNotFoundError: No module named 'flask'"
```bash
python -m pip install -r requirements.txt
```

### âŒ Porta 5000 em uso
```bash
# Mudar em VS Code Settings:
"privacy-scanner.serverPort": 5001
```

### âŒ TypeScript nÃ£o compila
```bash
cd vscode-extension
npm install
npm run compile
```

### âŒ Testes falham
```bash
# Limpar cache pytest:
pytest --cache-clear tests/ -v
```

---

## ðŸ“ˆ Performance

Tempo de execuÃ§Ã£o esperado:

| OperaÃ§Ã£o | Tempo |
|----------|-------|
| Analisar arquivo Ãºnico | ~50ms |
| Analisar projeto (10 arquivos) | ~200ms |
| Testes completos (56) | ~600ms |
| Exportar HTML | ~100ms |

---

## ðŸŽ“ ValidaÃ§Ã£o para TCC

### Checklist de ValidaÃ§Ã£o
- [x] Testes unitÃ¡rios rodando
- [x] Todos os testes passando (56/56)
- [x] Cobertura 74%+
- [x] Exemplos funcionando
- [x] ExtensÃ£o VS Code funcional
- [x] RelatÃ³rios gerando corretamente
- [x] Bugs corrigidos e validados

### MÃ©tricas Finais
- Testes: **56/56 âœ…**
- Cobertura: **74% âœ…**
- Completude: **76% âœ…**
- Status: **MVP ENTREGUE âœ…**

---

## ðŸ“ž PrÃ³ximos Passos

1. **Code Actions**: SugestÃµes inline de correÃ§Ã£o
2. **PDF Export**: RelatÃ³rios em PDF
3. **CI/CD**: GitHub Actions para testes automÃ¡ticos

---

**Ãšltima atualizaÃ§Ã£o**: 2026-06-01  
**Status**: âœ… Tudo funcionando


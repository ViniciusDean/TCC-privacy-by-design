# ▶️ RUN.md — Como Executar Privacy Scanner

Guia passo a passo para rodar a ferramenta completa.

---

## 🚀 Opção 1: Testes (Quick Validation)

### Rodar todos os testes
```bash
cd c:\Users\deanv\OneDrive\Documents\TCC
pytest tests/ -v
```

**Saída esperada**:
```
===== 51 passed in 0.59s =====
```

### Gerar relatório de cobertura
```bash
pytest tests/ --cov=code_analyzer --cov=db_analyzer --cov=reporter --cov-report=html
```

Abre relatório em: `htmlcov/index.html`

---

## 🎨 Opção 2: VS Code Extension (Recomendado)

### Pré-requisitos
```bash
# Windows/PowerShell
pip install flask
npm install -g typescript  # Se não tiver
```

### Abrir extensão no VS Code
```bash
cd c:\Users\deanv\OneDrive\Documents\TCC
code .
```

### Rodar no modo debug
1. Pressione `F5` ou `Ctrl+Shift+D`
2. Selecione **"Run Extension"**
3. Nova janela VS Code abre com extensão ativa

### Testar análise
1. Abra arquivo: `exemplo_vulneravel.py`
2. Pressione `Ctrl+S` (salvar)
3. Vulnerabilidades aparecem em **vermelho** ✨

### Comandos disponíveis
Pressione `Ctrl+Shift+P` e escolha:
- `Privacy Scanner: Analisar arquivo atual`
- `Privacy Scanner: Analisar projeto inteiro`
- `Privacy Scanner: Exportar relatório HTML`
- `Privacy Scanner: Exportar relatório JSON`

---

## 🖥️ Opção 3: Server Flask + CLI

### Iniciar servidor Flask
```bash
cd c:\Users\deanv\OneDrive\Documents\TCC
python server.py
```

**Saída**:
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

## 📊 Opção 4: CLI Python Direto

### Analisar um arquivo
```bash
python code_analyzer.py exemplo_vulneravel.py
```

**Saída**:
```
🔍 Analisando: exemplo_vulneravel.py
═══════════════════════════════════════════════════════════

Vulnerabilidade: DADO_HARDCODED
  Arquivo: exemplo_vulneravel.py, Linha: 1
  Descrição: Dado pessoal encontrado hardcoded
  Risco: ALTO
  LGPD: Art. 46

Vulnerabilidade: CRIPTOGRAFIA_FRACA
  ...
```

### Analisar banco de dados
```bash
python db_analyzer.py seu_banco.db
```

### Exportar relatório
```bash
python reporter.py --codigo . --json resultado.json --html resultado.html
```

---

## 📋 Validação Passo a Passo

### 1️⃣ Verificar instalação
```bash
python --version  # Deve ser 3.8+
flask --version   # Deve estar instalado
pytest --version  # Deve estar instalado
```

### 2️⃣ Rodar testes
```bash
pytest tests/ -v --tb=short
# Esperado: 51 passed
```

### 3️⃣ Testar análise manual
```bash
python code_analyzer.py exemplo_vulneravel.py
# Esperado: 6 vulnerabilidades detectadas
```

### 4️⃣ Testar análise correto (falsos positivos)
```bash
python code_analyzer.py exemplo_correto.py
# Esperado: 0 vulnerabilidades
```

### 5️⃣ Rodar extensão
```bash
# VS Code: F5 → Run Extension
# Em nova janela, abra exemplo_vulneravel.py
# Salve: Ctrl+S
# Esperado: Gutter icons vermelhos aparecem
```

---

## 🔍 Analisando Seu Código

### Arquivo único
```bash
python code_analyzer.py seu_arquivo.py
```

### Diretório inteiro
```bash
python reporter.py --codigo ./meu_projeto --json relatorio.json
```

### Banco SQLite
```bash
python db_analyzer.py ./database.db
```

---

## 📊 Visualizar Relatórios

### HTML (recomendado)
```bash
# Após gerar:
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

## 🔧 Troubleshooting

### ❌ Erro: "ModuleNotFoundError: No module named 'flask'"
```bash
pip install flask
```

### ❌ Porta 5000 em uso
```bash
# Mudar em VS Code Settings:
"privacy-scanner.serverPort": 5001
```

### ❌ TypeScript não compila
```bash
cd vscode-extension
npm install
npm run compile
```

### ❌ Testes falham
```bash
# Limpar cache pytest:
pytest --cache-clear tests/ -v
```

---

## 📈 Performance

Tempo de execução esperado:

| Operação | Tempo |
|----------|-------|
| Analisar arquivo único | ~50ms |
| Analisar projeto (10 arquivos) | ~200ms |
| Testes completos (51) | ~600ms |
| Exportar HTML | ~100ms |

---

## 🎓 Validação para TCC

### Checklist de Validação
- [x] Testes unitários rodando
- [x] Todos os testes passando (51/51)
- [x] Cobertura 74%+
- [x] Exemplos funcionando
- [x] Extensão VS Code funcional
- [x] Relatórios gerando corretamente
- [x] Bugs corrigidos e validados

### Métricas Finais
- Testes: **51/51 ✅**
- Cobertura: **74% ✅**
- Completude: **76% ✅**
- Status: **MVP ENTREGUE ✅**

---

## 📞 Próximos Passos

1. **Sidebar**: Implementar TreeView de vulnerabilidades
2. **Code Actions**: Sugestões inline de correção
3. **PDF Export**: Relatórios em PDF
4. **CI/CD**: GitHub Actions para testes automáticos

---

**Última atualização**: 2026-06-01  
**Status**: ✅ Tudo funcionando

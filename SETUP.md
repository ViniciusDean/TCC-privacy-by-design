# 🔒 Privacy Scanner LGPD — Setup Completo

## 📋 Estrutura do Projeto

```
TCC/
├── code_analyzer.py          ← Análise de código Python
├── db_analyzer.py            ← Análise de banco SQLite
├── reporter.py               ← Geração de relatórios
├── server.py                 ← Servidor Flask (NEW)
├── exemplo_vulneravel.py
├── exemplo_correto.py
├── teste_word_boundary.py
└── vscode-extension/         ← Extensão VS Code (NEW)
    ├── src/
    │   └── extension.ts
    ├── package.json
    ├── tsconfig.json
    ├── README.md
    └── ...
```

## 🚀 Instalação Rápida

### Opção Windows automática

Na raiz do projeto, execute:

```bat
setup_windows.bat
```

Esse script instala dependências Python, cria o workspace externo de teste, instala dependências npm e compila a extensão.

### 1️⃣ Python: Instale dependências

```bash
python -m pip install -r requirements.txt
```

### 2️⃣ Node.js: Compile a extensão

```bash
cd vscode-extension
npm install
npm run compile
cd ..
```

### 3️⃣ VS Code: Teste a extensão

- Abra o VS Code nesta pasta
- Pressione `Ctrl+Shift+D` (Debug)
- Clique em "Run Extension" ou `F5`

Abre uma nova janela VS Code com a extensão ativa! 🎉

Para gerar o workspace externo usado na demo:

```bash
python scripts/create_test_workspace.py
```

## 🧪 Teste Rápido

1. **Abrir arquivo Python**
   - Abra `exemplo_vulneravel.py` na extensão VS Code

2. **Análise automática**
   - Salve o arquivo (`Ctrl+S`)
   - Vulnerabilidades aparecem em vermelho no editor

3. **Analisar projeto**
   - `Ctrl+Shift+P` → "Privacy Scanner: Analisar projeto inteiro"

4. **Gerar relatório**
   - `Ctrl+Shift+P` → "Privacy Scanner: Exportar relatório HTML"
   - Abre `privacy-scan-YYYY-MM-DD.html` na raiz

## 📦 Dependências

| Projeto | Dependência | Versão | Instalação |
|---------|-------------|--------|------------|
| **Python** | Flask/Pytest | 2.x+/8.x+ | `python -m pip install -r requirements.txt` |
| **Node.js** | TypeScript | 4.x+ | `npm install` (automático) |
| **Node.js** | Axios | 1.4+ | `npm install` (automático) |
| **VS Code** | API | 1.60+ | Já incluído |

## ⚙️ Configurações

Em VS Code, pressione `Ctrl+,` e procure por `privacy-scanner`:

```json
{
  "privacy-scanner.serverPort": 5000,              // Porta do Flask
  "privacy-scanner.autoAnalyzeOnSave": true,      // Auto-análise ao salvar
  "privacy-scanner.pythonPath": "python",         // Caminho do Python
  "privacy-scanner.enableSidebar": true,          // Mostrar sidebar
  "privacy-scanner.showDiagnostics": true         // Mostrar no painel Problems
}
```

## 🔧 Solução de Problemas

### ❌ "Erro: Flask module not found"

```bash
python -m pip install -r requirements.txt
```

### ❌ "Erro: npm not found"

Instale Node.js em: https://nodejs.org/

### ❌ "Porta 5000 já em uso"

Altere em Settings:
```json
"privacy-scanner.serverPort": 5001
```

Ou libere a porta:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### ❌ "Python command not found"

Use o caminho absoluto em Settings:
```json
"privacy-scanner.pythonPath": "C:\\Python310\\python.exe"
```

## 📊 Fluxo de Funcionamento

```
┌─────────────────────────────────────────────────────────┐
│ VS Code (Extensão TypeScript)                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Salva arquivo .py                                   │ │
│ └────────────┬────────────────────────────────────────┘ │
│              │                                          │
│              ▼                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ axios.post('http://localhost:5000/api/...')        │ │
│ └────────────┬────────────────────────────────────────┘ │
└─────────────│──────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ Flask Server (server.py)                                │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ POST /api/analyze-file                              │ │
│ └────────────┬────────────────────────────────────────┘ │
│              │                                          │
│              ▼                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ analisar_arquivo(filepath) [Python]                 │ │
│ │  ├─ code_analyzer.py                                │ │
│ │  ├─ db_analyzer.py                                  │ │
│ │  └─ reporter.py                                     │ │
│ └────────────┬────────────────────────────────────────┘ │
│              │                                          │
│              ▼                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ return JSON com vulnerabilidades                    │ │
│ └────────────┬────────────────────────────────────────┘ │
└─────────────│──────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│ VS Code (Extensão TypeScript)                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ displayDiagnostics(uri, vulnerabilities)            │ │
│ │  ├─ Gutter icons (vermelho, amarelo, azul)         │ │
│ │  ├─ Painel Problems                                 │ │
│ │  └─ Hover info                                      │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## 📚 Referências

- [VS Code Extension API](https://code.visualstudio.com/api)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)

## ✅ Checklist de Deploy

- [ ] Python 3.8+ instalado
- [ ] Dependências Python instaladas (`python -m pip install -r requirements.txt`)
- [ ] Node.js instalado
- [ ] Dependências npm instaladas (`npm install`)
- [ ] TypeScript compilado (`npm run compile`)
- [ ] Extensão testada localmente (`F5`)
- [ ] Arquivos `.py` e `.ts` sem erros de sintaxe
- [ ] Servidor Flask inicia sem erros
- [ ] Análise retorna JSON correto

## 🎓 Próximos Passos

1. **Code actions** — Sugestões de correção direto no editor
2. **Publicação** — Empacotar como .vsix e publicar no marketplace
3. **CI/CD** — GitHub Actions para testar a cada commit

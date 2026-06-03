# Privacy Scanner — Extensão VS Code

Análise estática de vulnerabilidades de privacidade em Python conforme **LGPD e Privacy by Design**.

## Recursos

✅ **Análise em tempo real** — Ao salvar arquivo, vulnerabilidades aparecem imediatamente  
✅ **Problemas integrados** — Mostra alertas no painel Problems  
✅ **Análise de projeto** — Varre recursivamente arquivos Python  
✅ **Relatórios** — Exporta HTML e JSON para documentação  
✅ **Configurável** — Portas, caminhos Python, comportamentos  

## Instalação

### Pré-requisitos

- VS Code 1.60+
- Python 3.8+
- Flask (`pip install flask`)
- Axios (`npm install axios`)

### Setup da Extensão

1. **Clone/coloque a extensão no VS Code**

```bash
# No seu workspace TCC, entre na pasta vscode-extension
cd vscode-extension
npm install
npm run compile
```

2. **Instale Flask**

```bash
cd ..  # Volte para raiz TCC
pip install flask
```

3. **Abra como extensão em desenvolvimento**

No VS Code:
- Pressione `Ctrl+Shift+D` (Debug)
- Clique em "Run Extension"
- Abre uma nova janela VS Code com a extensão ativa

## Uso

### Análise automática ao salvar
Por padrão, quando você salva um arquivo `.py`, o Privacy Scanner analisa automaticamente e mostra vulnerabilidades.

### Comandos

Abra a Paleta de Comandos (`Ctrl+Shift+P`) e digite:

- `Privacy Scanner: Analisar arquivo atual` — Analisa só o arquivo aberto
- `Privacy Scanner: Analisar projeto inteiro` — Varre toda a pasta
- `Privacy Scanner: Analisar banco SQLite` — Seleciona um ou mais bancos `.db/.sqlite`
- `Privacy Scanner: Exportar relatório HTML` — Gera HTML na raiz do projeto
- `Privacy Scanner: Exportar relatório JSON` — Gera JSON na raiz do projeto

### Configurações

Em VS Code Settings (`Ctrl+,`), procure por `privacy-scanner`:

```json
{
  "privacy-scanner.serverPort": 5000,
  "privacy-scanner.autoAnalyzeOnSave": true,
  "privacy-scanner.pythonPath": "python",
  "privacy-scanner.enableSidebar": true,
  "privacy-scanner.showDiagnostics": true
}
```

## Arquitetura

```
vscode-extension/
├── src/
│   └── extension.ts         ← Código principal da extensão
├── out/
│   └── extension.js         ← Compilado (gerado por npm run compile)
├── package.json             ← Metadados e dependências
└── tsconfig.json            ← Configuração TypeScript

../server.py                 ← Servidor Flask (encapsula os analisadores)
../code_analyzer.py          ← Análise de código Python
../db_analyzer.py            ← Análise de banco SQLite
../reporter.py               ← Geração de relatórios
```

## Fluxo

1. **Salva arquivo Python** → VS Code trigger
2. **Extension.ts** → Chama `/api/analyze-file` no servidor Flask
3. **Server.py** → Executa `code_analyzer.analisar_arquivo()`
4. **Retorna JSON** com vulnerabilidades
5. **Extension.ts** → Exibe Diagnostics no editor (gutter icons)

## Troubleshooting

### "Servidor Flask não inicia"
- Verifique se Flask está instalado: `pip install flask`
- Verifique a porta em uso: `netstat -ano | findstr :5000`
- Altere em Settings: `privacy-scanner.serverPort`

### "Axios not found"
- Instale dependências: `cd vscode-extension && npm install`

### "Python not found"
- Configure o caminho em Settings: `privacy-scanner.pythonPath`
- Tente: `C:\Python310\python.exe` (caminho absoluto)

## Desenvolvimento

### Compilar TypeScript

```bash
npm run compile      # Uma vez
npm run watch        # Contínuo (auto-compile)
```

### Debug

Pressione `F5` para iniciar debug com breakpoints.

## Status

- [x] Análise de arquivo
- [x] Análise de projeto
- [x] Diagnostics API
- [ ] Sidebar com resumo
- [ ] Code actions (sugestões de correção)
- [ ] Testes unitários

## Licença

MIT

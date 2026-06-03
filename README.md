# 🔒 Privacy Scanner LGPD — TCC FATEC

**Privacy by Design no Ciclo de Desenvolvimento de Software**

Ferramenta de análise estática para detectar vulnerabilidades de privacidade em código Python e bancos SQLite conforme a Lei Geral de Proteção de Dados Pessoais (LGPD).

## 📊 Visão Geral

```
┌────────────────────────────────────────────────────────────┐
│ Privacy Scanner LGPD (Versão 1.0.0)                        │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  🔍 Análise Estática de Código Python                      │
│     ├─ Dados pessoais hardcoded                           │
│     ├─ Ausência/fraqueza de criptografia                  │
│     ├─ Dados em logs                                      │
│     ├─ Transferências sem base legal                      │
│     ├─ Coleta excessiva                                   │
│     └─ Ausência de métodos de exclusão                    │
│                                                             │
│  🗄️  Análise de Banco SQLite                               │
│     ├─ Campos sensíveis em texto puro                     │
│     ├─ Ausência de soft-delete                            │
│     ├─ Ausência de retenção                               │
│     ├─ Ausência de consentimento                          │
│     ├─ Mistura de dados                                   │
│     └─ Chaves primárias sensíveis                         │
│                                                             │
│  🎨 Interface VS Code                                       │
│     ├─ Análise em tempo real                              │
│     ├─ Gutter icons + Diagnostics API                     │
│     ├─ Comando manual                                     │
│     ├─ Exportação de relatórios                           │
│     └─ Configurações personalizáveis                      │
│                                                             │
│  📊 Relatórios                                             │
│     ├─ Terminal (sumário + detalhes)                      │
│     ├─ JSON (estrutura completa)                          │
│     ├─ HTML (visual com score)                            │
│     └─ (PDF — próximo)                                    │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

## 🗂️ Estrutura de Arquivos

```
TCC/
├── 📄 code_analyzer.py              ← Análise de código Python (AST)
├── 📄 db_analyzer.py                ← Análise de banco SQLite
├── 📄 reporter.py                   ← Geração de relatórios
├── 📄 server.py                     ← Servidor Flask (NEW)
│
├── 📚 Exemplos & Testes
│   ├── exemplo_vulneravel.py        ← 6 vulnerabilidades propositais
│   ├── exemplo_correto.py           ← Sem falsos positivos
│   ├── exemplo_parcial.py           ← Boas práticas parciais (NEW)
│   └── teste_word_boundary.py       ← Teste de word boundary
│
├── 🎨 vscode-extension/             ← Extensão VS Code (NEW)
│   ├── src/
│   │   └── extension.ts             ← Código TypeScript principal
│   ├── package.json                 ← Metadados & dependências
│   ├── tsconfig.json                ← Configuração TypeScript
│   ├── .vscodeignore                ← Empacotamento
│   ├── .gitignore
│   └── README.md                    ← Documentação da extensão
│
├── 📋 SETUP.md                      ← Guia de instalação (NEW)
└── 📋 README.md                     ← Este arquivo
```

## 🚀 Quick Start

### 1️⃣ Instalação Python

```bash
pip install flask
```

### 2️⃣ Compilar extensão

```bash
cd vscode-extension
npm install
npm run compile
```

### 3️⃣ Testar no VS Code

- Abra VS Code nesta pasta
- Pressione `F5` ou `Ctrl+Shift+D` → "Run Extension"
- Uma nova janela VS Code abre com a extensão ativa

### 4️⃣ Testar análise

- Abra `exemplo_vulneravel.py`
- Salve o arquivo (`Ctrl+S`)
- Vulnerabilidades aparecem em **vermelho** no editor ✨

## 📖 Uso

### CLI

```bash
# Analisar arquivo único
python code_analyzer.py exemplo_vulneravel.py

# Analisar projeto inteiro
python reporter.py --codigo . --json resultado.json --html resultado.html
```

### VS Code Extension

Paleta de Comandos (`Ctrl+Shift+P`):
- `Privacy Scanner: Analisar arquivo atual`
- `Privacy Scanner: Analisar projeto inteiro`
- `Privacy Scanner: Analisar banco SQLite`
- `Privacy Scanner: Exportar relatório HTML`
- `Privacy Scanner: Exportar relatório JSON`

## 📊 Vulnerabilidades Detectadas

### Código Python (7 regras)

| # | Categoria | Risco | Descrição |
|---|-----------|-------|-----------|
| 1 | DADO_HARDCODED | 🔴 ALTO | Dado pessoal fixo no código |
| 2 | DADO_SEM_CRIPTOGRAFIA | 🟡 MÉDIO | Sem hash ou criptografia |
| 3 | CRIPTOGRAFIA_FRACA | 🔴 ALTO | MD5, SHA1 (algoritmos fracos) |
| 4 | DADO_EM_LOG | 🔴 ALTO | Dado pessoal em print/logging |
| 5 | TRANSFERENCIA_SEM_BASE_LEGAL | 🔴 ALTO | Envio a terceiros sem justificação |
| 6 | COLETA_EXCESSIVA | 🟡 MÉDIO | Mais de 4 campos sensíveis |
| 7 | AUSENCIA_EXCLUSAO | 🟡 MÉDIO | Classe sem método delete/anonimizar |

### Banco SQLite (6 regras)

| # | Categoria | Risco | Descrição |
|---|-----------|-------|-----------|
| 1 | CAMPO_SEM_HASH | 🔴 ALTO | Campo sensível em TEXT puro |
| 2 | AUSENCIA_SOFT_DELETE | 🟡 MÉDIO | Sem coluna deleted_at |
| 3 | AUSENCIA_RETENCAO | 🔵 BAIXO | Sem política de retenção |
| 4 | AUSENCIA_CONSENTIMENTO | 🟡 MÉDIO | Sem coluna lgpd_aceito |
| 5 | MISTURA_DADOS | 🔵 BAIXO | Dados pessoais não segregados |
| 6 | DADO_SENSIVEL_COMO_PK | 🟡 MÉDIO | CPF/Email como chave primária |

## 📈 Score de Conformidade

Score LGPD = `100 - (ALTO×10 + MÉDIO×5 + BAIXO×2)`

- ✅ 80-100: Excelente conformidade
- ⚠️ 50-79: Conformidade aceitável
- 🔴 0-49: Crítico — correções necessárias

## 🧪 Exemplos

### exemplo_vulneravel.py
✗ 7 vulnerabilidades detectadas
```python
senha = "minhasenha123"        # DADO_HARDCODED (ALTO)
cpf = "123.456.789-00"         # DADO_HARDCODED (ALTO)
hash = hashlib.md5(...)        # CRIPTOGRAFIA_FRACA (ALTO)
logging.info(f"CPF: {cpf}")    # DADO_EM_LOG (ALTO)
requests.post(..., json={"cpf": cpf})  # TRANSFERENCIA (ALTO)
```

### exemplo_correto.py
✓ Sem falsos positivos
```python
nome = ""              # Inicialização vazia (OK)
user_agent = "..."    # Não é 'age' isolado (OK)
bcrypt.hashpw(...)    # Criptografia forte (OK)
Usuario.deletar()     # Método de exclusão (OK)
```

### exemplo_parcial.py
⚡ Boas práticas parciais
```python
bcrypt.hashpw(...)         # ✓ Forte
logging.info(email)        # ✗ Ainda expõe email
soft_delete()              # ✓ Implementado
exportar_usuario_json()    # ✗ Serializa tudo
```

## 🔧 Configuração

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

## 📦 Dependências

- **Python**: 3.8+
- **Flask**: 2.0+
- **Node.js**: 14+
- **TypeScript**: 4.0+
- **VS Code**: 1.60+

## 🚨 Troubleshooting

### ❌ Flask not found
```bash
pip install flask
```

### ❌ npm not found
Instale Node.js: https://nodejs.org/

### ❌ Porta 5000 em uso
Mude em VS Code Settings:
```json
"privacy-scanner.serverPort": 5001
```

## 📚 Documentação

- [SETUP.md](SETUP.md) — Instalação detalhada
- [vscode-extension/README.md](vscode-extension/README.md) — Docs da extensão
- [code_analyzer.py](code_analyzer.py) — Docstrings
- [db_analyzer.py](db_analyzer.py) — Docstrings

## 🧪 Testes Unitários

**Suite completa com 54 testes** — Todas as funcionalidades validadas ✅

### Executar Testes
```bash
pytest tests/ -v                    # Todos os testes
pytest tests/ --cov=. --cov-report=html  # Com cobertura (gera HTML)
```

### Cobertura Atual
```
code_analyzer.py:   86% (167 linhas, 23 não cobertas)
db_analyzer.py:     80% (128 linhas, 25 não cobertas)
reporter.py:        48% (103 linhas, 54 não cobertas)
─────────────────────────────────────────────
TOTAL:              74% (398 linhas, 102 não cobertas)
```

### Testes por Componente
- **code_analyzer.py**: 22 testes (detecção, word boundary, falsos positivos, LGPD)
- **db_analyzer.py**: 16 testes (schema, edge cases, artigos)
- **reporter.py**: 13 testes (sumário, score, export JSON/HTML)

Detalhes em [TESTS.md](TESTS.md)

## 🎓 Para o TCC

### Componentes Completados
- [x] Análise estática de Python
- [x] Análise de banco SQLite  
- [x] Mapeamento de artigos LGPD
- [x] Relatórios (terminal, JSON, HTML)
- [x] Extensão VS Code
- [x] Servidor Flask
- [x] Casos de teste (vulnerável, correto, parcial)
- [x] Configurações
- [x] Testes unitários (54 testes, 74% cobertura) ✅
- [x] Sidebar com resumo na extensão

### Próximos Passos (no escopo)
- [ ] Code actions (sugestões inline)
- [ ] Exportação PDF
- [ ] CI/CD (GitHub Actions)

### Fora do Escopo (futuro)
- [ ] Suporte a outras linguagens
- [ ] Suporte a MySQL, PostgreSQL
- [ ] Análise dinâmica (runtime)
- [ ] Dashboard web
- [ ] Publicação no Marketplace

## 📊 Métricas

| Componente | Linhas | Status | Completude | Cobertura |
|-----------|--------|--------|-----------|-----------|
| code_analyzer.py | ~350 | ✅ | 70% | **86%** |
| db_analyzer.py | ~250 | ✅ | 65% | **80%** |
| reporter.py | ~350 | ✅ | 60% | **48%** |
| server.py | ~250 | ✅ NEW | 100% | - |
| extension.ts | ~400 | ✅ NEW | 100% | - |
| **Testes** | **~1600** | ✅ NEW | **100%** | **54/54** ✅ |
| **Total** | **~3450** | ✅ | **76%** | **74%** |

## 👥 Autor

Desenvolvido como **TCC** na **FATEC** sob metodologia **DSR** (Design Science Research).

## 📄 Licença

MIT

---

**Status**: Versão 1.0.0 — Funcional ✅  
**Última atualização**: 2026-06-01  
**Próxima release**: Code Actions + PDF Export

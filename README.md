# Privacy Scanner LGPD — TCC FATEC

[![Validação e pacote VSIX](https://github.com/ViniciusDean/TCC-privacy-by-design/actions/workflows/ci.yml/badge.svg)](https://github.com/ViniciusDean/TCC-privacy-by-design/actions/workflows/ci.yml)

Ferramenta de análise estática para detectar indícios técnicos de risco à privacidade em código Python, código Java e bancos SQLite, com mapeamento das ocorrências para artigos da Lei Geral de Proteção de Dados Pessoais (LGPD).

Projeto desenvolvido no contexto de TCC sobre **Privacy by Design no Ciclo de Desenvolvimento de Software**.

## Visão Geral

O Privacy Scanner LGPD ajuda desenvolvedores a identificar riscos de privacidade ainda durante o desenvolvimento, sem executar o código analisado.

Os achados são evidências técnicas para revisão preliminar. Eles não comprovam, sozinhos, conformidade ou desconformidade jurídica com a LGPD, pois a conclusão depende de finalidade, base legal, políticas internas, arquitetura e processos fora do código-fonte.

## Fonte Canônica do TCC

O texto canônico é `latex_tcc/main.tex`. Os PDFs e DOCX históricos na raiz não
devem ser entregues como versão final. Para gerar o PDF atual, com XeLaTeX
instalado, execute:

```powershell
.\scripts\build_tcc.ps1
```

O script bloqueia termos obsoletos e marcadores de banca por padrão, gera o PDF
em `output/pdf/` e exige revisão visual posterior. O DOCX restaurado é fonte de
consulta; ele não deve ser regenerado automaticamente, pois o conversor atual
não preserva integralmente a estrutura.

Principais recursos:

- Análise estática de código Python usando AST.
- Análise inicial de código Java com regras textuais conservadoras.
- Análise de schema SQLite.
- Mapeamento automático para artigos da LGPD.
- Indicador técnico de risco de 0 a 100.
- Extensão VS Code com diagnósticos no editor.
- Sidebar com ações rápidas, resumo e agrupamento por risco.
- Ações no título do editor e nos menus de contexto do editor e Explorer.
- Code Actions com recomendações LGPD.
- Possibilidade de ocultar uma ocorrência somente na interface.
- Exportação de relatório HTML interativo.
- Exportação de relatório PDF formal.
- Exportação JSON estruturada.

## Estrutura do Projeto

```text
TCC/
|-- code_analyzer.py              # Análise de código Python via AST
|-- java_analyzer.py              # Análise inicial de código Java
|-- db_analyzer.py                # Análise de schema SQLite
|-- reporter.py                   # Agregação e relatórios JSON/HTML
|-- server.py                     # API Flask usada pela extensão VS Code
|-- requirements.txt              # Dependências Python
|-- pytest.ini                    # Configuração dos testes
|-- push_github.bat               # Script local para commit/push
|-- setup_windows.bat             # Setup inicial no Windows
|-- validate_project.bat          # Validação local do projeto
|
|-- exemplo_vulneravel.py         # Exemplo com achados propositais
|-- exemplo_correto.py            # Exemplo sem falsos positivos esperados
|-- exemplo_parcial.py            # Exemplo intermediário/realista
|-- exemplo_vulneravel.java       # Exemplo Java vulnerável
|-- exemplo_correto.java          # Exemplo Java sem alertas esperados
|-- examples/vulnerable/          # Cenários vulneráveis adicionais e fictícios
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
python -m pytest -q
cd vscode-extension
npm test
cd ..
```

O resultado reproduzido para a versão 1.2.0 é **181 testes Python aprovados**,
além da suíte TypeScript, lint e compilação da extensão. A versão 1.0.4,
com 135 testes Python, permanece como baseline histórica.

### 4. Testar a extensão no VS Code

1. Abra a pasta `TCC` no VS Code.
2. Pressione `F5`.
3. Uma nova janela `[Extension Development Host]` será aberta.
4. Abra a pasta de teste ou um arquivo Python.
5. Clique no ícone `Privacy Scanner` da barra de atividades e use `Ações rápidas`.

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

O fluxo principal da versão 1.2.0 é clicável:

1. Clique no ícone `Privacy Scanner` da barra de atividades.
2. Em `Ações rápidas`, escolha uma das cinco ações principais: analisar o
   arquivo atual, analisar o projeto inteiro, selecionar um banco SQLite,
   exportar relatório ou configurar o perfil por um assistente.
3. Expanda `Configuração e suporte` para limpar resultados, restaurar achados
   ocultados, configurar dependências, reiniciar o backend, abrir logs ou abrir
   as configurações.

O nome do arquivo ativo, o preset selecionado e o estado do backend aparecem no
próprio painel. Também é possível:

- clicar no botão de análise no título de um editor Python ou Java;
- clicar com o botão direito no editor ou em um arquivo `.py`/`.java` no
  Explorer e escolher `Analisar arquivo`;
- clicar com o botão direito em `.db`, `.sqlite` ou `.sqlite3` no Explorer e
  escolher `Analisar banco SQLite`;
- clicar no item da barra de status para abrir o painel.

A Paleta de Comandos (`Ctrl+Shift+P`) continua disponível como alternativa. Os
principais comandos são:

- `Privacy Scanner: Analisar agora`
- `Privacy Scanner: Analisar arquivo`
- `Privacy Scanner: Analisar projeto inteiro`
- `Privacy Scanner: Analisar banco SQLite`
- `Privacy Scanner: Limpar resultados`
- `Privacy Scanner: Exportar relatorio`
- `Privacy Scanner: Exportar relatório HTML`
- `Privacy Scanner: Exportar relatório JSON`
- `Privacy Scanner: Configurar perfil`
- `Privacy Scanner: Editar perfil JSON (avançado)`

A extensão também analisa arquivos Python e Java automaticamente ao abrir, trocar de aba ou salvar.

Arquivos Java (`.java`) seguem o mesmo fluxo de análise e diagnostics.

## Sidebar da Extensão

A sidebar possui `Ações rápidas`, `Achados` e `Resumo`. Ela mostra:

- achados técnicos agrupados por risco;
- arquivos afetados;
- indicador técnico;
- total de achados;
- contagem por risco;
- quantidade de arquivos Python, arquivos Java e bancos SQLite com achados.

Enquanto a análise está em andamento, a sidebar mostra estado de carregamento em vez de exibir `100/100` antes da hora.

Falhas conhecidas oferecem ações diretas: abrir configurações quando o
Python não é encontrado; configurar dependências ou abrir logs quando o
runtime está incompleto; reiniciar o backend ou abrir logs quando o serviço
está indisponível; e abrir o perfil quando sua configuração é inválida.

## Code Actions

Quando um achado aparece sublinhado no editor, use a lâmpada/Quick Fix para:

- ver a recomendação LGPD da regra;
- copiar a recomendação para a área de transferência.

Também é possível ignorar uma ocorrência na interface. O achado deixa de aparecer na sidebar e no painel `Problems`, mas continua presente nos relatórios HTML, JSON e PDF. Use `Privacy Scanner: Restaurar riscos ignorados` para exibi-lo novamente.

## Relatórios

### HTML

O relatório HTML inclui:

- indicador técnico;
- cards por risco;
- escopo analisado;
- resumo técnico;
- tabela de achados técnicos;
- recomendações;
- evidência técnica redigida, sem literais sensíveis do código/schema;
- filtro por risco;
- ordenação ao clicar nos cabeçalhos da tabela.

Na extensão, ao exportar HTML, o VS Code abre a janela do Windows para escolher nome e destino do arquivo.

### JSON

O JSON contém:

- metadados da ferramenta;
- timestamp;
- sumário;
- lista estruturada de achados técnicos;
- recomendação de correção por categoria.

### PDF

O relatório PDF inclui:

- cabeçalho formal;
- indicador técnico;
- resumo por risco;
- escopo analisado;
- achados técnicos agrupados por risco;
- recomendações;
- seção de evidências técnicas;
- rodapé com paginação.

A recomendação do projeto é manter:

- HTML como relatório interativo;
- PDF como documento técnico estático para revisão e evidência de teste, nunca
  como certificação de conformidade.

## Regras Detectadas

### Código Python

| Categoria | Risco | Artigo LGPD | Descrição |
|---|---|---|---|
| DADO_HARDCODED | ALTO | Art. 46 | Dado pessoal fixo no código |
| CRIPTOGRAFIA_FRACA | ALTO | Art. 46 | Uso de MD5 ou SHA1 |
| DADO_EM_LOG | ALTO | Art. 46 | Dado pessoal em print/logging |
| TRANSFERENCIA_SEM_BASE_LEGAL | ALTO | Art. 7 / Art. 33 | Integração externa com marcador técnico de base legal não evidenciado |
| COLETA_EXCESSIVA | MÉDIO | Art. 6 | Método com conjunto de campos sensíveis a revisar |
| AUSENCIA_EXCLUSAO | MÉDIO | Art. 18 | Evidência de exclusão/anonimização não identificada localmente |
| DADO_SEM_CRIPTOGRAFIA | MÉDIO | Art. 46 | Proteção do campo não evidenciada na análise estática |

### Código Java

| Categoria | Risco | Artigo LGPD | Descrição |
|---|---|---|---|
| DADO_HARDCODED | ALTO | Art. 46 | Dado pessoal literal atribuído a campo sensível |
| CRIPTOGRAFIA_FRACA | ALTO | Art. 46 | MD5 ou SHA-1 via `MessageDigest`, Apache Commons Codec ou Guava |
| DADO_EM_LOG | ALTO | Art. 46 / Art. 6 | Dado pessoal em logger ou `System.out/System.err` |
| TRANSFERENCIA_SEM_BASE_LEGAL | ALTO | Art. 7 / Art. 33 | Integração HTTP com marcador técnico de base legal não evidenciado |
| COLETA_EXCESSIVA | MÉDIO | Art. 6 | Método ou construtor com quatro ou mais parâmetros sensíveis |
| AUSENCIA_EXCLUSAO | MÉDIO | Art. 18 | Evidência de exclusão/anonimização não identificada localmente |
| DADO_SEM_CRIPTOGRAFIA | MÉDIO | Art. 46 | Proteção do campo não evidenciada na análise estática |

O suporte Java usa análise léxica conservadora, com reconhecimento de comentários,
strings, instruções multilinha, classes e assinaturas de métodos. Ele não compila
o projeto e não realiza análise de fluxo de dados entre métodos; por isso, os
achados devem ser revisados pelo desenvolvedor.

### Banco SQLite

| Categoria | Risco | Artigo LGPD | Descrição |
|---|---|---|---|
| CAMPO_SEM_HASH | ALTO | Art. 46 | Proteção de campo sensível não evidenciada no schema; hash não é prova genérica de proteção |
| AUSENCIA_SOFT_DELETE | MÉDIO | Art. 18 | Evidência de exclusão lógica ou anonimização não identificada no schema |
| AUSENCIA_CONSENTIMENTO | MÉDIO | Art. 7 / Art. 11 | Rótulo público: proteção/base legal não evidenciada; exige revisão humana |
| DADO_SENSIVEL_COMO_PK | MÉDIO | Art. 46 | CPF/email usado como chave primária |
| DADO_SENSIVEL_COMO_INDICE_UNICO | MÉDIO | Art. 46 | Identificador pessoal em índice único |
| AUSENCIA_RETENCAO | BAIXO | Art. 15--16 | Evidência de retenção ou expurgo não identificada no schema |
| MISTURA_DADOS | BAIXO | Art. 6 | Organização de dados que merece revisão de minimização e separação lógica |

Os códigos de categoria permanecem estáveis para compatibilidade e benchmark. A
interface e os relatórios exibem linguagem de evidência técnica, sem afirmar a
ausência jurídica de consentimento, base legal ou controle.

## Indicador Técnico LGPD

O indicador é uma métrica operacional baseada na quantidade e severidade dos achados. Ele facilita comparação entre execuções, mas não deve ser apresentado como certificação de conformidade.

A fórmula usa penalizações simples e crescentes por severidade: achados `ALTO`
pesam mais porque indicam exposição direta ou proteção insuficiente de dados
pessoais; achados `MÉDIO` sinalizam ausência de controles relevantes; achados
`BAIXO` indicam pontos de governança ou desenho que merecem revisão. Os pesos
`10`, `5` e `2` foram escolhidos como critério operacional de priorização, não
como medida estatística, jurídica ou regulatória.

Fórmula:

```text
100 - (ALTO * 10 + MÉDIO * 5 + BAIXO * 2)
```

Interpretação:

| Indicador | Situação |
|---|---|
| 80-100 | Baixo risco técnico |
| 50-79 | Revisar controles |
| 0-49 | Risco técnico crítico |

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
| POST | `/api/export` | Exporta relatório HTML/JSON/PDF |

As respostas canônicas usam `achados`, `resumo`, `criterio_indicador` e
metadados de escopo (`status`, arquivos elegíveis/analisados/ignorados/falhos e
erros por arquivo). O indicador é nulo quando não há escopo válido analisado.
Os campos `vulnerabilities`, `vulnerabilidades` e `score_conformidade`
permanecem como aliases idênticos de compatibilidade; interfaces novas devem
usar os campos canônicos.

## Configurações da Extensão

### Perfis de análise v1.1

A versão 1.1 aceita `.privacy-scanner.json` por pasta de workspace, com presets
`conservador`, `equilibrado` e `completo`. O perfil controla categorias, limiar
de confiança e severidade exibida sem apagar a severidade-base auditável. A
extensão valida o arquivo, registra seu hash nos resultados e bloqueia análises
quando a configuração é inválida.

Na 1.2.0, clique em `Configurar perfil` nas `Ações rápidas`. O assistente
abre `Configurar perfil — <pasta>` e permite escolher o preset base, marcar as
regras ativas e personalizar confiança mínima ou severidade técnica por regra.
Somente `Salvar perfil` grava o arquivo; `Cancelar sem salvar` e `Esc` preservam
o estado anterior. Em workspaces multirraiz, o título identifica a pasta em
edição. Se o perfil estiver inválido, a ação aparece como `Corrigir perfil`.

A severidade personalizada afeta agrupamentos, totais e o indicador técnico;
ela não representa conclusão jurídica de conformidade ou desconformidade.

A edição manual de `.privacy-scanner.json` fica reservada ao fluxo avançado
`Privacy Scanner: Editar perfil JSON (avançado)` na Paleta de Comandos.

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
- `test_reporter.py`: indicador técnico, ordenação, recomendações, JSON, HTML e PDF.

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
- indicador técnico de risco;
- relatório terminal;
- exportação JSON;
- exportação HTML interativa;
- exportação PDF formal;
- servidor Flask;
- extensão VS Code;
- sidebar;
- botão de análise;
- botão de exportação;
- Code Actions;
- workspace de teste;
- suíte automatizada Python e de extensão;
- benchmark controlado de regressão com 18 fixtures versionadas;
- validação externa adjudicada em PEAK, Flasky e Chinook SQLite;
- apresentação e roteiro de defesa em `output/presentation/`.

### Entrega 1.2.0 e artefatos históricos

- `output/release/privacy-scanner-lgpd-1.2.0.vsix`: pacote atual, com redução
  de falsos positivos, indicadores bruto/exibido, UX clicável e backend incluído.
  SHA-256: `88A02458FE00E4F658BA723F4B6D40D9AF499F1B6CF59F058FE0D490C39F95C6`.
- `output/release/privacy-scanner-lgpd-1.1.1.vsix`: pacote anterior da UX
  clicável, preservado como histórico.
- `output/release/privacy-scanner-lgpd-1.1.0.vsix`: release 1.1 anterior,
  preservada como histórico.
- `output/release/privacy-scanner-lgpd-1.0.4.vsix`: baseline histórica da
  extensão preservada na tag `v1.0.4`.
- `output/presentation/TCC_Privacy_by_Design_Banca.pptx`: apresentação de 10
  slides, acompanhada de roteiro para 12–15 minutos.
- `output/pdf/TCC_Privacy_by_Design_2026_PROVA_COM_PLACEHOLDERS.pdf`: somente
  prova visual enquanto os dois nomes da banca não forem preenchidos.
- `output/release/SHA256SUMS.txt`: hashes dos artefatos entregáveis.

### Gerar extensão instalável

```powershell
cd vscode-extension
npm install
npm run package
code --install-extension .\privacy-scanner-lgpd-1.2.0.vsix --force
```

O VSIX inclui o backend Python e funciona sem manter o repositório do TCC
aberto. Python, Flask e ReportLab precisam estar instalados no computador.

### Validação automática no GitHub

O workflow `.github/workflows/ci.yml` é executado em cada push para `main`,
pull request ou acionamento manual. Ele:

- instala as dependências Python;
- executa a suíte Python;
- instala as dependências da extensão com `npm ci`;
- compila o TypeScript;
- gera o VSIX;
- disponibiliza o pacote como artefato por 30 dias.

Para baixar, abra a aba `Actions` do repositório, selecione uma execução e
baixe o artefato `privacy-scanner-lgpd-vsix`.

### Exclusões da análise

A análise de projeto ignora automaticamente dependências e arquivos gerados,
incluindo `.venv`, `venv`, `site-packages`, `node_modules`, `build`, `dist`,
caches e o backend empacotado da extensão.

Para excluir fixtures ou exemplos específicos, crie `.privacyignore` na raiz:

```text
# Diretório completo
fixtures/

# Arquivo específico
exemplo_vulneravel.py
```

O `.privacyignore` afeta apenas a análise do projeto inteiro. Um arquivo
ignorado ainda pode ser analisado individualmente.

## Limitações Conhecidas

- A análise é estática e baseada em regras.
- A ferramenta não executa o código analisado.
- A ferramenta não substitui auditoria jurídica ou revisão completa de segurança.
- A análise Java é baseada em heurísticas léxicas e não substitui um parser ou compilador.
- O Java possui as mesmas sete categorias do analisador de código, mas sem análise de fluxo entre métodos.
- Algumas ocorrências podem exigir revisão manual para confirmar o contexto.

## Autor

Desenvolvido por Dean V. como TCC na FATEC.

## Licença

MIT

# Privacy Scanner LGPD - Extensão VS Code

Extensão do VS Code para executar o Privacy Scanner LGPD durante o desenvolvimento.

A extensão conversa com o servidor Flask do projeto e exibe os resultados dentro do VS Code, sem executar o código analisado.

## Recursos Implementados

- Análise de arquivo Python.
- Análise de arquivo Java com sete categorias de privacidade.
- Análise de projeto inteiro.
- Análise de banco SQLite (`.db`, `.sqlite`, `.sqlite3`).
- Diagnósticos no editor e no painel `Problems`.
- Sidebar com vulnerabilidades agrupadas por risco.
- Sidebar com score LGPD e resumo.
- Estado de carregamento durante a análise.
- Botão/comando `Analisar agora`.
- Code Actions com recomendações LGPD.
- Exportação HTML.
- Exportação PDF.
- Exportação JSON por comando específico.
- Janela do Windows para escolher nome e destino do relatório.
- Inicialização automática do servidor Flask.
- Reutilização do servidor Flask caso ele já esteja ativo na porta configurada.
- Opção de ocultar uma ocorrência na interface sem removê-la dos relatórios.

## Pré-requisitos

- VS Code 1.60 ou superior.
- Python 3.8 ou superior.
- Node.js e npm.
- Dependências Python instaladas na raiz do projeto.
- Dependências Node instaladas em `vscode-extension`.

Na raiz do projeto:

```powershell
python -m pip install -r requirements.txt
```

Na pasta da extensão:

```powershell
cd vscode-extension
npm install
npm run compile
```

## Rodar em Desenvolvimento

1. Abra a pasta `TCC` no VS Code.
2. Pressione `F5`.
3. Aguarde abrir a janela `[Extension Development Host]`.
4. Na nova janela, abra uma pasta de teste ou um arquivo Python.
5. Use a sidebar `Privacy Scanner`.

Se quiser recriar o workspace externo de teste:

```powershell
python scripts/create_test_workspace.py
```

## Comandos

Na Paleta de Comandos (`Ctrl+Shift+P`):

- `Privacy Scanner: Analisar agora`
- `Privacy Scanner: Analisar arquivo atual`
- `Privacy Scanner: Analisar projeto inteiro`
- `Privacy Scanner: Analisar banco SQLite`
- `Privacy Scanner: Limpar resultados`
- `Privacy Scanner: Exportar relatorio`
- `Privacy Scanner: Exportar relatório HTML`
- `Privacy Scanner: Exportar relatório JSON`
- `Privacy Scanner: Mostrar vulnerabilidades`

## Comportamento de Análise

### Analisar agora

O comando `Privacy Scanner: Analisar agora` funciona assim:

- se houver uma pasta aberta, analisa o projeto inteiro;
- se não houver pasta aberta, analisa o arquivo atual.

### Automático

Quando `privacy-scanner.autoAnalyzeOnSave` está ativado, arquivos Python, Java e bancos SQLite podem ser analisados ao:

- abrir arquivo;
- trocar de aba;
- salvar arquivo.

## Sidebar

A sidebar `Privacy Scanner` possui duas visões:

### Vulnerabilidades

Mostra:

- riscos `ALTO`, `MEDIO` e `BAIXO`;
- arquivos afetados;
- vulnerabilidades por arquivo;
- ícones diferentes para código e banco;
- clique para abrir vulnerabilidade de código na linha correspondente.

### Resumo

Mostra:

- score LGPD;
- total de vulnerabilidades;
- quantidade de arquivos Python com achados;
- quantidade de arquivos Java com achados;
- quantidade de bancos SQLite com achados;
- contagem por risco.

Durante a análise, a sidebar mostra estado de carregamento para evitar exibir `100/100` antes do resultado real.

## Code Actions

Quando uma vulnerabilidade aparece no editor:

1. Clique na lâmpada/Quick Fix.
2. Escolha `Ver recomendacao LGPD` ou `Copiar recomendacao LGPD`.

A extensão não altera o código automaticamente. Ela mostra a recomendação para orientar a correção manual.

## Ignorar Risco na Interface

Uma ocorrência pode ser ocultada de duas formas:

- clique com o botão direito na vulnerabilidade da sidebar e escolha `Ignorar risco na interface`;
- use a lâmpada/Quick Fix no editor e escolha `Ignorar este risco na interface`.

O risco deixa de aparecer na sidebar, no resumo e no painel `Problems`. A preferência fica salva no workspace.

Essa opção não altera a análise do backend. O risco continua aparecendo nos relatórios HTML, JSON e PDF.

Para mostrar tudo novamente, execute:

```text
Privacy Scanner: Restaurar riscos ignorados
```

## Exportação

Use:

```text
Privacy Scanner: Exportar relatorio
```

Depois escolha:

- `HTML`;
- `PDF`.

O VS Code abrirá a janela do Windows para escolher o destino e o nome do arquivo.

Também existem comandos diretos:

- `Privacy Scanner: Exportar relatório HTML`;
- `Privacy Scanner: Exportar relatório JSON`.

## Configurações

Em `settings.json`:

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

```text
VS Code Extension
  |
  | HTTP
  v
server.py (Flask)
  |
  |-- code_analyzer.py  -> análise Python
  |-- java_analyzer.py  -> análise inicial Java
  |-- db_analyzer.py    -> análise SQLite
  |-- reporter.py       -> HTML/JSON/PDF
```

Endpoints usados:

- `GET /health`;
- `POST /api/analyze-file`;
- `POST /api/analyze-directory`;
- `POST /api/analyze-database`;
- `POST /api/export`.

## Desenvolvimento

Compilar:

```powershell
npm run compile
```

Compilar em modo contínuo:

```powershell
npm run watch
```

Rodar testes Python na raiz:

```powershell
python -m pytest
```

Resultado esperado:

```text
79 passed
```

## Gerar e Instalar o VSIX

Na pasta `vscode-extension`, execute:

```powershell
npm install
npm run package
```

O comando:

1. copia o backend Python necessário para dentro do pacote;
2. compila o TypeScript;
3. gera `privacy-scanner-lgpd-1.0.1.vsix`.

Para instalar pelo terminal:

```powershell
code --install-extension .\privacy-scanner-lgpd-1.0.1.vsix --force
```

Também é possível abrir a área de extensões do VS Code, clicar em `...`,
selecionar `Install from VSIX...` e escolher o arquivo gerado.

Após instalar, use `Developer: Reload Window` ou reinicie o VS Code. A extensão
passa a funcionar em qualquer pasta aberta, sem depender do repositório do TCC.

O computador ainda precisa ter Python e as dependências de execução:

```powershell
python -m pip install flask reportlab
```

Se as dependências estiverem ausentes, a extensão mostrará o comando completo
usando o `requirements.txt` incluído no VSIX.

### Pacote gerado pelo GitHub

Cada push para `main` executa o workflow do GitHub Actions. Ao final de uma
execução bem-sucedida, o VSIX fica disponível na seção `Artifacts` com o nome
`privacy-scanner-lgpd-vsix`.

## Troubleshooting

### Servidor Flask não inicia

Instale as dependências Python:

```powershell
python -m pip install -r requirements.txt
```

### Porta 5000 em uso

A extensão tenta reutilizar o servidor se ele já estiver ativo. Se a porta estiver ocupada por outro processo, altere:

```json
{
  "privacy-scanner.serverPort": 5001
}
```

### Python não encontrado

Configure o caminho absoluto:

```json
{
  "privacy-scanner.pythonPath": "C:\\Python312\\python.exe"
}
```

### Extensão não atualiza depois de editar TypeScript

Compile novamente:

```powershell
npm run compile
```

Depois recarregue a janela `[Extension Development Host]`.

## Status

- [x] Análise de arquivo Python
- [x] Análise de arquivo Java com sete categorias
- [x] Análise de projeto
- [x] Análise de banco SQLite
- [x] Diagnostics API
- [x] Sidebar com resumo
- [x] Estado de carregamento
- [x] Code Actions
- [x] Exportação HTML
- [x] Exportação JSON
- [x] Exportação PDF
- [x] Save dialog para relatório
- [x] Reutilização de servidor Flask ativo
- [x] Ocultar riscos somente na interface

## Limitações

- A análise é estática e baseada em regras.
- A extensão não substitui auditoria jurídica.
- O suporte Java usa análise léxica e não compila o projeto.
- O Java cobre sete categorias, mas não acompanha fluxo de dados entre métodos.
- Algumas ocorrências podem exigir revisão manual.

# RUN.md - Como Executar o Privacy Scanner LGPD

Este guia descreve o fluxo real para rodar, testar e demonstrar o projeto.

## 1. Preparar o Ambiente

Na raiz do projeto:

```powershell
cd C:\Users\deanv\OneDrive\Documents\TCC
python -m pip install -r requirements.txt
```

Na pasta da extensão:

```powershell
cd vscode-extension
npm install
npm run compile
cd ..
```

Resultado esperado da compilação:

```text
privacy-scanner-lgpd@1.0.0 compile
tsc -p ./
```

## 2. Validar o Projeto

Rodar todos os testes Python:

```powershell
python -m pytest
```

Resultado esperado:

```text
79 passed
```

Compilar a extensão:

```powershell
cd vscode-extension
npm run compile
cd ..
```

Também é possível usar:

```powershell
validate_project.bat
```

Esse script roda a validação principal do projeto no Windows.

## 3. Rodar a Extensão no VS Code

1. Abra a pasta `TCC` no VS Code.
2. Pressione `F5`.
3. Se o VS Code perguntar a configuração de debug, selecione a opção da extensão.
4. Uma nova janela `[Extension Development Host]` será aberta.
5. Nessa nova janela, abra uma pasta ou arquivo Python para testar.

Se quiser recriar a pasta externa de testes:

```powershell
python scripts/create_test_workspace.py
```

O workspace de teste fica em:

```text
C:\Users\deanv\OneDrive\Documents\privacy-scanner-testes
```

## 4. Fluxo de Uso na Extensão

Na janela `[Extension Development Host]`, use a sidebar `Privacy Scanner`.

Comandos principais na Paleta de Comandos (`Ctrl+Shift+P`):

- `Privacy Scanner: Analisar agora`
- `Privacy Scanner: Analisar arquivo atual`
- `Privacy Scanner: Analisar projeto inteiro`
- `Privacy Scanner: Analisar banco SQLite`
- `Privacy Scanner: Limpar resultados`
- `Privacy Scanner: Exportar relatorio`

O comando `Analisar agora` usa este comportamento:

- se houver workspace aberto, analisa o projeto inteiro;
- se não houver workspace, analisa o arquivo atual.

Arquivos Python e bancos SQLite também podem ser analisados automaticamente ao abrir, trocar de aba ou salvar, conforme a configuração `privacy-scanner.autoAnalyzeOnSave`.

Arquivos Java (`.java`) também podem ser abertos, salvos e analisados pelo mesmo fluxo.

## 5. Teste Manual com Python

### Arquivo vulnerável

Abra `exemplo_vulneravel.py` e execute:

```text
Privacy Scanner: Analisar arquivo atual
```

Resultado esperado:

- marcações no editor;
- alertas no painel `Problems`;
- vulnerabilidades agrupadas por risco na sidebar;
- score LGPD menor que 100.

### Arquivo correto

Abra `exemplo_correto.py` e execute:

```text
Privacy Scanner: Analisar arquivo atual
```

Resultado esperado:

- nenhuma vulnerabilidade relevante;
- score LGPD próximo de 100;
- ausência de falsos positivos nas boas práticas demonstradas.

### Exemplos Java

Abra `exemplo_vulneravel.java` e execute:

```text
Privacy Scanner: Analisar arquivo atual
```

O exemplo demonstra:

- dado pessoal hardcoded;
- criptografia fraca;
- dado pessoal em log;
- transferência externa sem base legal documentada;
- coleta excessiva;
- ausência de exclusão/anonimização;
- atribuição de dado sensível sem proteção.

Depois abra `exemplo_correto.java`. Esse arquivo usa SHA-256, log com
identificador técnico, payload anonimizado e método de anonimização; portanto,
não deve gerar achados.

## 6. Teste Manual com Banco SQLite

Na extensão:

1. Execute `Privacy Scanner: Analisar banco SQLite`.
2. Selecione um arquivo `.db`, `.sqlite` ou `.sqlite3`.
3. Verifique os achados na sidebar.

Categorias esperadas em banco vulnerável:

- `CAMPO_SEM_HASH`;
- `AUSENCIA_SOFT_DELETE`;
- `AUSENCIA_RETENCAO`;
- `AUSENCIA_CONSENTIMENTO`;
- `DADO_SENSIVEL_COMO_PK`;
- `MISTURA_DADOS`.

Observação: vulnerabilidades de banco geralmente aparecem com linha `0`, pois vêm do schema e não de uma linha específica de código.

## 7. Exportar Relatórios

### Ignorar uma ocorrência na interface

Na sidebar, clique com o botão direito em uma vulnerabilidade e escolha `Ignorar risco na interface`. Também é possível usar a lâmpada/Quick Fix no editor.

O risco deixa de aparecer na sidebar, no score visível e no painel `Problems`, mas continua nos relatórios. Para desfazer, execute:

```text
Privacy Scanner: Restaurar riscos ignorados
```

Na extensão:

1. Execute `Privacy Scanner: Exportar relatorio`.
2. Escolha `HTML` ou `PDF`.
3. O VS Code abrirá a janela do Windows para escolher nome e destino.
4. Após salvar, clique em `Abrir` se quiser visualizar.

### HTML

O HTML é o relatório interativo. Ele contém:

- score LGPD;
- contagem por risco;
- escopo analisado;
- tabela de vulnerabilidades;
- recomendações;
- filtro por risco;
- ordenação por coluna.

### PDF

O PDF é o relatório formal e estático. Ele contém:

- cabeçalho do Privacy Scanner;
- score LGPD;
- resumo por risco;
- vulnerabilidades agrupadas;
- recomendações de correção;
- paginação.

## 8. Rodar pela CLI

Analisar arquivo Python:

```powershell
python code_analyzer.py exemplo_vulneravel.py
```

Analisar banco SQLite:

```powershell
python db_analyzer.py banco_vulneravel.db
```

Gerar relatório HTML:

```powershell
python reporter.py --codigo . --html resultado.html
```

Gerar relatório JSON:

```powershell
python reporter.py --codigo . --json resultado.json
```

Gerar relatório PDF:

```powershell
python reporter.py --codigo . --pdf resultado.pdf
```

## 9. Rodar a API Flask Manualmente

Normalmente a extensão inicia o Flask automaticamente. Para testar manualmente:

```powershell
python server.py 5000
```

Health check:

```powershell
curl http://localhost:5000/health
```

Analisar arquivo:

```powershell
curl -X POST http://localhost:5000/api/analyze-file `
  -H "Content-Type: application/json" `
  -d "{\"filepath\":\"C:\\Users\\deanv\\OneDrive\\Documents\\TCC\\exemplo_vulneravel.py\"}"
```

Analisar diretório:

```powershell
curl -X POST http://localhost:5000/api/analyze-directory `
  -H "Content-Type: application/json" `
  -d "{\"directory\":\"C:\\Users\\deanv\\OneDrive\\Documents\\TCC\"}"
```

Exportar relatório:

```powershell
curl -X POST http://localhost:5000/api/export `
  -H "Content-Type: application/json" `
  -d "{\"directory\":\"C:\\Users\\deanv\\OneDrive\\Documents\\TCC\",\"format\":\"html\"}"
```

## 10. Troubleshooting

### Flask não inicia

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

Se a porta 5000 estiver ocupada, altere no VS Code Settings:

```json
{
  "privacy-scanner.serverPort": 5001
}
```

### Extensão não compila

```powershell
cd vscode-extension
npm install
npm run compile
```

### PDF não exporta

Confirme se `reportlab` está instalado:

```powershell
python -m pip install -r requirements.txt
```

### Sumário da sidebar fica vazio

Execute:

```text
Privacy Scanner: Analisar agora
```

ou abra/salve um arquivo Python.

## 11. Limitações Conhecidas

- A análise é estática e baseada em regras.
- A ferramenta não executa o código analisado.
- A ferramenta não substitui auditoria jurídica ou revisão de segurança completa.
- O suporte Java usa análise léxica e não compila o projeto.
- O Java cobre sete categorias, mas não acompanha fluxo de dados entre métodos.
- Algumas regras são heurísticas e podem exigir revisão manual.

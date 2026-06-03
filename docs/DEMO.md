# Roteiro de Demo - Privacy Scanner LGPD

Este roteiro valida o fluxo principal da ferramenta para apresentacao e testes manuais.

## 1. Preparar ambiente

Na raiz do projeto:

```powershell
python -m pip install -r requirements.txt
python scripts/create_test_workspace.py
cd vscode-extension
npm install
npm run compile
cd ..
```

## 2. Abrir extensao em modo desenvolvimento

1. Abra `C:\Users\deanv\OneDrive\Documents\TCC` no VS Code.
2. Pressione `F5`.
3. Selecione `Run Privacy Scanner Extension`.
4. A janela `[Extension Development Host]` deve abrir o workspace:

```text
C:\Users\deanv\OneDrive\Documents\privacy-scanner-testes
```

## 3. Testar analise de codigo

1. Abra `exemplo_vulneravel.py`.
2. Rode `Ctrl+Shift+P`.
3. Execute `Privacy Scanner: Analisar arquivo atual`.
4. Verifique:

- alertas no painel `Problems`;
- marcacoes no editor;
- sidebar `Privacy Scanner` com achados agrupados por risco.

## 4. Testar analise do projeto inteiro

1. Rode `Ctrl+Shift+P`.
2. Execute `Privacy Scanner: Analisar projeto inteiro`.
3. Verifique:

- achados de arquivos Python;
- achados de `banco_vulneravel.db`;
- resumo com score, total, arquivos Python e bancos SQLite.

## 5. Testar analise de banco SQLite

1. Rode `Ctrl+Shift+P`.
2. Execute `Privacy Scanner: Analisar banco SQLite`.
3. Selecione `banco_vulneravel.db`.
4. Verifique se aparecem vulnerabilidades como:

- `CAMPO_SEM_HASH`;
- `AUSENCIA_SOFT_DELETE`;
- `AUSENCIA_RETENCAO`;
- `AUSENCIA_CONSENTIMENTO`;
- `DADO_SENSIVEL_COMO_PK`.

## 6. Exportar relatorio

1. Rode `Privacy Scanner: Exportar relatorio HTML`.
2. Abra o arquivo `privacy-scan-YYYY-MM-DD.html`.
3. Verifique:

- score LGPD;
- total por risco;
- recomendacoes;
- achados de codigo e banco.

## Resultado esperado

- A extensao inicia sem erro de Flask.
- A sidebar carrega automaticamente.
- `exemplo_vulneravel.py` gera alertas.
- `banco_vulneravel.db` gera alertas de schema.
- `npm run compile` passa.
- `pytest` passa com 56 testes.


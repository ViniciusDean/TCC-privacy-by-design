# Roteiro de Demonstração - Privacy Scanner LGPD

Este roteiro serve para apresentar a ferramenta de forma simples e reproduzível.

## Objetivo da Demo

Mostrar que a ferramenta consegue:

- analisar código Python;
- analisar código Java com as sete categorias de código;
- analisar banco SQLite;
- exibir vulnerabilidades no VS Code;
- mostrar resumo por risco;
- exportar relatório HTML e PDF.

## 1. Preparar Ambiente

Na raiz do projeto:

```powershell
cd C:\Users\deanv\OneDrive\Documents\TCC
python -m pip install -r requirements.txt
python scripts/create_test_workspace.py
```

Compilar a extensão:

```powershell
cd vscode-extension
npm install
npm run compile
cd ..
```

Validar testes:

```powershell
python -m pytest
```

Resultado esperado:

```text
79 passed
```

## 2. Abrir a Extensão

1. Abra `C:\Users\deanv\OneDrive\Documents\TCC` no VS Code.
2. Pressione `F5`.
3. Aguarde abrir a janela `[Extension Development Host]`.
4. Na nova janela, abra a pasta:

```text
C:\Users\deanv\OneDrive\Documents\privacy-scanner-testes
```

## 3. Demonstrar Análise de Código Vulnerável

1. Abra `exemplo_vulneravel.py`.
2. Execute `Ctrl+Shift+P`.
3. Rode `Privacy Scanner: Analisar arquivo atual`.
4. Mostre:

- marcações no editor;
- painel `Problems`;
- sidebar `Privacy Scanner`;
- agrupamento por risco;
- score LGPD.

Falar durante a apresentação:

```text
A ferramenta faz análise estática. Ela não executa o código; ela percorre a estrutura do arquivo Python e procura padrões associados a riscos de privacidade.
```

## 4. Demonstrar Arquivo Correto

1. Abra `exemplo_correto.py`.
2. Rode `Privacy Scanner: Analisar arquivo atual`.
3. Mostre que o número de achados é menor ou inexistente.

Falar durante a apresentação:

```text
Este exemplo serve para verificar falsos positivos em boas práticas simples, como uso de hash forte, método de exclusão e ausência de dados pessoais em logs.
```

## 5. Demonstrar Análise do Projeto Inteiro

1. Execute `Ctrl+Shift+P`.
2. Rode `Privacy Scanner: Analisar projeto inteiro`.
3. Mostre:

- arquivos Python analisados;
- bancos SQLite encontrados;
- total de vulnerabilidades;
- contagem por risco.

Falar durante a apresentação:

```text
A análise de projeto agrega os resultados de código e banco em uma visão única para apoiar revisão técnica e documentação de conformidade.
```

## 6. Demonstrar Java

1. Abra `exemplo_vulneravel.java`.
2. Rode `Privacy Scanner: Analisar arquivo atual`.
3. Mostre os achados das sete categorias: hardcoded, criptografia fraca, log,
   transferência externa, coleta excessiva, ausência de exclusão e dado sem proteção.
4. Abra `exemplo_correto.java` para demonstrar o cenário sem alertas esperados.

Falar durante a apresentação:

```text
O suporte Java aplica sete regras por análise léxica conservadora. Ele reconhece
estruturas comuns sem compilar ou executar o projeto e não faz análise de fluxo
de dados entre métodos.
```

## 7. Demonstrar Banco SQLite

1. Execute `Privacy Scanner: Analisar banco SQLite`.
2. Selecione `banco_vulneravel.db` na pasta de teste.
3. Mostre vulnerabilidades de schema, como:

- `CAMPO_SEM_HASH`;
- `AUSENCIA_SOFT_DELETE`;
- `AUSENCIA_RETENCAO`;
- `AUSENCIA_CONSENTIMENTO`;
- `DADO_SENSIVEL_COMO_PK`.

Falar durante a apresentação:

```text
No banco, a ferramenta não analisa linhas de dados pessoais. Ela analisa o schema: nomes de tabelas, nomes de colunas, tipos e presença de campos de controle.
```

## 8. Demonstrar Code Actions

1. Clique em uma vulnerabilidade no editor.
2. Use a lâmpada/Quick Fix.
3. Mostre as opções:

- ver recomendação LGPD;
- copiar recomendação LGPD.

Falar durante a apresentação:

```text
A ideia não é corrigir automaticamente qualquer código, porque isso poderia alterar regra de negócio. A ferramenta mostra uma recomendação técnica para orientar o desenvolvedor.
```

Também demonstre `Ignorar este risco na interface`. Confirme que a ocorrência desaparece da sidebar e do painel `Problems`, mas continua no relatório exportado.

## 9. Exportar Relatório HTML

1. Execute `Privacy Scanner: Exportar relatorio`.
2. Escolha `HTML`.
3. Selecione nome e destino pela janela do Windows.
4. Abra o arquivo gerado.
5. Mostre:

- score;
- cards de resumo;
- filtros por risco;
- ordenação da tabela;
- recomendações.

Falar durante a apresentação:

```text
O HTML é o relatório interativo, útil para inspeção técnica durante a revisão do projeto.
```

## 10. Exportar Relatório PDF

1. Execute `Privacy Scanner: Exportar relatorio`.
2. Escolha `PDF`.
3. Selecione nome e destino pela janela do Windows.
4. Abra o PDF.

Falar durante a apresentação:

```text
O PDF é uma versão formal e estática do relatório, pensada para anexar em documentação, evidência de teste ou material de compliance.
```

## 11. Evidências para o TCC

Durante a demo, vale tirar prints de:

- extensão carregada no VS Code;
- `exemplo_vulneravel.py` com marcações;
- sidebar com score e riscos;
- painel `Problems`;
- relatório HTML;
- relatório PDF;
- terminal com `79 passed`.

## Resultado Esperado

- A extensão inicia sem erro.
- O servidor Flask sobe automaticamente ou reutiliza servidor já ativo.
- `exemplo_vulneravel.py` gera vulnerabilidades.
- `exemplo_correto.py` não gera os mesmos alertas.
- `banco_vulneravel.db` gera alertas de schema.
- HTML e PDF são exportados.
- `pytest` passa com 79 testes.

## Limitações a Declarar

- A ferramenta é um MVP acadêmico.
- A análise é baseada em regras estáticas.
- A ferramenta não substitui auditoria jurídica.
- A ferramenta não mede todos os requisitos da LGPD.
- O suporte Java é heurístico e não compila o projeto.
- O Java cobre sete categorias, mas não resolve tipos nem fluxo entre métodos.

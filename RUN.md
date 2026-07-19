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
privacy-scanner-lgpd@1.2.0 compile
tsc -p ./
```

## 2. Validar o Projeto

Rodar todos os testes Python:

```powershell
python -m pytest -q
```

Resultado esperado:

```text
181 passed
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

Na janela `[Extension Development Host]`, clique no ícone `Privacy Scanner` da
barra de atividades. A seção `Ações rápidas` oferece:

- `Analisar arquivo atual`, com o nome do editor ativo;
- `Analisar projeto inteiro`;
- `Selecionar e analisar banco SQLite`;
- `Exportar relatório`, com opções HTML, PDF e JSON;
- `Configurar perfil`, com o preset ativo;
- `Configuração e suporte`, grupo recolhido com o estado do backend e ações
  de limpeza, dependências, reinício, logs e configurações.

Arquivos Python e Java também possuem um botão de análise no título do editor
e uma ação no menu de contexto. No Explorer, clique com o botão direito em
`.py`/`.java` para analisar o arquivo ou em `.db`/`.sqlite`/`.sqlite3` para
analisar diretamente o banco selecionado. O item da barra de status abre o
painel.

A Paleta de Comandos (`Ctrl+Shift+P`) permanece disponível como alternativa.
O comando `Privacy Scanner: Analisar agora` continua analisando o workspace
quando houver uma pasta aberta e, caso contrário, o arquivo atual.

### Configurar o perfil sem editar JSON

1. Clique em `Configurar perfil` nas `Ações rápidas`.
2. Em workspace multirraiz, ative um arquivo da pasta desejada; se a raiz não
   puder ser identificada, escolha-a quando o assistente solicitar.
3. Em `Preset base`, escolha `Conservador` (confiança alta), `Equilibrado`
   (alta e média) ou `Completo` (todas as faixas).
4. Se necessário, use `Regras ativas` ou `Ajustar uma regra` para personalizar
   confiança mínima e severidade técnica.
5. Clique em `Salvar perfil` e confirme que o resumo da sidebar foi atualizado.

`Cancelar sem salvar` e `Esc` encerram o assistente sem escrever no arquivo. A
severidade escolhida afeta agrupamentos, totais e o indicador técnico, mas não
é uma conclusão jurídica sobre a LGPD.

Quando houver configuração inválida, a ação muda para `Corrigir perfil`.
Somente usuários que precisarem editar campos avançados devem abrir a Paleta e
usar `Privacy Scanner: Editar perfil JSON (avançado)`.

Arquivos Python e bancos SQLite também podem ser analisados automaticamente ao abrir, trocar de aba ou salvar, conforme a configuração `privacy-scanner.autoAnalyzeOnSave`.

Arquivos Java (`.java`) também podem ser abertos, salvos e analisados pelo mesmo fluxo.

Depois de `Analisar projeto inteiro`, o resumo mantém os contadores do workspace
mesmo quando um arquivo é aberto ou ativado automaticamente. A árvore
`ACHADOS` lista somente arquivos que produziram indícios; compare
`Arquivos analisados` com `Arquivos com achados` para distinguir arquivos
verificados sem ocorrências.

## 5. Teste Manual com Python

### Arquivo vulnerável

Abra `exemplo_vulneravel.py` e clique na ação `Analisar arquivo atual` da
seção `Ações rápidas`. Como alternativa clicável, use o botão no título do
editor ou o menu de contexto.

Resultado esperado:

- marcações no editor;
- alertas no painel `Problems`;
- achados técnicos agrupados por risco na sidebar;
- indicadores técnicos bruto e exibido pelo perfil apresentados separadamente.

### Arquivo correto

Abra `exemplo_correto.py` e clique em `Analisar arquivo atual`.

Resultado esperado:

- nenhum achado técnico relevante;
- indicador técnico disponível apenas após uma varredura com escopo válido;
- ausência de falsos positivos nas boas práticas demonstradas.

### Exemplos Java

Abra `exemplo_vulneravel.java` e clique no botão de análise no título do editor.

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

### Cenários vulneráveis adicionais

O diretório `examples/vulnerable/` contém cenários fictícios de cadastro de
clientes, folha de pagamento e prontuário Java. Eles podem ser abertos e
analisados individualmente para variar a demonstração sem alterar as regras do
scanner. Consulte `examples/vulnerable/README.md` para os comandos e categorias
esperadas.

## 6. Teste Manual com Banco SQLite

Na extensão:

1. Clique em `Selecionar e analisar banco SQLite` nas `Ações rápidas`.
2. Selecione um arquivo `.db`, `.sqlite` ou `.sqlite3`.
3. Verifique os achados na sidebar.

Se o banco já estiver visível no Explorer, clique nele com o botão direito e
escolha `Analisar banco SQLite`; nesse fluxo o seletor não é aberto.

Categorias esperadas em banco vulnerável:

- `CAMPO_SEM_HASH`;
- `AUSENCIA_SOFT_DELETE`;
- `AUSENCIA_RETENCAO`;
- `AUSENCIA_CONSENTIMENTO`;
- `DADO_SENSIVEL_COMO_PK`;
- `DADO_SENSIVEL_COMO_INDICE_UNICO`;
- `MISTURA_DADOS`.

Observação: achados de banco geralmente aparecem com linha `0`, pois vêm do schema e não de uma linha específica de código.

## 7. Exportar Relatórios

### Ignorar uma ocorrência na interface

Na sidebar, clique com o botão direito em um achado e escolha `Ignorar risco na interface`. Também é possível usar a lâmpada/Quick Fix no editor.

O achado deixa de aparecer na sidebar e no painel `Problems`, mas continua nos
relatórios. O indicador técnico bruto não é alterado. Para desfazer, expanda
`Configuração e suporte` e clique em `Restaurar achados ocultados`.

Na extensão:

1. Clique em `Exportar relatório` nas `Ações rápidas`.
2. Escolha `HTML`, `PDF` ou `JSON`.
3. O VS Code abrirá a janela do Windows para escolher nome e destino.
4. Após salvar, clique em `Abrir` se quiser visualizar.

### HTML

O HTML é o relatório interativo. Ele contém:

- indicador técnico;
- contagem por risco;
- escopo analisado;
- tabela de achados técnicos;
- recomendações;
- filtro por risco;
- ordenação por coluna.

### PDF

O PDF é o relatório formal e estático. Ele contém:

- cabeçalho do Privacy Scanner;
- indicador técnico;
- resumo por risco;
- achados técnicos agrupados;
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

Expanda `Configuração e suporte`. Se o backend aparecer como
`indisponível`, tente `Configurar dependências` e depois `Reiniciar backend`.
Use `Abrir logs` para consultar o diagnóstico sem sair do painel.

Se o Python não for encontrado, use `Abrir configurações` na mensagem de erro
e ajuste `privacy-scanner.pythonPath`. A instalação manual continua possível:

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

Clique em `Analisar projeto inteiro` nas `Ações rápidas` ou abra um arquivo
Python/Java e clique em `Analisar arquivo atual`.

### Perfil inválido

Clique em `Abrir perfil` na mensagem de erro ou em `Corrigir perfil` nas
`Ações rápidas`. Refaça a configuração no assistente antes de repetir a
análise. A edição direta do JSON é uma alternativa avançada na Paleta.

## 11. Limitações Conhecidas

- A análise é estática e baseada em regras.
- A ferramenta não executa o código analisado.
- A ferramenta não substitui auditoria jurídica ou revisão de segurança completa.
- O suporte Java usa análise léxica e não compila o projeto.
- O Java cobre sete categorias, mas não acompanha fluxo de dados entre métodos.
- Algumas regras são heurísticas e podem exigir revisão manual.

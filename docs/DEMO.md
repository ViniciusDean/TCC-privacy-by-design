# Roteiro de Demonstração - Privacy Scanner LGPD

Este roteiro serve para apresentar a ferramenta de forma simples e reproduzível.

## Demonstração curta para a banca (1.2.2)

Gerar novamente o exemplo e seus relatórios, sem modificar o benchmark:

```powershell
.\.venv\Scripts\python.exe scripts\demo_banca.py
```

O script copia a fixture `py_hardcoded_log.py` para um workspace exclusivo em
`output/demo-banca/workspace`, analisa a versão inicial, grava uma correção
mínima e repete a análise. Ele usa os endpoints reais via cliente de teste
Flask e verifica a igualdade entre o resumo de análise e os relatórios.

| Etapa | Código do exemplo | Resultado esperado |
|---|---|---|
| Antes | Identificador pessoal fictício fixo e enviado a `print` | 2 achados altos; indicador 80 |
| Depois | Apenas mensagem técnica estática, sem o identificador | 0 achados; indicador 100 |

Os arquivos `antes.py` e `depois.py` ficam fora do workspace analisado. O
workspace termina com a versão corrigida. Para demonstrar no VS Code:

1. Abra somente `output/demo-banca/workspace` e copie o conteúdo de `antes.py`
   para `app.py`; salve e analise o projeto.
2. Mostre o alvo, o horário e os dois achados do resumo. Explique por que o
   identificador e seu registro em log são desnecessários neste exemplo mínimo.
3. Troque pelo conteúdo de `depois.py`, sem salvar. Mostre o aviso de resumo
   desatualizado. A análise automática aguarda o salvamento.
4. Solicite a análise do projeto e escolha salvar e continuar. Confirme que
   os diagnósticos desaparecem e o resumo corresponde à nova análise.
5. Exporte o relatório e mostre seu escopo e a ausência de achados. Se mudar
   o arquivo novamente antes de exportar, a ferramenta oferece salvar ou cancelar.

Relatórios verificados: [antes](../output/demo-banca/antes.html) e
[depois](../output/demo-banca/depois.html), também disponíveis em JSON e PDF.
O arquivo [verificacao.json](../output/demo-banca/verificacao.json) registra
versão, perfil, hashes do código e resumos. As capturas reais do navegador
estão em `output/playwright/relatorio-banca-antes.png` e
`output/playwright/relatorio-banca-depois.png`.

O indicador 100 significa ausência de achados neste escopo e perfil. A
demonstração sintética não comprova conformidade jurídica nem eficácia geral.
Ela não altera resultados históricos nem substitui a revisão independente.

As recomendações de eliminação consideram as hipóteses dos arts. 18, IV e VI,
e 16 da [LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm).
Uma coluna de exclusão lógica ou um método isolado não comprova o atendimento
dos pedidos dos titulares.

## Objetivo da Demo

Mostrar que a ferramenta consegue:

- analisar código Python;
- analisar código Java com as sete categorias de código;
- analisar banco SQLite;
- exibir achados tecnicos no VS Code;
- mostrar resumo por risco;
- exportar relatórios HTML, PDF e JSON.

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
suíte concluída sem falhas
```

## 2. Abrir a Extensão

1. Abra `C:\Users\deanv\OneDrive\Documents\TCC` no VS Code.
2. Pressione `F5`.
3. Aguarde abrir a janela `[Extension Development Host]`.
4. Na nova janela, abra a pasta:

```text
C:\Users\deanv\OneDrive\Documents\privacy-scanner-testes
```

5. Clique no ícone `Privacy Scanner` da barra de atividades.
6. Confirme que `Ações rápidas` aparece acima de `Achados` e `Resumo` e que
   `Configuração e suporte` informa o estado do backend.

## 3. Demonstrar Análise de Código Vulnerável

1. Abra `exemplo_vulneravel.py`.
2. Em `Ações rápidas`, clique em `Analisar arquivo atual` e confirme que o
   nome de `exemplo_vulneravel.py` aparece na ação.
3. Mostre:

- marcações no editor;
- painel `Problems`;
- sidebar `Privacy Scanner`;
- agrupamento por risco;
- indicador técnico de risco.

Falar durante a apresentação:

```text
A ferramenta faz análise estática. Ela não executa o código; ela percorre a estrutura do arquivo Python e procura padrões associados a riscos de privacidade.
```

## 4. Demonstrar Arquivo Correto

1. Abra `exemplo_correto.py`.
2. Clique no botão de análise no título do editor.
3. Mostre que o número de achados é menor ou inexistente.

Falar durante a apresentação:

```text
Este exemplo serve para verificar falsos positivos em boas práticas simples, como uso de hash forte, método de exclusão e ausência de dados pessoais em logs.
```

## 5. Demonstrar Análise do Projeto Inteiro

1. Clique em `Analisar projeto inteiro` nas `Ações rápidas`.
2. Mostre:

- arquivos Python analisados;
- bancos SQLite encontrados;
- total de achados técnicos;
- contagem por risco.

Clique em `Configurar perfil`, abra `Preset base`, escolha `Equilibrado` e use
`Salvar perfil`. Mostre que o preset ativo é atualizado no painel sem editar
JSON. Explique que `Regras ativas` e `Ajustar uma regra` permitem personalizar o
perfil, mas que severidade técnica não é conclusão jurídica. Para a sequência
reproduzível da demo, restaure o preset original e salve. A edição JSON
avançada fica apenas na Paleta e não faz parte do fluxo principal.

Falar durante a apresentação:

```text
A análise de projeto agrega os resultados de código e banco em uma visão única para apoiar revisão técnica de privacidade. Ela não substitui uma análise jurídica de conformidade.
```

## 6. Demonstrar Java

1. Abra `exemplo_vulneravel.java`.
2. Clique com o botão direito no editor e escolha
   `Privacy Scanner: Analisar arquivo`.
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

1. No Explorer, clique com o botão direito em `banco_vulneravel.db`.
2. Escolha `Privacy Scanner: Analisar banco SQLite`; o arquivo selecionado é
   analisado sem abrir outro seletor.
3. Mostre achados técnicos de schema, como:

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

1. Clique em um achado técnico no editor.
2. Use a lâmpada/Quick Fix.
3. Mostre as opções:

- ver recomendação LGPD;
- copiar recomendação LGPD.

Falar durante a apresentação:

```text
A ideia não é corrigir automaticamente qualquer código, porque isso poderia alterar regra de negócio. A ferramenta mostra uma recomendação técnica para orientar o desenvolvedor.
```

Também demonstre `Ignorar este risco na interface`. Confirme que a ocorrência desaparece da sidebar e do painel `Problems`, mas continua no relatório exportado e não altera o indicador técnico bruto.

## 9. Exportar Relatório HTML

1. Clique em `Exportar relatório` nas `Ações rápidas`.
2. Escolha `HTML`.
3. Selecione nome e destino pela janela do Windows.
4. Abra o arquivo gerado.
5. Mostre:

- indicador técnico;
- cards de resumo;
- filtros por risco;
- ordenação da tabela;
- recomendações.

Falar durante a apresentação:

```text
O HTML é o relatório interativo, útil para inspeção técnica durante a revisão do projeto.
```

## 10. Exportar Relatório PDF

1. Clique em `Exportar relatório` nas `Ações rápidas`.
2. Escolha `PDF`.
3. Selecione nome e destino pela janela do Windows.
4. Abra o PDF.

Falar durante a apresentação:

```text
O PDF é uma versão formal e estática do relatório, pensada para anexar como evidência técnica de teste ou material de apoio à revisão de privacidade.
```

## 11. Exportar Relatório JSON

1. Clique em `Exportar relatório` nas `Ações rápidas`.
2. Escolha `JSON` e salve o arquivo.
3. Mostre os metadados, o resumo e a lista estruturada de achados técnicos.

## 12. Evidências para o TCC

Durante a demo, vale tirar prints de:

- extensão carregada no VS Code;
- `exemplo_vulneravel.py` com marcações;
- sidebar com indicador técnico e riscos;
- painel `Problems`;
- relatório HTML;
- relatório PDF;
- relatório JSON;
- terminal com a suíte concluída sem falhas.

## Resultado Esperado

- A extensão inicia sem erro.
- O servidor Flask sobe automaticamente ou reutiliza servidor já ativo.
- `exemplo_vulneravel.py` gera achados tecnicos.
- `exemplo_correto.py` não gera os mesmos alertas.
- `banco_vulneravel.db` gera alertas de schema.
- HTML, PDF e JSON são exportados.
- `pytest` passa com 164 testes.

## Limitações a Declarar

- A ferramenta é um MVP acadêmico.
- A análise é baseada em regras estáticas.
- A ferramenta não substitui auditoria jurídica.
- A ferramenta não mede todos os requisitos da LGPD.
- O suporte Java é heurístico e não compila o projeto.
- O Java cobre sete categorias, mas não resolve tipos nem fluxo entre métodos.

Se algum componente clicável não estiver disponível durante a demonstração,
a Paleta de Comandos (`Ctrl+Shift+P`) permanece como alternativa com os mesmos
IDs de comando. Ela não é o fluxo principal deste roteiro.

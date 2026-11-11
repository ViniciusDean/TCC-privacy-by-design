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
4. Solicite a análise do projeto e escolha `Salvar e analisar`. Confirme que
   os diagnósticos desaparecem e o resumo corresponde à nova análise.
5. Exporte o relatório e mostre seu escopo e a ausência de achados. Se mudar
   o arquivo novamente antes de exportar, a ferramenta oferece `Salvar e exportar`.

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

A fala e a ordem da demonstração ao vivo da banca (slide 12) estão em
`output/presentation/ROTEIRO_BANCA.md`. Este guia detalha cada funcionalidade
para ensaio e conferência.

Mostrar que a ferramenta consegue:

- analisar código Python e Java com as sete categorias de código;
- analisar o schema de bancos SQLite com as sete categorias de banco;
- exibir achados técnicos no editor, no painel `Problems`, na sidebar e na barra de status;
- analisar automaticamente ao abrir, ativar ou salvar arquivos;
- ajustar o perfil de análise sem editar JSON;
- ocultar e restaurar achados apenas na interface;
- respeitar o `.privacyignore` na análise de projeto;
- exportar relatórios HTML, PDF e JSON.

## Mapa de cobertura

Use esta tabela para conferir que nenhuma funcionalidade ficou sem demonstração.

| Funcionalidade | Onde aparece no roteiro |
|---|---|
| Ações rápidas, Achados, Resumo, Configuração e suporte | Seções 2 e 14 |
| Barra de status (abre o painel) | Seção 2 |
| Analisar arquivo atual (Ações rápidas, título do editor, menu de contexto, Explorer) | Seções 3, 4 e 6 |
| Análise automática ao abrir, ativar ou salvar | Seção 3 |
| Clique no achado leva à linha no editor | Seção 3 |
| Caso intermediário (`exemplo_parcial.py`) | Seção 4 |
| Analisar projeto inteiro, arquivos ignorados e `.privacyignore` | Seção 5 |
| Perfil: presets, regras ativas, ajuste de regra, limpar e restaurar, selecionar e validar | Seção 5 |
| Java com sete categorias | Seção 6 |
| Novos exemplos (`novos_exemplos_vulneraveis/`) | Seção 6 |
| SQLite com sete categorias (dois bancos) | Seção 7 |
| Quick Fix: ver, copiar recomendação e ocultar achado | Seção 8 |
| Analisar agora, Limpar resultados, Restaurar achados ocultados | Seção 8 |
| Resumo desatualizado e salvar antes de analisar | Demonstração curta (1.2.2) |
| Exportação HTML, PDF e JSON | Seções 9 a 11 |
| Configurar dependências, reiniciar backend, abrir logs e configurações | Seção 14 |
| Configurações da extensão | Seção 14 |

## 1. Preparar Ambiente

Na raiz do projeto:

```powershell
python -m pip install -r requirements.txt
python scripts/create_test_workspace.py
```

O script recria `C:\Users\deanv\OneDrive\Documents\privacy-scanner-testes`
com os exemplos `exemplo_*`, o `banco_vulneravel.db` e a pasta
`novos_exemplos_vulneraveis/` (cópia de `examples/vulnerable`). Ele sobrescreve
alterações feitas antes nessa pasta.

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
208 testes aprovados, sem falhas
```

Para a banca, prefira instalar o pacote publicado
`output/release/privacy-scanner-lgpd-1.2.2.vsix` (SHA-256
`825fac393979a36501faf25d81677e66f4c7623a256992ae6f3908231c1d11e3`) em um perfil
limpo do VS Code em vez de usar o `F5`.

## 2. Abrir a Extensão

1. Abra a pasta do repositório no VS Code.
2. Pressione `F5`, ou use o VSIX instalado.
3. Aguarde abrir a janela `[Extension Development Host]`.
4. Na nova janela, abra a pasta:

```text
C:\Users\deanv\OneDrive\Documents\privacy-scanner-testes
```

5. Mostre o item `Privacy Scanner` na barra de status, no canto inferior
   direito. Ele indica o estado (iniciando, analisando, pronto) e abre o painel
   ao ser clicado.
6. Clique no ícone `Privacy Scanner` da barra de atividades.
7. Confirme que `Ações rápidas` aparece acima de `Achados` e `Resumo` e que
   `Configuração e suporte` informa o estado do backend.

## 3. Demonstrar Análise de Código Vulnerável

1. Abra `exemplo_vulneravel.py`. Com a análise automática ligada, os achados
   aparecem ao abrir o arquivo, sem clicar em nada.
2. Em `Ações rápidas`, clique em `Analisar arquivo atual` e confirme que o
   nome de `exemplo_vulneravel.py` aparece na ação.
3. Mostre os 7 achados de 6 categorias:
   - `DADO_HARDCODED` (2);
   - `CRIPTOGRAFIA_FRACA`;
   - `DADO_EM_LOG`;
   - `TRANSFERENCIA_SEM_BASE_LEGAL`;
   - `COLETA_EXCESSIVA`;
   - `AUSENCIA_EXCLUSAO`.
4. Mostre:
   - marcações no editor;
   - painel `Problems`;
   - sidebar `Privacy Scanner`;
   - agrupamento por risco;
   - indicador técnico de risco.
5. Clique em um achado na sidebar e mostre que o editor vai direto para a linha.
6. Edite e salve o arquivo para mostrar que a análise roda de novo sozinha.

Falar durante a apresentação:

```text
A ferramenta faz análise estática. Ela não executa o código; ela percorre a estrutura do arquivo Python e procura padrões associados a riscos de privacidade.
```

## 4. Demonstrar Arquivo Correto e Caso Intermediário

1. Abra `exemplo_correto.py`.
2. Clique no botão de análise no título do editor.
3. Mostre que não há achados.
4. Abra `exemplo_parcial.py` e analise. Mostre os 5 achados: `DADO_EM_LOG` (3),
   `DADO_HARDCODED` e `COLETA_EXCESSIVA`. Explique que o arquivo aplica
   algumas boas práticas, mas ainda tem pontos para revisão.

Falar durante a apresentação:

```text
O exemplo correto serve para verificar falsos positivos em boas práticas simples, como uso de hash forte, método de exclusão e ausência de dados pessoais em logs. O parcial mostra que a ferramenta não é tudo ou nada.
```

## 5. Demonstrar Análise do Projeto Inteiro e Perfil

1. Clique em `Analisar projeto inteiro` nas `Ações rápidas`.
2. Mostre no `Resumo`:
   - arquivos Python e Java analisados;
   - bancos SQLite encontrados;
   - arquivos ignorados;
   - total de achados técnicos;
   - contagem por risco.
3. Explique o `.privacyignore`: padrões no estilo `.gitignore` na raiz do
   projeto que tiram arquivos ou pastas da análise do projeto. No repositório
   do scanner, ele exclui os exemplos vulneráveis, os testes e os corpora de
   avaliação. Esses arquivos ainda podem ser analisados um a um.

Perfil de análise:

1. Clique em `Configurar perfil` e abra `Preset base`. Mostre os três presets:
   `Conservador`, `Equilibrado` e `Completo`, cada um com sua confiança mínima.
2. Escolha `Equilibrado`.
3. Abra `Regras ativas` e mostre as 14 regras agrupadas em Código e SQLite.
4. Em `Ajustar uma regra`, escolha uma regra e mostre `Confiança mínima`
   (ALTA, MÉDIA, BAIXA) e `Severidade técnica` (ALTO, MÉDIO, BAIXO).
5. Mostre `Limpar personalizações` e `Restaurar padrão conservador`.
6. Use `Salvar perfil`. Aceite reanalisar o workspace e mostre que o preset
   ativo é atualizado no painel sem editar JSON.
7. Pela Paleta de Comandos, mostre `Privacy Scanner: Selecionar perfil`
   (troca rápida de preset) e `Privacy Scanner: Validar perfil` (confere o
   `.privacy-scanner.json`).
8. Para a sequência reproduzível da demo, restaure o preset conservador e salve.

Explique que severidade técnica não é conclusão jurídica. A edição JSON
avançada (`Editar perfil JSON`) fica apenas na Paleta e não faz parte do fluxo
principal.

Falar durante a apresentação:

```text
A análise de projeto agrega os resultados de código e banco em uma visão única para apoiar revisão técnica de privacidade. Ela não substitui uma análise jurídica de conformidade.
```

## 6. Demonstrar Java e os Novos Exemplos

1. Abra `exemplo_vulneravel.java`.
2. Clique com o botão direito no editor e escolha
   `Privacy Scanner: Analisar arquivo`.
3. Mostre os 9 achados das sete categorias: hardcoded, criptografia fraca, log,
   transferência externa, coleta excessiva, ausência de exclusão e dado sem proteção.
4. Abra `exemplo_correto.java` para demonstrar o cenário sem alertas esperados.
5. Na pasta `novos_exemplos_vulneraveis/`, clique com o botão direito em
   `ProntuarioVulneravel.java` no Explorer e escolha
   `Privacy Scanner: Analisar arquivo`. Ele gera 9 achados das sete categorias,
   em um cenário de prontuário de pacientes.
6. Analise `cadastro_clientes_vulneravel.py` e `folha_pagamento_vulneravel.py`.
   Cada um gera 7 achados de 6 categorias, em cenários de cadastro de clientes
   e folha de pagamento.

Falar durante a apresentação:

```text
O suporte Java aplica sete regras por análise léxica conservadora. Ele reconhece
estruturas comuns sem compilar ou executar o projeto e não faz análise de fluxo
de dados entre métodos.
```

## 7. Demonstrar Banco SQLite

Nenhum banco sozinho gera as sete categorias de SQLite. Use os dois para
cobrir todas.

1. No Explorer, clique com o botão direito em `banco_vulneravel.db`.
2. Escolha `Privacy Scanner: Analisar banco SQLite`; o arquivo selecionado é
   analisado sem abrir outro seletor.
3. Mostre os 14 achados de schema:
   - `CAMPO_SEM_HASH` (7);
   - `AUSENCIA_SOFT_DELETE` (2);
   - `AUSENCIA_RETENCAO` (2);
   - `AUSENCIA_CONSENTIMENTO`;
   - `DADO_SENSIVEL_COMO_PK`;
   - `MISTURA_DADOS`.
4. Em `novos_exemplos_vulneraveis/`, analise `clientes_demo.db` (o banco da
   Seção 5.3 do TCC). Mostre os 12 achados, com destaque para:
   - `DADO_SENSIVEL_COMO_PK` (CPF como chave primária);
   - `DADO_SENSIVEL_COMO_INDICE_UNICO` (e-mail em índice único).
5. Comente que `clientes_demo.db` mistura dados pessoais e do pedido, mas
   `MISTURA_DADOS` não dispara: a regra exige três colunas operacionais pelo
   nome e só `status_pedido` atende. É o mesmo exemplo de dependência de
   nomenclatura discutido no TCC.
6. Para escolher um banco por diálogo, use `Selecionar e analisar banco SQLite`
   nas `Ações rápidas`.

Os números acima são da análise sem filtro de perfil. No preset conservador,
achados de baixa confiança podem não aparecer.

Falar durante a apresentação:

```text
No banco, a ferramenta não analisa linhas de dados pessoais. Ela analisa o schema: nomes de tabelas, nomes de colunas, tipos, chaves, índices e presença de campos de controle.
```

## 8. Demonstrar Code Actions e Controle da Lista

1. Clique em um achado técnico no editor.
2. Use a lâmpada/Quick Fix.
3. Mostre as opções:
   - `Ver recomendacao LGPD`;
   - `Copiar recomendacao LGPD`;
   - `Ocultar achado na interface`.

Falar durante a apresentação:

```text
A ideia não é corrigir automaticamente qualquer código, porque isso poderia alterar regra de negócio. A ferramenta mostra uma recomendação técnica para orientar o desenvolvedor.
```

4. Use `Ocultar achado na interface`, também disponível pelo ícone ao lado do
   achado na sidebar. Confirme que a ocorrência desaparece da sidebar e do
   painel `Problems`, mas continua no relatório exportado e não altera o
   indicador técnico bruto.
5. No topo da lista `Achados`, clique em `Restaurar achados ocultados` e mostre
   que a ocorrência volta. A mesma ação aparece em `Configuração e suporte`
   com a contagem de achados ocultados.
6. Ainda no topo da lista, mostre `Limpar resultados` (zera a lista e o resumo)
   e `Analisar agora` (analisa o projeto aberto de novo).

## 9. Exportar Relatório HTML

1. Clique em `Exportar relatório` nas `Ações rápidas`.
2. Escolha `HTML`.
3. Selecione nome e destino pela janela do Windows.
4. Abra o arquivo gerado.
5. Mostre:
   - aviso “Limite da análise” no topo;
   - perfil usado na análise;
   - indicador técnico;
   - cards de resumo;
   - filtros por risco;
   - ordenação da tabela;
   - recomendações e artigo da LGPD relacionado.

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

A exportação sempre faz uma nova análise do projeto. Se houver arquivos
Python ou Java não salvos, a ferramenta oferece salvar ou cancelar.

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

## 13. Resultado Esperado

- A extensão inicia sem erro.
- O servidor Flask sobe automaticamente ou reutiliza servidor já ativo.
- `exemplo_vulneravel.py` gera 7 achados técnicos.
- `exemplo_correto.py` e `exemplo_correto.java` não geram achados.
- `banco_vulneravel.db` e `clientes_demo.db` juntos cobrem as sete categorias de SQLite.
- HTML, PDF e JSON são exportados.
- `pytest` passa com 208 testes.

## 14. Configuração e Suporte

Abra o grupo `Configuração e suporte` nas `Ações rápidas`:

1. Mostre o estado do backend na descrição do grupo (`Backend: pronto`).
2. `Limpar resultados` e `Restaurar achados ocultados` (já vistos na Seção 8).
3. `Configurar dependências`: cria o ambiente Python isolado e instala as
   dependências do backend.
4. `Reiniciar backend`: para e inicia de novo o servidor local.
5. `Abrir logs`: mostra o canal de saída do Privacy Scanner.
6. `Abrir configurações`: abre só as configurações desta extensão.

Nas configurações (`privacy-scanner.*`), mostre rapidamente:

- `autoAnalyzeOnSave` e `autoAnalyzeDelayMs`: análise automática;
- `showDiagnostics`: liga ou desliga os achados no painel `Problems`;
- `enableSidebar`: liga ou desliga a sidebar;
- `serverPort`, `pythonPath` e `analysisTimeoutMs`: backend.

## Limitações a Declarar

- A ferramenta é um MVP acadêmico.
- A análise é baseada em regras estáticas.
- A ferramenta não substitui auditoria jurídica.
- A ferramenta não mede todos os requisitos da LGPD.
- O suporte Java é heurístico e não compila o projeto.
- O Java cobre sete categorias, mas não resolve tipos nem fluxo entre métodos.
- As regras de SQLite dependem dos nomes das colunas, como mostra o `clientes_demo.db`.

Se algum componente clicável não estiver disponível durante a demonstração,
a Paleta de Comandos (`Ctrl+Shift+P`) permanece como alternativa com os mesmos
IDs de comando. Ela não é o fluxo principal deste roteiro.

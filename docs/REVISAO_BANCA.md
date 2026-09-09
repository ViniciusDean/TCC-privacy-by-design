# Revisão para a banca — progresso por partes

Atualizado em 9 de setembro de 2026.

Prioridade definida: apresentação à banca, usando as evidências existentes.
Preservar arquitetura, linguagens, categorias, heurísticas e corpus. Concluir
uma parte por rodada, com testes, para permitir controle do consumo do plano.

## Parte 1 — Base do app, exportação e perfis: concluída

- Branch de trabalho: `codex/tcc-banca-refinamentos`.
- Incorporado o commit existente `2b0a1a1` (1.2.1), mantendo a revisão do texto
  e o README de instalação. Reaproveitados o suporte à exportação de SQLite
  interno/externo e os ajustes de inicialização e empacotamento.
- Corrigido o resumo da resposta de `/api/export`: o envelope recebe achados
  brutos para preservar contagens, ocultações e severidades originais.
- Validados os tipos de preset, confiança mínima e severidade. Entradas
  inválidas retornam HTTP 400 JSON com `PERFIL_INVALIDO`; severidade nula
  continua significando ausência de personalização.
- Acrescentadas regressões para filtros, severidade personalizada, tipos
  inválidos e contrato de erro HTTP. Os casos de exportação falharam antes
  da correção e passaram depois dela.

Validação executada nesta parte:

- Suíte Python completa: **208 testes aprovados**.
- `npm.cmd test`: versão, compilação TypeScript, lint e suítes aprovados.
- `git diff --check`: sem erros de whitespace.

O código tem a base 1.2.1 com ajustes locais. O VSIX histórico da release
permanece histórico; um pacote com as novas correções será gerado e validado
na parte 2. Esta parte não incluiu teste visual da interface, Extension Host,
instalação de novo pacote ou publicação remota.

## Parte 2 — Interface e demonstração: pendente

- Mostrar alvo e horário do resumo e marcar quando ficar desatualizado após
  alterações nos diagnósticos de um arquivo.
- Antes de analisar o projeto/exportar, oferecer salvar arquivos suportados
  modificados ou cancelar; a análise automática deve aguardar o salvamento.
- Refinar recomendações de eliminação conforme art. 18, IV e VI, e art. 16;
  não apresentar método de exclusão ou coluna `deleted_at` como suficiente.
- Conferir o fluxo analisar → corrigir → salvar → reanalisar → exportar,
  usando fixtures existentes, e obter captura real para o texto.
- Executar testes pertinentes, Extension Host, empacotamento e instalação
  isolada do novo VSIX. Não sobrescrever o artefato da release histórica.

## Parte 3 — Texto e PDF: pendente

- Trabalhar em `latex_tcc/main.tex`, mantendo a comparação do SDLC existente.
- Explicar TP/FP/FN, precisão/recall/F1, as 120 decisões caso–categoria e a
  diferença entre a contagem do benchmark e dos achados externos.
- Delimitar controle de acesso, finalidade e usabilidade ao alcance avaliado.
- Explicar fórmula, exemplo e limites dos indicadores bruto e exibido.
- Inserir o exemplo e a captura obtidos na parte 2; registrar versão/commit
  da demonstração sem substituir as métricas históricas por números atuais.
- Corrigir a numeração das páginas textuais e revisar a quebra da conclusão.
- Recompilar e conferir visualmente todas as páginas, tabelas e sumário.
- Manter revisão independente pendente como limitação; não ampliar corpus
  nem preencher os sete itens como se existisse um segundo revisor.
- Tratar nomes/instituições da banca, data e ficha catalográfica como dados
  pendentes para a versão definitiva, sem inventar informações.

As alterações prévias dos PDFs locais pertencem ao usuário e foram preservadas.

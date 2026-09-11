# Revisão para a banca — progresso por partes

Atualizado em 10 de setembro de 2026.

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

Esta etapa consolidou a base 1.2.1 com ajustes locais, sem substituir o VSIX
histórico. Os testes no Extension Host e o pacote atualizado foram concluídos
na parte 2.

## Parte 2 — Interface e demonstração: concluída

- Resumo com alvo, horário e aviso de desatualização. Alterações durante a
  requisição permanecem sinalizadas; abrir novamente um arquivo sem mudança
  nos achados não invalida o resumo do projeto.
- Salvamento limitado aos arquivos Python/Java modificados nas raízes
  selecionadas, com cancelamento e interrupção quando o salvamento falha.
- Análise automática respeita a preferência desde a ativação, aguarda o
  salvamento e descarta respostas de versões anteriores do documento.
- A fila automática anterior é descartada somente no escopo já coberto pela
  nova varredura; novos salvamentos durante a requisição são preservados.
- Exportação escolhe o projeto antes do destino e informa que faz nova análise.
- Recomendações de eliminação revisadas conforme art. 18, IV e VI, e art. 16;
  método isolado ou coluna de exclusão lógica não são apresentados como suficientes.
- Versão local sincronizada em **1.2.2**, distinguindo o pacote atualizado
  da release histórica 1.2.1. Não houve publicação remota.

Validação:

- Suíte Python: **208 testes aprovados** na preparação desta parte.
- TypeScript, lint e suítes aprovados; novas regressões para multirraiz,
  arquivos modificados, respostas antigas, fila e salvamento/cancelamento.
- Extension Host **VS Code 1.134.0**: análise real, conflito de porta,
  edição sem salvar, salvamento e reanálise passaram. Diagnósticos antigos
  desapareceram somente após salvar a correção. Os diálogos de confirmação
  são cobertos pelo helper testado; não foi realizada sessão manual desses diálogos.
- VSIX gerado e instalado em ambiente isolado, com versão e exports verificados.
- Demonstração via API real: **2 achados antes, 0 depois**, com resumos iguais
  na análise e nas exportações HTML/JSON/PDF. Filtro e ordenação HTML conferidos
  no navegador; capturas e páginas dos PDFs inspecionadas visualmente.

Artefatos:

- `output/release/banca/privacy-scanner-lgpd-1.2.2.vsix` e `SHA256SUMS.txt`.
- `output/demo-banca/`: código sintético, relatórios antes/depois e recibo com hashes.
- `output/playwright/relatorio-banca-antes.png` e `relatorio-banca-depois.png`.
- `scripts/demo_banca.py` reproduz a demonstração; `docs/DEMO.md` traz o roteiro.

A instalação do teste usa perfil isolado; a extensão no perfil pessoal do
VS Code não foi substituída automaticamente.

## Parte 3 — Texto e PDF: em validação

Fonte revisado em 10/09/2026: definições e unidades de avaliação, fórmula e
limites do indicador, versão 1.2.2 separada das métricas históricas,
demonstração com captura real, limites de cobertura/usabilidade e conclusão
mais concisa. O estilo textual agora restaura explicitamente os números.
Cadastro, execução congelada e registro de FN foram conferidos separadamente.
Falta compilar e inspecionar visualmente a prova antes da entrega.

Checklist da etapa:

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

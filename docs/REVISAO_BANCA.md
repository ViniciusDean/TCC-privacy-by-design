# Revisão para a banca — progresso por partes

Atualizado em 11 de setembro de 2026.

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

## Parte 3 — Texto e PDF: concluída

- Revisado o fonte canônico `latex_tcc/main.tex`, preservando a comparação
  de modelos e práticas do SDLC.
- Acrescentados quadro de TP/FP/FN/TN, fórmulas de precisão/recall/F1 e
  especificidade e distinção entre decisão caso–categoria e achado externo.
  Explicitadas as 120 decisões: 6×7 + 6×7 + 6×6.
- Conferidos cadastro, execução histórica `20260710T024446Z-d034f8fc` e
  registro separado de FN; corrigida a descrição de onde ficam as evidências.
- Explicados fórmula, exemplo, severidade-base, perfil, escopo vazio,
  saturação e limites de comparação dos indicadores.
- Delimitados controle de acesso, finalidade e ausência de estudo de usabilidade.
- Atualizados resumo, abstract, resultados e conclusão para distinguir
  as verificações de 1.2.2 dos resultados históricos de 1.0.4 e 1.2.0.
- Incluídos código antes/depois e recortes legíveis da captura real do HTML,
  com versão 1.2.2, commit `8e76a09` e caminhos para reprodução.
- Restaurada explicitamente a numeração de todas as páginas textuais;
  conclusão reduzida a uma página. Acrescentada a lista de figuras.

Validação da parte:

- Sete testes de proteção do fonte aprovados; `git diff --check` sem erros.
- XeLaTeX executado em três passagens, sem referências indefinidas nem
  caixas excedendo a largura disponível.
- **51 páginas** renderizadas e inspecionadas; quadro de métricas e figura
  também conferidos em resolução maior.
- **61 entradas** do sumário e das listas conferidas contra os destinos do PDF.
- Numeração impressa contínua de **11 a 50**, pré-textuais sem número visível,
  conclusão na página impressa **46**, referências a partir da **47**.
- A recompilação após ajustar o recorte alterou somente a imagem da página
  física 37; as outras 50 páginas renderizadas permaneceram idênticas.

Entrega:

- `output/pdf/TCC_Privacy_by_Design_2026_REVISAO_BANCA_PROVA.pdf`.
- `output/pdf/TCC_Privacy_by_Design_2026_REVISAO_BANCA_VERIFICACAO.json`,
  com hashes do fonte/PDF e resultados da conferência.
- Ponto de retomada do texto salvo antes da compilação no commit `185c1bc`.

As três partes previstas estão concluídas no escopo autorizado. A versão
definitiva depende dos nomes/instituições dos convidados da banca, data
de aprovação e ficha catalográfica oficial. A revisão independente permanece
explicitamente pendente como limitação: os sete itens não foram preenchidos
como se existisse um segundo revisor, e nenhum novo corpus foi criado.

As alterações prévias dos PDFs locais pertencem ao usuário e foram preservadas.

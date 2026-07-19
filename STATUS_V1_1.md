# Privacy Scanner LGPD — estado da versão 1.2.0

Última validação local: 19 de julho de 2026.

## Congelamento das regras

- Commit congelado: `5a891e8da2da4d16e381247162427242c1293a78`.
- CI inicial: execução `29454538863`, aprovada em Linux e Windows com VS Code
  `1.85.2` e `1.128.0`.
- A partir desse commit, resultados do `holdout_v1_1` não podem orientar novas
  heurísticas da versão 1.1; eventuais correções ficam para a versão 1.2.

## Implementado

- Redução contextual de falsos positivos em literais, logs, chamadas externas,
  persistência Python, Java e schemas SQLite.
- Contrato explícito entre achados brutos e exibidos pelo perfil, com os dois
  indicadores técnicos e quantidade ocultada auditáveis.
- Supressões estáveis, debounce da análise automática, timeout configurável e
  confirmação para arquivos ainda não salvos.

- Perfis `conservador`, `equilibrado` e `completo` por workspace.
- Validação estrita e schema de `.privacy-scanner.json`.
- Confiança e severidade-base auditável nos achados.
- Contexto estrutural para modelos Python e tabelas SQLite.
- Propagação local simples de proteção no analisador Java.
- Protocolo da API versionado e metadados do perfil nos resultados.
- Descoberta de Python, fallback de porta, reinício com uma tentativa e logs seguros.
- Reinício serializado, recuperação automática e proteção contra callbacks de processos antigos.
- Detecção independente de porta ocupada, inclusive quando `/health` retorna erro HTTP ou não há serviço HTTP compatível.
- IDs reproduzíveis, independentes da severidade e sem colisão entre colunas SQLite.
- Configuração assistida de ambiente virtual e smoke-test de instalação do VSIX.
- Suporte multi-root na extensão.
- Estado de achados/exclusões, diagnósticos, HTTP, processo e coordenação extraídos em módulos testáveis.
- Seção `Ações rápidas` acima de `Achados` e `Resumo`, com arquivo ativo,
  preset e estado do backend visíveis sem abrir a Paleta de Comandos.
- Assistente clicável `Configurar perfil`, com `Corrigir perfil` para estado
  inválido, gravação somente por confirmação e severidade explicitamente
  técnica, sem conclusão jurídica; o JSON fica identificado como avançado.
- Ações de análise no título e menu de contexto do editor e nos menus do
  Explorer para Python, Java e SQLite.
- Barra de status dedicada a abrir o painel, apresentação única introduzida na 1.1.1 e
  mensagens de erro com recuperação clicável.
- Resumo da varredura do workspace preservado quando a análise automática abre,
  ativa ou salva um arquivo; a sidebar distingue arquivos analisados de arquivos
  que efetivamente produziram achados.
- Testes unitários Python/TypeScript e teste real no Extension Host.
- CI em Windows e Linux.
- Corpus `holdout_v1_1` registrado e habilitado somente após o congelamento.

## Estado de validação

- Código e VSIX estão sincronizados em 1.2.0. Os VSIX 1.1.1, 1.1.0 e 1.0.4
  permanecem como artefatos históricos; a 1.0.4 também é a baseline preservada
  na tag `v1.0.4`.
- 181 testes Python e a suíte TypeScript, incluindo os contratos da nova UX,
  passam localmente.
- O benchmark controlado 2 permanece em 100% de aderência ao gabarito; o benchmark 1 está preservado na tag `v1.0.4`.
- O Extension Host executa reinícios, conflito real com serviço incompatível e
  análises reais no VS Code `1.85.2` e `1.128.0`; o VSIX também foi instalado
  em diretório isolado nas duas versões.
- O `holdout_v1_1` foi executado uma única vez no run
  `20260715T221415Z-3302b677`, sobre o commit de configuração `f1eed20`, com
  origem limpa e os três commits externos pré-registrados. Os escopos foram
  desabilitados novamente após o run para impedir repetição acidental.
- A revisão primária classificou todos os 22 achados exibidos e concluiu a
  inspeção de falsos negativos dos três projetos.
- A amostra estratificada de dupla revisão contém 7 itens. O arquivo cego do
  revisor B está pronto, mas nenhuma classificação independente foi importada.
- As métricas primárias permanecem apenas em
  `evaluation/real_projects/results/latest_review_summary.md` e não devem ser
  publicadas na dissertação antes da conclusão da revisão independente.
- A prova de 39 páginas com placeholders foi recompilada e revisada visualmente
  página a página. O pacote atual é
  `output/release/privacy-scanner-lgpd-1.2.0.vsix`; os VSIX 1.1.1, 1.1.0 e
  1.0.4 são mantidos como histórico. SHA-256 do pacote 1.2.0:
  `88A02458FE00E4F658BA723F4B6D40D9AF499F1B6CF59F058FE0D490C39F95C6`.

`STATUS.md` descreve a antiga fase MVP e é mantido apenas como histórico.

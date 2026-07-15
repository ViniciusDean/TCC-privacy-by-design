# Privacy Scanner LGPD — estado da versão 1.1

Última validação local: 15 de julho de 2026.

## Congelamento das regras

- Commit congelado: `5a891e8da2da4d16e381247162427242c1293a78`.
- CI inicial: execução `29454538863`, aprovada em Linux e Windows com VS Code
  `1.85.2` e `1.128.0`.
- A partir desse commit, resultados do `holdout_v1_1` não podem orientar novas
  heurísticas da versão 1.1; eventuais correções ficam para a versão 1.2.

## Implementado

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
- Testes unitários Python/TypeScript e teste real no Extension Host.
- CI em Windows e Linux.
- Corpus `holdout_v1_1` registrado e habilitado somente após o congelamento.

## Estado de validação

- A versão 1.0.4 permanece como baseline histórica na tag `v1.0.4`.
- 164 testes Python e 29 verificações TypeScript passam localmente.
- O benchmark controlado 2 permanece em 100% de aderência ao gabarito; o benchmark 1 está preservado na tag `v1.0.4`.
- O Extension Host executa reinícios, conflito real com serviço incompatível e uma análise real; o VSIX é instalado em diretório isolado.
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
  página a página; o VSIX 1.1.0 foi reempacotado e instalado em ambiente isolado.

`STATUS.md` descreve a antiga fase MVP e é mantido apenas como histórico.

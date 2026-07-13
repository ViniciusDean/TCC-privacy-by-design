# Privacy Scanner LGPD — estado da versão 1.1

Última validação local: 13 de julho de 2026.

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
- Corpus `holdout_v1_1` registrado, mas desabilitado até o congelamento.

## Estado de validação

- A versão 1.0.4 permanece como baseline histórica na tag `v1.0.4`.
- 160 testes Python e 29 verificações TypeScript passam localmente.
- O benchmark controlado 2 permanece em 100% de aderência ao gabarito; o benchmark 1 está preservado na tag `v1.0.4`.
- O Extension Host executa reinícios, conflito real com serviço incompatível e uma análise real; o VSIX é instalado em diretório isolado.
- Os novos projetos externos ainda não foram executados nem adjudicados.
- Nenhuma métrica da versão 1.1 deve ser publicada antes da revisão manual.

`STATUS.md` descreve a antiga fase MVP e é mantido apenas como histórico.

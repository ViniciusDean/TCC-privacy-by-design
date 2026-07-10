# Revisao preliminar - PEAK-TCC/back-end

Repositorio: https://github.com/PEAK-TCC/back-end

Commit analisado: `7503f50`

Data da execucao: 2026-06-25

## Escopo analisado

| Item | Valor |
|---|---:|
| Arquivos Java analisados | 130 |
| Arquivos Python analisados | 0 |
| Bancos SQLite analisados | 0 |
| Tempo de execucao | 0,2361 s |
| Achados brutos | 94 |

## Distribuicao dos achados brutos

| Categoria | Quantidade |
|---|---:|
| DADO_SEM_CRIPTOGRAFIA | 80 |
| AUSENCIA_EXCLUSAO | 11 |
| COLETA_EXCESSIVA | 2 |
| TRANSFERENCIA_SEM_BASE_LEGAL | 1 |

## Interpretacao preliminar

A execucao no projeto real mostrou que o analisador Java consegue percorrer um
backend Spring de tamanho moderado sem erro de execucao e em tempo baixo. Isso e
uma evidencia positiva de viabilidade operacional.

Ao mesmo tempo, os achados brutos indicam uma taxa relevante de falsos positivos
provaveis. A maior concentracao ocorreu em `DADO_SEM_CRIPTOGRAFIA`, com alertas
em anotacoes JPA como `@Column(name = "...")`. Nesses casos, o analisador parece
interpretar o atributo `name` da anotacao como um campo pessoal, embora a linha
esteja apenas declarando metadados de persistencia.

Tambem ha falsos positivos provaveis em `AUSENCIA_EXCLUSAO`, porque algumas
classes sinalizadas sao componentes de configuracao, services ou controllers, e
nao modelos de dados pessoais. Essa evidencia sugere que a regra deve ser
restringida principalmente a entidades, DTOs ou classes com campos pessoais
declarados diretamente.

O alerta `TRANSFERENCIA_SEM_BASE_LEGAL` em `EnderecoController` tambem parece
ser falso positivo preliminar, pois a linha retorna uma resposta HTTP da propria
API (`ResponseEntity.body(...)`) e nao necessariamente envia dados pessoais para
um servico externo.

Os dois alertas de `COLETA_EXCESSIVA` em `DataSeeder` sao plausiveis como
evidencia tecnica, pois os metodos recebem simultaneamente campos como nome,
email, CPF, celular e nascimento. Ainda assim, por se tratar de uma classe de
popularizacao inicial de dados, a classificacao final deve registrar esse
contexto.

## Implicacao para o TCC

Esta validacao externa inicial e util porque mostra uma diferenca entre o
benchmark sintetico e um projeto real. Enquanto o benchmark controlado obteve
100% nas metricas definidas, o projeto real revelou pontos de melhoria nas regras
heuristicas do analisador Java.

Essa diferenca deve ser apresentada como resultado metodologicamente positivo:
o benchmark valida a consistencia das regras conhecidas, e a validacao externa
mostra limitacoes e oportunidades de refinamento em codigo real.

## Proximas acoes

1. Preencher `latest_raw_findings.csv` com `TP` ou `FP` nos principais achados.
2. Refinar a regra Java para ignorar atributos de anotacoes como `name = ...`.
3. Restringir `AUSENCIA_EXCLUSAO` a classes que sejam entidades, DTOs ou modelos.
4. Ajustar a deteccao de transferencia externa para nao confundir
   `ResponseEntity.body(...)` com chamada a servico de terceiro.
5. Reexecutar a validacao e comparar os numeros antes/depois.

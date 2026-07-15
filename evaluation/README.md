# Avaliacao experimental

Este diretorio contem um benchmark versionado para medir a capacidade de
deteccao do Privacy Scanner LGPD.

O benchmark inicial possui 18 casos:

- 6 arquivos Python;
- 6 arquivos Java;
- 6 schemas SQLite descritos em SQL.

O gabarito esta em `benchmark/gabarito.json`. Cada caso declara as categorias
que deveriam ser encontradas. A avaliacao compara a presenca de categorias por
caso, evitando que alertas duplicados na mesma categoria distorcam as metricas.

## Executar

Na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe evaluation\run_benchmark.py
```

Os resultados sao gravados em:

- `evaluation/results/latest.json`: dados completos para processamento;
- `evaluation/results/latest.md`: tabela pronta para consulta e uso no TCC.

## Metricas

- **Precisao**: proporcao dos alertas emitidos que constam no gabarito.
- **Recall**: proporcao das vulnerabilidades do gabarito que foram detectadas.
- **F1**: media harmonica entre precisao e recall.
- **Especificidade**: proporcao dos pares caso/categoria negativos corretamente
  classificados.

Este conjunto inicial e controlado e nao substitui a avaliacao posterior em
projetos reais. Ele mede decisoes **caso--categoria** no gabarito versionado:
resultados de 100% descrevem consistencia interna com as fixtures, nao desempenho
generalizavel. Casos novos devem ser revisados manualmente antes de entrarem no
gabarito.

O benchmark 2 torna explícito o contexto estrutural de persistência nas três
fixtures de modelo/schema alteradas. O benchmark 1 permanece auditável na tag
`v1.0.4`; resultados de versões diferentes só devem ser comparados quando
executados sobre a mesma versão do corpus.

O executor de projetos reais registra separadamente os achados brutos
(`latest_unfiltered_findings.json`) e os achados selecionados pelo perfil
(`latest_raw_findings.json`, mantido com esse nome por compatibilidade). Cada
projeto registra preset, origem e hash da configuração aplicada.

## Validação externa

Depois do benchmark sintético, use `real_projects/` para cadastrar projetos
reais e gerar achados técnicos para revisão manual:

```powershell
python evaluation\real_projects\run_real_projects.py
```

Cada execução é gravada em `real_projects/results/runs/<run_id>/` com commit,
versão, ambiente, papel de avaliação e hash do escopo. O resumo mais recente é atualizado em
`real_projects/results/latest_summary.md`.

Classifique cada achado em `real_projects/results/manual_adjudication.csv`, pelo
seu `finding_id`, usando apenas `TP` ou `FP`; registre falsos negativos em
`real_projects/manual_false_negatives.csv`. Esses arquivos manuais não são
sobrescritos por uma nova execução. As métricas externas de precisão, recall e
F1 só são exibidas após todos os achados terem sido classificados e a inspeção
de falsos negativos do projeto ter sido concluída.

O PEAK Java é o conjunto de ajuste. Flasky e Chinook são conjuntos de validação;
suas métricas são publicadas separadamente e não orientam novas alterações de
regras nesta versão. Mesmo após a revisão completa, os valores descrevem apenas
essa amostra e não certificam desempenho geral ou conformidade jurídica.

## Protocolo da versão 1.1

Django Oscar, Spring PetClinic e Northwind SQLite foram cadastrados como
`holdout_v1_1`, inicialmente com `enabled: false`. Eles foram habilitados somente
depois do congelamento das regras da versão 1.1 e executados pela primeira e
única vez no run `20260715T221415Z-3302b677`. Os resultados não podem orientar
novas heurísticas da versão 1.1. Após essa execução, os três escopos foram
desabilitados novamente para impedir uma repetição acidental.

```powershell
# Histórico do comando já executado; não executar novamente:
# python evaluation\real_projects\run_real_projects.py --role holdout_v1_1
python evaluation\real_projects\create_double_review_sample.py
python evaluation\real_projects\double_review_blind.py export
# O segundo revisor preenche apenas reviewer_b no CSV exportado.
python evaluation\real_projects\double_review_blind.py import --input evaluation\real_projects\results\double_review_reviewer_b.csv
python evaluation\real_projects\calculate_agreement.py
python evaluation\real_projects\review_frozen_run.py --run-id ID_DA_EXECUCAO
```

A amostra dupla usa 25% de cada estrato projeto/categoria/risco e semente fixa.
O arquivo exportado omite os rótulos do primeiro revisor para preservar a
independência. As colunas `confidence` e `base_risk` preservam a justificativa
do perfil aplicado. A recomposição da revisão não executa novamente os
analisadores e mantém intactos os arquivos originais do run congelado.

# Validação externa em projetos reais

Esta etapa complementa o benchmark sintético em `evaluation/benchmark/`.
O objetivo é medir como o Privacy Scanner LGPD se comporta em projetos que não
foram criados especificamente para o teste.

## Objetivo

Registrar evidências para o capítulo de resultados:

- quantidade de arquivos analisados;
- quantidade de achados por projeto;
- categorias encontradas;
- falsos positivos identificados por revisão manual;
- falsos negativos observados por inspeção humana;
- tempo de execução;
- limitações percebidas.

## Como usar

1. Copie `projects.example.json` para `projects.json`.
2. Edite `projects.json` com os caminhos dos projetos reais.
3. Execute, na raiz do repositório:

```powershell
.\.venv\Scripts\python.exe evaluation\real_projects\run_real_projects.py
```

O script gera uma execução imutável em `results/runs/<run_id>/`, registrando
commit, versão, ambiente, escopo e SHA-256 dos arquivos analisados, e atualiza os
atalhos de leitura mais recente:

- `results/latest_raw_findings.json`: achados técnicos e metadados de escopo;
- `results/latest_raw_findings.csv`: espelho para consulta, com o `finding_id`;
- `results/latest_summary.md`: resumo de projeto, proveniência e cobertura da revisão;
- `results/manual_adjudication.csv`: classificações manuais persistentes.

Cada projeto declara `evaluation_role` (`tuning` ou `validation`) e
`fn_review_complete`. O resumo publica métricas por projeto e por papel, evitando
combinar o conjunto usado para ajustar regras com os conjuntos independentes.

## Revisão manual

Após a execução, abra `results/manual_adjudication.csv` e preencha, para cada
`finding_id` presente em `latest_raw_findings.csv`:

- `manual_classification`: `TP` para verdadeiro positivo ou `FP` para falso positivo;
- `reviewer_notes`: justificativa curta da classificação;
- `suggested_fix`: correção sugerida, quando aplicável.

Falsos negativos devem ser registrados em `manual_false_negatives.csv`, com
localizador de evidência, estado `OPEN` ou `RESOLVED` e versão de resolução.
Somente linhas abertas entram no cálculo atual de recall e F1. Uma nova execução
nunca sobrescreve os arquivos manuais.

## Critérios sugeridos para escolher projetos

- Um projeto Python com Flask, FastAPI, Django ou scripts de backend.
- Um projeto Java com classes de domínio, serviços ou controladores.
- Um projeto com banco SQLite ou arquivo `.db` usado por aplicação real.

Evite projetos enormes nesta fase. A meta é gerar evidência analisável para o
TCC, não auditar um sistema de produção completo.

## Observação metodológica

Os resultados não comprovam conformidade jurídica completa com a LGPD. Métricas
externas só são apresentadas quando todos os achados do escopo estiverem
classificados como TP/FP e a revisão de falsos negativos estiver marcada como
concluída. Mesmo completas, precisão, recall e F1 descrevem somente os projetos,
commits e escopos registrados; não devem ser generalizados.

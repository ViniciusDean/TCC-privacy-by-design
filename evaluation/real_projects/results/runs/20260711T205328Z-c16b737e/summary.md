# Validação externa - achados técnicos

Gerado em: `2026-07-11T20:53:28.786256+00:00`
Execução: `20260711T205328Z-c16b737e`
Commit: `ac9604432fb44fd621227855fb92042ba2341947` (dirty)

## Projetos analisados

| Projeto | Papel | Tipo | Perfil | Brutos | Exibidos | Python | Java | SQLite | Tempo (s) | Hash do escopo |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| peak_back_end | tuning | source | conservador | 8 | 4 | 0 | 130 | 0 | 0.1612 | badc5dd118d8 |
| flasky | validation | source | conservador | 8 | 2 | 39 | 0 | 0 | 0.0400 | 67962b6e8c35 |
| chinook_sqlite | validation | sqlite | conservador | 16 | 0 | 0 | 0 | 1 | 0.0538 | 264a04693434 |

## Revisão manual por projeto

| Projeto | Papel | TP | FP | FN | Sem classificação | Precisão | Recall | F1 | Pronto |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| peak_back_end | tuning | 4 | 0 | 1 | 0 | 100.00% | 80.00% | 88.89% | sim |
| flasky | validation | 2 | 0 | 3 | 0 | 100.00% | 40.00% | 57.14% | sim |
| chinook_sqlite | validation | 0 | 0 | 17 | 0 | n/a | 0.00% | n/a | sim |

## Síntese por papel

- `tuning`: precisão **100.00%**, recall **80.00%**, F1 **88.89%**.
- `validation`: precisão **100.00%**, recall **9.09%**, F1 **16.67%**.

A revisão manual foi concluída para os escopos registrados. As métricas descrevem somente estes projetos e commits; não devem ser generalizadas para outros sistemas.

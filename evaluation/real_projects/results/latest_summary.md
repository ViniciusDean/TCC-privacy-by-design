# Validação externa - achados técnicos

Gerado em: `2026-07-15T22:14:15.566057+00:00`
Execução: `20260715T221415Z-3302b677`
Commit: `f1eed20d70f42cb6f8bc81de42084da40044c6fe` (clean)

## Projetos analisados

| Projeto | Papel | Tipo | Perfil | Brutos | Exibidos | Python | Java | SQLite | Tempo (s) | Hash do escopo |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| django_oscar_v1_1 | holdout_v1_1 | source | conservador | 80 | 20 | 483 | 0 | 0 | 0.4776 | 8499cd0ef9b5 |
| spring_petclinic_v1_1 | holdout_v1_1 | source | conservador | 3 | 2 | 0 | 30 | 0 | 0.0353 | 817a46a1d716 |
| northwind_sqlite_v1_1 | holdout_v1_1 | sqlite | conservador | 12 | 0 | 0 | 0 | 1 | 0.0664 | 9bef6b22624f |

## Revisão manual por projeto

| Projeto | Papel | TP | FP | FN | Sem classificação | Precisão | Recall | F1 | Pronto |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| django_oscar_v1_1 | holdout_v1_1 | 0 | 0 | 0 | 20 | n/a | n/a | n/a | não |
| spring_petclinic_v1_1 | holdout_v1_1 | 0 | 0 | 0 | 2 | n/a | n/a | n/a | não |
| northwind_sqlite_v1_1 | holdout_v1_1 | 0 | 0 | 0 | 0 | n/a | n/a | n/a | não |

## Síntese por papel

- `holdout_v1_1`: revisão incompleta; métricas ainda não publicadas.

A execução externa é exploratória até que a revisão manual esteja completa; ela não deve ser usada como estimativa de precisão em projetos reais antes disso.

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
| django_oscar_v1_1 | holdout_v1_1 | 3 | 17 | 3 | 0 | 15.00% | 50.00% | 23.08% | sim |
| spring_petclinic_v1_1 | holdout_v1_1 | 1 | 1 | 1 | 0 | 50.00% | 50.00% | 50.00% | sim |
| northwind_sqlite_v1_1 | holdout_v1_1 | 0 | 0 | 40 | 0 | n/a | 0.00% | n/a | sim |

## Síntese por papel

- `holdout_v1_1`: precisão **18.18%**, recall **8.33%**, F1 **11.43%**.

A revisão manual foi concluída para os escopos registrados. As métricas descrevem somente estes projetos e commits; não devem ser generalizadas para outros sistemas.

## Dupla revisão

- Amostra: **7** itens; pares completos: **0**.
- Revisão independente pendente; métricas primárias não devem ser publicadas na dissertação.

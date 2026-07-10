# Validação externa - achados técnicos

Gerado em: `2026-07-10T02:00:55.010913+00:00`
Execução: `20260710T020055Z-a120fe5d`
Commit: `12eceb859b705347c42f8149fc64009ad8607b48` (dirty)

## Projetos analisados

| Projeto | Papel | Tipo | Arquivos Python | Arquivos Java | SQLite | Achados | Tempo (s) | Hash do escopo |
|---|---|---|---:|---:|---:|---:|---:|---|
| peak_back_end | tuning | source | 0 | 130 | 0 | 10 | 0.1746 | badc5dd118d8 |
| flasky | validation | source | 39 | 0 | 0 | 16 | 0.0474 | 67962b6e8c35 |
| chinook_sqlite | validation | sqlite | 0 | 0 | 1 | 32 | 0.0540 | 264a04693434 |

## Revisão manual por projeto

| Projeto | Papel | TP | FP | FN | Sem classificação | Precisão | Recall | F1 | Pronto |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| peak_back_end | tuning | 6 | 0 | 1 | 4 | n/a | n/a | n/a | não |
| flasky | validation | 0 | 0 | 0 | 16 | n/a | n/a | n/a | não |
| chinook_sqlite | validation | 0 | 0 | 0 | 32 | n/a | n/a | n/a | não |

## Síntese por papel

- `tuning`: revisão incompleta; métricas ainda não publicadas.
- `validation`: revisão incompleta; métricas ainda não publicadas.

A execução externa é exploratória até que a revisão manual esteja completa; ela não deve ser usada como estimativa de precisão em projetos reais antes disso.

# Validação externa - achados técnicos

Gerado em: `2026-07-10T02:07:16.459842+00:00`
Execução: `20260710T020716Z-e3b1571f`
Commit: `12eceb859b705347c42f8149fc64009ad8607b48` (dirty)

## Projetos analisados

| Projeto | Papel | Tipo | Arquivos Python | Arquivos Java | SQLite | Achados | Tempo (s) | Hash do escopo |
|---|---|---|---:|---:|---:|---:|---:|---|
| peak_back_end | tuning | source | 0 | 130 | 0 | 8 | 0.1469 | badc5dd118d8 |
| flasky | validation | source | 39 | 0 | 0 | 16 | 0.0412 | 67962b6e8c35 |
| chinook_sqlite | validation | sqlite | 0 | 0 | 1 | 32 | 0.0491 | 264a04693434 |

## Revisão manual por projeto

| Projeto | Papel | TP | FP | FN | Sem classificação | Precisão | Recall | F1 | Pronto |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| peak_back_end | tuning | 8 | 0 | 1 | 0 | 100.00% | 88.89% | 94.12% | sim |
| flasky | validation | 3 | 13 | 3 | 0 | 18.75% | 50.00% | 27.27% | sim |
| chinook_sqlite | validation | 16 | 16 | 17 | 0 | 50.00% | 48.48% | 49.23% | sim |

## Síntese por papel

- `tuning`: precisão **100.00%**, recall **88.89%**, F1 **94.12%**.
- `validation`: precisão **39.58%**, recall **48.72%**, F1 **43.68%**.

A execução externa é exploratória até que a revisão manual esteja completa; ela não deve ser usada como estimativa de precisão em projetos reais antes disso.

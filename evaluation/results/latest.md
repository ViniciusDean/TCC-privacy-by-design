# Resultado do benchmark

Gerado em: `2026-06-15T03:13:27.715364+00:00`

Casos avaliados: **18**

## Resultado global

| TP | FP | FN | TN | Precisao | Recall | F1 | Especificidade |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 24 | 0 | 0 | 96 | 100.00% | 100.00% | 100.00% | 100.00% |

## Por tipo

| Tipo | Precisao | Recall | F1 |
|---|---:|---:|---:|
| java | 100.00% | 100.00% | 100.00% |
| python | 100.00% | 100.00% | 100.00% |
| sqlite | 100.00% | 100.00% | 100.00% |

## Divergencias por caso

| Caso | Tipo | Ausentes | Inesperadas |
|---|---|---|---|
| py_hardcoded_log | python | - | - |
| py_crypto_transfer | python | - | - |
| py_model_without_controls | python | - | - |
| py_excessive_collection | python | - | - |
| py_safe_hashing | python | - | - |
| py_safe_technical_metadata | python | - | - |
| java_hardcoded_log | java | - | - |
| java_crypto_transfer | java | - | - |
| java_model_without_controls | java | - | - |
| java_excessive_collection | java | - | - |
| java_safe_hashing | java | - | - |
| java_safe_technical_metadata | java | - | - |
| db_plaintext_missing_controls | sqlite | - | - |
| db_sensitive_primary_key | sqlite | - | - |
| db_mixed_data | sqlite | - | - |
| db_missing_retention | sqlite | - | - |
| db_safe_protected_schema | sqlite | - | - |
| db_safe_operational_schema | sqlite | - | - |

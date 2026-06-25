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
projetos reais. Casos novos devem ser revisados manualmente antes de entrarem no
gabarito.

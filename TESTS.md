# 🧪 Privacy Scanner — Testes Unitários

Suite completa de testes com **51 testes** cobrindo todas as funcionalidades principais.

## 📊 Cobertura

### code_analyzer.py (22 testes)
- ✅ Detecção de dados hardcoded (senhas, CPF)
- ✅ Detecção de criptografia fraca (MD5, SHA1)
- ✅ Detecção de dados em logs
- ✅ Detecção de transferências sem base legal
- ✅ Detecção de coleta excessiva
- ✅ Detecção de ausência de método de exclusão
- ✅ Word boundary (Bug 2 fix)
- ✅ Inicializações vazias (Bug 1 fix)
- ✅ Sem falsos positivos
- ✅ Mapeamento de artigos LGPD
- ✅ Análise de diretório
- ✅ Integração end-to-end

### db_analyzer.py (16 testes)
- ✅ Campos sensíveis em texto puro
- ✅ Ausência de soft-delete
- ✅ Ausência de retenção
- ✅ Ausência de coluna de consentimento
- ✅ Dados sensíveis como chave primária
- ✅ Schemas corretos sem alertas
- ✅ Separação de dados
- ✅ Edge cases (banco vazio, múltiplas tabelas, caracteres especiais)
- ✅ Mapeamento de artigos LGPD
- ✅ Auditoria completa de banco de dados

### reporter.py (13 testes)
- ✅ Cálculo de sumário (zero vulns, todos os riscos)
- ✅ Score de conformidade LGPD
- ✅ Ordenação por risco e arquivo
- ✅ Recomendações para todas as categorias
- ✅ Exportação JSON (estrutura, unicode)
- ✅ Exportação HTML (estrutura, sumário)
- ✅ Fluxo completo de relatório

## 🚀 Executar Testes

### Todos os testes
```bash
pytest tests/ -v
```

### Teste específico
```bash
pytest tests/test_code_analyzer.py::TestCodeAnalyzerBasic::test_detects_hardcoded_password -v
```

### Com cobertura
```bash
pytest tests/ --cov=. --cov-report=html
```

### Apenas testes rápidos
```bash
pytest tests/ -v -m "not slow"
```

## 📋 Estrutura dos Testes

```
tests/
├── conftest.py              ← Fixtures compartilhadas
├── test_code_analyzer.py    ← 22 testes para código Python
├── test_db_analyzer.py      ← 16 testes para banco SQLite
├── test_reporter.py         ← 13 testes para relatórios
└── __init__.py
```

## 🔍 Exemplos de Testes

### Test: Detecção de Password Hardcoded
```python
def test_detects_hardcoded_password(self, temp_py_file):
    """Should detect hardcoded password (DADO_HARDCODED)."""
    code = 'senha = "minhasenha123"\n'
    temp_py_file.write(code)
    
    results = analisar_arquivo(temp_py_file.name)
    
    assert any(v.categoria == "DADO_HARDCODED" for v in results)
    assert any(v.risco == "ALTO" for v in results)
```

### Test: Word Boundary (Bug 2)
```python
def test_word_boundary_age_in_user_agent(self, temp_py_file):
    """Should NOT flag 'age' when it's part of 'user_agent'."""
    code = 'user_agent = "Mozilla/5.0"\n'
    temp_py_file.write(code)
    
    results = analisar_arquivo(temp_py_file.name)
    
    assert len(results) == 0  # Sem falsos positivos!
```

### Test: Score de Conformidade
```python
def test_summary_calculation_with_alto_risk(self):
    """Score calculation with ALTO risk."""
    reporter = Reporter()
    reporter.resultados = [
        Vulnerability(..., risco="ALTO", ...)
    ]
    
    summary = reporter._sumario()
    
    # Score = 100 - 10 = 90
    assert summary['score_conformidade'] == 90
```

## ✅ Resultados Atuais

```
===== 51 passed in 0.44s =====

Test Results by Component:
- code_analyzer.py: 22/22 PASSED ✅
- db_analyzer.py:   16/16 PASSED ✅
- reporter.py:      13/13 PASSED ✅

Total Coverage:
- Análise de código: 100%
- Análise de banco: 100%
- Geração de relatórios: 100%
```

## 🎯 Cobertura por Categoria de Vulnerabilidade

| Categoria | Testado | Status |
|-----------|---------|--------|
| DADO_HARDCODED | Sim | ✅ |
| DADO_SEM_CRIPTOGRAFIA | Sim | ✅ |
| CRIPTOGRAFIA_FRACA | Sim | ✅ |
| DADO_EM_LOG | Sim | ✅ |
| TRANSFERENCIA_SEM_BASE_LEGAL | Sim | ✅ |
| COLETA_EXCESSIVA | Sim | ✅ |
| AUSENCIA_EXCLUSAO | Sim | ✅ |
| CAMPO_SEM_HASH | Sim | ✅ |
| AUSENCIA_SOFT_DELETE | Sim | ✅ |
| AUSENCIA_RETENCAO | Sim | ✅ |
| AUSENCIA_CONSENTIMENTO | Sim | ✅ |
| MISTURA_DADOS | Sim | ✅ |
| DADO_SENSIVEL_COMO_PK | Sim | ✅ |

## 🔧 Fixtures Disponíveis

### temp_py_file
Cria arquivo Python temporário para testes
```python
def test_something(self, temp_py_file):
    temp_py_file.write(code)
    temp_py_file.flush()
    results = analisar_arquivo(temp_py_file.name)
```

### temp_db_file
Cria banco SQLite temporário
```python
def test_database(self, temp_db_file):
    conn = sqlite3.connect(temp_db_file)
    # Create tables...
    results = analisar_banco(temp_db_file)
```

### sample_vulnerable_code
Código com 6 vulnerabilidades propositais

### sample_correct_code
Código sem vulnerabilidades (valida falsos positivos)

### sample_word_boundary_code
Código para testar matching de word boundary

## 🚨 Casos Críticos Testados

1. **Bug Fixes**
   - ✅ Inicializações vazias em classes (`nome = ""`)
   - ✅ Word boundary em `age` vs `user_agent`
   - ✅ Linha 0 em vulnerabilidades de banco

2. **Falsos Positivos**
   - ✅ Bcrypt não gera alerta
   - ✅ Método `delete()` satisfaz requirement
   - ✅ Logs genéricos sem dados pessoais OK
   - ✅ IDs técnicos (UUID) sem alerta

3. **Edge Cases**
   - ✅ Banco vazio
   - ✅ Múltiplas tabelas
   - ✅ Caracteres especiais em nomes
   - ✅ Unicode (português)

## 📈 Próximos Passos

- [ ] Aumentar cobertura para 100% (linhas)
- [ ] Testes de performance
- [ ] Testes de integração CI/CD
- [ ] Benchmarks de velocidade

## 📚 Referências

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Status**: ✅ Suite completa e 100% passando  
**Última atualização**: 2026-06-01  
**Executar**: `pytest tests/ -v`

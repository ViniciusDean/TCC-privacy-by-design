# Testes do Privacy Scanner LGPD

A suíte automatizada possui atualmente **79 testes**, todos passando.

## Executar

Na raiz do projeto:

```powershell
python -m pytest
```

Resultado esperado:

```text
79 passed
```

Para saída detalhada:

```powershell
python -m pytest -v
```

Para gerar cobertura:

```powershell
python -m pytest --cov=code_analyzer --cov=java_analyzer --cov=db_analyzer --cov=reporter --cov-report=html
```

O relatório será criado em `htmlcov/index.html`.

## Organização

### `test_code_analyzer.py`

Valida o analisador Python:

- dados pessoais hardcoded;
- criptografia fraca;
- dados pessoais em logs;
- transferência sem base legal;
- coleta excessiva;
- ausência de exclusão;
- dado sem criptografia;
- limites de palavras;
- redução de falsos positivos;
- análise de diretório.

### `test_java_analyzer.py`

Valida as sete categorias de código no suporte Java:

- dado pessoal hardcoded;
- MD5 e SHA-1 com `MessageDigest`, Apache Commons Codec e Guava;
- dado pessoal em logs;
- transferência externa sem marcador de base legal;
- coleta excessiva em métodos e construtores;
- classe sem exclusão ou anonimização;
- atribuição de dado sensível sem proteção;
- instruções multilinha, comentários e precisão das linhas;
- inicializações vazias e atribuições de construtor sem falso positivo;
- identificadores técnicos, SHA-256 e payload anonimizado sem alerta;
- exemplos Java correto e vulnerável;
- diretório contendo Python e Java.

O suporte Java usa análise léxica conservadora. Ele não compila o projeto nem
acompanha o fluxo de um valor entre métodos diferentes.

### `test_db_analyzer.py`

Valida o analisador SQLite:

- campo sensível em texto puro;
- ausência de soft delete;
- ausência de retenção;
- ausência de consentimento;
- dado sensível como chave primária;
- schema correto;
- banco vazio;
- múltiplas tabelas;
- caracteres especiais;
- mapeamento para artigos da LGPD.

### `test_reporter.py`

Valida relatórios e score:

- cálculo do score;
- ordenação por risco;
- recomendações;
- exportação JSON;
- exportação HTML;
- escape de conteúdo HTML;
- exportação PDF;
- fluxo integrado.

## Validação da Extensão

O TypeScript deve ser compilado separadamente:

```powershell
cd vscode-extension
npm run compile
```

Essa compilação verifica erros de tipo e gera `out/extension.js`.

## Teste Manual Recomendado

1. Pressione `F5` no VS Code.
2. Abra `exemplo_vulneravel.py`.
3. Execute `Privacy Scanner: Analisar arquivo atual`.
4. Abra `exemplo_vulneravel.java` e repita.
5. Analise `banco_vulneravel.db`.
6. Ignore uma ocorrência na interface.
7. Confirme que ela desaparece da sidebar e do painel `Problems`.
8. Exporte HTML ou PDF e confirme que a ocorrência continua no relatório.

## Limitações

- Os testes usam exemplos controlados.
- Eles não comprovam cobertura completa da LGPD.
- Eles não substituem avaliação jurídica.
- O suporte Java não realiza análise de fluxo entre métodos ou resolução de tipos.

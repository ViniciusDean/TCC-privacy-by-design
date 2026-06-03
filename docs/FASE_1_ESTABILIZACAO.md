# Fase 1 - Estabilizacao Tecnica

Objetivo: garantir que o projeto seja reproduzivel, testavel e demonstravel sem passos manuais escondidos.

## Entregas

- `requirements.txt` com dependencias Python.
- `package-lock.json` para dependencias da extensao.
- `.vscode/launch.json` e `.vscode/tasks.json` para rodar a extensao com `F5`.
- `scripts/create_test_workspace.py` para gerar workspace externo de teste.
- `docs/DEMO.md` com roteiro de apresentacao.
- `setup_windows.bat` para preparar ambiente.
- `validate_project.bat` para validar testes e build.
- `.gitignore` ignorando caches, cobertura, `node_modules` e build da extensao.

## Checklist Antes de Apresentar

Execute na raiz do projeto:

```bat
validate_project.bat
```

Resultado esperado:

- workspace `privacy-scanner-testes` criado;
- `pytest` passando com 56 testes;
- `npm run compile` sem erros;
- extensao abrindo com `F5`;
- comando `Privacy Scanner: Analisar projeto inteiro` populando a sidebar;
- comando `Privacy Scanner: Analisar banco SQLite` analisando `banco_vulneravel.db`.

## Proximo Marco

Fase 2: UX da extensao.

Prioridades:

- comandos para limpar resultados e reanalisar;
- botoes na sidebar;
- exibicao melhor para vulnerabilidades de banco (`tabela.coluna`);
- mensagens de erro mais claras para Flask/Python;
- primeiro pacote `.vsix` local.


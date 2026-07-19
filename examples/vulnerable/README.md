# Novos exemplos intencionalmente vulneráveis

Estes arquivos contêm padrões inseguros propositais para demonstrar os
**indícios técnicos** produzidos pelo Privacy Scanner LGPD. Todos os dados são
fictícios e os exemplos não devem ser reutilizados em produção.

## Cenários

- `cadastro_clientes_vulneravel.py`: cadastro e envio de dados de clientes para
  um serviço externo.
- `folha_pagamento_vulneravel.py`: processamento de dados pessoais e
  financeiros de funcionários.
- `ProntuarioVulneravel.java`: persistência e compartilhamento de dados de
  pacientes em Java.

Os dois cenários Python exercitam seis categorias:

- `DADO_HARDCODED`;
- `CRIPTOGRAFIA_FRACA`;
- `DADO_EM_LOG`;
- `TRANSFERENCIA_SEM_BASE_LEGAL`;
- `COLETA_EXCESSIVA`;
- `AUSENCIA_EXCLUSAO`.

O cenário Java exercita as mesmas seis categorias e também
`DADO_SEM_CRIPTOGRAFIA`.

## Análise direta

```powershell
python code_analyzer.py examples\vulnerable\cadastro_clientes_vulneravel.py
python code_analyzer.py examples\vulnerable\folha_pagamento_vulneravel.py
python code_analyzer.py examples\vulnerable\ProntuarioVulneravel.java
```

A detecção representa pontos para revisão humana e não certificação jurídica ou
conclusão automática de desconformidade com a LGPD.

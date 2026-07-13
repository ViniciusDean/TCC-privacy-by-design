# Roteiro de apresentação — Privacy Scanner LGPD

Duração-alvo: **13 minutos**, com margem para chegar a 12–15 minutos sem acelerar.

## Fala por slide

1. **Abertura — 45 s**
   - “Este trabalho investiga como princípios de Privacy by Design podem aparecer no fluxo de desenvolvimento por meio de indícios técnicos reproduzíveis.”
   - Antecipar a delimitação: o scanner apoia triagem; não certifica conformidade com a LGPD.

2. **Problema e lacuna — 1 min 15 s**
   - Dados pessoais surgem em modelos, logs, integrações e bancos antes da revisão especializada.
   - SAST generalista prioriza segurança; necessidade, retenção e minimização exigem sinais próprios.
   - Hipótese: alertas contextualizados durante o desenvolvimento antecipam a revisão.

3. **Método DSR — 1 min**
   - Relevância: problema observado no processo de software.
   - Conhecimento: LGPD, Privacy by Design e análise estática.
   - Construção: extensão, API, analisadores e relatórios.
   - Avaliação: benchmark controlado, ajuste no PEAK e validação independente.

4. **Arquitetura — 1 min**
   - A extensão envia o escopo à API local.
   - A API aplica regras consistentes de análise e exclusão.
   - Os analisadores retornam evidência segura e relatórios HTML/JSON.
   - Reforçar: execução local e objetos de saída auditáveis.

5. **Escopo da afirmação — 1 min**
   - Explicar um achado: categoria, local, artigo relacionado, descrição, recomendação e evidência.
   - Mostrar confiança, severidade-base e o perfil conservador versionado da versão 1.1.
   - O indicador ordena prioridade; não decide base legal nem contexto de negócio.

6. **Benchmark controlado — 1 min**
   - 18 casos, 120 decisões: 24 TP, 0 FP, 0 FN, 96 TN.
   - 135 testes Python garantem regressão e contratos do artefato.
   - Dizer explicitamente: resultado controlado não estima desempenho universal.

7. **Validação externa — 2 min**
   - PEAK foi conjunto de ajuste: F1 94,12%.
   - Flasky e Chinook foram congelados como validação: F1 27,27% e 49,23%.
   - Síntese dos conjuntos de validação: precisão 39,58%, recall 48,72%, F1 43,68%.
   - Interpretação: o scanner encontra indícios úteis, mas ainda depende de revisão humana e não generaliza bem fora das convenções previstas.

8. **Falhas e aprendizado — 1 min 15 s**
   - Flasky: nomes genéricos e formulários pedem contexto semântico.
   - Chinook: chaves e convenções de esquema produzem ambiguidades.
   - Java: fluxos entre instruções e camadas escapam da análise local.
   - Próximo avanço científico: análise de fluxo e corpus maior, sem retunar nos conjuntos já avaliados.

9. **Demonstração — 2 min**
   - Abrir um arquivo de exemplo e executar `Privacy Scanner: Analisar arquivo atual`.
   - Selecionar um achado e explicar categoria, local, evidência segura e recomendação.
   - Exportar o relatório e apontar o aviso de limite no topo.
   - Se a demonstração falhar, usar a captura presente no slide e abrir `docs/relatorio_teste.html`.

10. **Conclusão — 45 s**
    - “O artefato é reprodutível, integrado ao desenvolvimento e útil como triagem.”
    - “A validação externa mostra que a decisão precisa continuar humana.”
    - “A contribuição não é uma certificação LGPD; é uma forma auditável de antecipar perguntas de privacidade.”

## Checklist de demonstração

- Instalar `privacy-scanner-lgpd-1.0.4.vsix` em perfil limpo.
- Abrir uma pasta que não seja o repositório do scanner.
- Abrir `exemplo_vulneravel.py` e executar a análise do arquivo.
- Verificar que a API local inicia e que o painel mostra 7 achados.
- Exportar o HTML e confirmar o aviso “Limite da análise”.
- Manter `docs/relatorio_teste.html` e a captura do slide 9 disponíveis como contingência.

## Respostas curtas para perguntas prováveis

### “Por que houve tantos falsos positivos?”

As regras são predominantemente sintáticas e locais. Projetos reais usam nomes genéricos, camadas e convenções que exigem contexto semântico. A validação independente foi mantida sem retuning para expor essa limitação, e não para produzir um número artificialmente favorável.

### “Como foram definidos os pesos do indicador?”

Os pesos representam prioridade técnica por severidade e quantidade de indícios. Eles são heurísticos e não equivalem a risco jurídico, multa ou probabilidade de incidente. A saída sempre preserva os achados individuais para revisão.

### “Por que o Java tem limitações?”

O analisador reconhece padrões estruturais e chamadas locais, mas não realiza análise interprocedural completa nem resolve todos os fluxos entre controller, service e repositório. Isso afeta especialmente transferência, logging e minimização distribuídos entre camadas.

### “Isso comprova conformidade com a LGPD?”

Não. O scanner identifica indícios técnicos relacionados a princípios e artigos; base legal, finalidade, governança e contexto organizacional não são inferidos apenas do código.

### “Qual a diferença para Veracode ou Semgrep?”

Veracode e ferramentas SAST similares têm cobertura ampla de segurança. Semgrep permite regras flexíveis. Este artefato concentra regras e apresentação em perguntas de privacidade, integra SQLite e explicita artigo, recomendação e limite jurídico. Não pretende competir em escala ou profundidade de análise de fluxo.

### “Por que usar PEAK como ajuste e Flasky/Chinook como validação?”

Separar ajuste e validação reduz o risco de alterar regras depois de observar os resultados que serão reportados como evidência independente. Os três projetos também exercitam Java, Python e SQLite.

### “Qual é a principal ameaça à validade?”

O corpus é pequeno e a adjudicação foi feita por um único revisor. Por isso as métricas descrevem somente os projetos escolhidos, não o universo de projetos reais.

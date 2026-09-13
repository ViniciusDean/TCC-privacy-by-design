# Auditoria de referências e originalidade — em andamento

Data: 12/09/2026. Fonte: latex_tcc/main.tex. Base: commit 5faec9e.

## Progresso

- Parte 1: leitura integral e cruzamento inicial realizados; verificação externa em curso.
- Parte 2: comparação de fontes e buscas de similaridade em curso.
- Parte 3: correções parciais salvas; parecer final e PDF ainda pendentes.

## Achados já confirmados

1. Metodologia declarava consultas a IEEE Xplore, ACM, Scopus e Google Scholar,
   combinações de descritores e prioridade cronológica sem registros localizados
   em docs/scripts/histórico do trecho. Substituída por descrição do levantamento
   narrativo comprovável; não foi atribuída ao autor uma pesquisa não documentada.
2. Definição de dado pessoal reproduzia literalmente o art. 5º, I, da LGPD sem
   aspas. Atribuição já existia; corrigida a apresentação como citação direta.
3. Introdução tinha afirmação histórica/causal genérica sem fonte.
   Substituída por contextualização sustentada em Spiekermann e Cranor, seção 3.1.
4. Referência ao considerando 30 do GDPR era insuficiente para localização e
   meios de identificação: acrescentados art. 4º, 1, e considerando 26.
5. ANPD: confirmadas 163 comunicações; predominância de ransomware decorre de
   levantamento amostral. Explicitado o recorte e localizadas páginas 31–32.
6. Fórmulas de avaliação requerem referência bibliográfica; fonte acadêmica
   pública localizada, inclusão e conferência em curso.

## Evidências locais conferidas

- evaluation/results/latest.md: scanner 1.2.0, execução 20/07/2026, 18 casos,
  120 decisões, 24 TP, 96 TN, 0 FP e 0 FN.
- evaluation/real_projects/results/runs/20260710T024446Z-d034f8fc/summary.md:
  PEAK 8/0/1; Flasky 3/13/3; Chinook 16/16/17. Agregado independente
  19 TP, 29 FP, 20 FN; precisão 39,58%, recall 48,72%, F1 43,68%.

## Limite da auditoria

A leitura e buscas públicas não substituem uma base acadêmica de similaridade.
Ausência de resultado em busca não comprova originalidade. Não será emitida
porcentagem de plágio nem garantia de ausência de plágio. O TCC completo não
foi enviado a serviços externos.

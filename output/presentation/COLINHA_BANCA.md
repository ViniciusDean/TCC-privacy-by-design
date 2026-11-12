# Colinha da defesa

Versão para o celular: https://claude.ai/artifact/7xf6xoTTuU8suRgR5Nnmth

**1. Capa (0:30)**
- Boa noite, agradecer banca e Prof. Adilson
- Privacy Scanner LGPD: análise estática de Python, Java e SQLite
- Roda como extensão do VS Code

**2. Roteiro (0:15)**
- Introdução, fundamentação, requisitos e tecnologias
- Maior parte do tempo: demo ao vivo
- Avaliação e considerações finais

**3. Contexto e problema (1:00)**
- LGPD art. 46: medidas técnicas desde a concepção
- Art. 52: multa até 2% do faturamento, teto R$ 50 mi por infração
- 163 incidentes comunicados à ANPD no 1º sem. de 2023
- Problema: operacionalizar princípios no dia a dia do dev
- SAST de mercado foca segurança e qualidade, não privacidade

**4. Pergunta-problema (0:30)**
- "A pergunta que guiou a pesquisa foi…" (ler do slide)
- Análise estática de **código e esquema de banco**
- Orientada pelo **Privacy by Design**
- Achar **indícios técnicos de risco** e apoiar a **LGPD**

**5. Objetivo e hipótese (0:30)**
- **Objetivo**: a ferramenta como extensão do VS Code + servidor local Python
- **Específicos**: revisar PbD/LGPD · comparar modelos de desenvolvimento · comparar ferramentas · definir requisitos · construir e avaliar
- **Hipótese**: antecipa os riscos, principalmente na **implementação**
- Achados = **indícios a revisar**, não conclusão jurídica

**6. Metodologia DSR (0:45)**
- Design Science Research: construir e avaliar um artefato
- 1 revisão e mapeamentos · 2 escopo técnico · 3 construção · 4 avaliação
- Projetos externos fixados por commit: tudo reproduzível

**7. Fundamentação teórica (0:05)**
- Transição

**8. Privacy by Design (0:50)**
- 7 princípios → **3 caixas** no slide
- **Apoio indireto**: Proativo
- **Apoio parcial**: Padrão · Incorporada · Funcionalidade · Ponta a ponta
- **Fora do escopo**: Transparência · Respeito ao usuário
- **Não certifica conformidade**

**9. Ferramentas correlatas (0:45)**
- Veracode, Checkmarx, Snyk, SonarQube, Semgrep, GitHub Code Scanning
- Comparação documental, não teste de desempenho
- Lacuna: local, simples, categorias de privacidade, LGPD, SQLite
- Complementar, não melhor

**10. Requisitos e tecnologias (0:05)**
- Transição

**11. Requisitos não funcionais (0:45)**
- 11 RF, 11 RNF, 14 regras (RF aparecem na demo)
- Local · evidência segura (não mostra CPF/senha) · estática
- Bruto separado do exibido (auditável)
- Todo relatório avisa: indício, não certificação

**12. Tecnologias e arquitetura (0:50)**
- Extensão TypeScript → HTTP → Flask em localhost
- Python: módulo ast · Java: léxico, sem compilar · SQLite: sqlite3
- Relatórios JSON, HTML e PDF (ReportLab)
- pytest com 208 testes, Git/GitHub
- Tudo na linha tracejada roda na máquina do dev

**13. Demo ao vivo (10:00)**
- Pronto antes: VS Code no repo, vsix 1.2.2, servidor ligado, perfil conservador, demo.py vazio
- Barra lateral: Ações rápidas, Achados, Resumo, status; Analisar agora (topo de Achados), Limpar resultados (Configuração e suporte)
- Python: 7 achados (5A 2M), indicador 40; Resumo com alvo e horário; hover, Problems, clicar e ir à linha, Quick Fix ver e copiar recomendação; exemplo_correto.py → 0 achados
- Java: 5 de 9, 55 vs 30; perfil completo mostra 9; ajustar regra, Limpar personalizações, Restaurar padrão; Ocultar e Restaurar achado
- SQLite clientes_demo.db: 12 brutos, 3 exibidos, 33 → 75; mistura de dados não dispara (limitação)
- Projeto inteiro: .privacyignore e contador de arquivos ignorados
- Ao salvar: CPF + print sem salvar → Resultado desatualizado; salvar → 2 altos, 80; corrigir → 0, 100; projeto e exportação pedem Salvar e analisar / Salvar e exportar
- Relatórios HTML, JSON, PDF; indicador 100 − 10A − 5M − 2B
- Configuração e suporte: Configurar dependências, Reiniciar backend, Abrir logs, configurações; também roda por CLI
- Falhou? Slides 19 a 27 ocultos (digitar número + Enter)

**14. Validação controlada (0:50)**
- 135 testes (1.0.4) → 208 (1.2.2), todos aprovados
- Extensão: testes TS, integração, instalação isolada do VSIX
- Benchmark: 18 casos, 120 decisões, zero divergência
- 100% = consistência contra regressão, não desempenho real

**15. Validação externa (1:15)**
- PEAK (Java) só para ajuste
- Flasky (Python) e Chinook (SQLite) com regras congeladas
- Precisão 39,6% · recall 48,7% · F1 43,7%
- Erros: heurísticas por nome (formulários, "Name" de catálogo, endereço)
- 1.1 e 1.2 corrigiram, sem novo corpus → triagem com revisão humana

**16. Uso no ciclo (0:45)**
- Condição técnica: existir código ou esquema
- Requisitos: preparar perfil · implementação: execução principal · repetir em revisão, testes, CI
- Cascata antes dos testes · espiral cada ciclo · Scrum na DoD · DevSecOps na esteira
- Indicador não bloqueia entrega sozinho

**17. Considerações finais (1:10)**
- Objetivos atendidos no recorte; hipótese com apoio parcial
- Funciona e é reproduzível; eficácia real limitada
- Limites: Java léxico, nomes de campos, indicador não calibrado, 1 revisor, sem estudo com usuários
- Futuro: nova validação 1.2.2 com 2 revisores, Java semântico, JS/TS, PostgreSQL/MySQL, perfis com equipes

**18. Obrigado (0:30)**
- Código, benchmark, gabarito e scripts no GitHub
- Abrir para perguntas

## Perguntas prováveis

- **Muito falso positivo?** Regras sintáticas e locais; mantive sem ajuste para expor o limite
- **Pesos do indicador?** Heurísticos, para prioridade; não é risco jurídico
- **Java limitado?** Léxico, sem fluxo entre controller, service e repositório
- **Prova conformidade?** Não: base legal e finalidade não saem do código
- **Semgrep/Veracode?** Segurança ampla; aqui é privacidade, LGPD e SQLite. Complementar
- **Por que PEAK de ajuste?** Separar ajuste e validação evita mexer depois de ver o resultado
- **Maior ameaça?** Corpus pequeno e um revisor

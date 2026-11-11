# Colinha da defesa: Privacy Scanner LGPD 1.2.2

Total: cerca de 21 min. Demo: 10 min no slide 12. Reserva: slides 18 a 26 ocultos (digitar o número e apertar Enter).

## 1. Capa (0:30 · 0:30)
- Boa noite; agradecer a banca e o Prof. Adilson
- Privacy Scanner LGPD: análise estática de Python, Java e SQLite
- Roda como extensão do VS Code

## 2. Roteiro (0:15 · 0:45)
- Introdução → fundamentação → requisitos e tecnologias
- **Maior parte: demo ao vivo**
- Avaliação → considerações finais

## 3. Contexto e problema (1:00 · 1:45)
- LGPD art. 46: medidas técnicas **desde a concepção**
- Art. 52: multa até **2% do faturamento**, teto **R$ 50 mi** por infração
- **163 incidentes** comunicados à ANPD no 1º sem. de 2023
- Problema: transformar princípio em algo que o dev revise no dia a dia
- SAST de mercado foca segurança e qualidade, não privacidade
- Público: equipes de dev, inclusive sem especialista em privacidade

## 4. Pergunta, objetivo e hipótese (1:00 · 2:45)
- Pergunta: como a análise estática orientada ao PbD ajuda a achar indícios de risco e apoia a LGPD
- Objetivo: extensão VS Code + servidor local Python
- Específicos: PbD/LGPD · modelos de SDLC · ferramentas · requisitos · construir e avaliar
- Hipótese: antecipa riscos na implementação
- **Achado = indício, não conclusão jurídica**

## 5. Metodologia DSR (0:45 · 3:30)
- Design Science Research: construir e avaliar um artefato
- 1 revisão e mapeamentos · 2 escopo técnico · 3 construção · 4 avaliação
- Benchmark + validação externa com projetos fixados por commit
- **Tudo reproduzível a partir do repositório**

## 6. Fundamentação teórica (0:05 · 3:35)
- Só transição

## 7. Privacy by Design (0:50 · 4:25)
- 7 princípios da Cavoukian
- **Parcial:** privacidade como padrão, segurança de ponta a ponta
- **Indireto:** proativo (revisão antes da entrega)
- **Fora:** transparência e respeito ao usuário
- Organiza evidência técnica, **não certifica conformidade**

## 8. Ferramentas correlatas (0:45 · 5:10)
- Veracode, Checkmarx, Snyk, SonarQube, Semgrep, GitHub Code Scanning
- Comparação **documental**, não teste de desempenho
- Lacuna: local, simples, categorias de privacidade, LGPD, SQLite
- **Complementar, não melhor**

## 9. Requisitos e tecnologias (0:05 · 5:15)
- Só transição

## 10. Requisitos não funcionais (0:45 · 6:00)
- **11 RF · 11 RNF · 14 regras** (os RF aparecem na demo)
- Local · evidência segura (não mostra CPF/senha) · estática (nunca executa)
- Bruto separado do exibido → auditável
- Todo relatório avisa: indício, não certificação

## 11. Tecnologias e arquitetura (0:50 · 6:50)
- Extensão TypeScript → HTTP → Flask em **localhost**: código não sai da máquina
- Python: `ast` · Java: léxico, sem compilar · SQLite: `sqlite3`
- Relatórios JSON, HTML e PDF (ReportLab)
- pytest com **208 testes** · Git/GitHub
- Tudo dentro da linha tracejada roda na máquina do dev

## 12. Demo ao vivo (10:00 · 16:50)
**Antes de começar:** VS Code no repo · VSIX 1.2.2 · backend ligado · perfil conservador · `demo.py` vazio

1. **Barra lateral (0:45)**
   - Ações rápidas, Achados, Resumo; estado na barra de status
   - "Analisar agora": ícone no topo de **Achados**
   - "Limpar resultados": em **Configuração e suporte**
   - Tudo local; o código nunca é executado
2. **Python (1:30)**: `examples/vulnerable/cadastro_clientes_vulneravel.py`
   - **7 achados (5A 2M), indicador 40**
   - Sublinhado + mouse (regra, confiança, artigo, recomendação) + Problems
   - Clicar no achado → pula para a linha
   - Quick Fix → Copiar recomendação
   - Evidência não mostra CPF nem senha
3. **Java e perfis (1:45)**: `ProntuarioVulneravel.java`
   - Conservador: **5 de 9**, indicador **55 exibido vs 30 bruto**
   - Configurar perfil → **Completo** → 9
   - Ajustar uma regra · Limpar personalizações · Restaurar padrão conservador
   - Citar Selecionar perfil e Validar perfil · voltar ao conservador
   - Ocultar achado → resumo mantém o bruto → Restaurar achados ocultados
4. **SQLite (1:15)**: `clientes_demo.db`
   - **12 brutos, 3 exibidos · 33 → 75**
   - CPF como PK · e-mail em índice único · campos sem hash
   - Limitação: MISTURA_DADOS não dispara (depende do nome das colunas)
5. **Projeto inteiro (0:45)**
   - Respeita o `.privacyignore`
   - Mostrar o contador de arquivos ignorados no Resumo
6. **Ao salvar (1:30)**: `demo.py`
   - `cpf = "123.456.789-00"` + `print(cpf)` → salvar → **2 altos, 80**
   - Trocar por `print("Operação concluída")` → **0 achados, 100**
   - É caso conhecido: mostra o fluxo, não prova eficácia
7. **Relatórios (1:45)**
   - Exportar HTML: aviso de limite, totais exibido/bruto/oculto, indicador
   - Mostrar rapidamente JSON e PDF
   - **I = 100 − 10A − 5M − 2B**: não é % de conformidade nem probabilidade
8. **Backend (0:30)**
   - Configuração e suporte: **Configurar dependências · Reiniciar backend · Abrir logs · Abrir configurações**
   - Também roda por linha de comando
- **Se falhar:** slides 18 a 26

## 13. Validação controlada (0:50 · 17:40)
- **135 testes (1.0.4) → 208 (1.2.2)**, todos aprovados
- Extensão: testes TS, lint, integração no VS Code, instalação isolada do VSIX
- Benchmark: **18 casos, 120 decisões, zero divergência**
- 100% mede consistência contra regressão, **não desempenho real**

## 14. Validação externa (1:15 · 18:55)
- PEAK (Java): **só ajuste** (8 TP / 0 FP / 1 FN)
- Flasky (Python) e Chinook (SQLite) com regras **congeladas**
- **19 TP · 29 FP · 20 FN → precisão 39,6% · recall 48,7% · F1 43,7%**
- Erros vêm das heurísticas por nome:
  - formulário confundido com modelo
  - coluna "Name" de catálogo tratada como nome de pessoa
  - cidade e CEP sem contexto
- 1.1 e 1.2 corrigiram vários, sem novo corpus → **triagem com revisão humana**

## 15. Uso no ciclo (0:45 · 19:40)
- Condição técnica: **existir código ou esquema**
- Requisitos: preparar perfil · implementação: execução principal · repetir em revisão, testes, CI
- Cascata: antes dos testes · espiral: cada ciclo · Scrum: na DoD · DevSecOps: na esteira
- **Indicador não bloqueia entrega sozinho**

## 16. Considerações finais (1:10 · 20:50)
- Objetivos atendidos no recorte; **hipótese com apoio parcial**
- Funciona e é reproduzível; eficácia real limitada
- Limites:
  - Java só léxico
  - regras dependem do nome dos campos
  - indicador não calibrado
  - 1 revisor e nenhum estudo com usuários
- Futuro:
  - validação da 1.2.2 com 2 revisores
  - Java semântico
  - JS/TS e PostgreSQL/MySQL
  - perfis testados com equipes

## 17. Obrigado (0:30 · 21:20)
- Código, benchmark, gabarito e scripts no GitHub
- Abrir para perguntas

---

## Reserva (slides ocultos)
- **18 Riscos:**
  - criptografia fraca ou ausente
  - coleta e retenção excessiva
  - sem pseudonimização
  - dado em log
  - transferência sem base legal
  - controle de acesso **fora do escopo**
- **19 RF:** Python, Java, SQLite, exportação, achados no editor, perfis por pasta
- **20 Regras:** 7 de código + 7 de SQLite, cada uma com severidade-base e artigo da LGPD
- **21 Python:** 7 achados (5A 2M), indicador 40, evidência sem o dado
- **22 Java:** 9 achados (5A 4M), indicador 30 → conservador mostra 5, exibido 55
- **23 SQLite:** 12 brutos, 3 exibidos, 33 → 75; mistura não dispara
- **24 Indicador:** 100 − 10A − 5M − 2B (ex.: 1A + 2M = 80); pesos não calibrados; não compara projetos
- **25 Extensão:** sidebar, sublinhado + hover, assistente de perfil, análise ao salvar; sem estudo com usuários
- **26 Antes/depois:** CPF + print → 2 altos, 80 · mensagem fixa → 0, 100

## Respostas rápidas
- **Muito falso positivo?** Regras sintáticas e locais; mantive sem retuning para expor o limite.
- **Pesos do indicador?** Heurísticos, para prioridade; não é risco jurídico nem multa.
- **Por que Java limitado?** Léxico, sem fluxo entre controller, service e repositório.
- **Comprova conformidade?** Não. Base legal, finalidade e governança não saem do código.
- **E Semgrep ou Veracode?** Cobertura ampla de segurança; aqui o foco é privacidade, LGPD e SQLite. É complementar.
- **Por que PEAK de ajuste?** Separar ajuste e validação evita mexer nas regras depois de ver o resultado.
- **Maior ameaça à validade?** Corpus pequeno e um único revisor.

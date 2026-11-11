# Roteiro da defesa — Privacy Scanner LGPD 1.2.2

Apresentação: `output/presentation/TCC_Privacy_by_Design_Banca.pptx` (17 slides visíveis, cerca de 21 min, com demonstração ao vivo de 10 min no slide 12; slides 18 a 26 ocultos como reserva). A mesma fala está nas anotações do apresentador.

## Colinha (tópicos por slide)

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

**4. Pergunta, objetivo e hipótese (1:00)**
- Pergunta: como análise estática orientada ao PbD ajuda a achar indícios de risco
- Objetivo: extensão VS Code + servidor local Python
- Específicos: PbD/LGPD, modelos de SDLC, ferramentas, requisitos, construir e avaliar
- Hipótese: antecipa riscos na implementação; achado é indício, não conclusão jurídica

**5. Metodologia DSR (0:45)**
- Design Science Research: construir e avaliar um artefato
- 1 revisão e mapeamentos · 2 escopo técnico · 3 construção · 4 avaliação
- Projetos externos fixados por commit: tudo reproduzível

**6. Fundamentação teórica (0:05)**
- Transição

**7. Privacy by Design (0:50)**
- 7 princípios da Cavoukian
- Parcial: privacidade como padrão, segurança de ponta a ponta
- Indireto: proativo (revisão antes da entrega)
- Fora: transparência e respeito ao usuário
- Não certifica conformidade

**8. Ferramentas correlatas (0:45)**
- Veracode, Checkmarx, Snyk, SonarQube, Semgrep, GitHub Code Scanning
- Comparação documental, não teste de desempenho
- Lacuna: local, simples, categorias de privacidade, LGPD, SQLite
- Complementar, não melhor

**9. Requisitos e tecnologias (0:05)**
- Transição

**10. Requisitos não funcionais (0:45)**
- 11 RF, 11 RNF, 14 regras (RF aparecem na demo)
- Local · evidência segura (não mostra CPF/senha) · estática
- Bruto separado do exibido (auditável)
- Todo relatório avisa: indício, não certificação

**11. Tecnologias e arquitetura (0:50)**
- Extensão TypeScript → HTTP → Flask em localhost
- Python: módulo ast · Java: léxico, sem compilar · SQLite: sqlite3
- Relatórios JSON, HTML e PDF (ReportLab)
- pytest com 208 testes, Git/GitHub
- Tudo na linha tracejada roda na máquina do dev

**12. Demo ao vivo (10:00)**
- Pronto antes: VS Code no repo, vsix 1.2.2, servidor ligado, perfil conservador, demo.py vazio
- Barra lateral: Ações rápidas, Achados, Resumo, status; Analisar agora (topo de Achados), Limpar resultados (Configuração e suporte)
- Python: 7 achados (5A 2M), indicador 40; Resumo com alvo e horário; hover, Problems, clicar e ir à linha, Quick Fix ver e copiar recomendação; exemplo_correto.py → 0 achados
- Java: 5 de 9, 55 vs 30; perfil completo mostra 9; ajustar regra, Limpar personalizações, Restaurar padrão; Ocultar e Restaurar achado
- SQLite clientes_demo.db: 12 brutos, 3 exibidos, 33 → 75; mistura de dados não dispara (limitação)
- Projeto inteiro: .privacyignore e contador de arquivos ignorados
- Ao salvar: CPF + print sem salvar → Resultado desatualizado; salvar → 2 altos, 80; corrigir → 0, 100; projeto e exportação pedem Salvar e analisar / Salvar e exportar
- Relatórios HTML, JSON, PDF; indicador 100 − 10A − 5M − 2B
- Configuração e suporte: Configurar dependências, Reiniciar backend, Abrir logs, configurações; também roda por CLI
- Falhou? Slides 18 a 26 ocultos (digitar número + Enter)

**13. Validação controlada (0:50)**
- 135 testes (1.0.4) → 208 (1.2.2), todos aprovados
- Extensão: testes TS, integração, instalação isolada do VSIX
- Benchmark: 18 casos, 120 decisões, zero divergência
- 100% = consistência contra regressão, não desempenho real

**14. Validação externa (1:15)**
- PEAK (Java) só para ajuste
- Flasky (Python) e Chinook (SQLite) com regras congeladas
- Precisão 39,6% · recall 48,7% · F1 43,7%
- Erros: heurísticas por nome (formulários, "Name" de catálogo, endereço)
- 1.1 e 1.2 corrigiram, sem novo corpus → triagem com revisão humana

**15. Uso no ciclo (0:45)**
- Condição técnica: existir código ou esquema
- Requisitos: preparar perfil · implementação: execução principal · repetir em revisão, testes, CI
- Cascata antes dos testes · espiral cada ciclo · Scrum na DoD · DevSecOps na esteira
- Indicador não bloqueia entrega sozinho

**16. Considerações finais (1:10)**
- Objetivos atendidos no recorte; hipótese com apoio parcial
- Funciona e é reproduzível; eficácia real limitada
- Limites: Java léxico, nomes de campos, indicador não calibrado, 1 revisor, sem estudo com usuários
- Futuro: nova validação 1.2.2 com 2 revisores, Java semântico, JS/TS, PostgreSQL/MySQL, perfis com equipes

**17. Obrigado (0:30)**
- Código, benchmark, gabarito e scripts no GitHub
- Abrir para perguntas

## Fala completa por slide

### Slide 1: Privacy by design no ciclo de desenvolvimento de software

*0:30 | acumulado 0:30*

Boa noite a todos. Agradeço a presença da banca e ao meu orientador, Prof. Adilson.

Meu trabalho se chama "Privacy by Design no Ciclo de Desenvolvimento de Software". Nele eu desenvolvi o Privacy Scanner LGPD, uma ferramenta de análise estática que procura indícios técnicos de risco à privacidade em código Python, Java e em esquemas de banco SQLite, e que roda como extensão do VS Code.

### Slide 2: Roteiro de apresentação

*0:15 | acumulado 0:45*

Vou seguir este roteiro: introdução, fundamentação teórica, requisitos e tecnologias, e então a maior parte do tempo vai para a demonstração ao vivo da ferramenta. Depois, a avaliação e as considerações finais.

### Slide 3: Contexto e problema

*1:00 | acumulado 1:45*

O ponto de partida é a LGPD. O artigo 46 diz que os agentes de tratamento devem adotar medidas técnicas e administrativas para proteger dados pessoais desde a fase de concepção do produto. Ou seja, privacidade não é só política: ela precisa aparecer no software.

O descumprimento tem consequência: o artigo 52 prevê multa de até 2% do faturamento, limitada a 50 milhões de reais por infração. E incidentes acontecem: só no primeiro semestre de 2023, a ANPD recebeu 163 comunicações de incidentes.

O problema que eu tratei é de operacionalização: como transformar esses princípios em algo que o desenvolvedor consiga revisar no dia a dia. As ferramentas de análise estática de mercado focam em segurança e qualidade, e não trazem esse recorte de privacidade já organizado. O público-alvo são equipes de desenvolvimento, inclusive as que não têm um especialista em privacidade.

### Slide 4: Pergunta, objetivo e hipótese

*1:00 | acumulado 2:45*

A pergunta que guiou a pesquisa foi: de que forma uma ferramenta de análise estática de código e de esquemas de banco, orientada pelo Privacy by Design, pode contribuir para identificar indícios técnicos de risco à privacidade e apoiar a adequação à LGPD?

O objetivo geral foi desenvolver essa ferramenta, distribuída como extensão do VS Code e apoiada por um servidor local em Python.

Os objetivos específicos foram: revisar os fundamentos do Privacy by Design e da LGPD; comparar modelos de desenvolvimento para saber em que etapa usar a ferramenta; comparar ferramentas existentes; definir tecnologias e requisitos; e desenvolver e avaliar a ferramenta.

A hipótese é que ela ajuda a antecipar a identificação desses riscos, principalmente na implementação, desde que os achados sejam lidos como indícios a revisar, e não como conclusão jurídica.

### Slide 5: Metodologia: design science research

*0:45 | acumulado 3:30*

Como método usei a Design Science Research, que é próprio de Sistemas de Informação: a gente produz conhecimento construindo um artefato e avaliando esse artefato.

Foram quatro fases. Primeiro, revisão da literatura e dois mapeamentos documentais: modelos de desenvolvimento e ferramentas de mercado. Segundo, definição do escopo técnico: tecnologias, requisitos e regras. Terceiro, a construção da ferramenta. E quarto, a avaliação, com um benchmark controlado e uma validação externa em projetos públicos fixados por commit, para que tudo possa ser reproduzido a partir do repositório.

### Slide 6: Fundamentação teórica

*0:05 | acumulado 3:35*

Passo agora para a fundamentação teórica.

### Slide 7: Privacy by design

*0:50 | acumulado 4:25*

O Privacy by Design, sistematizado pela Ann Cavoukian, tem sete princípios. Uma preocupação do trabalho foi deixar claro o que a ferramenta cobre e o que ela não cobre.

Ela apoia parcialmente a privacidade como padrão e a segurança de ponta a ponta, porque tem regras de minimização, proteção, retenção e logs. Apoia indiretamente o princípio proativo, porque leva a revisão para antes da entrega. Já transparência e respeito ao usuário estão fora do escopo: isso não dá para verificar só olhando o código.

Por isso, em todo o trabalho e nos próprios relatórios, a ferramenta deixa explícito que organiza evidências técnicas e não certifica conformidade com a LGPD.

### Slide 8: Ferramentas correlatas

*0:45 | acumulado 5:10*

Comparei documentalmente seis ferramentas: Veracode, Checkmarx, Snyk Code, SonarQube, Semgrep e GitHub Code Scanning. Foi uma comparação pela documentação pública, não um teste de desempenho.

Essas ferramentas são focadas em segurança de aplicação e qualidade. Algumas, como o Semgrep, até permitem criar regras próprias de privacidade. A lacuna que identifiquei é de recorte: uma ferramenta simples, local, que já venha com categorias de privacidade organizadas, relatórios ligados à LGPD e inspeção de esquema SQLite.

Então eu não afirmo que a minha ferramenta é melhor que essas. Ela é complementar.

### Slide 9: Requisitos e tecnologias

*0:05 | acumulado 5:15*

Com essa base, defini os requisitos e as tecnologias da ferramenta.

### Slide 10: Requisitos não funcionais

*0:45 | acumulado 6:00*

Defini 11 requisitos funcionais, 11 não funcionais e 14 regras de detecção; os funcionais vocês vão ver funcionando na demonstração.

Destaco os não funcionais ligados à própria privacidade: a análise é local; o relatório nunca reproduz o CPF ou a senha encontrados, só descreve a evidência; a análise é estática; o resultado bruto é preservado separado do que o perfil exibe, para ser auditável; e todo relatório avisa que são indícios, não certificação.

### Slide 11: Tecnologias e arquitetura

*0:50 | acumulado 6:50*

Esta é a arquitetura. O desenvolvedor trabalha no VS Code; a extensão, escrita em TypeScript, envia as solicitações por HTTP para um servidor local em Python com Flask, que roda em localhost. Ou seja, o código analisado nunca sai da máquina, o que é coerente com o tema de privacidade.

O servidor aciona três analisadores: o de Python usa o módulo ast, que lê a árvore sintática sem executar o código; o de Java é uma análise léxica conservadora, para não exigir compilador; e o de esquema lê o banco SQLite pelo sqlite3. No fim, o gerador produz relatórios em JSON, HTML e PDF, este último com ReportLab.

Embaixo estão as ferramentas de qualidade: pytest para os 208 testes, Git e GitHub para versionar código, regras e benchmark. Tudo o que está dentro da linha tracejada roda na máquina do desenvolvedor.

### Slide 12: Apresentação do sistema

*10:00 | acumulado 16:50*

DEMONSTRAÇÃO AO VIVO (cerca de 10 minutos). Antes da banca, deixe pronto: o VS Code aberto na pasta do repositório, a extensão 1.2.2 instalada pelo VSIX, o servidor local já iniciado, o perfil conservador e um arquivo demo.py vazio.

1. Barra lateral (0:45): mostrar Ações rápidas, Achados e Resumo, e o perfil e o estado do servidor na barra de status; Analisar agora é o ícone no topo da lista Achados e Limpar resultados fica em Configuração e suporte. Falar: tudo roda na máquina, em localhost; o código analisado não é enviado a ninguém e nunca é executado.
2. Python (1:45): abrir examples/vulnerable/cadastro_clientes_vulneravel.py e analisar o arquivo. São 7 achados, 5 altos e 2 médios, indicador 40; no Resumo, mostrar o alvo da análise e o horário em que ela foi feita. Mostrar as linhas sublinhadas, passar o mouse num achado (regra, confiança, artigo da LGPD e recomendação) e o painel Problems. Clicar num achado na barra lateral e mostrar que o editor pula para a linha. Na lâmpada (Quick Fix), mostrar Ver recomendação LGPD e Copiar recomendação. Mostrar que a evidência não reproduz o CPF nem a senha. Para contraste, abrir exemplo_correto.py e analisar: 0 achados (hash forte, método de exclusão e log sem dado pessoal).
3. Java, perfis e ocultar (1:45): abrir examples/vulnerable/ProntuarioVulneravel.java e analisar. No perfil conservador aparecem 5 dos 9 achados, indicador exibido 55 contra 30 bruto. Abrir Configurar perfil, trocar para completo e mostrar os 9. Ainda no assistente, ajustar uma regra (confiança mínima ou severidade), mostrar Limpar personalizações e Restaurar padrão conservador; citar Selecionar perfil e Validar perfil para quem prefere editar o JSON. Voltar para o conservador. Depois, clicar com o botão direito num achado, Ocultar achado na interface, e mostrar que o resumo continua contando o total bruto; em seguida, Restaurar achados ocultados.
4. SQLite (1:15): Analisar banco SQLite e escolher examples/vulnerable/clientes_demo.db. São 12 achados brutos e 3 exibidos (indicador 33 para 75): CPF como chave primária, e-mail em índice único e campos pessoais sem hash. Falar a limitação: a regra de mistura de dados não disparou porque depende dos nomes das colunas.
5. Projeto inteiro (0:45): Analisar projeto inteiro. Mostrar que ele percorre a pasta e respeita o arquivo .privacyignore, que exclui dependências, testes e exemplos; no Resumo, apontar o contador de arquivos ignorados.
6. Corrigir e reanalisar ao salvar (1:30): com a análise automática ao salvar ligada, digitar no demo.py cpf = "123.456.789-00" e print(cpf) sem salvar: o Resumo avisa Resultado desatualizado, porque a análise usa a versão salva em disco. Salvar: 2 achados altos, indicador 80, sem clicar em nada. Apagar o literal, deixar print("Operação concluída") e salvar: 0 achados, indicador 100. Comentar que Analisar projeto inteiro e Exportar relatório perguntam antes quando há arquivos não salvos (Salvar e analisar, Salvar e exportar). Lembrar que é um caso conhecido: mostra o fluxo, não prova eficácia em projetos reais.
7. Relatórios e indicador (1:30): Exportar relatório em HTML e abrir o painel (aviso de limite, totais exibido, bruto e oculto, indicador); mostrar rapidamente que também exporta JSON e PDF. Explicar o indicador: parte de 100 e desconta 10 por alto, 5 por médio e 2 por baixo; não é porcentagem de conformidade nem probabilidade de incidente.
8. Servidor local (0:30): mostrar no menu Configurar dependências, Reiniciar backend e Abrir logs, abrir rapidamente as configurações da extensão (porta, timeout, análise ao salvar, Python e diagnósticos), e dizer que a ferramenta também roda pela linha de comando com resumo no terminal. Voltar para os slides.

Se algo falhar ou a banca perguntar: os slides 18 a 26 estão ocultos no fim (riscos, requisitos funcionais, regras, cada módulo, relatórios, extensão e antes/depois). Para abrir um deles, digite o número do slide e aperte Enter.

### Slide 13: Validação controlada

*0:50 | acumulado 17:40*

A avaliação teve duas partes. A primeira é a validação controlada. A suíte automatizada cresceu de 135 testes na versão 1.0.4 para 208 na 1.2.2, todos aprovados. A extensão também passou por testes em TypeScript, integração real dentro do VS Code e instalação isolada do pacote.

O benchmark tem 18 casos sintéticos, seis para cada analisador, o que dá 120 decisões caso–categoria. Executado com a versão 1.2.0, ele não teve nenhuma divergência do gabarito.

Mas atenção: esses casos foram feitos para exercitar regras conhecidas. Esse 100% mede consistência e serve para pegar regressões; não mede desempenho em projetos reais. Por isso a segunda parte é a validação externa.

### Slide 14: Validação externa

*1:15 | acumulado 18:55*

Na validação externa, usei projetos públicos fixados por commit. Para não "treinar" a ferramenta com os mesmos dados que avaliam, o back-end Java do PEAK foi usado só como conjunto de ajuste; Flasky, em Python, e Chinook, em SQLite, foram avaliados depois das regras congeladas.

O resultado foi bem diferente do benchmark: nos dois projetos independentes, a precisão foi de 39,6%, o recall de 48,7% e o F1 de 43,7%. Eu apresento esses números sem esconder, porque eles são o resultado mais importante para entender o limite da ferramenta.

Os erros vieram principalmente das heurísticas por nome: formulários confundidos com modelos, colunas "Name" de catálogo de músicas tratadas como nome de pessoa, e endereço sem contexto não reconhecido. As versões 1.1 e 1.2 corrigiram vários desses padrões, mas ainda não passaram por um novo corpus independente. Então a conclusão é: a ferramenta serve para triagem, com revisão humana.

### Slide 15: Uso no ciclo de desenvolvimento

*0:45 | acumulado 19:40*

Um dos objetivos era definir em que etapa do ciclo de desenvolvimento usar a ferramenta. Comparando cascata, espiral, Scrum e DevSecOps, a conclusão é que, apesar dos nomes diferentes, a condição técnica é a mesma: precisa existir código ou esquema.

Então, em requisitos e modelagem a equipe só prepara o perfil, os dados e a retenção. A execução principal é na implementação. E ela deve ser repetida na revisão de código, nos testes, na integração e na evolução.

Na cascata, antes do marco de testes; na espiral, em cada ciclo; no Scrum, pode entrar na Definition of Done; e no DevSecOps, na esteira de integração. Mas, pelos números da validação externa, o indicador não deve bloquear entrega sozinho.

### Slide 16: Considerações finais

*1:10 | acumulado 20:50*

Para concluir: os objetivos foram atendidos no recorte definido, e a hipótese tem apoio parcial. O artefato funciona, é reproduzível e consistente nos cenários testados, mas a validação externa mostrou que a eficácia em projetos reais ainda é limitada. Ele apoia uma triagem preventiva de privacidade no ambiente do desenvolvedor, sem substituir a análise jurídica nem a revisão humana.

As principais limitações são: o suporte Java é só léxico; as regras dependem de nomes de campos; o indicador não foi calibrado; e a avaliação teve um revisor principal e nenhum estudo com usuários.

Como trabalhos futuros: uma nova validação externa da versão 1.2.2 com dois revisores independentes, análise semântica para Java, suporte a JavaScript e TypeScript, PostgreSQL e MySQL, e avaliação dos perfis com equipes reais.

### Slide 17: Obrigado

*0:30 | acumulado 21:20*

Muito obrigado pela atenção. O código, o benchmark, o gabarito e os scripts de avaliação estão todos no repositório do GitHub. Fico à disposição para as perguntas da banca.

### Slide 18 (oculto): Riscos de privacidade

*0:00 | acumulado 21:20*

RESERVA (slide oculto): use para responder perguntas da banca ou se a demonstração ao vivo falhar.

Na fundamentação, levantei os principais tipos de risco de privacidade que deixam rastro no código ou no esquema do banco.

Proteção criptográfica não evidenciada, como senha sem hash ou uso de MD5 e SHA-1. Coleta e retenção excessiva, que fere o princípio da necessidade. Ausência de pseudonimização. Dados pessoais em logs. E transferência de dados a terceiros sem base legal.

Controle de acesso também foi discutido, mas deixei claro no texto que ele está fora do que o scanner verifica. Importante: a ausência de evidência no trecho analisado é um ponto de revisão, não prova de que o controle não existe em outra camada.

### Slide 19 (oculto): Requisitos funcionais

*0:00 | acumulado 21:20*

RESERVA (slide oculto): use para responder perguntas da banca ou se a demonstração ao vivo falhar.

A partir da fundamentação, defini 11 requisitos funcionais, 11 não funcionais e 14 regras de detecção.

Nos funcionais, destaco a análise de Python, Java e do esquema SQLite, a exportação dos relatórios, a exibição dos achados no editor e os perfis de análise por pasta.

### Slide 20 (oculto): Regras de detecção

*0:00 | acumulado 21:20*

RESERVA (slide oculto): use para responder perguntas da banca ou se a demonstração ao vivo falhar.

As regras se dividem em sete para código Python e Java, como dado pessoal fixo no código, criptografia fraca, dado em log e transferência sem base legal; e sete para esquema SQLite, como campo sensível sem hash, CPF como chave primária e ausência de retenção. Cada regra tem severidade-base e referência potencial a um artigo da LGPD.

### Slide 21 (oculto): Módulo de análise python

*0:00 | acumulado 21:20*

RESERVA (slide oculto): use para responder perguntas da banca ou se a demonstração ao vivo falhar.

Começando pelo Python: analisei um arquivo propositalmente vulnerável, com dados fictícios: tem CPF e senha fixos no código, SHA-1 aplicado ao CPF, um log com e-mail e CPF, envio de sete campos pessoais para um serviço externo e uma classe sem método de exclusão.

A ferramenta encontrou sete achados: cinco altos e dois médios, e o indicador técnico ficou em 40.

Cada linha do relatório mostra severidade, categoria, local, artigo da LGPD relacionado, descrição e recomendação. E repare na coluna de evidência: ela explica o motivo sem mostrar o CPF ou a senha.

### Slide 22 (oculto): Módulo de análise java

*0:00 | acumulado 21:20*

RESERVA (slide oculto): use para responder perguntas da banca ou se a demonstração ao vivo falhar.

O módulo Java usa as mesmas categorias do Python, mas com análise léxica, por padrões, sem compilar. Analisei um prontuário fictício e ele retornou nove achados, cinco altos e quatro médios, com indicador 30.

Aqui aparece um recurso importante: os perfis. Na extensão, com o perfil conservador, apareceram cinco dos nove achados; os outros quatro foram ocultados, e o indicador exibido subiu de 30 para 55.

Isso reduz o ruído para o desenvolvedor, mas sem esconder nada: o resumo sempre mostra o total bruto e quantos foram ocultados, e o achado pode ser recuperado. Essa separação entre bruto e exibido foi uma decisão de auditabilidade.

### Slide 23 (oculto): Módulo de análise de esquemas sqlite

*0:00 | acumulado 21:20*

RESERVA (slide oculto): use para responder perguntas da banca ou se a demonstração ao vivo falhar.

O terceiro módulo olha o esquema do banco. Criei um banco SQLite vazio com essa tabela de clientes: CPF como chave primária, e-mail único, senha, telefone, endereço, misturados com dados do pedido.

Foram doze achados: sete campos pessoais sem indicação de proteção, CPF como chave primária, e-mail em índice único, falta de exclusão lógica, de registro de consentimento e de retenção. Com o perfil conservador, a extensão mostrou os três mais graves, e o indicador foi de 33 para 75.

Um ponto honesto: a regra de mistura de dados não disparou, porque só reconheceu uma coluna operacional pelo nome. Isso mostra que as regras dependem da nomenclatura, e isso aparece de novo na validação externa.

### Slide 24 (oculto): Relatórios e indicador técnico

*0:00 | acumulado 21:20*

RESERVA (slide oculto): use para responder perguntas da banca ou se a demonstração ao vivo falhar.

Os resultados saem em quatro formatos: resumo no terminal, JSON, HTML e PDF. O painel do HTML mostra o aviso de limite da análise, os totais exibido, bruto e oculto, a contagem por severidade e o indicador.

O indicador parte de 100 e desconta 10 por achado alto, 5 por médio e 2 por baixo, com mínimo zero. Por exemplo, um alto e dois médios dão 80.

E eu faço questão de dizer o que ele não é: não é porcentagem de conformidade, não é probabilidade de incidente e não serve para comparar projetos de tamanhos diferentes. Os pesos são operacionais, não foram calibrados empiricamente. Ele serve para acompanhar a evolução de um mesmo escopo.

### Slide 25 (oculto): Extensão para o vs code

*0:00 | acumulado 21:20*

RESERVA (slide oculto): use para responder perguntas da banca ou se a demonstração ao vivo falhar.

Esta é a extensão instalada a partir do pacote VSIX da versão 1.2.2. À esquerda, a barra lateral com Ações rápidas, Achados e Resumo. No editor, as linhas com problema ficam sublinhadas e, passando o mouse, aparece a regra, a confiança e a recomendação. Embaixo, o painel de problemas do próprio VS Code.

Tudo é acessível por cliques, sem depender da paleta de comandos. Tem um assistente para configurar o perfil por pasta e a opção de analisar automaticamente ao salvar.

A ideia é aproximar a revisão de privacidade do momento em que o código é escrito. Vale dizer: não fiz estudo com usuários, então a facilidade de uso é uma intenção de projeto, não algo medido.

### Slide 26 (oculto): Demonstração: antes e depois

*0:00 | acumulado 21:20*

RESERVA (slide oculto): use para responder perguntas da banca ou se a demonstração ao vivo falhar.

Para mostrar o ciclo completo, fiz uma demonstração reproduzível, que está no repositório como script.

Antes: um código mínimo com um CPF fictício fixo no código e um print desse CPF. A ferramenta acusa dois achados altos: dado fixo no código, na linha 1, e dado em log, na linha 2. Indicador 80.

A correção é simples: o CPF não era necessário para a mensagem, então removi o literal e deixei só a mensagem operacional. Depois de salvar e analisar de novo, os achados vão a zero e o indicador a 100. Os relatórios HTML, JSON e PDF batem em cada etapa.

É só um caso conhecido: isso demonstra o fluxo, não prova eficácia em projetos reais, nem que não existem outros riscos quando não há alertas.


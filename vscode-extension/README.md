# Privacy Scanner LGPD - Extensão VS Code

## Ajustes da versão 1.2.2

- O resumo identifica o alvo e o horário da análise e avisa quando ficou
  desatualizado após uma edição ou mudança nos achados de um arquivo.
- Análises automáticas aguardam o salvamento; respostas de uma versão anterior
  do documento são descartadas quando ele muda durante a requisição.
- Analisar o projeto ou exportar oferece salvar os arquivos Python/Java
  modificados do escopo escolhido ou cancelar. Arquivos de outras pastas
  permanecem como estão.
- A exportação identifica que realiza uma nova análise e preserva os totais
  brutos, os filtros e as severidades originais para auditoria.
- Perfis inválidos retornam mensagem estruturada. As recomendações de
  eliminação distinguem as hipóteses legais e os limites da exclusão lógica.

Extensão do VS Code para executar o Privacy Scanner LGPD durante o desenvolvimento.

A extensão conversa com o servidor Flask do projeto e exibe os resultados dentro do VS Code, sem executar o código analisado.

## Recursos Implementados

- Análise de arquivo Python.
- Análise de arquivo Java com sete categorias de privacidade.
- Análise de projeto inteiro.
- Análise de banco SQLite (`.db`, `.sqlite`, `.sqlite3`).
- Diagnósticos no editor e no painel `Problems`.
- Sidebar com ações rápidas e achados técnicos agrupados por risco.
- Sidebar com indicador técnico e resumo canônico fornecido pelo backend.
- Estado de carregamento durante a análise.
- Cancelamento de requisições antigas, timeout e proteção contra respostas fora de ordem.
- Botão/comando `Analisar agora`.
- Code Actions com recomendações LGPD.
- Exportação HTML.
- Exportação PDF.
- Exportação JSON por comando específico.
- Janela do Windows para escolher nome e destino do relatório.
- Inicialização automática do servidor Flask.
- Reutilização do servidor Flask caso ele já esteja ativo na porta configurada.
- Opção de ocultar uma ocorrência na interface sem removê-la dos relatórios.
- Botão no título do editor e menus de contexto para Python, Java e SQLite.
- Recuperação clicável para falhas de Python, dependências, backend e perfil.

## Pré-requisitos

- VS Code 1.85 ou superior (Extension Host com Node 18).
- Python 3.8 ou superior.
- Node.js e npm.
- Dependências Python instaladas na raiz do projeto.
- Dependências Node instaladas em `vscode-extension`.

Na raiz do projeto:

```powershell
python -m pip install -r requirements.txt
```

Na pasta da extensão:

```powershell
cd vscode-extension
npm install
npm run compile
```

## Rodar em Desenvolvimento

1. Abra a pasta `TCC` no VS Code.
2. Pressione `F5`.
3. Aguarde abrir a janela `[Extension Development Host]`.
4. Na nova janela, abra uma pasta de teste ou um arquivo Python.
5. Clique no ícone `Privacy Scanner` da barra de atividades e use
   `Ações rápidas`.

Se quiser recriar o workspace externo de teste:

```powershell
python scripts/create_test_workspace.py
```

## Fluxo Clicável

Abra a sidebar `Privacy Scanner`. Em `Ações rápidas`, estão disponíveis:

- `Analisar arquivo atual`, mostrando o nome do arquivo ativo;
- `Analisar projeto inteiro`;
- `Selecionar e analisar banco SQLite`;
- `Exportar relatório`, para HTML, PDF ou JSON;
- `Configurar perfil`, mostrando o preset ativo;
- `Configuração e suporte`, grupo recolhido que mostra o estado do backend.

O grupo de suporte contém as ações para limpar resultados, restaurar achados
ocultados, configurar dependências, reiniciar o backend, abrir logs e abrir
configurações.

Outros pontos de acesso:

- botão no título e menu de contexto do editor para Python e Java;
- menu de contexto do Explorer para arquivos `.py`, `.java`, `.db`, `.sqlite`
  e `.sqlite3`;
- item da barra de status, que abre a sidebar.

Na primeira ativação após a introdução da sidebar na 1.1.1, uma única
notificação oferece `Abrir painel`. A atualização para 1.2.0 não repete esse
aviso para quem já o recebeu.
Ela não abre a sidebar automaticamente e não aparece quando
`privacy-scanner.enableSidebar` está desativado.

Erros conhecidos oferecem a próxima ação no próprio aviso: abrir configurações
para Python ausente; `Configurar agora` e `Abrir logs` para
dependências ausentes; `Reiniciar` e `Abrir logs` para backend indisponível; e
`Abrir perfil` para configuração de perfil inválida.

## Paleta de Comandos

A Paleta (`Ctrl+Shift+P`) continua como alternativa com os IDs existentes:

- `Privacy Scanner: Analisar agora`
- `Privacy Scanner: Analisar arquivo`
- `Privacy Scanner: Analisar projeto inteiro`
- `Privacy Scanner: Analisar banco SQLite`
- `Privacy Scanner: Limpar resultados`
- `Privacy Scanner: Exportar relatorio`
- `Privacy Scanner: Exportar relatório HTML`
- `Privacy Scanner: Exportar relatório JSON`
- `Privacy Scanner: Configurar perfil`
- `Privacy Scanner: Editar perfil JSON (avançado)`
- `Privacy Scanner: Abrir painel`

## Comportamento de Análise

### Analisar agora

O comando `Privacy Scanner: Analisar agora` funciona assim:

- se houver uma pasta aberta, analisa o projeto inteiro;
- se não houver pasta aberta, analisa o arquivo atual.

### Automático

Quando `privacy-scanner.autoAnalyzeOnSave` está ativado, arquivos Python, Java e bancos SQLite podem ser analisados ao:

- abrir arquivo;
- trocar de aba;
- salvar arquivo.

Após uma análise do projeto inteiro, essas atualizações automáticas preservam
os contadores e o resumo da última varredura do workspace. A árvore de achados
mostra apenas os arquivos que produziram indícios técnicos.

## Sidebar

A sidebar `Privacy Scanner` possui três visões:

### Ações rápidas

Centraliza os fluxos principais e o suporte. A árvore se atualiza quando o
editor, o perfil, o backend ou os resultados mudam.

### Achados técnicos

Mostra:

- riscos `ALTO`, `MEDIO` e `BAIXO`;
- arquivos afetados;
- achados por arquivo;
- ícones diferentes para código e banco;
- clique para abrir o achado de código na linha correspondente.

Cada achado mostra somente categoria, arquivo, linha e evidência segura. A extensão
não exibe nem persiste a linha bruta do código-fonte.

### Resumo

Mostra lado a lado o indicador e o total **exibidos pelo perfil** e os valores
**brutos recebidos do backend**, inclusive quantos achados o perfil ocultou. A
extensão não recalcula esses valores a partir dos itens da árvore. Quando o
backend não puder calcular o indicador para aquele escopo, ela mostra “não
disponível”.

O total de achados visíveis é apenas um estado da interface e fica separado do
resumo bruto. Assim, ocultar um achado não muda o indicador técnico, as métricas
brutas nem a exportação.

Durante a análise, a sidebar mostra estado de carregamento para evitar exibir `100/100` antes do resultado real.

## Code Actions

Quando um achado técnico aparece no editor:

1. Clique na lâmpada/Quick Fix.
2. Escolha `Ver recomendacao LGPD` ou `Copiar recomendacao LGPD`.

A extensão não altera o código automaticamente. Ela mostra a recomendação para orientar a correção manual.

## Ocultar Achado na Interface

Uma ocorrência pode ser ocultada de duas formas:

- clique com o botão direito no achado da sidebar e escolha `Ocultar achado na interface`;
- use a lâmpada/Quick Fix no editor e escolha `Ignorar este risco na interface`.

O achado deixa de aparecer na sidebar e no painel `Problems`. A preferência fica salva no workspace.

Essa opção não altera a análise do backend. O indicador técnico e o resumo bruto
permanecem iguais, e o achado continua aparecendo nos relatórios HTML, JSON e PDF.
Na atualização para 1.0.3, ocultações antigas são redefinidas para remover chaves
locais que podiam conter trechos de código.

Para mostrar tudo novamente, expanda `Configuração e suporte` e clique em
`Restaurar achados ocultados`.

## Exportação

Clique em `Exportar relatório` nas `Ações rápidas`.

Depois escolha:

- `HTML`;
- `PDF`;
- `JSON`.

O VS Code abrirá a janela do Windows para escolher o destino e o nome do arquivo.

Também existem comandos diretos na Paleta:

- `Privacy Scanner: Exportar relatório HTML`;
- `Privacy Scanner: Exportar relatório JSON`.

## Configurações

### Perfil versionado da versão 1.1

Cada pasta pode conter `.privacy-scanner.json`. O preset `conservador` é o
padrão; `equilibrado` inclui confiança média e `completo` inclui também baixa.
Cada preset também define as regras ativas: o `conservador` ativa 7 regras de
evidência direta, o `equilibrado` ativa 12 (deixa de fora retenção e
consentimento, que só geram indícios de confiança baixa) e o `completo` ativa
as 14. Uma regra desativada pelo preset pode ser ligada com `"enabled": true`.
Categorias podem ser desativadas ou receber limiar de confiança e severidade
próprios. O arquivo possui validação e autocomplete no VS Code.

#### Assistente recomendado

Clique em `Configurar perfil` nas `Ações rápidas`. Em workspaces com mais de
uma raiz, a extensão usa a pasta do arquivo ativo ou solicita a raiz quando ela
não puder ser determinada. O menu `Configurar perfil — <pasta>` oferece:

- `Preset base`: Conservador (confiança alta, 7 regras), Equilibrado (alta e
  média, 12 regras) ou Completo (todas as faixas, 14 regras); trocar o preset
  aplica as regras ativas dele e preserva ajustes de confiança e severidade;
- `Regras ativas`: seleção das 14 regras, separadas entre Código e SQLite;
- `Ajustar uma regra`: confiança mínima, severidade técnica ou limpeza dos
  ajustes daquela regra;
- `Limpar personalizações` e `Restaurar padrão conservador`;
- `Salvar perfil` e `Cancelar sem salvar`.

Somente `Salvar perfil` persiste as alterações; `Esc` e o cancelamento não
escrevem. A severidade personalizada altera agrupamentos, totais e o indicador
técnico, mas não produz conclusão jurídica. O resumo da sidebar mostra preset e
quantidade de personalizações. Se o perfil atual estiver inválido, a ação
aparece como `Corrigir perfil`.

#### Edição JSON avançada

O arquivo bruto não é necessário no fluxo comum. Para editar limites e
categorias diretamente, abra a Paleta e use
`Privacy Scanner: Editar perfil JSON (avançado)`. Exemplo:

```json
{
  "schemaVersion": 1,
  "preset": "conservador",
  "categories": {
    "DADO_EM_LOG": {
      "enabled": true,
      "minimumConfidence": "ALTA",
      "severity": "ALTO"
    }
  }
}
```

Os comandos antigos de seleção e validação permanecem compatíveis, mas o
assistente é a interface recomendada. Configuração inválida bloqueia a análise
sem fallback silencioso. Workspaces com várias pastas aplicam o perfil de cada
raiz.

Em `settings.json`:

```json
{
  "privacy-scanner.serverPort": 5000,
  "privacy-scanner.autoAnalyzeOnSave": true,
  "privacy-scanner.pythonPath": "python",
  "privacy-scanner.enableSidebar": true,
  "privacy-scanner.showDiagnostics": true
}
```

- `enableSidebar`: mostra ou oculta as três visões da sidebar imediatamente.
- `showDiagnostics`: mostra ou remove os diagnósticos do painel `Problems` imediatamente.

## Arquitetura

```text
VS Code Extension
  |
  | HTTP
  v
server.py (Flask)
  |
  |-- code_analyzer.py  -> análise Python
  |-- java_analyzer.py  -> análise inicial Java
  |-- db_analyzer.py    -> análise SQLite
  |-- reporter.py       -> HTML/JSON/PDF
```

Endpoints usados:

- `GET /health`;
- `POST /api/analyze-file`;
- `POST /api/analyze-directory`;
- `POST /api/analyze-database`;
- `POST /api/export`.

O `GET /health` precisa declarar `status: "ok"`, a identidade
`service: "privacy-scanner"` (ou `privacy-scanner-lgpd`) e uma versão semver
compatível com a série 1.x. A extensão recusa reutilizar uma porta ocupada por
outro serviço.

Para análises, o contrato canônico é `achados`, `resumo`,
`criterio_indicador` e metadados de escopo. Os aliases legados
`vulnerabilities`, `vulnerabilidades`, `summary` e `score_conformidade` são
aceitos somente para compatibilidade.

## Desenvolvimento

Compilar:

```powershell
npm run compile
```

Executar a validação TypeScript, lint e testes unitários do contrato:

```powershell
npm test
```

Esse comando também confirma que `VERSION` e `reporter.VERSAO_FERRAMENTA` na
raiz correspondem à versão declarada pela extensão. Durante o empacotamento, a
mesma verificação é repetida sobre o backend copiado para o VSIX.

Compilar em modo contínuo:

```powershell
npm run watch
```

Rodar testes Python na raiz:

```powershell
python -m pytest -q
```

## Gerar e Instalar o VSIX

Na pasta `vscode-extension`, execute:

```powershell
npm install
npm run package
```

O comando:

1. copia o backend Python necessário para dentro do pacote;
2. compila o TypeScript;
3. gera `privacy-scanner-lgpd-1.2.2.vsix`.

Para instalar pelo terminal:

```powershell
code --install-extension .\privacy-scanner-lgpd-1.2.2.vsix --force
```

Também é possível abrir a área de extensões do VS Code, clicar em `...`,
selecionar `Install from VSIX...` e escolher o arquivo gerado.

Após instalar, use `Developer: Reload Window` ou reinicie o VS Code. A extensão
passa a funcionar em qualquer pasta aberta, sem depender do repositório do TCC.

O computador ainda precisa ter Python 3. As dependências podem ser preparadas
sem alterar o ambiente global pelo comando:

`Privacy Scanner: Configurar dependencias do backend`

Após confirmação, a extensão cria um ambiente virtual em seu armazenamento
privado, instala apenas Flask e ReportLab e valida o `/health`. A instalação
manual por `requirements-runtime.txt` continua disponível para ambientes sem
acesso de rede.

### Pacote gerado pelo GitHub

Cada push para `main` executa o workflow do GitHub Actions. Ao final de uma
execução bem-sucedida, o VSIX fica disponível na seção `Artifacts` com o nome
`privacy-scanner-lgpd-vsix-<versao-do-vscode>`.

## Exclusões e falsos positivos

Na análise do projeto inteiro, a extensão ignora automaticamente ambientes
virtuais, dependências, caches, builds e o backend empacotado.

Use `.privacyignore` na raiz do projeto para excluir fixtures próprias:

```text
tests/fixtures/
exemplo_vulneravel.py
```

A exclusão não impede o comando `Analisar arquivo`.

## Troubleshooting

### Servidor Flask não inicia

Instale as dependências Python:

```powershell
python -m pip install -r requirements.txt
```

### Porta 5000 em uso

A extensão tenta reutilizar somente um backend que passe na validação de
identidade e versão. Se a porta estiver ocupada por outro processo, altere:

```json
{
  "privacy-scanner.serverPort": 5001
}
```

### Python não encontrado

Configure o caminho absoluto:

```json
{
  "privacy-scanner.pythonPath": "C:\\Python312\\python.exe"
}
```

### Extensão não atualiza depois de editar TypeScript

Compile novamente:

```powershell
npm run compile
```

Depois recarregue a janela `[Extension Development Host]`.

## Status

- [x] Análise de arquivo Python
- [x] Análise de arquivo Java com sete categorias
- [x] Análise de projeto
- [x] Análise de banco SQLite
- [x] Diagnostics API
- [x] Sidebar com resumo
- [x] Estado de carregamento
- [x] Code Actions
- [x] Exportação HTML
- [x] Exportação JSON
- [x] Exportação PDF
- [x] Save dialog para relatório
- [x] Reutilização de servidor Flask ativo
- [x] Resumo canônico do backend sem recálculo no cliente
- [x] Timeout, cancelamento e proteção contra respostas fora de ordem
- [x] Ocultar achados somente na interface

## Limitações

- A análise é estática e baseada em regras.
- A extensão não substitui auditoria jurídica.
- O suporte Java usa análise léxica e não compila o projeto.
- O Java cobre sete categorias, mas não acompanha fluxo de dados entre métodos.
- Algumas ocorrências podem exigir revisão manual.
- Confiança e severidade configurável são critérios operacionais, não
  probabilidades estatísticas nem classificações jurídicas.

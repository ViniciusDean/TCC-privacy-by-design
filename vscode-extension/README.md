# Privacy Scanner LGPD - Extensão VS Code

Extensão do VS Code para executar o Privacy Scanner LGPD durante o desenvolvimento.

A extensão conversa com o servidor Flask do projeto e exibe os resultados dentro do VS Code, sem executar o código analisado.

## Recursos Implementados

- Análise de arquivo Python.
- Análise de arquivo Java com sete categorias de privacidade.
- Análise de projeto inteiro.
- Análise de banco SQLite (`.db`, `.sqlite`, `.sqlite3`).
- Diagnósticos no editor e no painel `Problems`.
- Sidebar com achados técnicos agrupados por risco.
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
5. Use a sidebar `Privacy Scanner`.

Se quiser recriar o workspace externo de teste:

```powershell
python scripts/create_test_workspace.py
```

## Comandos

Na Paleta de Comandos (`Ctrl+Shift+P`):

- `Privacy Scanner: Analisar agora`
- `Privacy Scanner: Analisar arquivo atual`
- `Privacy Scanner: Analisar projeto inteiro`
- `Privacy Scanner: Analisar banco SQLite`
- `Privacy Scanner: Limpar resultados`
- `Privacy Scanner: Exportar relatorio`
- `Privacy Scanner: Exportar relatório HTML`
- `Privacy Scanner: Exportar relatório JSON`
- `Privacy Scanner: Mostrar achados`

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

## Sidebar

A sidebar `Privacy Scanner` possui duas visões:

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

Mostra o indicador técnico, o total e as contagens por risco **recebidos no
`resumo` do backend**. A extensão não recalcula o indicador a partir dos itens
visíveis. Quando o backend não puder calcular o indicador para aquele escopo,
ela mostra “não disponível”.

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

Para mostrar tudo novamente, execute:

```text
Privacy Scanner: Restaurar achados ocultados
```

## Exportação

Use:

```text
Privacy Scanner: Exportar relatorio
```

Depois escolha:

- `HTML`;
- `PDF`.

O VS Code abrirá a janela do Windows para escolher o destino e o nome do arquivo.

Também existem comandos diretos:

- `Privacy Scanner: Exportar relatório HTML`;
- `Privacy Scanner: Exportar relatório JSON`.

## Configurações

### Perfil versionado da versão 1.1

Cada pasta pode conter `.privacy-scanner.json`. O preset `conservador` é o
padrão; `equilibrado` inclui confiança média e `completo` inclui também baixa.
Categorias podem ser desativadas ou receber limiar de confiança e severidade
próprios. O arquivo possui validação e autocomplete no VS Code.

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

Comandos adicionais permitem criar, selecionar e validar o perfil, reiniciar o
backend e abrir logs seguros. Configuração inválida bloqueia a análise sem
fallback silencioso. Workspaces com várias pastas aplicam o perfil de cada raiz.

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

- `enableSidebar`: mostra ou oculta as duas visões da sidebar imediatamente.
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
3. gera `privacy-scanner-lgpd-1.1.0.vsix`.

Para instalar pelo terminal:

```powershell
code --install-extension .\privacy-scanner-lgpd-1.1.0.vsix --force
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

A exclusão não impede o comando `Analisar arquivo atual`.

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

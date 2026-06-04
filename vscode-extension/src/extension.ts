import * as vscode from 'vscode';
import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { spawn, ChildProcessWithoutNullStreams } from 'child_process';


// ─────────────────────────────────────────────────────────────────────────────
// Interfaces
// ─────────────────────────────────────────────────────────────────────────────

interface Vulnerability {
    arquivo: string;
    linha: number;
    categoria: string;
    descricao: string;
    risco: 'ALTO' | 'MEDIO' | 'BAIXO';
    artigo_lgpd: string;
    trecho?: string;
    recomendacao?: string;
}

interface AnalysisResponse {
    success: boolean;
    vulnerabilities: Vulnerability[];
    summary?: {
        total: number;
        por_risco: {
            ALTO: number;
            MEDIO: number;
            BAIXO: number;
        };
        score_conformidade: number;
    };
}

interface RecommendationPayload {
    categoria: string;
    mensagem: string;
    recomendacao: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Configuração global
// ─────────────────────────────────────────────────────────────────────────────

let diagnosticCollection: vscode.DiagnosticCollection;
let serverPort: number = 5000;
let serverRunning: boolean = false;
let flaskProcess: ChildProcessWithoutNullStreams | undefined;
let statusBar: vscode.StatusBarItem;
let isAnalyzing: boolean = false;

// Mapa global de vulnerabilidades: filePath -> Vulnerability[]
let allVulnerabilities: Map<string, Vulnerability[]> = new Map();
let vulnerabilitiesProvider: VulnerabilitiesProvider;
let summaryProvider: SummaryProvider;

const DB_FILE_PATTERN = '**/*.{db,sqlite,sqlite3}';
const EXCLUDE_PATTERN = '**/{node_modules,.git,__pycache__,htmlcov,.pytest_cache}/**';

const riskToSeverity = (risk: string): vscode.DiagnosticSeverity => {
    switch (risk) {
        case 'ALTO': return vscode.DiagnosticSeverity.Error;
        case 'MEDIO': return vscode.DiagnosticSeverity.Warning;
        case 'BAIXO': return vscode.DiagnosticSeverity.Information;
        default: return vscode.DiagnosticSeverity.Information;
    }
};

const riskOrder: Record<string, number> = { ALTO: 0, MEDIO: 1, BAIXO: 2 };

function isDatabaseUri(uri: vscode.Uri): boolean {
    const filePath = uri.fsPath.toLowerCase();
    return filePath.endsWith('.db') || filePath.endsWith('.sqlite') || filePath.endsWith('.sqlite3');
}

function refreshViews(): void {
    vulnerabilitiesProvider.refresh();
    summaryProvider.refresh();
}

function setAnalyzing(value: boolean, message: string = 'Analisando...'): void {
    isAnalyzing = value;
    if (value) {
        updateStatusBar(message, 'loading');
    }
    refreshViews();
}

// ─────────────────────────────────────────────────────────────────────────────
// Inicialização da extensão
// ─────────────────────────────────────────────────────────────────────────────

export async function activate(context: vscode.ExtensionContext) {
    console.log('🔒 Privacy Scanner LGPD ativado');

    // Status bar
    statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBar.command = 'privacy-scanner.analyze';
    updateStatusBar('Iniciando...', 'loading');
    isAnalyzing = true;
    context.subscriptions.push(statusBar);

    // Diagnostic collection
    diagnosticCollection = vscode.languages.createDiagnosticCollection('privacy-scanner');
    context.subscriptions.push(diagnosticCollection);

    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            { scheme: 'file', language: 'python' },
            new PrivacyCodeActionProvider(),
            { providedCodeActionKinds: [vscode.CodeActionKind.QuickFix] }
        )
    );

    // Tree View Providers
    vulnerabilitiesProvider = new VulnerabilitiesProvider();
    summaryProvider = new SummaryProvider();
    
    context.subscriptions.push(
        vscode.window.registerTreeDataProvider('privacy-scanner-vulnerabilities', vulnerabilitiesProvider),
        vscode.window.registerTreeDataProvider('privacy-scanner-summary', summaryProvider)
    );

    // Set context keys to show views
    vscode.commands.executeCommand('setContext', 'privacy-scanner:showVulnerabilities', true);
    vscode.commands.executeCommand('setContext', 'privacy-scanner:showSummary', true);

    // Carregar configurações
    loadConfig();

    // Iniciar servidor Flask
    await startFlaskServer(context);

    // Registrar comandos
    registerCommands(context);

    // Listeners
    registerListeners(context);

    const activeEditor = vscode.window.activeTextEditor;
    if (activeEditor && (activeEditor.document.languageId === 'python' || isDatabaseUri(activeEditor.document.uri))) {
        await analyzeFile(activeEditor.document.uri);
    } else {
        setAnalyzing(false);
    }

    if (!isAnalyzing) {
        updateStatusBar('Privacy Scanner pronto', 'pass');
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Comandos
// ─────────────────────────────────────────────────────────────────────────────

function registerCommands(context: vscode.ExtensionContext) {
    // Analisar agora: workspace quando aberto, senao arquivo atual
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.analyzeNow', async () => {
            if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
                await analyzeWorkspace();
                return;
            }

            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('Nenhuma pasta ou arquivo aberto para analisar');
                return;
            }

            await analyzeFile(editor.document.uri);
        })
    );

    // Analisar arquivo atual
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.analyze', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('Nenhum arquivo aberto');
                return;
            }
            await analyzeFile(editor.document.uri);
        })
    );

    // Analisar projeto inteiro
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.analyzeAll', async () => {
            await analyzeWorkspace();
        })
    );

    // Analisar banco SQLite
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.analyzeDatabase', async () => {
            await analyzeDatabaseFromPicker();
        })
    );

    // Limpar resultados
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.clearResults', async () => {
            allVulnerabilities.clear();
            diagnosticCollection.clear();
            refreshViews();
            updateStatusBar('Resultados limpos', 'pass');
        })
    );

    // Exportar HTML
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.exportHTML', async () => {
            await exportReportWithSaveDialog('html');
        })
    );

    // Exportar JSON
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.exportJSON', async () => {
            await exportReportWithSaveDialog('json');
        })
    );

    // Exportar relatorio: seletor de formato
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.exportReport', async () => {
            await exportReportFromPicker();
        })
    );

    // Mostrar sidebar
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.showSidebar', async () => {
            vscode.commands.executeCommand('workbench.view.extension.privacy-scanner-sidebar');
        })
    );

    // Mostra recomendacao LGPD via Code Action
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.showRecommendation', async (payload: RecommendationPayload) => {
            const choice = await vscode.window.showInformationMessage(
                `${payload.categoria}: ${payload.recomendacao}`,
                { modal: true },
                'Copiar'
            );

            if (choice === 'Copiar') {
                await vscode.env.clipboard.writeText(payload.recomendacao);
                vscode.window.showInformationMessage('Recomendacao LGPD copiada');
            }
        })
    );

    // Copia recomendacao LGPD via Code Action
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.copyRecommendation', async (payload: RecommendationPayload) => {
            await vscode.env.clipboard.writeText(payload.recomendacao);
            vscode.window.showInformationMessage(`Recomendacao copiada: ${payload.categoria}`);
        })
    );

    // Abrir vulnerabilidade (comando interno)
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.openVulnerability', async (filePath: string, line: number) => {
            const uri = vscode.Uri.file(filePath);
            const document = await vscode.workspace.openTextDocument(uri);
            const editor = await vscode.window.showTextDocument(document);
            
            if (line > 0) {
                const range = new vscode.Range(line - 1, 0, line - 1, 0);
                editor.selection = new vscode.Selection(range.start, range.end);
                editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
            }
        })
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// Análise de arquivos
// ─────────────────────────────────────────────────────────────────────────────

async function analyzeFile(uri: vscode.Uri) {
    const isPython = uri.path.endsWith('.py');
    const isDB = isDatabaseUri(uri);

    if (!isPython && !isDB) {
        return;
    }

    try {
        setAnalyzing(true);

        const filePath = uri.fsPath;
        let endpoint = isPython ? '/api/analyze-file' : '/api/analyze-database';
        let payload = isPython ? { filepath: filePath } : { database: filePath };

        const response = await axios.post<AnalysisResponse>(
            `http://localhost:${serverPort}${endpoint}`,
            payload
        );

        if (response.data.success) {
            const vulns = response.data.vulnerabilities;
            
            // Atualizar diagnósticos (apenas para Python, pois banco não tem linha útil no editor)
            if (isPython) {
                displayDiagnostics(uri, vulns);
            }

            // Atualizar mapa global
            if (vulns.length > 0) {
                allVulnerabilities.set(filePath, vulns);
            } else {
                allVulnerabilities.delete(filePath);
            }

            setAnalyzing(false);

            updateStatusBar(`${vulns.length} vulnerabilidades`, vulns.length === 0 ? 'pass' : 'alert');
        } else {
            setAnalyzing(false);
        }
    } catch (error) {
        console.error('Erro ao analisar arquivo:', error);
        setAnalyzing(false);
        updateStatusBar('Erro na análise', 'error');
    }
}

function getRecommendationFromDiagnostic(diagnostic: vscode.Diagnostic): string | undefined {
    const relatedMessage = diagnostic.relatedInformation?.find(info =>
        info.message.toLowerCase().startsWith('corre')
    )?.message;

    if (relatedMessage) {
        return relatedMessage.replace(/^Corre[cç][aã]o:\s*/i, '').trim();
    }

    return undefined;
}

function getCategoryFromDiagnostic(diagnostic: vscode.Diagnostic): string {
    if (typeof diagnostic.code === 'string') {
        return diagnostic.code;
    }

    return diagnostic.message.split(':')[0] || 'Vulnerabilidade LGPD';
}

class PrivacyCodeActionProvider implements vscode.CodeActionProvider {
    provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range,
        context: vscode.CodeActionContext
    ): vscode.CodeAction[] {
        const actions: vscode.CodeAction[] = [];
        const diagnostics = context.diagnostics.filter(diagnostic =>
            diagnostic.source === 'Privacy Scanner' && diagnostic.range.intersection(range)
        );

        for (const diagnostic of diagnostics) {
            const recomendacao = getRecommendationFromDiagnostic(diagnostic);

            if (!recomendacao) {
                continue;
            }

            const payload: RecommendationPayload = {
                categoria: getCategoryFromDiagnostic(diagnostic),
                mensagem: diagnostic.message,
                recomendacao
            };

            const showAction = new vscode.CodeAction(
                `Ver recomendacao LGPD: ${payload.categoria}`,
                vscode.CodeActionKind.QuickFix
            );
            showAction.diagnostics = [diagnostic];
            showAction.command = {
                command: 'privacy-scanner.showRecommendation',
                title: 'Ver recomendacao LGPD',
                arguments: [payload]
            };
            actions.push(showAction);

            const copyAction = new vscode.CodeAction(
                `Copiar recomendacao LGPD: ${payload.categoria}`,
                vscode.CodeActionKind.QuickFix
            );
            copyAction.diagnostics = [diagnostic];
            copyAction.command = {
                command: 'privacy-scanner.copyRecommendation',
                title: 'Copiar recomendacao LGPD',
                arguments: [payload]
            };
            actions.push(copyAction);
        }

        return actions;
    }
}

async function analyzeDatabaseFromPicker() {
    const files = await vscode.window.showOpenDialog({
        canSelectFiles: true,
        canSelectFolders: false,
        canSelectMany: true,
        filters: {
            'SQLite databases': ['db', 'sqlite', 'sqlite3']
        },
        title: 'Selecionar banco SQLite para análise LGPD'
    });

    if (!files || files.length === 0) {
        return;
    }

    setAnalyzing(true, 'Analisando banco...');
    let total = 0;
    for (const file of files) {
        total += await analyzeDatabaseUri(file);
    }

    setAnalyzing(false);
    vscode.window.showInformationMessage(
        `Análise de banco concluída: ${total} vulnerabilidades encontradas`
    );
}

async function analyzeDatabaseUri(uri: vscode.Uri): Promise<number> {
    const filePath = uri.fsPath;
    const response = await axios.post<AnalysisResponse>(
        `http://localhost:${serverPort}/api/analyze-database`,
        { database: filePath }
    );

    if (!response.data.success) {
        return 0;
    }

    const vulns = response.data.vulnerabilities;
    if (vulns.length > 0) {
        allVulnerabilities.set(filePath, vulns);
    } else {
        allVulnerabilities.delete(filePath);
    }

    return vulns.length;
}

async function analyzeWorkspace() {
    try {
        setAnalyzing(true, 'Analisando projeto...');

        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            vscode.window.showWarningMessage('Nenhuma pasta de trabalho aberta');
            setAnalyzing(false);
            return;
        }

        const workspacePath = vscode.workspace.workspaceFolders[0].uri.fsPath;
        const response = await axios.post<AnalysisResponse>(
            `http://localhost:${serverPort}/api/analyze-directory`,
            { directory: workspacePath }
        );

        if (response.data.success) {
            // Limpar mapa global antes de análise completa
            allVulnerabilities.clear();
            let totalVulnerabilities = response.data.vulnerabilities.length;

            // Agrupar vulnerabilidades por arquivo
            const grouped = new Map<string, Vulnerability[]>();
            for (const vuln of response.data.vulnerabilities) {
                if (!grouped.has(vuln.arquivo)) {
                    grouped.set(vuln.arquivo, []);
                }
                grouped.get(vuln.arquivo)!.push(vuln);
            }

            // Adicionar diagnostics e atualizar mapa global
            for (const [arquivo, vulns] of grouped) {
                allVulnerabilities.set(arquivo, vulns);
                
                // Só mostra diagnósticos se for Python
                if (arquivo.endsWith('.py')) {
                    const uri = vscode.Uri.file(arquivo);
                    displayDiagnostics(uri, vulns);
                }
            }

            const databaseUris = await vscode.workspace.findFiles(DB_FILE_PATTERN, EXCLUDE_PATTERN);
            for (const dbUri of databaseUris) {
                totalVulnerabilities += await analyzeDatabaseUri(dbUri);
            }

            // Refresh TreeViews
            setAnalyzing(false);

            vscode.window.showInformationMessage(
                `Análise concluída: ${totalVulnerabilities} vulnerabilidades encontradas`
            );
            updateStatusBar(`${totalVulnerabilities} vulns`, totalVulnerabilities === 0 ? 'pass' : 'alert');
        } else {
            setAnalyzing(false);
        }
    } catch (error) {
        console.error('Erro ao analisar projeto:', error);
        setAnalyzing(false);
        vscode.window.showErrorMessage('Erro ao analisar projeto');
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Exibição de diagnósticos
// ─────────────────────────────────────────────────────────────────────────────

function displayDiagnostics(uri: vscode.Uri, vulnerabilities: Vulnerability[]) {
    const diagnostics: vscode.Diagnostic[] = [];

    for (const vuln of vulnerabilities) {
        if (vuln.linha <= 0) {
            continue; // Ignora vulnerabilidades de banco (linha 0)
        }

        const range = new vscode.Range(
            new vscode.Position(vuln.linha - 1, 0),
            new vscode.Position(vuln.linha - 1, 1000)
        );

        const diagnostic = new vscode.Diagnostic(
            range,
            `${vuln.categoria}: ${vuln.descricao}\n${vuln.artigo_lgpd}`,
            riskToSeverity(vuln.risco)
        );

        diagnostic.code = vuln.categoria;
        diagnostic.source = 'Privacy Scanner';

        // Adiciona recomendação ao code action
        if (vuln.recomendacao) {
            diagnostic.relatedInformation = [
                new vscode.DiagnosticRelatedInformation(
                    new vscode.Location(uri, range),
                    `Correção: ${vuln.recomendacao}`
                )
            ];
        }

        diagnostics.push(diagnostic);
    }

    diagnosticCollection.set(uri, diagnostics);
}

// ─────────────────────────────────────────────────────────────────────────────
// Listeners
// ─────────────────────────────────────────────────────────────────────────────

function registerListeners(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('privacy-scanner');
    const autoAnalyze = config.get('autoAnalyzeOnSave', true);

    if (autoAnalyze) {
        context.subscriptions.push(
            vscode.workspace.onDidSaveTextDocument(async (document) => {
                if (document.languageId === 'python' || isDatabaseUri(document.uri)) {
                    await analyzeFile(document.uri);
                }
            }),
            vscode.workspace.onDidOpenTextDocument(async (document) => {
                if (document.languageId === 'python' || isDatabaseUri(document.uri)) {
                    await analyzeFile(document.uri);
                }
            }),
            vscode.window.onDidChangeActiveTextEditor(async (editor) => {
                if (!editor) {
                    return;
                }
                if (editor.document.languageId === 'python' || isDatabaseUri(editor.document.uri)) {
                    await analyzeFile(editor.document.uri);
                }
            })
        );
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Servidor Flask
// ─────────────────────────────────────────────────────────────────────────────

async function startFlaskServer(context: vscode.ExtensionContext): Promise<void> {
    return new Promise((resolve) => {
        const pythonPath = vscode.workspace.getConfiguration('privacy-scanner').get('pythonPath', 'python');
        
        // Arquivo do servidor está em ../server.py (relativo à extensão)
        const extensionPath = context.extensionPath;
        const serverScript = path.join(extensionPath, '..', 'server.py');

        if (!fs.existsSync(serverScript)) {
            console.warn(`Arquivo do servidor não encontrado: ${serverScript}`);
            vscode.window.showWarningMessage('Erro: server.py não encontrado. Certifique-se de que está na raiz do projeto TCC.');
            resolve();
            return;
        }

        flaskProcess = spawn(pythonPath, [serverScript, String(serverPort)], {
            cwd: path.dirname(serverScript),
            windowsHide: true
        });

        flaskProcess.stdout.on('data', (data) => {
            console.log(`[Privacy Scanner Server] ${data.toString().trim()}`);
        });

        flaskProcess.stderr.on('data', (data) => {
            console.error(`[Privacy Scanner Server] ${data.toString().trim()}`);
        });

        flaskProcess.on('error', (error) => {
            console.error(`Erro ao iniciar servidor Flask: ${error}`);
            vscode.window.showErrorMessage(`Erro ao iniciar servidor Flask: ${error.message}`);
            resolve();
        });

        flaskProcess.on('exit', (code) => {
            serverRunning = false;
            if (code !== 0 && code !== null) {
                console.error(`Servidor Flask encerrado com codigo ${code}`);
            }
        });

        // Aguardar servidor ficar pronto
        let attempts = 0;
        const checkServer = setInterval(async () => {
            try {
                await axios.get(`http://localhost:${serverPort}/health`);
                clearInterval(checkServer);
                serverRunning = true;
                console.log('✅ Servidor Flask ativo');
                resolve();
            } catch {
                attempts++;
                if (attempts > 30) {
                    clearInterval(checkServer);
                    console.error('Timeout ao conectar ao servidor Flask');
                    resolve();
                }
            }
        }, 500);
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Exportação de relatórios
// ─────────────────────────────────────────────────────────────────────────────

async function exportReportFromPicker() {
    const choice = await vscode.window.showQuickPick(
        [
            {
                label: 'HTML',
                description: 'Disponivel agora',
                detail: 'Gera um relatorio visual em HTML na raiz do workspace',
                format: 'html' as const
            },
            {
                label: 'PDF',
                description: 'Em desenvolvimento',
                detail: 'Formato reservado para a proxima etapa do projeto',
                format: 'pdf' as const
            }
        ],
        {
            title: 'Exportar relatorio LGPD',
            placeHolder: 'Selecione o formato do relatorio'
        }
    );

    if (!choice) {
        return;
    }

    const saveUri = await vscode.window.showSaveDialog({
        title: `Salvar relatorio ${choice.label}`,
        defaultUri: getDefaultReportUri(choice.format),
        filters: choice.format === 'html'
            ? { 'Relatorio HTML': ['html', 'htm'] }
            : { 'Relatorio PDF': ['pdf'] },
        saveLabel: 'Exportar'
    });

    if (!saveUri) {
        return;
    }

    if (choice.format === 'pdf') {
        vscode.window.showInformationMessage('Exportacao em PDF ainda sera implementada. Use HTML por enquanto.');
        return;
    }

    await exportReport(choice.format, saveUri);
}

function getDefaultReportUri(format: 'html' | 'json' | 'pdf'): vscode.Uri | undefined {
    if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
        return undefined;
    }

    const workspacePath = vscode.workspace.workspaceFolders[0].uri.fsPath;
    const timestamp = new Date().toISOString().split('T')[0];
    return vscode.Uri.file(path.join(workspacePath, `privacy-scan-${timestamp}.${format}`));
}

async function exportReportWithSaveDialog(format: 'html' | 'json') {
    const filters: { [name: string]: string[] } = format === 'html'
        ? { 'Relatorio HTML': ['html', 'htm'] }
        : { 'Relatorio JSON': ['json'] };

    const saveUri = await vscode.window.showSaveDialog({
        title: `Salvar relatorio ${format.toUpperCase()}`,
        defaultUri: getDefaultReportUri(format),
        filters,
        saveLabel: 'Exportar'
    });

    if (!saveUri) {
        return;
    }

    await exportReport(format, saveUri);
}

async function exportReport(format: 'html' | 'json', targetUri?: vscode.Uri) {
    try {
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            vscode.window.showWarningMessage('Nenhuma pasta de trabalho aberta');
            return;
        }

        const workspacePath = vscode.workspace.workspaceFolders[0].uri.fsPath;
        const filepath = targetUri?.fsPath || getDefaultReportUri(format)?.fsPath;

        if (!filepath) {
            vscode.window.showWarningMessage('Destino do relatorio nao informado');
            return;
        }

        const filename = path.basename(filepath);

        const response = await axios.post(
            `http://localhost:${serverPort}/api/export`,
            { directory: workspacePath, format }
        );

        if (response.data.content) {
            fs.writeFileSync(filepath, response.data.content);
            vscode.window.showInformationMessage(
                `📄 Relatório ${format.toUpperCase()} gerado: ${filename}`,
                'Abrir'
            ).then((choice) => {
                if (choice === 'Abrir') {
                    vscode.commands.executeCommand('vscode.open', vscode.Uri.file(filepath));
                }
            });
        }
    } catch (error) {
        console.error('Erro ao exportar relatório:', error);
        vscode.window.showErrorMessage('Erro ao exportar relatório');
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Utilitários
// ─────────────────────────────────────────────────────────────────────────────

function loadConfig() {
    const config = vscode.workspace.getConfiguration('privacy-scanner');
    serverPort = config.get('serverPort', 5000);
}

function updateStatusBar(text: string, state: 'loading' | 'pass' | 'alert' | 'error') {
    const icons: Record<string, string> = {
        'loading': '⏳',
        'pass': '✅',
        'alert': '⚠️',
        'error': '❌'
    };
    statusBar.text = `${icons[state]} ${text}`;
    statusBar.show();
}

// ─────────────────────────────────────────────────────────────────────────────
// Tree View Providers
// ─────────────────────────────────────────────────────────────────────────────

class VulnerabilityTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly type: 'risk' | 'file' | 'vulnerability' | 'summary' | 'empty' | 'loading',
        public readonly data?: any
    ) {
        super(label, collapsibleState);

        if (type === 'risk') {
            this.iconPath = new vscode.ThemeIcon(
                data.risk === 'ALTO' ? 'error' : data.risk === 'MEDIO' ? 'warning' : 'info'
            );
            this.description = `${data.count}`;
        } else if (type === 'file') {
            this.iconPath = new vscode.ThemeIcon(data?.isDatabase ? 'database' : 'file-code');
            this.contextValue = 'file';
            this.resourceUri = vscode.Uri.file(data?.filePath || label);
            this.tooltip = data?.filePath || label;
            this.description = `${data?.count || 0}`;
        } else if (type === 'vulnerability') {
            const risk = data.risco;
            this.iconPath = new vscode.ThemeIcon(
                risk === 'ALTO' ? 'error' : risk === 'MEDIO' ? 'warning' : 'info'
            );
            this.description = data.linha > 0 ? `Linha ${data.linha}` : path.basename(data.arquivo);
            this.tooltip = `${data.categoria}: ${data.descricao}\nLGPD: ${data.artigo_lgpd}`;
            if (data.linha > 0) {
                this.command = {
                    command: 'privacy-scanner.openVulnerability',
                    title: 'Abrir Vulnerabilidade',
                    arguments: [data.arquivo, data.linha]
                };
            }
        } else if (type === 'summary') {
            this.iconPath = new vscode.ThemeIcon(data.icon);
        } else if (type === 'loading') {
            this.iconPath = new vscode.ThemeIcon('loading~spin');
        }
    }
}

class VulnerabilitiesProvider implements vscode.TreeDataProvider<VulnerabilityTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<VulnerabilityTreeItem | undefined | null | void> = new vscode.EventEmitter<VulnerabilityTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<VulnerabilityTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: VulnerabilityTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: VulnerabilityTreeItem): Thenable<VulnerabilityTreeItem[]> {
        if (!element) {
            if (isAnalyzing) {
                return Promise.resolve([
                    new VulnerabilityTreeItem('Analisando...', vscode.TreeItemCollapsibleState.None, 'loading')
                ]);
            }

            if (allVulnerabilities.size === 0) {
                return Promise.resolve([new VulnerabilityTreeItem('Nenhuma vulnerabilidade encontrada', vscode.TreeItemCollapsibleState.None, 'empty')]);
            }

            const risks: Array<'ALTO' | 'MEDIO' | 'BAIXO'> = ['ALTO', 'MEDIO', 'BAIXO'];
            const groups = risks
                .map(risk => ({
                    risk,
                    count: Array.from(allVulnerabilities.values())
                        .flat()
                        .filter(v => v.risco === risk).length
                }))
                .filter(group => group.count > 0);

            return Promise.resolve(groups.map(group =>
                new VulnerabilityTreeItem(
                    `Risco ${group.risk}`,
                    vscode.TreeItemCollapsibleState.Expanded,
                    'risk',
                    group
                )
            ));
        } else if (element.type === 'risk') {
            const risk = element.data.risk;
            const files = Array.from(allVulnerabilities.entries())
                .filter(([, vulns]) => vulns.some(v => v.risco === risk))
                .sort(([a], [b]) => a.localeCompare(b));

            return Promise.resolve(files.map(([filePath, vulns]) => {
                const count = vulns.filter(v => v.risco === risk).length;
                const isDatabase = isDatabaseUri(vscode.Uri.file(filePath));
                return new VulnerabilityTreeItem(
                    path.basename(filePath),
                    vscode.TreeItemCollapsibleState.Collapsed,
                    'file',
                    { filePath, risk, count, isDatabase }
                );
            }));
        } else if (element.type === 'file') {
            const filePath = element.data.filePath;
            const risk = element.data.risk;
            const vulns = (allVulnerabilities.get(filePath) || [])
                .filter(v => v.risco === risk)
                .sort((a, b) => a.linha - b.linha || a.categoria.localeCompare(b.categoria));

            return Promise.resolve(vulns.map(v => 
                new VulnerabilityTreeItem(v.categoria, vscode.TreeItemCollapsibleState.None, 'vulnerability', v)
            ));
        }
        return Promise.resolve([]);
    }
}

class SummaryProvider implements vscode.TreeDataProvider<VulnerabilityTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<VulnerabilityTreeItem | undefined | null | void> = new vscode.EventEmitter<VulnerabilityTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<VulnerabilityTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: VulnerabilityTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: VulnerabilityTreeItem): Thenable<VulnerabilityTreeItem[]> {
        if (element) return Promise.resolve([]);

        if (isAnalyzing) {
            return Promise.resolve([
                new VulnerabilityTreeItem('Score LGPD: calculando...', vscode.TreeItemCollapsibleState.None, 'loading'),
                new VulnerabilityTreeItem('Analise em andamento', vscode.TreeItemCollapsibleState.None, 'loading'),
                new VulnerabilityTreeItem('Aguardando resultado do scanner', vscode.TreeItemCollapsibleState.None, 'loading')
            ]);
        }

        const allVulns = Array.from(allVulnerabilities.values()).flat();
        const counts = {
            ALTO: allVulns.filter(v => v.risco === 'ALTO').length,
            MEDIO: allVulns.filter(v => v.risco === 'MEDIO').length,
            BAIXO: allVulns.filter(v => v.risco === 'BAIXO').length,
        };

        const total = allVulns.length;
        const score = Math.max(0, 100 - (counts.ALTO * 10 + counts.MEDIO * 5 + counts.BAIXO * 2));
        const filesWithFindings = Array.from(allVulnerabilities.keys());
        const databaseCount = filesWithFindings.filter(f => isDatabaseUri(vscode.Uri.file(f))).length;
        const pythonCount = filesWithFindings.filter(f => f.endsWith('.py')).length;

        return Promise.resolve([
            new VulnerabilityTreeItem(`Score LGPD: ${score}/100`, vscode.TreeItemCollapsibleState.None, 'summary', { icon: 'shield' }),
            new VulnerabilityTreeItem(`Total: ${total} vulnerabilidades`, vscode.TreeItemCollapsibleState.None, 'summary', { icon: 'search' }),
            new VulnerabilityTreeItem(`Arquivos Python: ${pythonCount}`, vscode.TreeItemCollapsibleState.None, 'summary', { icon: 'file-code' }),
            new VulnerabilityTreeItem(`Bancos SQLite: ${databaseCount}`, vscode.TreeItemCollapsibleState.None, 'summary', { icon: 'database' }),
            new VulnerabilityTreeItem(`Risco ALTO: ${counts.ALTO}`, vscode.TreeItemCollapsibleState.None, 'summary', { icon: 'error' }),
            new VulnerabilityTreeItem(`Risco MÉDIO: ${counts.MEDIO}`, vscode.TreeItemCollapsibleState.None, 'summary', { icon: 'warning' }),
            new VulnerabilityTreeItem(`Risco BAIXO: ${counts.BAIXO}`, vscode.TreeItemCollapsibleState.None, 'summary', { icon: 'info' })
        ]);
    }
}

export function deactivate() {
    if (flaskProcess && !flaskProcess.killed) {
        flaskProcess.kill();
        flaskProcess = undefined;
    }
    console.log('Privacy Scanner desativado');
}

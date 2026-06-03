import * as vscode from 'vscode';
import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { exec } from 'child_process';


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

// ─────────────────────────────────────────────────────────────────────────────
// Configuração global
// ─────────────────────────────────────────────────────────────────────────────

let diagnosticCollection: vscode.DiagnosticCollection;
let serverPort: number = 5000;
let serverRunning: boolean = false;
let statusBar: vscode.StatusBarItem;

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

// ─────────────────────────────────────────────────────────────────────────────
// Inicialização da extensão
// ─────────────────────────────────────────────────────────────────────────────

export async function activate(context: vscode.ExtensionContext) {
    console.log('🔒 Privacy Scanner LGPD ativado');

    // Status bar
    statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBar.command = 'privacy-scanner.analyze';
    updateStatusBar('Iniciando...', 'loading');
    context.subscriptions.push(statusBar);

    // Diagnostic collection
    diagnosticCollection = vscode.languages.createDiagnosticCollection('privacy-scanner');
    context.subscriptions.push(diagnosticCollection);

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

    if (vscode.window.activeTextEditor) {
        await analyzeFile(vscode.window.activeTextEditor.document.uri);
    }

    updateStatusBar('Privacy Scanner pronto', 'pass');
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
            await exportReport('html');
        })
    );

    // Exportar JSON
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.exportJSON', async () => {
            await exportReport('json');
        })
    );

    // Mostrar sidebar
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.showSidebar', async () => {
            vscode.commands.executeCommand('workbench.view.extension.privacy-scanner-sidebar');
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
        updateStatusBar('Analisando...', 'loading');

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

            refreshViews();

            updateStatusBar(`${vulns.length} vulnerabilidades`, vulns.length === 0 ? 'pass' : 'alert');
        }
    } catch (error) {
        console.error('Erro ao analisar arquivo:', error);
        updateStatusBar('Erro na análise', 'error');
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

    let total = 0;
    for (const file of files) {
        total += await analyzeDatabaseUri(file);
    }

    refreshViews();
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
        updateStatusBar('Analisando projeto...', 'loading');

        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            vscode.window.showWarningMessage('Nenhuma pasta de trabalho aberta');
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
            refreshViews();

            vscode.window.showInformationMessage(
                `Análise concluída: ${totalVulnerabilities} vulnerabilidades encontradas`
            );
            updateStatusBar(`${totalVulnerabilities} vulns`, totalVulnerabilities === 0 ? 'pass' : 'alert');
        }
    } catch (error) {
        console.error('Erro ao analisar projeto:', error);
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

        const command = `"${pythonPath}" "${serverScript}" ${serverPort}`;

        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error(`Erro ao iniciar servidor Flask: ${error}`);
                vscode.window.showErrorMessage(`Erro ao iniciar servidor Flask: ${error.message}`);
                resolve();
                return;
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

async function exportReport(format: 'html' | 'json') {
    try {
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            vscode.window.showWarningMessage('Nenhuma pasta de trabalho aberta');
            return;
        }

        const workspacePath = vscode.workspace.workspaceFolders[0].uri.fsPath;
        const timestamp = new Date().toISOString().split('T')[0];
        const filename = `privacy-scan-${timestamp}.${format}`;
        const filepath = path.join(workspacePath, filename);

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
        public readonly type: 'risk' | 'file' | 'vulnerability' | 'summary' | 'empty',
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
    console.log('Privacy Scanner desativado');
}

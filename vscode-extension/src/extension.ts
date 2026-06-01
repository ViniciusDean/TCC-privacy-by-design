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

const riskToSeverity = (risk: string): vscode.DiagnosticSeverity => {
    switch (risk) {
        case 'ALTO': return vscode.DiagnosticSeverity.Error;
        case 'MEDIO': return vscode.DiagnosticSeverity.Warning;
        case 'BAIXO': return vscode.DiagnosticSeverity.Information;
        default: return vscode.DiagnosticSeverity.Information;
    }
};

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

    // Carregar configurações
    loadConfig();

    // Iniciar servidor Flask
    await startFlaskServer(context);

    // Registrar comandos
    registerCommands(context);

    // Listeners
    registerListeners(context);

    updateStatusBar('Privacy Scanner pronto', 'pass');
}

// ─────────────────────────────────────────────────────────────────────────────
// Comandos
// ─────────────────────────────────────────────────────────────────────────────

function registerCommands(context: vscode.ExtensionContext) {
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
}

// ─────────────────────────────────────────────────────────────────────────────
// Análise de arquivos
// ─────────────────────────────────────────────────────────────────────────────

async function analyzeFile(uri: vscode.Uri) {
    if (!uri.path.endsWith('.py')) {
        return; // Apenas Python
    }

    try {
        updateStatusBar('Analisando...', 'loading');

        const filePath = uri.fsPath;
        const response = await axios.post<AnalysisResponse>(
            `http://localhost:${serverPort}/api/analyze-file`,
            { filepath: filePath }
        );

        if (response.data.success) {
            displayDiagnostics(uri, response.data.vulnerabilities);
            updateStatusBar(`${response.data.vulnerabilities.length} vulnerabilidades`, response.data.vulnerabilities.length === 0 ? 'pass' : 'alert');
        }
    } catch (error) {
        console.error('Erro ao analisar arquivo:', error);
        updateStatusBar('Erro na análise', 'error');
    }
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
            // Agrupar vulnerabilidades por arquivo
            const grouped = new Map<string, Vulnerability[]>();
            for (const vuln of response.data.vulnerabilities) {
                if (!grouped.has(vuln.arquivo)) {
                    grouped.set(vuln.arquivo, []);
                }
                grouped.get(vuln.arquivo)!.push(vuln);
            }

            // Adicionar diagnostics para cada arquivo
            for (const [arquivo, vulns] of grouped) {
                const uri = vscode.Uri.file(arquivo);
                displayDiagnostics(uri, vulns);
            }

            vscode.window.showInformationMessage(
                `✅ Análise concluída: ${response.data.vulnerabilities.length} vulnerabilidades encontradas`
            );
            updateStatusBar(`${response.data.vulnerabilities.length} vulns`, 'alert');
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
                if (document.languageId === 'python') {
                    await analyzeFile(document.uri);
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

export function deactivate() {
    console.log('Privacy Scanner desativado');
}

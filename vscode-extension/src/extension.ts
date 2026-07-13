import * as vscode from 'vscode';
import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import { spawn, ChildProcessWithoutNullStreams } from 'child_process';
import {
    checkBackendHealth,
    findAvailablePort,
    normalizeServerPort,
    selectBackendPort
} from './backendEndpoint';
import { resolvePythonCommand, runProcess } from './processUtils';
import { postWithSingleRecovery } from './httpClient';
import { AnalysisCoordinator, CoordinatedAnalysisSession } from './analysisCoordinator';
import { FindingStateStore } from './findingState';
import { buildDiagnostics } from './diagnostics';
import {
    AnalysisResponse,
    AnalysisSummary,
    Finding,
    ScopeMetadata,
    aggregateAnalysisResponses,
    normalizeAnalysisResponse
} from './contract';
import {
    AnalysisProfile,
    DEFAULT_PROFILE,
    Preset,
    ProfileError,
    loadProfile,
    profileFilePath,
    serializeProfile
} from './profile';


// ─────────────────────────────────────────────────────────────────────────────
// Interfaces
// ─────────────────────────────────────────────────────────────────────────────

type Vulnerability = Finding;

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
let backendGeneration = 0;
let backendStartPromise: Promise<void> | undefined;
let statusBar: vscode.StatusBarItem;
let isAnalyzing: boolean = false;
let extensionContext: vscode.ExtensionContext;
let outputChannel: vscode.OutputChannel;
const findingState = new FindingStateStore();
let canonicalSummary: AnalysisSummary | undefined;
let currentScope: ScopeMetadata | undefined;
let currentScopeNotice: string | undefined;
let sidebarEnabled: boolean = true;
let diagnosticsEnabled: boolean = true;
const analysisCoordinator = new AnalysisCoordinator();

const ANALYSIS_TIMEOUT_MS = 15000;
const HEALTH_TIMEOUT_MS = 2000;

// Mapa global de achados: filePath -> Vulnerability[]
const allVulnerabilities = findingState.byFile;
let vulnerabilitiesProvider: VulnerabilitiesProvider;
let summaryProvider: SummaryProvider;

const IGNORED_FINDINGS_KEY = 'privacy-scanner.ignoredFindings.v2';
const LEGACY_IGNORED_VULNERABILITIES_KEY = 'privacy-scanner.ignoredVulnerabilities';

function log(message: string): void {
    outputChannel?.appendLine(`[${new Date().toISOString()}] ${message}`);
}

function workspaceRootForUri(uri?: vscode.Uri): string | undefined {
    if (uri) {
        return vscode.workspace.getWorkspaceFolder(uri)?.uri.fsPath;
    }
    return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

function profileForRoot(root?: string): AnalysisProfile | undefined {
    try {
        const profile = loadProfile(root);
        log(`Perfil carregado: ${profile.preset}.`);
        return profile;
    } catch (error) {
        const message = error instanceof ProfileError ? error.message : String(error);
        log(`Perfil invalido: ${message}`);
        vscode.window.showErrorMessage(`Perfil do Privacy Scanner invalido: ${message}`);
        return undefined;
    }
}

function isDatabaseUri(uri: vscode.Uri): boolean {
    const filePath = uri.fsPath.toLowerCase();
    return filePath.endsWith('.db') || filePath.endsWith('.sqlite') || filePath.endsWith('.sqlite3');
}

function isSupportedCodeDocument(document: vscode.TextDocument): boolean {
    return document.languageId === 'python'
        || document.languageId === 'java'
        || document.uri.fsPath.toLowerCase().endsWith('.java');
}

function vulnerabilityKey(vulnerability: Vulnerability): string {
    return findingState.key(vulnerability);
}

function isIgnored(vulnerability: Vulnerability): boolean {
    return findingState.isIgnored(vulnerability);
}

function visibleVulnerabilities(): Vulnerability[] {
    return findingState.visible();
}

function activeIgnoredCount(): number {
    return findingState.ignoredCount();
}

function refreshAllDiagnostics(): void {
    diagnosticCollection.clear();
    if (!diagnosticsEnabled) {
        return;
    }
    for (const [filePath, vulnerabilities] of allVulnerabilities) {
        if (filePath.toLowerCase().endsWith('.py') || filePath.toLowerCase().endsWith('.java')) {
            displayDiagnostics(vscode.Uri.file(filePath), vulnerabilities);
        }
    }
}

function refreshViews(): void {
    if (vulnerabilitiesProvider) {
        vulnerabilitiesProvider.refresh();
    }
    if (summaryProvider) {
        summaryProvider.refresh();
    }
}

function setAnalyzing(value: boolean, message: string = 'Analisando...'): void {
    isAnalyzing = value;
    if (value) {
        updateStatusBar(message, 'loading');
    }
    refreshViews();
}

type AnalysisSession = CoordinatedAnalysisSession;

function beginAnalysis(message: string): AnalysisSession {
    // Nenhum indicador de uma varredura anterior deve sobreviver enquanto o
    // novo escopo ainda não foi validado pelo backend.
    canonicalSummary = undefined;
    currentScope = undefined;
    currentScopeNotice = undefined;
    const session = analysisCoordinator.begin(message);
    setAnalyzing(true, message);
    return session;
}

function isCurrentSession(session: AnalysisSession): boolean {
    return analysisCoordinator.isCurrent(session);
}

function finishAnalysis(session: AnalysisSession): void {
    if (!analysisCoordinator.finish(session)) {
        return;
    }
    log(`${session.label} finalizada em ${Date.now() - session.startedAt} ms.`);
    setAnalyzing(false);
}

function cancelActiveAnalysis(): void {
    analysisCoordinator.cancel();
    if (isAnalyzing) {
        setAnalyzing(false);
    }
}

function isCancellation(error: unknown): boolean {
    return axios.isCancel(error) || (error instanceof Error && error.name === 'CanceledError');
}

function responseFromAxiosError(error: unknown): AnalysisResponse | undefined {
    if (axios.isAxiosError(error) && error.response) {
        return normalizeAnalysisResponse(error.response.data);
    }
    return undefined;
}

function applyViewConfiguration(): void {
    void vscode.commands.executeCommand(
        'setContext',
        'privacy-scanner:showVulnerabilities',
        sidebarEnabled
    );
    void vscode.commands.executeCommand(
        'setContext',
        'privacy-scanner:showSummary',
        sidebarEnabled
    );
    refreshAllDiagnostics();
    refreshViews();
}

function updateCanonicalState(result: AnalysisResponse): void {
    canonicalSummary = result.resumo;
    currentScope = result.escopo;
    currentScopeNotice = result.aviso_escopo;
}

function updateFailedScopeState(result: AnalysisResponse): void {
    updateCanonicalState(result);
    if (canonicalSummary) {
        canonicalSummary = { ...canonicalSummary, indicador_tecnico: null };
    }
}

async function ensureBackendRunning(): Promise<boolean> {
    if (serverRunning) {
        return true;
    }
    log('Backend indisponivel; iniciando recuperacao automatica.');
    await startFlaskServer(extensionContext);
    if (serverRunning) {
        return true;
    }
    vscode.window.showWarningMessage(
        'O backend compatível do Privacy Scanner não está disponível. Verifique a inicialização e a porta configurada.'
    );
    return false;
}

async function stopBackend(): Promise<void> {
    const processToStop = flaskProcess;
    backendGeneration += 1;
    flaskProcess = undefined;
    serverRunning = false;
    if (!processToStop || processToStop.killed || processToStop.exitCode !== null) {
        return;
    }
    let exited = false;
    await new Promise<void>(resolve => {
        let settled = false;
        const finish = () => {
            if (!settled) {
                settled = true;
                resolve();
            }
        };
        processToStop.once('exit', () => {
            exited = true;
            finish();
        });
        processToStop.kill();
        setTimeout(finish, 3000);
    });
    if (!exited) {
        const previousPort = serverPort;
        serverPort = await findAvailablePort();
        log(`Processo antigo nao encerrou no prazo; porta ${previousPort} abandonada e ${serverPort} selecionada.`);
    }
}

async function postBackend<T>(
    endpoint: string,
    payload: unknown,
    options: { timeout: number; signal?: AbortSignal }
): Promise<{ data: T }> {
    return postWithSingleRecovery(endpoint, payload, options, {
        baseUrl: () => `http://localhost:${serverPort}`,
        log,
        recover: async () => {
            await stopBackend();
            await startFlaskServer(extensionContext);
            return serverRunning;
        }
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Inicialização da extensão
// ─────────────────────────────────────────────────────────────────────────────

export async function activate(context: vscode.ExtensionContext) {
    console.log('🔒 Privacy Scanner LGPD ativado');
    extensionContext = context;
    outputChannel = vscode.window.createOutputChannel('Privacy Scanner');
    context.subscriptions.push(outputChannel);
    log('Extensao v1.1.0 ativada. Logs nao incluem codigo-fonte.');
    // A chave anterior podia conter o trecho usado como identificador. Ela é
    // removida na migração para não manter código-fonte bruto no estado local.
    await context.workspaceState.update(LEGACY_IGNORED_VULNERABILITIES_KEY, undefined);
    findingState.replaceIgnored(
        context.workspaceState.get<string[]>(IGNORED_FINDINGS_KEY, [])
    );

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
            [
                { scheme: 'file', language: 'python' },
                { scheme: 'file', language: 'java' }
            ],
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

    // Carregar configurações
    loadConfig();

    // Iniciar servidor Flask
    await startFlaskServer(context);
    if (!serverRunning) {
        setAnalyzing(false);
    }

    // Registrar comandos
    registerCommands(context);

    // Listeners
    registerListeners(context);

    const activeEditor = vscode.window.activeTextEditor;
    if (activeEditor && (isSupportedCodeDocument(activeEditor.document) || isDatabaseUri(activeEditor.document.uri))) {
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

    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.createProfile', async () => {
            const root = workspaceRootForUri(vscode.window.activeTextEditor?.document.uri);
            if (!root) {
                vscode.window.showWarningMessage('Abra uma pasta para criar o perfil.');
                return;
            }
            const target = profileFilePath(root);
            if (!fs.existsSync(target)) {
                fs.writeFileSync(target, serializeProfile(DEFAULT_PROFILE), 'utf8');
            }
            const document = await vscode.workspace.openTextDocument(vscode.Uri.file(target));
            await vscode.window.showTextDocument(document);
        }),
        vscode.commands.registerCommand('privacy-scanner.selectProfile', async () => {
            const selectedPreset = await vscode.window.showQuickPick(
                ['conservador', 'equilibrado', 'completo'],
                { title: 'Selecionar perfil de analise' }
            );
            const preset = selectedPreset as Preset | undefined;
            const root = workspaceRootForUri(vscode.window.activeTextEditor?.document.uri);
            if (!preset || !root) {
                return;
            }
            const current = profileForRoot(root);
            if (!current) {
                return;
            }
            fs.writeFileSync(
                profileFilePath(root),
                serializeProfile({ ...current, preset }),
                'utf8'
            );
            vscode.window.showInformationMessage(`Perfil ${preset} selecionado.`);
        }),
        vscode.commands.registerCommand('privacy-scanner.validateProfile', async () => {
            const root = workspaceRootForUri(vscode.window.activeTextEditor?.document.uri);
            if (profileForRoot(root)) {
                vscode.window.showInformationMessage('Perfil do Privacy Scanner valido.');
            }
        }),
        vscode.commands.registerCommand('privacy-scanner.showLogs', () => outputChannel.show(true)),
        vscode.commands.registerCommand('privacy-scanner.setupBackend', async () => {
            await setupBackendEnvironment();
        }),
        vscode.commands.registerCommand('privacy-scanner.restartBackend', async () => {
            await stopBackend();
            await startFlaskServer(extensionContext);
            vscode.window.showInformationMessage(
                serverRunning ? 'Backend reiniciado.' : 'Nao foi possivel reiniciar o backend.'
            );
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
            cancelActiveAnalysis();
            allVulnerabilities.clear();
            canonicalSummary = undefined;
            currentScope = undefined;
            currentScopeNotice = undefined;
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

    // Ignorar uma ocorrência apenas na interface.
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.ignoreVulnerability', async (target: VulnerabilityTreeItem | Vulnerability) => {
            const vulnerability = target instanceof VulnerabilityTreeItem ? target.data as Vulnerability : target;
            if (!vulnerability?.arquivo || !vulnerability?.categoria) {
                return;
            }

            findingState.ignoredKeys.add(vulnerabilityKey(vulnerability));
            await extensionContext.workspaceState.update(
                IGNORED_FINDINGS_KEY,
                Array.from(findingState.ignoredKeys)
            );
            refreshAllDiagnostics();
            refreshViews();
            const visibleCount = visibleVulnerabilities().length;
            updateStatusBar(`${visibleCount} achados`, visibleCount === 0 ? 'pass' : 'alert');
            vscode.window.showInformationMessage(
                'Achado ocultado somente na interface. O indicador técnico e os relatórios não são alterados.'
            );
        })
    );

    // Restaurar todas as ocorrências ocultadas no workspace.
    context.subscriptions.push(
        vscode.commands.registerCommand('privacy-scanner.restoreIgnoredVulnerabilities', async () => {
            if (findingState.ignoredKeys.size === 0) {
                vscode.window.showInformationMessage('Nenhum achado está ocultado na interface.');
                return;
            }

            findingState.ignoredKeys.clear();
            await extensionContext.workspaceState.update(IGNORED_FINDINGS_KEY, []);
            refreshAllDiagnostics();
            refreshViews();
            const visibleCount = visibleVulnerabilities().length;
            updateStatusBar(`${visibleCount} achados`, visibleCount === 0 ? 'pass' : 'alert');
            vscode.window.showInformationMessage('Achados ocultados restaurados na interface.');
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
            if (!sidebarEnabled) {
                vscode.window.showInformationMessage(
                    'A sidebar está desativada em privacy-scanner.enableSidebar.'
                );
                return;
            }
            await vscode.commands.executeCommand('workbench.view.extension.privacy-scanner-sidebar');
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

async function analyzeFile(uri: vscode.Uri): Promise<void> {
    const isCode = uri.path.toLowerCase().endsWith('.py') || uri.path.toLowerCase().endsWith('.java');
    const isDB = isDatabaseUri(uri);
    const filePath = uri.fsPath;

    if (!isCode && !isDB) {
        return;
    }
    if (!await ensureBackendRunning()) {
        return;
    }
    const profile = profileForRoot(workspaceRootForUri(uri));
    if (!profile) {
        return;
    }

    const session = beginAnalysis('Analisando arquivo...');
    try {
        const endpoint = isCode ? '/api/analyze-file' : '/api/analyze-database';
        const payload = isCode ? { filepath: filePath, profile } : { database: filePath, profile };

        const response = await postBackend<unknown>(
            endpoint,
            payload,
            { timeout: ANALYSIS_TIMEOUT_MS, signal: session.controller.signal }
        );
        if (!isCurrentSession(session)) {
            return;
        }

        const result = normalizeAnalysisResponse(response.data);
        if (!result.success) {
            allVulnerabilities.delete(filePath);
            if (isCode) {
                diagnosticCollection.delete(uri);
            }
            updateFailedScopeState(result);
            vscode.window.showWarningMessage('O backend não concluiu a análise do arquivo.');
            updateStatusBar('Análise não concluída', 'error');
            return;
        }

        // Atualizar diagnósticos para código; banco não tem linha útil no editor.
        if (isCode) {
            displayDiagnostics(uri, result.achados);
        }

        if (result.achados.length > 0) {
            allVulnerabilities.set(filePath, result.achados);
        } else {
            allVulnerabilities.delete(filePath);
        }

        updateCanonicalState(result);
        const rawTotal = result.resumo?.total ?? result.achados.length;
        updateStatusBar(
            `${rawTotal} achados técnicos`,
            rawTotal === 0 ? 'pass' : 'alert'
        );
    } catch (error) {
        if (!isCurrentSession(session) || isCancellation(error)) {
            return;
        }
        const backendFailure = responseFromAxiosError(error);
        if (backendFailure) {
            allVulnerabilities.delete(filePath);
            if (isCode) {
                diagnosticCollection.delete(uri);
            }
            updateFailedScopeState(backendFailure);
            vscode.window.showWarningMessage('O backend recusou a análise do arquivo.');
            updateStatusBar('Análise não concluída', 'error');
            return;
        }
        console.error('Erro ao analisar arquivo:', error);
        log(`Falha na analise de arquivo: ${error instanceof Error ? error.name : 'erro desconhecido'}.`);
        vscode.window.showErrorMessage('Erro ao analisar arquivo. Verifique o backend e tente novamente.');
        updateStatusBar('Erro na análise', 'error');
    } finally {
        finishAnalysis(session);
    }
}

async function setupBackendEnvironment(): Promise<void> {
    const confirmation = await vscode.window.showInformationMessage(
        'Criar um ambiente Python isolado e instalar Flask/ReportLab para o Privacy Scanner?',
        { modal: true },
        'Configurar'
    );
    if (confirmation !== 'Configurar') {
        return;
    }
    const configured = vscode.workspace.getConfiguration('privacy-scanner').get('pythonPath', 'python');
    const python = resolvePythonCommand(configured);
    if (!python) {
        vscode.window.showErrorMessage('Python 3 nao encontrado. Instale o Python ou configure privacy-scanner.pythonPath.');
        return;
    }
    const storagePath = extensionContext.globalStorageUri.fsPath;
    const venvPath = path.join(storagePath, 'backend-venv');
    const venvPython = path.join(
        venvPath,
        process.platform === 'win32' ? 'Scripts' : 'bin',
        process.platform === 'win32' ? 'python.exe' : 'python'
    );
    const requirementsPath = path.join(
        extensionContext.extensionPath,
        'python_backend',
        'requirements-runtime.txt'
    );
    try {
        await vscode.window.withProgress(
            {
                location: vscode.ProgressLocation.Notification,
                title: 'Configurando backend do Privacy Scanner',
                cancellable: false
            },
            async progress => {
                fs.mkdirSync(storagePath, { recursive: true });
                if (!fs.existsSync(venvPython)) {
                    progress.report({ message: 'criando ambiente Python' });
                    await runProcess(python.command, [...python.prefixArgs, '-m', 'venv', venvPath], storagePath);
                }
                progress.report({ message: 'instalando dependencias runtime' });
                await runProcess(
                    venvPython,
                    ['-m', 'pip', 'install', '--disable-pip-version-check', '-r', requirementsPath],
                    storagePath
                );
            }
        );
        await vscode.workspace.getConfiguration('privacy-scanner').update(
            'pythonPath',
            venvPython,
            vscode.ConfigurationTarget.Global
        );
        await stopBackend();
        await startFlaskServer(extensionContext);
        vscode.window.showInformationMessage(
            serverRunning ? 'Backend configurado e validado.' : 'Dependencias instaladas, mas o backend nao respondeu.'
        );
    } catch (error) {
        log(`Falha ao configurar backend: ${error instanceof Error ? error.name : 'erro desconhecido'}.`);
        vscode.window.showErrorMessage('Nao foi possivel configurar o backend. Abra os logs para detalhes.');
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

    return diagnostic.message.split(':')[0] || 'Achado técnico de privacidade';
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

            const vulnerability = (allVulnerabilities.get(document.uri.fsPath) || []).find(v =>
                v.linha === diagnostic.range.start.line + 1
                && v.categoria === payload.categoria
            );
            if (vulnerability) {
                const ignoreAction = new vscode.CodeAction(
                    `Ocultar este achado na interface: ${payload.categoria}`,
                    vscode.CodeActionKind.QuickFix
                );
                ignoreAction.diagnostics = [diagnostic];
                ignoreAction.command = {
                    command: 'privacy-scanner.ignoreVulnerability',
                    title: 'Ocultar achado na interface',
                    arguments: [vulnerability]
                };
                actions.push(ignoreAction);
            }
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
    if (!await ensureBackendRunning()) {
        return;
    }

    const session = beginAnalysis('Analisando banco SQLite...');
    let total = 0;
    let failures = 0;
    try {
        for (const file of files) {
            if (!isCurrentSession(session)) {
                return;
            }

            try {
                const result = await analyzeDatabaseUri(file, session);
                if (!isCurrentSession(session)) {
                    return;
                }
                if (!result.success) {
                    failures += 1;
                    updateFailedScopeState(result);
                    continue;
                }
                total += result.resumo?.total ?? result.achados.length;
                updateCanonicalState(result);
            } catch (error) {
                if (isCancellation(error) || !isCurrentSession(session)) {
                    return;
                }
                failures += 1;
                console.error(`Erro ao analisar banco ${file.fsPath}:`, error);
                log(`Falha na analise de banco: ${error instanceof Error ? error.name : 'erro desconhecido'}.`);
            }
        }

        if (!isCurrentSession(session)) {
            return;
        }
        const suffix = failures > 0 ? ` (${failures} banco(s) não analisado(s))` : '';
        vscode.window.showInformationMessage(
            `Análise de banco concluída: ${total} achados técnicos encontrados${suffix}`
        );
        updateStatusBar(`${total} achados técnicos`, total === 0 ? 'pass' : 'alert');
    } finally {
        finishAnalysis(session);
    }
}

async function analyzeDatabaseUri(uri: vscode.Uri, session: AnalysisSession): Promise<AnalysisResponse> {
    const filePath = uri.fsPath;
    const profile = profileForRoot(workspaceRootForUri(uri));
    if (!profile) {
        throw new ProfileError('Perfil invalido para o banco selecionado.');
    }
    let response: { data: unknown };
    try {
        response = await postBackend<unknown>(
            '/api/analyze-database',
            { database: filePath, profile },
            { timeout: ANALYSIS_TIMEOUT_MS, signal: session.controller.signal }
        );
    } catch (error) {
        const backendFailure = responseFromAxiosError(error);
        if (backendFailure) {
            allVulnerabilities.delete(filePath);
            return backendFailure;
        }
        throw error;
    }
    if (!isCurrentSession(session)) {
        throw new Error('Resposta de análise de banco ultrapassada.');
    }

    const result = normalizeAnalysisResponse(response.data);
    if (!result.success) {
        allVulnerabilities.delete(filePath);
        return result;
    }

    if (result.achados.length > 0) {
        allVulnerabilities.set(filePath, result.achados);
    } else {
        allVulnerabilities.delete(filePath);
    }

    return result;
}

async function analyzeWorkspace(): Promise<void> {
    if (!await ensureBackendRunning()) {
        return;
    }
    const session = beginAnalysis('Analisando projeto...');
    try {
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            vscode.window.showWarningMessage('Nenhuma pasta de trabalho aberta');
            return;
        }

        allVulnerabilities.clear();
        diagnosticCollection.clear();
        const responses: AnalysisResponse[] = [];
        for (const folder of vscode.workspace.workspaceFolders) {
            const profile = profileForRoot(folder.uri.fsPath);
            if (!profile) {
                return;
            }
            const response = await postBackend<unknown>(
                '/api/analyze-directory',
                { directory: folder.uri.fsPath, profile },
                { timeout: ANALYSIS_TIMEOUT_MS, signal: session.controller.signal }
            );
            if (!isCurrentSession(session)) {
                return;
            }
            const normalized = normalizeAnalysisResponse(response.data);
            if (!normalized.success) {
                vscode.window.showWarningMessage(
                    `O backend não concluiu a análise de ${folder.name}.`
                );
                updateStatusBar('Análise não concluída', 'error');
            }
            responses.push(normalized);
        }
        const result = aggregateAnalysisResponses(responses);
        if (!result.success) {
            updateFailedScopeState(result);
            updateStatusBar('Analise nao concluida', 'error');
            return;
        }

        // Limpar mapa global antes de análise completa.
        // Agrupar achados por arquivo.
        const grouped = new Map<string, Vulnerability[]>();
        for (const finding of result.achados) {
            if (!grouped.has(finding.arquivo)) {
                grouped.set(finding.arquivo, []);
            }
            grouped.get(finding.arquivo)!.push(finding);
        }

        // Adicionar diagnósticos e atualizar mapa global.
        for (const [arquivo, findings] of grouped) {
            allVulnerabilities.set(arquivo, findings);

            // Só mostra diagnósticos para arquivos de código suportados.
            if (arquivo.toLowerCase().endsWith('.py') || arquivo.toLowerCase().endsWith('.java')) {
                displayDiagnostics(vscode.Uri.file(arquivo), findings);
            }
        }

        updateCanonicalState(result);
        const rawTotal = result.resumo?.total ?? result.achados.length;
        vscode.window.showInformationMessage(
            `Análise concluída: ${rawTotal} achados técnicos encontrados`
        );
        updateStatusBar(`${rawTotal} achados técnicos`, rawTotal === 0 ? 'pass' : 'alert');
    } catch (error) {
        if (!isCurrentSession(session) || isCancellation(error)) {
            return;
        }
        const backendFailure = responseFromAxiosError(error);
        if (backendFailure) {
            allVulnerabilities.clear();
            diagnosticCollection.clear();
            updateFailedScopeState(backendFailure);
            vscode.window.showWarningMessage('O backend recusou a análise do projeto.');
            updateStatusBar('Análise não concluída', 'error');
            return;
        }
        console.error('Erro ao analisar projeto:', error);
        log(`Falha na analise de projeto: ${error instanceof Error ? error.name : 'erro desconhecido'}.`);
        vscode.window.showErrorMessage('Erro ao analisar projeto. Verifique o backend e tente novamente.');
        updateStatusBar('Erro na análise', 'error');
    } finally {
        finishAnalysis(session);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Exibição de diagnósticos
// ─────────────────────────────────────────────────────────────────────────────

function displayDiagnostics(uri: vscode.Uri, vulnerabilities: Vulnerability[]): void {
    if (!diagnosticsEnabled) {
        diagnosticCollection.delete(uri);
        return;
    }
    diagnosticCollection.set(uri, buildDiagnostics(uri, vulnerabilities, isIgnored));
}

// ─────────────────────────────────────────────────────────────────────────────
// Listeners
// ─────────────────────────────────────────────────────────────────────────────

function registerListeners(context: vscode.ExtensionContext) {
    const autoAnalyzeEnabled = (): boolean => vscode.workspace
        .getConfiguration('privacy-scanner')
        .get('autoAnalyzeOnSave', true);

    const analyzeDocumentIfEnabled = async (document: vscode.TextDocument): Promise<void> => {
        if (isAnalyzing) {
            log('Analise automatica adiada porque outra analise esta em andamento.');
            return;
        }
        if (
            autoAnalyzeEnabled()
            && (isSupportedCodeDocument(document) || isDatabaseUri(document.uri))
        ) {
            await analyzeFile(document.uri);
        }
    };

    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(analyzeDocumentIfEnabled),
        vscode.workspace.onDidOpenTextDocument(analyzeDocumentIfEnabled),
        vscode.window.onDidChangeActiveTextEditor(async (editor) => {
            if (editor) {
                await analyzeDocumentIfEnabled(editor.document);
            }
        }),
        vscode.workspace.onDidChangeConfiguration(event => {
            if (
                event.affectsConfiguration('privacy-scanner.enableSidebar')
                || event.affectsConfiguration('privacy-scanner.showDiagnostics')
            ) {
                loadConfig(false);
            }
            if (event.affectsConfiguration('privacy-scanner.serverPort')) {
                vscode.window.showInformationMessage(
                    'A alteração de privacy-scanner.serverPort será aplicada após recarregar a janela.'
                );
            }
        })
    );

    const profileWatcher = vscode.workspace.createFileSystemWatcher('**/.privacy-scanner.json');
    const profileChanged = async (uri: vscode.Uri): Promise<void> => {
        const profile = profileForRoot(path.dirname(uri.fsPath));
        log('Arquivo de perfil alterado.');
        if (!profile) {
            return;
        }
        const choice = await vscode.window.showInformationMessage(
            `Perfil ${profile.preset} atualizado. Reanalisar o workspace?`,
            'Reanalisar'
        );
        if (choice === 'Reanalisar') {
            await analyzeWorkspace();
        }
    };
    context.subscriptions.push(
        profileWatcher,
        profileWatcher.onDidChange(profileChanged),
        profileWatcher.onDidCreate(profileChanged),
        profileWatcher.onDidDelete(profileChanged)
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// Servidor Flask
// ─────────────────────────────────────────────────────────────────────────────

function wait(milliseconds: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, milliseconds));
}

async function startFlaskServer(context: vscode.ExtensionContext): Promise<void> {
    if (backendStartPromise) {
        return backendStartPromise;
    }
    backendStartPromise = startFlaskServerInternal(context);
    try {
        await backendStartPromise;
    } finally {
        backendStartPromise = undefined;
    }
}

async function startFlaskServerInternal(context: vscode.ExtensionContext): Promise<void> {
    const pythonPath = vscode.workspace.getConfiguration('privacy-scanner').get('pythonPath', 'python');
    const extensionPath = context.extensionPath;
    const bundledServer = path.join(extensionPath, 'python_backend', 'server.py');
    const developmentServer = path.join(extensionPath, '..', 'server.py');
    const serverScript = fs.existsSync(bundledServer)
        ? bundledServer
        : developmentServer;

    if (!fs.existsSync(serverScript)) {
        console.warn(`Arquivo do servidor não encontrado: ${serverScript}`);
        vscode.window.showErrorMessage(
            'Backend do Privacy Scanner não encontrado. Reinstale a extensão ou gere novamente o pacote VSIX.'
        );
        return;
    }

    const portDecision = await selectBackendPort(serverPort);
    serverPort = portDecision.port;
    if (portDecision.action === 'relocate') {
        log(`Porta ${portDecision.occupiedPort} ocupada; usando porta livre ${serverPort}.`);
    } else if (portDecision.action === 'reuse') {
        serverRunning = true;
        log(`Backend compativel reutilizado na porta ${serverPort}.`);
        return;
    }

    let stderrOutput = '';
    const python = resolvePythonCommand(pythonPath);
    if (!python) {
        vscode.window.showErrorMessage(
            'Python 3 nao encontrado. Configure privacy-scanner.pythonPath.'
        );
        return;
    }
    log(`Interpretador Python validado; porta ${serverPort}.`);
    const startedProcess = spawn(
        python.command,
        [...python.prefixArgs, serverScript, String(serverPort)],
        { cwd: path.dirname(serverScript), windowsHide: true }
    );
    const generation = ++backendGeneration;
    flaskProcess = startedProcess;

    startedProcess.stdout.on('data', data => {
        console.log(`[Privacy Scanner Server] ${data.toString().trim()}`);
    });
    startedProcess.stderr.on('data', data => {
        const message = data.toString();
        stderrOutput += message;
        console.error(`[Privacy Scanner Server] ${message.trim()}`);
    });
    startedProcess.on('error', error => {
        if (generation === backendGeneration && flaskProcess === startedProcess) {
            serverRunning = false;
        }
        console.error(`Erro ao iniciar servidor Flask: ${error}`);
    });
    startedProcess.on('exit', code => {
        if (generation === backendGeneration && flaskProcess === startedProcess) {
            serverRunning = false;
            flaskProcess = undefined;
        }
        if (code !== 0 && code !== null) {
            console.error(`Servidor Flask encerrado com código ${code}`);
        }
    });

    for (let attempt = 0; attempt < 30; attempt += 1) {
        await wait(500);
        const health = await checkBackendHealth(serverPort, HEALTH_TIMEOUT_MS);
        if (health.reachable && health.valid) {
            serverRunning = true;
            log(`Backend iniciado na porta ${serverPort}, versao ${health.version}.`);
            return;
        }
        if (health.reachable && !health.valid) {
            startedProcess.kill();
            vscode.window.showErrorMessage(
                `O serviço iniciado na porta ${serverPort} não é um backend compatível. ${health.reason || ''}`
            );
            return;
        }
    }

    console.error('Timeout ao conectar ao servidor Flask');
    if (!startedProcess.killed) {
        startedProcess.kill();
    }
    if (
        stderrOutput.includes('ModuleNotFoundError')
        || stderrOutput.includes('No module named')
    ) {
        vscode.window.showErrorMessage(
            'Dependencias Python ausentes. Execute "Privacy Scanner: Configurar dependencias do backend".'
        );
        return;
    }
    vscode.window.showErrorMessage(
        `Não foi possível iniciar o Privacy Scanner na porta ${serverPort}. Consulte o console "Extension Host".`
    );
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
                description: 'Relatorio formal',
                detail: 'Gera um relatorio PDF estatico para entrega/compliance',
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

async function exportReport(format: 'html' | 'json' | 'pdf', targetUri?: vscode.Uri) {
    try {
        if (!await ensureBackendRunning()) {
            return;
        }
        if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
            vscode.window.showWarningMessage('Nenhuma pasta de trabalho aberta');
            return;
        }

        let selectedFolder = vscode.workspace.workspaceFolders[0];
        if (vscode.workspace.workspaceFolders.length > 1) {
            const selected = await vscode.window.showQuickPick(
                vscode.workspace.workspaceFolders.map(folder => ({
                    label: folder.name,
                    description: folder.uri.fsPath,
                    folder
                })),
                { title: 'Selecionar pasta para exportar' }
            );
            if (!selected) {
                return;
            }
            selectedFolder = selected.folder;
        }
        const workspacePath = selectedFolder.uri.fsPath;
        const profile = profileForRoot(workspacePath);
        if (!profile) {
            return;
        }
        const filepath = targetUri?.fsPath || getDefaultReportUri(format)?.fsPath;

        if (!filepath) {
            vscode.window.showWarningMessage('Destino do relatorio nao informado');
            return;
        }

        const filename = path.basename(filepath);

        const response = await postBackend<any>(
            '/api/export',
            { directory: workspacePath, format, profile },
            { timeout: ANALYSIS_TIMEOUT_MS }
        );

        if (response.data.content) {
            const content = response.data.encoding === 'base64'
                ? Buffer.from(response.data.content, 'base64')
                : response.data.content;
            fs.writeFileSync(filepath, content);
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
        log(`Falha na exportacao: ${error instanceof Error ? error.name : 'erro desconhecido'}.`);
        vscode.window.showErrorMessage('Erro ao exportar relatório');
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Utilitários
// ─────────────────────────────────────────────────────────────────────────────

function loadConfig(loadServerPort: boolean = true): void {
    const config = vscode.workspace.getConfiguration('privacy-scanner');
    if (loadServerPort) {
        serverPort = normalizeServerPort(config.get<unknown>('serverPort', 5000));
    }
    sidebarEnabled = config.get('enableSidebar', true);
    diagnosticsEnabled = config.get('showDiagnostics', true);
    applyViewConfiguration();
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
            this.contextValue = 'vulnerability';
            const risk = data.risco;
            this.iconPath = new vscode.ThemeIcon(
                risk === 'ALTO' ? 'error' : risk === 'MEDIO' ? 'warning' : 'info'
            );
            this.description = data.linha > 0 ? `Linha ${data.linha}` : path.basename(data.arquivo);
            this.tooltip = [
                `Categoria: ${data.categoria}`,
                `Confiança: ${data.confianca || 'ALTA'}`,
                data.risco_base && data.risco_base !== data.risco
                    ? `Severidade base: ${data.risco_base}`
                    : undefined,
                `Arquivo: ${data.arquivo}`,
                data.linha > 0 ? `Linha: ${data.linha}` : undefined,
                `Evidência segura: ${data.evidencia_segura}`,
                data.artigo_lgpd ? `Referência normativa potencial: ${data.artigo_lgpd}` : undefined
            ].filter(Boolean).join('\n');
            if (data.linha > 0) {
                this.command = {
                    command: 'privacy-scanner.openVulnerability',
                    title: 'Abrir achado técnico',
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

            const visible = visibleVulnerabilities();
            if (visible.length === 0) {
                const message = activeIgnoredCount() > 0
                    ? 'Nenhum achado visível'
                    : 'Nenhum achado encontrado';
                return Promise.resolve([new VulnerabilityTreeItem(message, vscode.TreeItemCollapsibleState.None, 'empty')]);
            }

            const risks: Array<'ALTO' | 'MEDIO' | 'BAIXO'> = ['ALTO', 'MEDIO', 'BAIXO'];
            const groups = risks
                .map(risk => ({
                    risk,
                    count: visible
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
                .filter(([, vulns]) => vulns.some(v => v.risco === risk && !isIgnored(v)))
                .sort(([a], [b]) => a.localeCompare(b));

            return Promise.resolve(files.map(([filePath, vulns]) => {
                const count = vulns.filter(v => v.risco === risk && !isIgnored(v)).length;
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
                .filter(v => v.risco === risk && !isIgnored(v))
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
                new VulnerabilityTreeItem('Indicador técnico: calculando...', vscode.TreeItemCollapsibleState.None, 'loading'),
                new VulnerabilityTreeItem('Analise em andamento', vscode.TreeItemCollapsibleState.None, 'loading'),
                new VulnerabilityTreeItem('Aguardando resultado do scanner', vscode.TreeItemCollapsibleState.None, 'loading')
            ]);
        }

        const summary = canonicalSummary;
        const visibleCount = visibleVulnerabilities().length;
        const displayMetric = (value: number | null | undefined): string => value === null || value === undefined
            ? 'não informado'
            : String(value);
        const indicator = summary?.indicador_tecnico;
        const items = [
            new VulnerabilityTreeItem(
                indicator === null || indicator === undefined
                    ? 'Indicador técnico: não disponível para este escopo'
                    : `Indicador técnico: ${indicator}/100`,
                vscode.TreeItemCollapsibleState.None,
                'summary',
                { icon: 'shield' }
            ),
            new VulnerabilityTreeItem(
                'Limite: indícios técnicos, não conclusão jurídica',
                vscode.TreeItemCollapsibleState.None,
                'summary',
                { icon: 'info' }
            ),
            new VulnerabilityTreeItem(
                `Total bruto do backend: ${displayMetric(summary?.total)} achados`,
                vscode.TreeItemCollapsibleState.None,
                'summary',
                { icon: 'search' }
            ),
            new VulnerabilityTreeItem(
                `Risco ALTO (backend): ${displayMetric(summary?.por_risco.ALTO)}`,
                vscode.TreeItemCollapsibleState.None,
                'summary',
                { icon: 'error' }
            ),
            new VulnerabilityTreeItem(
                `Risco MÉDIO (backend): ${displayMetric(summary?.por_risco.MEDIO)}`,
                vscode.TreeItemCollapsibleState.None,
                'summary',
                { icon: 'warning' }
            ),
            new VulnerabilityTreeItem(
                `Risco BAIXO (backend): ${displayMetric(summary?.por_risco.BAIXO)}`,
                vscode.TreeItemCollapsibleState.None,
                'summary',
                { icon: 'info' }
            ),
            new VulnerabilityTreeItem(
                `Achados visíveis na interface: ${visibleCount}`,
                vscode.TreeItemCollapsibleState.None,
                'summary',
                { icon: 'eye' }
            )
        ];

        if (summary?.criterio_indicador) {
            items.push(new VulnerabilityTreeItem(
                `Critério do indicador: ${summary.criterio_indicador}`,
                vscode.TreeItemCollapsibleState.None,
                'summary',
                { icon: 'note' }
            ));
        }
        const scopeNotice = summary?.aviso_escopo || currentScopeNotice;
        if (scopeNotice) {
            items.push(new VulnerabilityTreeItem(
                `Escopo: ${scopeNotice}`,
                vscode.TreeItemCollapsibleState.None,
                'summary',
                { icon: 'info' }
            ));
        }
        if (currentScope?.status) {
            items.push(new VulnerabilityTreeItem(
                `Status da varredura: ${currentScope.status}`,
                vscode.TreeItemCollapsibleState.None,
                'summary',
                { icon: 'pulse' }
            ));
        }
        const scopeCounters: Array<[string, number | undefined, string]> = [
            ['Arquivos elegíveis', currentScope?.arquivos_elegiveis, 'files'],
            ['Arquivos analisados', currentScope?.arquivos_analisados, 'file-code'],
            ['Arquivos ignorados', currentScope?.arquivos_ignorados, 'eye-closed'],
            ['Arquivos com falha', currentScope?.arquivos_falhos, 'warning']
        ];
        for (const [label, value, icon] of scopeCounters) {
            if (value !== undefined) {
                items.push(new VulnerabilityTreeItem(
                    `${label}: ${value}`,
                    vscode.TreeItemCollapsibleState.None,
                    'summary',
                    { icon }
                ));
            }
        }
        const ignoredCount = activeIgnoredCount();
        if (ignoredCount > 0) {
            items.push(new VulnerabilityTreeItem(
                `Ocultados somente na interface: ${ignoredCount}`,
                vscode.TreeItemCollapsibleState.None,
                'summary',
                { icon: 'eye-closed' }
            ));
        }
        return Promise.resolve(items);
    }
}

export async function deactivate() {
    cancelActiveAnalysis();
    await stopBackend();
    console.log('Privacy Scanner desativado');
}

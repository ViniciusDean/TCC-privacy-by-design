import type * as vscode from 'vscode';

export type QuickActionsBackendStatus = 'starting' | 'ready' | 'unavailable';

export interface QuickActionsState {
    activeResource?: vscode.Uri;
    activeFileName?: string;
    activeFileSupported: boolean;
    hasWorkspace: boolean;
    profilePreset?: string;
    profileCustomizationCount?: number;
    invalidProfileRoots?: readonly string[];
    profileValid: boolean;
    backendStatus: QuickActionsBackendStatus;
    ignoredCount: number;
}

export interface QuickActionCommandIds {
    analyze: string;
    analyzeAll: string;
    analyzeDatabase: string;
    exportReport: string;
    configureProfile: string;
    selectProfile: string;
    createProfile: string;
    validateProfile: string;
    clearResults: string;
    restoreIgnoredVulnerabilities: string;
    setupBackend: string;
    restartBackend: string;
    showLogs: string;
    openSettings: string;
}

export const DEFAULT_QUICK_ACTION_COMMAND_IDS: Readonly<QuickActionCommandIds> = {
    analyze: 'privacy-scanner.analyze',
    analyzeAll: 'privacy-scanner.analyzeAll',
    analyzeDatabase: 'privacy-scanner.analyzeDatabase',
    exportReport: 'privacy-scanner.exportReport',
    configureProfile: 'privacy-scanner.configureProfile',
    selectProfile: 'privacy-scanner.selectProfile',
    createProfile: 'privacy-scanner.createProfile',
    validateProfile: 'privacy-scanner.validateProfile',
    clearResults: 'privacy-scanner.clearResults',
    restoreIgnoredVulnerabilities: 'privacy-scanner.restoreIgnoredVulnerabilities',
    setupBackend: 'privacy-scanner.setupBackend',
    restartBackend: 'privacy-scanner.restartBackend',
    showLogs: 'privacy-scanner.showLogs',
    openSettings: 'workbench.action.openSettings'
};

export interface QuickActionCommandDescriptor {
    id: string;
    arguments?: readonly unknown[];
}

export interface QuickActionDescriptor {
    id: string;
    kind: 'action' | 'group';
    label: string;
    description?: string;
    tooltip: string;
    icon: string;
    enabled: boolean;
    command?: QuickActionCommandDescriptor;
    children?: readonly QuickActionDescriptor[];
}

export type QuickActionsStateSource = QuickActionsState | (() => QuickActionsState);

type VscodeApi = typeof import('vscode');

const SETTINGS_QUERY = '@ext:fatec-tcc.privacy-scanner-lgpd';

export function shouldShowQuickActionsOnboarding(
    sidebarEnabled: boolean,
    alreadyShown: boolean
): boolean {
    return sidebarEnabled && !alreadyShown;
}

function command(
    id: string,
    enabled: boolean,
    args?: readonly unknown[]
): QuickActionCommandDescriptor | undefined {
    if (!enabled) {
        return undefined;
    }
    return args && args.length > 0 ? { id, arguments: args } : { id };
}

function supportAction(
    id: string,
    label: string,
    tooltip: string,
    icon: string,
    commandId: string,
    enabled: boolean = true,
    description?: string,
    args?: readonly unknown[]
): QuickActionDescriptor {
    return {
        id,
        kind: 'action',
        label,
        description,
        tooltip,
        icon,
        enabled,
        command: command(commandId, enabled, args)
    };
}

function backendDescription(status: QuickActionsBackendStatus): string {
    switch (status) {
        case 'starting':
            return 'Backend: iniciando';
        case 'ready':
            return 'Backend: pronto';
        case 'unavailable':
            return 'Backend: indisponível';
    }
}

/**
 * Cria a estrutura da árvore sem acessar a API do VS Code. Isso mantém as regras
 * de habilitação, rótulos e comandos testáveis em Node puro.
 */
export function buildQuickActionDescriptors(
    state: QuickActionsState,
    commandOverrides: Partial<QuickActionCommandIds> = {}
): readonly QuickActionDescriptor[] {
    const commandIds: QuickActionCommandIds = {
        ...DEFAULT_QUICK_ACTION_COMMAND_IDS,
        ...commandOverrides
    };
    const activeFileName = state.activeFileName?.trim();
    const canAnalyzeFile = Boolean(state.activeResource && state.activeFileSupported);
    const analyzeFileDescription = canAnalyzeFile
        ? activeFileName
        : activeFileName
            ? `${activeFileName} não é Python ou Java`
            : 'Nenhum arquivo ativo';
    const analyzeFileTooltip = canAnalyzeFile
        ? `Analisar ${activeFileName || 'o arquivo ativo'}`
        : 'Abra um arquivo Python ou Java para analisar.';
    const canConfigureProfile = state.hasWorkspace;
    const profilePreset = state.profilePreset?.trim() || 'conservador';
    const rawCustomizationCount = state.profileCustomizationCount ?? 0;
    const profileCustomizationCount = Number.isFinite(rawCustomizationCount)
        ? Math.max(0, Math.floor(rawCustomizationCount))
        : 0;
    const profileSummary = profileCustomizationCount > 0
        ? `${profilePreset} + ${profileCustomizationCount} personaliza${profileCustomizationCount === 1 ? 'ção' : 'ções'}`
        : profilePreset;
    const invalidProfileRoots = (state.invalidProfileRoots ?? [])
        .map(root => root.trim())
        .filter(Boolean);
    const invalidProfileDescription = invalidProfileRoots.length > 0
        ? `Inválido: ${invalidProfileRoots.join(', ')}`
        : 'Perfil inválido';
    const profileDescription = !state.hasWorkspace
        ? 'Abra uma pasta de trabalho'
        : !state.profileValid
            ? invalidProfileDescription
            : profileSummary;
    const profileTooltip = !state.hasWorkspace
        ? 'Abra uma pasta de trabalho para configurar um perfil.'
        : !state.profileValid
            ? `${invalidProfileDescription}. Abrir o assistente para corrigir ou recriar o perfil.`
            : `Configurar perfil de análise. Atual: ${profileSummary}.`;
    const ignoredCount = Math.max(0, state.ignoredCount);
    const canRestoreIgnored = ignoredCount > 0;
    const canRestartBackend = state.backendStatus !== 'starting';

    const supportChildren: readonly QuickActionDescriptor[] = [
        supportAction(
            'clear-results',
            'Limpar resultados',
            'Remover os achados e diagnósticos exibidos na interface.',
            'clear-all',
            commandIds.clearResults
        ),
        supportAction(
            'restore-ignored',
            'Restaurar achados ocultados',
            canRestoreIgnored
                ? `Restaurar ${ignoredCount} achado${ignoredCount === 1 ? '' : 's'} ocultado${ignoredCount === 1 ? '' : 's'} na interface.`
                : 'Nenhum achado está ocultado na interface.',
            'eye',
            commandIds.restoreIgnoredVulnerabilities,
            canRestoreIgnored,
            canRestoreIgnored
                ? `${ignoredCount} ocultado${ignoredCount === 1 ? '' : 's'}`
                : 'Nenhum ocultado'
        ),
        supportAction(
            'setup-backend',
            'Configurar dependências',
            'Criar o ambiente Python isolado e instalar as dependências do backend.',
            'package',
            commandIds.setupBackend
        ),
        supportAction(
            'restart-backend',
            'Reiniciar backend',
            canRestartBackend
                ? 'Parar e iniciar novamente o backend local.'
                : 'Aguarde a inicialização do backend antes de reiniciá-lo.',
            'debug-restart',
            commandIds.restartBackend,
            canRestartBackend,
            state.backendStatus === 'starting' ? 'Inicializando' : undefined
        ),
        supportAction(
            'show-logs',
            'Abrir logs',
            'Mostrar o canal de saída do Privacy Scanner.',
            'output',
            commandIds.showLogs
        ),
        supportAction(
            'open-settings',
            'Abrir configurações',
            'Abrir somente as configurações desta extensão.',
            'settings-gear',
            commandIds.openSettings,
            true,
            undefined,
            [SETTINGS_QUERY]
        )
    ];

    return [
        {
            id: 'analyze-file',
            kind: 'action',
            label: 'Analisar arquivo atual',
            description: analyzeFileDescription,
            tooltip: analyzeFileTooltip,
            icon: 'file-code',
            enabled: canAnalyzeFile,
            command: command(
                commandIds.analyze,
                canAnalyzeFile,
                state.activeResource ? [state.activeResource] : undefined
            )
        },
        {
            id: 'analyze-workspace',
            kind: 'action',
            label: 'Analisar projeto inteiro',
            description: state.hasWorkspace ? undefined : 'Nenhuma pasta aberta',
            tooltip: state.hasWorkspace
                ? 'Analisar todos os arquivos suportados do projeto.'
                : 'Abra uma pasta de trabalho para analisar o projeto inteiro.',
            icon: 'folder-opened',
            enabled: state.hasWorkspace,
            command: command(commandIds.analyzeAll, state.hasWorkspace)
        },
        {
            id: 'analyze-database',
            kind: 'action',
            label: 'Selecionar e analisar banco SQLite',
            tooltip: 'Selecionar um arquivo .db, .sqlite ou .sqlite3 para análise.',
            icon: 'database',
            enabled: true,
            command: command(commandIds.analyzeDatabase, true)
        },
        {
            id: 'export-report',
            kind: 'action',
            label: 'Exportar relatório',
            description: state.hasWorkspace ? 'HTML, PDF ou JSON' : 'Nenhuma pasta aberta',
            tooltip: state.hasWorkspace
                ? 'Escolher o formato e exportar o relatório.'
                : 'Abra uma pasta de trabalho para exportar um relatório.',
            icon: 'export',
            enabled: state.hasWorkspace,
            command: command(commandIds.exportReport, state.hasWorkspace)
        },
        {
            id: 'configure-profile',
            kind: 'action',
            label: state.hasWorkspace && !state.profileValid
                ? 'Corrigir perfil'
                : 'Configurar perfil',
            description: profileDescription,
            tooltip: profileTooltip,
            icon: state.profileValid ? 'settings' : 'warning',
            enabled: canConfigureProfile,
            command: command(
                commandIds.configureProfile,
                canConfigureProfile,
                state.activeResource ? [state.activeResource] : undefined
            )
        },
        {
            id: 'support',
            kind: 'group',
            label: 'Configuração e suporte',
            description: backendDescription(state.backendStatus),
            tooltip: `${backendDescription(state.backendStatus)}. Abrir ações de configuração e suporte.`,
            icon: 'tools',
            enabled: true,
            children: supportChildren
        }
    ];
}

function loadVscodeApi(): VscodeApi {
    // A carga tardia permite importar e testar os descritores fora do Extension Host.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    return require('vscode') as VscodeApi;
}

export class QuickActionsProvider implements vscode.TreeDataProvider<QuickActionDescriptor> {
    private readonly vscodeApi: VscodeApi;
    private readonly emitter: vscode.EventEmitter<QuickActionDescriptor | undefined | null | void>;
    private stateSource: QuickActionsStateSource;
    private readonly commandIds: Partial<QuickActionCommandIds>;

    readonly onDidChangeTreeData: vscode.Event<QuickActionDescriptor | undefined | null | void>;

    constructor(
        stateSource: QuickActionsStateSource,
        commandIds: Partial<QuickActionCommandIds> = {},
        vscodeApi: VscodeApi = loadVscodeApi()
    ) {
        this.stateSource = stateSource;
        this.commandIds = commandIds;
        this.vscodeApi = vscodeApi;
        this.emitter = new this.vscodeApi.EventEmitter<QuickActionDescriptor | undefined | null | void>();
        this.onDidChangeTreeData = this.emitter.event;
    }

    updateState(state: QuickActionsState): void {
        this.stateSource = state;
        this.refresh();
    }

    refresh(): void {
        this.emitter.fire();
    }

    dispose(): void {
        this.emitter.dispose();
    }

    getTreeItem(element: QuickActionDescriptor): vscode.TreeItem {
        const collapsibleState = element.kind === 'group'
            ? this.vscodeApi.TreeItemCollapsibleState.Collapsed
            : this.vscodeApi.TreeItemCollapsibleState.None;
        const item = new this.vscodeApi.TreeItem(element.label, collapsibleState);
        item.id = `privacy-scanner.quick-actions.${element.id}`;
        item.description = element.description;
        item.tooltip = element.tooltip;
        item.contextValue = element.enabled ? 'quickAction' : 'quickActionDisabled';
        item.iconPath = new this.vscodeApi.ThemeIcon(element.enabled ? element.icon : 'circle-slash');
        item.accessibilityInformation = {
            label: [element.label, element.description, element.enabled ? undefined : 'indisponível']
                .filter(Boolean)
                .join(', ')
        };
        if (element.enabled && element.command) {
            item.command = {
                command: element.command.id,
                title: element.label,
                arguments: element.command.arguments
                    ? Array.from(element.command.arguments)
                    : undefined
            };
        }
        return item;
    }

    getChildren(element?: QuickActionDescriptor): Thenable<QuickActionDescriptor[]> {
        if (element) {
            return Promise.resolve(Array.from(element.children || []));
        }
        const state = typeof this.stateSource === 'function'
            ? this.stateSource()
            : this.stateSource;
        return Promise.resolve(Array.from(buildQuickActionDescriptors(state, this.commandIds)));
    }
}

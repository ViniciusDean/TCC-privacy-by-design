import * as assert from 'assert';
import {
    DEFAULT_QUICK_ACTION_COMMAND_IDS,
    QuickActionDescriptor,
    QuickActionsState,
    buildQuickActionDescriptors,
    shouldShowQuickActionsOnboarding
} from '../quickActions';

function run(name: string, test: () => void): void {
    try {
        test();
        console.log(`ok - ${name}`);
    } catch (error) {
        console.error(`not ok - ${name}`);
        throw error;
    }
}

function state(overrides: Partial<QuickActionsState> = {}): QuickActionsState {
    return {
        activeFileSupported: true,
        hasWorkspace: true,
        profilePreset: 'conservador',
        profileCustomizationCount: 0,
        profileValid: true,
        backendStatus: 'ready',
        ignoredCount: 0,
        ...overrides
    };
}

function item(items: readonly QuickActionDescriptor[], id: string): QuickActionDescriptor {
    const found = items.find(candidate => candidate.id === id);
    assert.ok(found, `item ${id} nao encontrado`);
    return found;
}

run('exibe cinco acoes principais e o grupo de suporte recolhivel', () => {
    const items = buildQuickActionDescriptors(state());

    assert.strictEqual(items.length, 6);
    assert.deepStrictEqual(
        items.slice(0, 5).map(candidate => candidate.label),
        [
            'Analisar arquivo atual',
            'Analisar projeto inteiro',
            'Selecionar e analisar banco SQLite',
            'Exportar relatório',
            'Configurar perfil'
        ]
    );

    const support = item(items, 'support');
    assert.strictEqual(support.kind, 'group');
    assert.strictEqual(support.description, 'Backend: pronto');
    assert.deepStrictEqual(
        support.children?.map(candidate => candidate.label),
        [
            'Limpar resultados',
            'Restaurar achados ocultados',
            'Configurar dependências',
            'Reiniciar backend',
            'Abrir logs',
            'Abrir configurações'
        ]
    );
});

run('associa o recurso ativo somente quando o arquivo e suportado', () => {
    const uri = { fsPath: 'C:\\projeto\\dados.py' } as QuickActionsState['activeResource'];
    const supported = item(buildQuickActionDescriptors(state({
        activeResource: uri,
        activeFileName: 'dados.py'
    })), 'analyze-file');

    assert.strictEqual(supported.enabled, true);
    assert.strictEqual(supported.description, 'dados.py');
    assert.strictEqual(supported.command?.id, DEFAULT_QUICK_ACTION_COMMAND_IDS.analyze);
    assert.deepStrictEqual(supported.command?.arguments, [uri]);

    const unsupported = item(buildQuickActionDescriptors(state({
        activeResource: uri,
        activeFileName: 'README.md',
        activeFileSupported: false
    })), 'analyze-file');
    assert.strictEqual(unsupported.enabled, false);
    assert.strictEqual(unsupported.command, undefined);
    assert.strictEqual(unsupported.description, 'README.md não é Python ou Java');
});

run('mantem itens de workspace visiveis e instrutivos sem pasta aberta', () => {
    const items = buildQuickActionDescriptors(state({
        hasWorkspace: false,
        profilePreset: undefined
    }));

    for (const id of ['analyze-workspace', 'export-report', 'configure-profile']) {
        assert.strictEqual(item(items, id).enabled, false);
        assert.strictEqual(item(items, id).command, undefined);
    }
    assert.strictEqual(item(items, 'analyze-workspace').description, 'Nenhuma pasta aberta');
    assert.strictEqual(item(items, 'configure-profile').description, 'Abra uma pasta de trabalho');
});

run('mantem perfil invalido clicavel para correcao assistida', () => {
    const activeResource = { fsPath: 'C:\\projeto\\dados.py' } as QuickActionsState['activeResource'];
    const configureProfile = item(buildQuickActionDescriptors(state({
        activeResource,
        profilePreset: 'equilibrado',
        invalidProfileRoots: ['api', 'dados'],
        profileValid: false
    })), 'configure-profile');

    assert.strictEqual(configureProfile.label, 'Corrigir perfil');
    assert.strictEqual(configureProfile.description, 'Inválido: api, dados');
    assert.strictEqual(configureProfile.enabled, true);
    assert.strictEqual(configureProfile.command?.id, DEFAULT_QUICK_ACTION_COMMAND_IDS.configureProfile);
    assert.deepStrictEqual(configureProfile.command?.arguments, [activeResource]);
});

run('resume preset e quantidade de personalizacoes', () => {
    const withoutOverrides = item(buildQuickActionDescriptors(state()), 'configure-profile');
    assert.strictEqual(withoutOverrides.description, 'conservador');

    const oneOverride = item(buildQuickActionDescriptors(state({
        profilePreset: 'equilibrado',
        profileCustomizationCount: 1
    })), 'configure-profile');
    assert.strictEqual(oneOverride.description, 'equilibrado + 1 personalização');

    const multipleOverrides = item(buildQuickActionDescriptors(state({
        profilePreset: 'múltiplos perfis',
        profileCustomizationCount: 3
    })), 'configure-profile');
    assert.strictEqual(multipleOverrides.description, 'múltiplos perfis + 3 personalizações');
});

run('reflete backend e contagem de achados ocultados', () => {
    const items = buildQuickActionDescriptors(state({
        backendStatus: 'starting',
        ignoredCount: 2
    }));
    const support = item(items, 'support');

    assert.strictEqual(support.description, 'Backend: iniciando');
    const restore = item(support.children || [], 'restore-ignored');
    assert.strictEqual(restore.enabled, true);
    assert.strictEqual(restore.description, '2 ocultados');
    const restart = item(support.children || [], 'restart-backend');
    assert.strictEqual(restart.enabled, false);
    assert.strictEqual(restart.command, undefined);
});

run('usa picker para SQLite e filtro da extensao ao abrir configuracoes', () => {
    const items = buildQuickActionDescriptors(state());
    const database = item(items, 'analyze-database');
    assert.strictEqual(database.command?.id, DEFAULT_QUICK_ACTION_COMMAND_IDS.analyzeDatabase);
    assert.strictEqual(database.command?.arguments, undefined);

    const settings = item(item(items, 'support').children || [], 'open-settings');
    assert.strictEqual(settings.command?.id, 'workbench.action.openSettings');
    assert.deepStrictEqual(settings.command?.arguments, ['@ext:fatec-tcc.privacy-scanner-lgpd']);
});

run('aceita IDs de comando fornecidos pela integracao', () => {
    const items = buildQuickActionDescriptors(state(), { analyze: 'teste.analyze' });
    assert.strictEqual(item(items, 'analyze-file').command, undefined);

    const uri = { fsPath: 'C:\\projeto\\dados.java' } as QuickActionsState['activeResource'];
    const withResource = buildQuickActionDescriptors(state({ activeResource: uri }), {
        analyze: 'teste.analyze'
    });
    assert.strictEqual(item(withResource, 'analyze-file').command?.id, 'teste.analyze');

    const profile = item(buildQuickActionDescriptors(state({ activeResource: uri }), {
        configureProfile: 'teste.configureProfile'
    }), 'configure-profile');
    assert.strictEqual(profile.command?.id, 'teste.configureProfile');
    assert.deepStrictEqual(profile.command?.arguments, [uri]);
});

run('mostra o onboarding uma unica vez e somente com a sidebar habilitada', () => {
    assert.strictEqual(shouldShowQuickActionsOnboarding(true, false), true);
    assert.strictEqual(shouldShowQuickActionsOnboarding(true, true), false);
    assert.strictEqual(shouldShowQuickActionsOnboarding(false, false), false);
});

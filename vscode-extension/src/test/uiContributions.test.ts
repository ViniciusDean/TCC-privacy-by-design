import * as assert from 'assert';
import * as fs from 'fs';
import * as path from 'path';

interface CommandContribution {
    command: string;
    title?: string;
}

interface ViewContribution {
    id: string;
    name: string;
    when?: string;
}

interface MenuContribution {
    command: string;
    when?: string;
    group?: string;
}

interface ExtensionManifest {
    version: string;
    activationEvents?: string[];
    contributes: {
        commands?: CommandContribution[];
        views?: Record<string, ViewContribution[]>;
        menus?: Record<string, MenuContribution[]>;
    };
}

const manifestPath = path.resolve(__dirname, '..', '..', 'package.json');
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8')) as ExtensionManifest;

function run(name: string, test: () => void): void {
    try {
        test();
        console.log(`ok - ${name}`);
    } catch (error) {
        console.error(`not ok - ${name}`);
        throw error;
    }
}

function assertMenuContribution(menu: string, expected: MenuContribution): void {
    const entries = manifest.contributes.menus?.[menu] ?? [];
    assert.ok(
        entries.some(entry => (
            entry.command === expected.command
            && entry.when === expected.when
            && entry.group === expected.group
        )),
        `${menu} deve conter ${expected.command} com when "${expected.when}" e grupo "${expected.group}".`
    );
}

run('declara a versao 1.2.3 e ativa a view de acoes rapidas', () => {
    assert.strictEqual(manifest.version, '1.2.3');
    assert.ok(
        manifest.activationEvents?.includes('onView:privacy-scanner-actions'),
        'A extensao deve ativar quando a view de acoes rapidas for aberta.'
    );
});

run('ordena Acoes rapidas antes de Achados e Resumo', () => {
    const views = manifest.contributes.views?.['privacy-scanner-sidebar'] ?? [];
    assert.deepStrictEqual(
        views.map(view => view.id),
        [
            'privacy-scanner-actions',
            'privacy-scanner-vulnerabilities',
            'privacy-scanner-summary'
        ]
    );
    assert.deepStrictEqual(
        views.map(view => view.name),
        ['Ações rápidas', 'Achados', 'Resumo']
    );
    assert.deepStrictEqual(
        views.map(view => view.when),
        [
            'config.privacy-scanner.enableSidebar',
            'config.privacy-scanner.enableSidebar',
            'config.privacy-scanner.enableSidebar'
        ],
        'As views devem estar registradas antes da ativacao e obedecer diretamente à configuração da sidebar.'
    );
});

run('preserva todos os IDs de comandos publicos da versao anterior', () => {
    const commandIds = new Set(
        (manifest.contributes.commands ?? []).map(contribution => contribution.command)
    );
    const preservedCommandIds = [
        'privacy-scanner.analyzeNow',
        'privacy-scanner.analyze',
        'privacy-scanner.analyzeAll',
        'privacy-scanner.analyzeDatabase',
        'privacy-scanner.clearResults',
        'privacy-scanner.exportReport',
        'privacy-scanner.exportHTML',
        'privacy-scanner.exportJSON',
        'privacy-scanner.showSidebar',
        'privacy-scanner.ignoreVulnerability',
        'privacy-scanner.restoreIgnoredVulnerabilities',
        'privacy-scanner.configureProfile',
        'privacy-scanner.createProfile',
        'privacy-scanner.selectProfile',
        'privacy-scanner.validateProfile',
        'privacy-scanner.restartBackend',
        'privacy-scanner.setupBackend',
        'privacy-scanner.showLogs'
    ];

    for (const commandId of preservedCommandIds) {
        assert.ok(commandIds.has(commandId), `Comando removido do manifesto: ${commandId}`);
    }
});

run('mantem o JSON somente como comando avancado', () => {
    const contribution = (manifest.contributes.commands ?? []).find(
        candidate => candidate.command === 'privacy-scanner.createProfile'
    );
    assert.ok(contribution, 'O comando legado createProfile deve continuar declarado.');
    assert.ok(
        contribution.title?.includes('JSON') && contribution.title?.includes('avan'),
        'O titulo deve deixar claro que a abertura do JSON e uma opcao avancada.'
    );
});

run('oferece analise clicavel apenas para linguagens e extensoes suportadas', () => {
    assertMenuContribution('editor/title', {
        command: 'privacy-scanner.analyze',
        when: 'resourceLangId == python || resourceLangId == java',
        group: 'navigation@10'
    });
    assertMenuContribution('editor/context', {
        command: 'privacy-scanner.analyze',
        when: 'editorLangId == python || editorLangId == java',
        group: 'privacy-scanner@1'
    });
    assertMenuContribution('explorer/context', {
        command: 'privacy-scanner.analyze',
        when: 'resourceExtname == .py || resourceExtname == .java',
        group: 'privacy-scanner@1'
    });
    assertMenuContribution('explorer/context', {
        command: 'privacy-scanner.analyzeDatabase',
        when: 'resourceExtname == .db || resourceExtname == .sqlite || resourceExtname == .sqlite3',
        group: 'privacy-scanner@2'
    });
});

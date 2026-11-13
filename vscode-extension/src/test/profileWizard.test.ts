import * as assert from 'assert';
import { AnalysisProfile } from '../profile';
import { showProfileWizard } from '../profileWizard';

type WizardApi = Parameters<typeof showProfileWizard>[1];

async function run(name: string, test: () => Promise<void>): Promise<void> {
    try {
        await test();
        console.log(`ok - ${name}`);
    } catch (error) {
        console.error(`not ok - ${name}`);
        throw error;
    }
}

function fakeApi(
    choose: (items: ReadonlyArray<{ label: string }>) => unknown,
    warningChoice?: string
): WizardApi {
    return {
        QuickPickItemKind: { Default: 0, Separator: -1 },
        window: {
            showQuickPick: async (items: ReadonlyArray<{ label: string }>) => choose(items),
            showWarningMessage: async () => warningChoice
        }
    } as unknown as WizardApi;
}

async function main(): Promise<void> {
    await run('Esc cancela sem chamar a persistencia', async () => {
        let saveCalls = 0;
        const result = await showProfileWizard({
            initialProfile: { schemaVersion: 1, preset: 'conservador', categories: {} },
            onSave: () => { saveCalls += 1; }
        }, fakeApi(() => undefined));

        assert.strictEqual(result, undefined);
        assert.strictEqual(saveCalls, 0);
    });

    await run('salva explicitamente o perfil normalizado retornado pelo assistente', async () => {
        let step = 0;
        let persisted: AnalysisProfile | undefined;
        const api = fakeApi(items => {
            step += 1;
            if (step === 1) {
                return items.find(item => item.label.includes('Preset base'));
            }
            if (step === 2) {
                return items.find(item => item.label === 'Equilibrado');
            }
            return items.find(item => item.label.includes('Salvar perfil'));
        });

        const result = await showProfileWizard({
            initialProfile: {
                schemaVersion: 1,
                preset: 'conservador',
                categories: { DADO_EM_LOG: { minimumConfidence: 'MEDIA' } }
            },
            scopeLabel: 'raiz-a',
            onSave: profile => { persisted = profile; }
        }, api);

        assert.deepStrictEqual(result, {
            schemaVersion: 1,
            preset: 'equilibrado',
            categories: {}
        });
        assert.deepStrictEqual(persisted, result);
        assert.strictEqual(step, 3);
    });

    await run('aplica selecao multipla de regras somente ao salvar', async () => {
        let step = 0;
        const api = fakeApi(items => {
            step += 1;
            if (step === 1) {
                return items.find(item => item.label.includes('Regras ativas'));
            }
            if (step === 2) {
                return items.filter(item => item.label.includes('dado pessoal em log'));
            }
            return items.find(item => item.label.includes('Salvar perfil'));
        });

        const result = await showProfileWizard({
            initialProfile: { schemaVersion: 1, preset: 'conservador', categories: {} },
            onSave: () => undefined
        }, api);

        assert.ok(result);
        // O conservador ativa 7 regras; desmarcar as 6 restantes gera 6 overrides.
        assert.strictEqual(Object.keys(result.categories).length, 6);
        assert.strictEqual(result.categories.DADO_EM_LOG, undefined);
        assert.ok(Object.values(result.categories).every(options => options.enabled === false));
    });

    await run('ajusta ativacao confianca e severidade de uma regra', async () => {
        let step = 0;
        const api = fakeApi(items => {
            step += 1;
            switch (step) {
                case 1:
                    return items.find(item => item.label.includes('Ajustar uma regra'));
                case 2:
                    return items.find(item => item.label.includes('dado pessoal em log'));
                case 3:
                    return items.find(item => item.label.includes('Desativar regra'));
                case 4:
                    return items.find(item => item.label.includes('Confiança mínima'));
                case 5:
                    return items.find(item => item.label === 'MÉDIA');
                case 6:
                    return items.find(item => item.label.includes('Severidade técnica'));
                case 7:
                    return items.find(item => item.label === 'BAIXO');
                case 8:
                    return items.find(item => item.label.includes('Concluir ajustes'));
                default:
                    return items.find(item => item.label.includes('Salvar perfil'));
            }
        }, 'Ajustar severidade');

        const result = await showProfileWizard({
            initialProfile: { schemaVersion: 1, preset: 'conservador', categories: {} },
            onSave: () => undefined
        }, api);

        assert.deepStrictEqual(result?.categories.DADO_EM_LOG, {
            enabled: false,
            minimumConfidence: 'MEDIA',
            severity: 'BAIXO'
        });
    });

    await run('restaura o perfil padrao apenas quando o usuario salva', async () => {
        let step = 0;
        const api = fakeApi(items => {
            step += 1;
            return step === 1
                ? items.find(item => item.label.includes('Restaurar padrão'))
                : items.find(item => item.label.includes('Salvar perfil'));
        });

        const result = await showProfileWizard({
            initialProfile: {
                schemaVersion: 1,
                preset: 'completo',
                categories: { MISTURA_DADOS: { enabled: false } }
            },
            onSave: () => undefined
        }, api);

        assert.deepStrictEqual(result, {
            schemaVersion: 1,
            preset: 'conservador',
            categories: {}
        });
    });
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});

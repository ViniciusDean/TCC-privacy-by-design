import * as assert from 'assert';
import * as path from 'path';
import { AnalysisProfile } from '../profile';
import {
    PROFILE_CATEGORIES,
    PROFILE_CATEGORY_IDS,
    PROFILE_PRESETS,
    presetMinimumConfidence
} from '../profileCatalog';
import {
    changeDraftPreset,
    clearDraftCategory,
    clearDraftCustomizations,
    countProfileCustomizations,
    createProfileDraft,
    formatProfileSummary,
    getEffectiveCategorySettings,
    getEnabledCategoryIds,
    invalidProfileBackupPath,
    normalizeProfileDraft,
    resetProfileDraft,
    setDraftCategoryEnabled,
    setDraftCategoryConfidence,
    setDraftCategorySeverity,
    setDraftEnabledCategories
} from '../profileDraft';

function run(name: string, test: () => void): void {
    try {
        test();
        console.log(`ok - ${name}`);
    } catch (error) {
        console.error(`not ok - ${name}`);
        throw error;
    }
}

run('cataloga as 14 regras humanas nos grupos Codigo e SQLite', () => {
    assert.strictEqual(PROFILE_CATEGORIES.length, 14);
    assert.strictEqual(new Set(PROFILE_CATEGORY_IDS).size, 14);
    assert.strictEqual(PROFILE_CATEGORIES.filter(category => category.group === 'code').length, 7);
    assert.strictEqual(PROFILE_CATEGORIES.filter(category => category.group === 'sqlite').length, 7);
    assert.strictEqual(
        PROFILE_CATEGORIES.find(category => category.id === 'AUSENCIA_CONSENTIMENTO')?.label,
        'Proteção/base legal não evidenciada'
    );
    assert.ok(PROFILE_CATEGORIES.every(category => category.label.length > 0));
});

run('mantem os tres presets sincronizados com seus limiares', () => {
    assert.deepStrictEqual(
        PROFILE_PRESETS.map(preset => [preset.id, preset.minimumConfidence]),
        [
            ['conservador', 'ALTA'],
            ['equilibrado', 'MEDIA'],
            ['completo', 'BAIXA']
        ]
    );
    assert.strictEqual(presetMinimumConfidence('equilibrado'), 'MEDIA');
});

run('normaliza somente overrides reais sem alterar o perfil recebido', () => {
    const profile: AnalysisProfile = {
        schemaVersion: 1,
        preset: 'conservador',
        categories: {
            DADO_EM_LOG: {
                enabled: true,
                minimumConfidence: 'ALTA',
                severity: 'MEDIO'
            },
            AUSENCIA_RETENCAO: {
                enabled: false,
                minimumConfidence: 'MEDIA'
            }
        }
    };
    const snapshot = JSON.parse(JSON.stringify(profile));
    const normalized = normalizeProfileDraft(createProfileDraft(profile));

    assert.deepStrictEqual(normalized, {
        schemaVersion: 1,
        preset: 'conservador',
        categories: {
            DADO_EM_LOG: { severity: 'MEDIO' },
            AUSENCIA_RETENCAO: { enabled: false, minimumConfidence: 'MEDIA' }
        }
    });
    assert.deepStrictEqual(profile, snapshot);
    assert.strictEqual(countProfileCustomizations(normalized), 2);
});

run('preserva personalizacoes ao trocar o preset e elimina redundancias no salvamento', () => {
    let draft = createProfileDraft({
        schemaVersion: 1,
        preset: 'conservador',
        categories: {
            DADO_EM_LOG: { minimumConfidence: 'MEDIA', severity: 'ALTO' }
        }
    });
    draft = changeDraftPreset(draft, 'equilibrado');

    assert.deepStrictEqual(draft.categories.DADO_EM_LOG, {
        minimumConfidence: 'MEDIA',
        severity: 'ALTO'
    });
    assert.deepStrictEqual(normalizeProfileDraft(draft).categories.DADO_EM_LOG, {
        severity: 'ALTO'
    });
    assert.strictEqual(countProfileCustomizations(draft), 1);
});

run('seleciona regras ativas sem perder ajustes finos', () => {
    let draft = createProfileDraft({
        schemaVersion: 1,
        preset: 'equilibrado',
        categories: { DADO_EM_LOG: { severity: 'BAIXO' } }
    });
    const withoutLog = PROFILE_CATEGORY_IDS.filter(id => id !== 'DADO_EM_LOG');
    draft = setDraftEnabledCategories(draft, withoutLog);

    assert.strictEqual(getEnabledCategoryIds(draft).includes('DADO_EM_LOG'), false);
    assert.deepStrictEqual(normalizeProfileDraft(draft).categories.DADO_EM_LOG, {
        enabled: false,
        severity: 'BAIXO'
    });

    draft = setDraftEnabledCategories(draft, PROFILE_CATEGORY_IDS);
    assert.strictEqual(getEnabledCategoryIds(draft).length, 14);
    assert.deepStrictEqual(normalizeProfileDraft(draft).categories.DADO_EM_LOG, {
        severity: 'BAIXO'
    });
});

run('ajusta e remove confianca e severidade por regra', () => {
    let draft = resetProfileDraft();
    draft = setDraftCategoryEnabled(draft, 'COLETA_EXCESSIVA', false);
    draft = setDraftCategoryConfidence(draft, 'COLETA_EXCESSIVA', 'MEDIA');
    draft = setDraftCategorySeverity(draft, 'COLETA_EXCESSIVA', 'BAIXO');

    assert.deepStrictEqual(getEffectiveCategorySettings(draft, 'COLETA_EXCESSIVA'), {
        enabled: false,
        minimumConfidence: 'MEDIA',
        severity: 'BAIXO',
        customized: true
    });
    assert.strictEqual(formatProfileSummary(draft), 'conservador + 1 personalização');

    draft = setDraftCategoryEnabled(draft, 'COLETA_EXCESSIVA', true);
    assert.deepStrictEqual(normalizeProfileDraft(draft).categories.COLETA_EXCESSIVA, {
        minimumConfidence: 'MEDIA',
        severity: 'BAIXO'
    });

    draft = clearDraftCategory(draft, 'COLETA_EXCESSIVA');
    assert.strictEqual(countProfileCustomizations(draft), 0);
    assert.strictEqual(formatProfileSummary(draft), 'conservador');
});

run('limpa personalizacoes preservando preset e restaura o padrao completo', () => {
    let draft = createProfileDraft({
        schemaVersion: 1,
        preset: 'completo',
        categories: { MISTURA_DADOS: { enabled: false } }
    });
    draft = clearDraftCustomizations(draft);
    assert.deepStrictEqual(normalizeProfileDraft(draft), {
        schemaVersion: 1,
        preset: 'completo',
        categories: {}
    });

    assert.deepStrictEqual(normalizeProfileDraft(resetProfileDraft()), {
        schemaVersion: 1,
        preset: 'conservador',
        categories: {}
    });
});

run('gera caminho deterministico para backup de perfil invalido', () => {
    const profilePath = path.join('C:\\projeto', '.privacy-scanner.json');
    const at = new Date('2026-07-15T12:34:56.000Z');
    assert.strictEqual(
        invalidProfileBackupPath(profilePath, at),
        path.join(
            path.dirname(profilePath),
            '.privacy-scanner.json.invalid-20260715-123456.bak'
        )
    );
    assert.throws(
        () => invalidProfileBackupPath(profilePath, new Date(Number.NaN)),
        /Data inválida/
    );
});

import * as path from 'path';
import {
    AnalysisProfile,
    CategoryProfile,
    Confidence,
    DEFAULT_PROFILE,
    Preset,
    Risk
} from './profile';
import {
    isProfileCategoryId,
    presetEnablesCategory,
    presetMinimumConfidence,
    PROFILE_CATEGORY_IDS,
    ProfileCategoryId
} from './profileCatalog';

export interface ProfileDraft {
    readonly preset: Preset;
    readonly categories: Readonly<Record<string, Readonly<CategoryProfile>>>;
}

export interface EffectiveCategorySettings {
    readonly enabled: boolean;
    readonly minimumConfidence: Confidence;
    readonly severity?: Risk;
    readonly customized: boolean;
}

function cloneOptions(options: Readonly<CategoryProfile>): CategoryProfile {
    return {
        ...(options.enabled !== undefined ? { enabled: options.enabled } : {}),
        ...(options.minimumConfidence !== undefined
            ? { minimumConfidence: options.minimumConfidence }
            : {}),
        ...(options.severity !== undefined ? { severity: options.severity } : {})
    };
}

function cloneCategories(
    categories: Readonly<Record<string, Readonly<CategoryProfile>>>
): Record<string, CategoryProfile> {
    const result: Record<string, CategoryProfile> = {};
    for (const [id, options] of Object.entries(categories)) {
        if (isProfileCategoryId(id)) {
            result[id] = cloneOptions(options);
        }
    }
    return result;
}

function setCategoryOptions(
    draft: ProfileDraft,
    categoryId: ProfileCategoryId,
    update: (current: CategoryProfile) => CategoryProfile
): ProfileDraft {
    const categories = cloneCategories(draft.categories);
    const next = update(cloneOptions(categories[categoryId] || {}));
    if (Object.keys(next).length === 0) {
        delete categories[categoryId];
    } else {
        categories[categoryId] = next;
    }
    return { preset: draft.preset, categories };
}

/**
 * Cria um rascunho independente e remove apenas opções que já são equivalentes
 * ao preset carregado. O objeto recebido nunca é alterado.
 */
export function createProfileDraft(profile: AnalysisProfile): ProfileDraft {
    const normalized = normalizeProfileDraft(profile);
    return { preset: normalized.preset, categories: normalized.categories };
}

/**
 * Converte o rascunho no contrato público versionado. Somente diferenças reais
 * em relação ao preset são serializadas.
 */
export function normalizeProfileDraft(draft: ProfileDraft): AnalysisProfile {
    const categories: Record<string, CategoryProfile> = {};
    const presetConfidence = presetMinimumConfidence(draft.preset);

    for (const id of PROFILE_CATEGORY_IDS) {
        const raw = draft.categories[id];
        if (!raw) {
            continue;
        }
        const normalized: CategoryProfile = {};
        if (raw.enabled !== undefined && raw.enabled !== presetEnablesCategory(draft.preset, id)) {
            normalized.enabled = raw.enabled;
        }
        if (
            raw.minimumConfidence !== undefined
            && raw.minimumConfidence !== presetConfidence
        ) {
            normalized.minimumConfidence = raw.minimumConfidence;
        }
        if (raw.severity !== undefined) {
            normalized.severity = raw.severity;
        }
        if (Object.keys(normalized).length > 0) {
            categories[id] = normalized;
        }
    }

    return { schemaVersion: 1, preset: draft.preset, categories };
}

/**
 * Troca o preset aplicando o conjunto de regras ativas do novo preset. Ajustes
 * de confiança e severidade por regra são preservados; a seleção manual de
 * regras ativas é descartada para que o preset escolhido tenha efeito.
 */
export function changeDraftPreset(draft: ProfileDraft, preset: Preset): ProfileDraft {
    const categories = cloneCategories(draft.categories);
    for (const [id, options] of Object.entries(categories)) {
        delete options.enabled;
        if (Object.keys(options).length === 0) {
            delete categories[id];
        }
    }
    return { preset, categories };
}

function isCategoryEnabled(draft: ProfileDraft, categoryId: ProfileCategoryId): boolean {
    const explicit = draft.categories[categoryId]?.enabled;
    return explicit !== undefined ? explicit : presetEnablesCategory(draft.preset, categoryId);
}

export function setDraftEnabledCategories(
    draft: ProfileDraft,
    enabledCategoryIds: readonly ProfileCategoryId[]
): ProfileDraft {
    const enabled = new Set<ProfileCategoryId>(enabledCategoryIds);
    let next = { preset: draft.preset, categories: cloneCategories(draft.categories) } as ProfileDraft;
    for (const categoryId of PROFILE_CATEGORY_IDS) {
        next = setCategoryOptions(next, categoryId, options => {
            const wanted = enabled.has(categoryId);
            if (wanted === presetEnablesCategory(draft.preset, categoryId)) {
                delete options.enabled;
            } else {
                options.enabled = wanted;
            }
            return options;
        });
    }
    return next;
}

export function setDraftCategoryEnabled(
    draft: ProfileDraft,
    categoryId: ProfileCategoryId,
    enabled: boolean
): ProfileDraft {
    return setCategoryOptions(draft, categoryId, options => {
        if (enabled === presetEnablesCategory(draft.preset, categoryId)) {
            delete options.enabled;
        } else {
            options.enabled = enabled;
        }
        return options;
    });
}

export function setDraftCategoryConfidence(
    draft: ProfileDraft,
    categoryId: ProfileCategoryId,
    minimumConfidence?: Confidence
): ProfileDraft {
    return setCategoryOptions(draft, categoryId, options => {
        if (minimumConfidence === undefined) {
            delete options.minimumConfidence;
        } else {
            options.minimumConfidence = minimumConfidence;
        }
        return options;
    });
}

export function setDraftCategorySeverity(
    draft: ProfileDraft,
    categoryId: ProfileCategoryId,
    severity?: Risk
): ProfileDraft {
    return setCategoryOptions(draft, categoryId, options => {
        if (severity === undefined) {
            delete options.severity;
        } else {
            options.severity = severity;
        }
        return options;
    });
}

export function clearDraftCategory(
    draft: ProfileDraft,
    categoryId: ProfileCategoryId
): ProfileDraft {
    const categories = cloneCategories(draft.categories);
    delete categories[categoryId];
    return { preset: draft.preset, categories };
}

export function clearDraftCustomizations(draft: ProfileDraft): ProfileDraft {
    return { preset: draft.preset, categories: {} };
}

export function resetProfileDraft(): ProfileDraft {
    return { preset: DEFAULT_PROFILE.preset, categories: {} };
}

export function getEnabledCategoryIds(draft: ProfileDraft): readonly ProfileCategoryId[] {
    return PROFILE_CATEGORY_IDS.filter(id => isCategoryEnabled(draft, id));
}

export function getEffectiveCategorySettings(
    draft: ProfileDraft,
    categoryId: ProfileCategoryId
): EffectiveCategorySettings {
    const normalized = normalizeProfileDraft(draft);
    const options = normalized.categories[categoryId] || {};
    return {
        enabled: options.enabled !== undefined
            ? options.enabled
            : presetEnablesCategory(draft.preset, categoryId),
        minimumConfidence: options.minimumConfidence || presetMinimumConfidence(draft.preset),
        severity: options.severity,
        customized: Object.keys(options).length > 0
    };
}

/** Conta categorias que possuem ao menos uma diferença real em relação ao preset. */
export function countProfileCustomizations(profile: ProfileDraft): number {
    return Object.keys(normalizeProfileDraft(profile).categories).length;
}

export function formatProfileSummary(profile: ProfileDraft): string {
    const count = countProfileCustomizations(profile);
    if (count === 0) {
        return profile.preset;
    }
    return `${profile.preset} + ${count} personaliza${count === 1 ? 'ção' : 'ções'}`;
}

/**
 * Gera, em UTC, o caminho determinístico usado antes de substituir um perfil
 * inválido. A cópia em si fica a cargo da integração.
 */
export function invalidProfileBackupPath(
    profilePath: string,
    at: Date | number = new Date()
): string {
    const date = typeof at === 'number' ? new Date(at) : at;
    if (Number.isNaN(date.getTime())) {
        throw new Error('Data inválida para o backup do perfil.');
    }
    const pad = (value: number): string => String(value).padStart(2, '0');
    const timestamp = [
        date.getUTCFullYear(),
        pad(date.getUTCMonth() + 1),
        pad(date.getUTCDate()),
        '-',
        pad(date.getUTCHours()),
        pad(date.getUTCMinutes()),
        pad(date.getUTCSeconds())
    ].join('');
    return path.join(
        path.dirname(profilePath),
        `${path.basename(profilePath)}.invalid-${timestamp}.bak`
    );
}

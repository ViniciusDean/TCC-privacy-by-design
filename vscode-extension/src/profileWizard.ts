import type * as vscode from 'vscode';
import type { AnalysisProfile, Confidence, Preset, Risk } from './profile';
import {
    getProfileCategory,
    getProfilePreset,
    PROFILE_CATEGORIES,
    PROFILE_CATEGORY_GROUPS,
    PROFILE_CATEGORY_IDS,
    PROFILE_PRESETS,
    ProfileCategoryId
} from './profileCatalog';
import {
    changeDraftPreset,
    clearDraftCategory,
    clearDraftCustomizations,
    countProfileCustomizations,
    createProfileDraft,
    formatProfileSummary,
    getEffectiveCategorySettings,
    getEnabledCategoryIds,
    normalizeProfileDraft,
    ProfileDraft,
    resetProfileDraft,
    setDraftCategoryEnabled,
    setDraftCategoryConfidence,
    setDraftCategorySeverity,
    setDraftEnabledCategories
} from './profileDraft';

type VscodeApi = typeof import('vscode');

export interface ProfileWizardOptions {
    readonly initialProfile: AnalysisProfile;
    /** Nome curto da pasta escolhida, especialmente útil em workspaces multirraiz. */
    readonly scopeLabel?: string;
    /** Único ponto autorizado a persistir o perfil. */
    readonly onSave: (profile: AnalysisProfile) => void | Promise<void>;
}

type MainAction =
    | 'preset'
    | 'enabled-categories'
    | 'adjust-category'
    | 'clear'
    | 'reset'
    | 'save'
    | 'cancel';

interface MainActionItem extends vscode.QuickPickItem {
    readonly action: MainAction;
}

interface PresetItem extends vscode.QuickPickItem {
    readonly preset?: Preset;
    readonly back?: boolean;
}

interface CategoryItem extends vscode.QuickPickItem {
    readonly categoryId?: ProfileCategoryId;
    readonly back?: boolean;
}

type CategoryAdjustmentAction =
    | 'toggle-enabled'
    | 'confidence'
    | 'severity'
    | 'clear'
    | 'another-category'
    | 'summary';

interface CategoryAdjustmentItem extends vscode.QuickPickItem {
    readonly action: CategoryAdjustmentAction;
}

type ConfidenceChoice = Confidence | 'default' | 'back';

interface ConfidenceItem extends vscode.QuickPickItem {
    readonly value: ConfidenceChoice;
}

type SeverityChoice = Risk | 'default' | 'back';

interface SeverityItem extends vscode.QuickPickItem {
    readonly value: SeverityChoice;
}

function loadVscodeApi(): VscodeApi {
    // A carga tardia mantém catálogo e modelo importáveis nos testes Node puros.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    return require('vscode') as VscodeApi;
}

function wizardTitle(scopeLabel?: string, section?: string): string {
    const scope = scopeLabel?.trim();
    const parts = ['Configurar perfil', scope, section].filter(Boolean);
    return parts.join(' — ');
}

function customizationText(count: number): string {
    return `${count} personaliza${count === 1 ? 'ção' : 'ções'}`;
}

function categoryStatus(draft: ProfileDraft, categoryId: ProfileCategoryId): string {
    const settings = getEffectiveCategorySettings(draft, categoryId);
    if (!settings.enabled) {
        return 'Desativada';
    }
    const severity = settings.severity
        ? `severidade ${settings.severity.toLocaleLowerCase('pt-BR')}`
        : 'severidade original';
    return `Confiança ${settings.minimumConfidence.toLocaleLowerCase('pt-BR')} · ${severity}`;
}

async function pickMainAction(
    draft: ProfileDraft,
    scopeLabel: string | undefined,
    api: VscodeApi
): Promise<MainAction | undefined> {
    const preset = getProfilePreset(draft.preset);
    const enabledCount = getEnabledCategoryIds(draft).length;
    const customizationCount = countProfileCustomizations(draft);
    const items: MainActionItem[] = [
        {
            label: '$(settings) Preset base',
            description: preset.label,
            detail: preset.description,
            action: 'preset'
        },
        {
            label: '$(checklist) Regras ativas',
            description: `${enabledCount} de ${PROFILE_CATEGORY_IDS.length}`,
            detail: 'Marque as regras que devem participar das análises.',
            action: 'enabled-categories'
        },
        {
            label: '$(tune) Ajustar uma regra',
            description: customizationText(customizationCount),
            detail: 'Personalize confiança mínima ou severidade técnica por regra.',
            action: 'adjust-category'
        },
        {
            label: '$(clear-all) Limpar personalizações',
            description: `Manter ${preset.label.toLocaleLowerCase('pt-BR')}`,
            detail: 'Remove ajustes de regras e preserva o preset base.',
            action: 'clear'
        },
        {
            label: '$(discard) Restaurar padrão conservador',
            detail: 'Volta ao preset conservador com todas as regras nos valores padrão.',
            action: 'reset'
        },
        {
            label: '$(save) Salvar perfil',
            description: formatProfileSummary(draft),
            detail: 'Confirma e grava as alterações deste assistente.',
            action: 'save'
        },
        {
            label: '$(close) Cancelar sem salvar',
            detail: 'Descarta todo o rascunho mantido neste assistente.',
            action: 'cancel'
        }
    ];
    const selected = await api.window.showQuickPick(items, {
        title: wizardTitle(scopeLabel),
        placeHolder: 'Escolha o que deseja configurar; somente “Salvar perfil” grava alterações.',
        ignoreFocusOut: true,
        matchOnDescription: true,
        matchOnDetail: true
    });
    return selected?.action;
}

async function pickPreset(
    draft: ProfileDraft,
    scopeLabel: string | undefined,
    api: VscodeApi
): Promise<Preset | null | undefined> {
    const customizations = countProfileCustomizations(draft);
    const items: PresetItem[] = PROFILE_PRESETS.map(preset => ({
        label: preset.label,
        description: preset.id === draft.preset ? 'Atual' : undefined,
        detail: `${preset.description} Confiança mínima padrão: ${preset.minimumConfidence}.`,
        preset: preset.id,
        picked: preset.id === draft.preset
    }));
    items.push({
        label: '$(arrow-left) Voltar ao resumo',
        detail: 'Não altera o preset.',
        back: true
    });
    const selected = await api.window.showQuickPick(items, {
        title: wizardTitle(scopeLabel, 'Preset base'),
        placeHolder: customizations > 0
            ? `${customizationText(customizations)} serão preservadas ao trocar o preset.`
            : 'Escolha o limiar padrão de confiança.',
        ignoreFocusOut: true,
        matchOnDescription: true,
        matchOnDetail: true
    });
    if (!selected) {
        return undefined;
    }
    return selected.back ? null : selected.preset;
}

function groupedCategoryItems(
    draft: ProfileDraft,
    api: VscodeApi,
    includeBack: boolean
): CategoryItem[] {
    const items: CategoryItem[] = [];
    for (const group of PROFILE_CATEGORY_GROUPS) {
        items.push({
            label: group.label,
            description: group.description,
            kind: api.QuickPickItemKind.Separator
        });
        for (const category of PROFILE_CATEGORIES.filter(candidate => candidate.group === group.id)) {
            items.push({
                label: category.label,
                description: categoryStatus(draft, category.id),
                detail: category.description,
                categoryId: category.id,
                picked: getEffectiveCategorySettings(draft, category.id).enabled
            });
        }
    }
    if (includeBack) {
        items.push({
            label: 'Navegação',
            kind: api.QuickPickItemKind.Separator
        });
        items.push({
            label: '$(arrow-left) Voltar ao resumo',
            detail: 'Mantém o rascunho atual.',
            back: true
        });
    }
    return items;
}

async function pickEnabledCategories(
    draft: ProfileDraft,
    scopeLabel: string | undefined,
    api: VscodeApi
): Promise<readonly ProfileCategoryId[] | undefined> {
    const selected = await api.window.showQuickPick(groupedCategoryItems(draft, api, false), {
        title: wizardTitle(scopeLabel, 'Regras ativas'),
        placeHolder: 'Marque as regras ativas e pressione Enter; Esc cancela todo o assistente.',
        canPickMany: true,
        ignoreFocusOut: true,
        matchOnDescription: true,
        matchOnDetail: true
    });
    if (!selected) {
        return undefined;
    }
    return selected
        .map(item => item.categoryId)
        .filter((id): id is ProfileCategoryId => id !== undefined);
}

async function pickCategory(
    draft: ProfileDraft,
    scopeLabel: string | undefined,
    api: VscodeApi
): Promise<ProfileCategoryId | null | undefined> {
    const selected = await api.window.showQuickPick(groupedCategoryItems(draft, api, true), {
        title: wizardTitle(scopeLabel, 'Ajustar uma regra'),
        placeHolder: 'Escolha uma regra para ajustar.',
        ignoreFocusOut: true,
        matchOnDescription: true,
        matchOnDetail: true
    });
    if (!selected) {
        return undefined;
    }
    return selected.back ? null : selected.categoryId;
}

async function pickCategoryAdjustment(
    draft: ProfileDraft,
    categoryId: ProfileCategoryId,
    scopeLabel: string | undefined,
    api: VscodeApi
): Promise<CategoryAdjustmentAction | undefined> {
    const category = getProfileCategory(categoryId);
    const settings = getEffectiveCategorySettings(draft, categoryId);
    const items: CategoryAdjustmentItem[] = [
        {
            label: settings.enabled ? '$(debug-pause) Desativar regra' : '$(play) Ativar regra',
            description: settings.enabled ? 'Ativa' : 'Desativada',
            detail: settings.enabled
                ? 'A regra deixará de participar das análises.'
                : 'A regra voltará a participar das análises.',
            action: 'toggle-enabled'
        },
        {
            label: '$(filter) Confiança mínima',
            description: settings.minimumConfidence,
            detail: 'Define o limiar mínimo de confiança somente para esta regra.',
            action: 'confidence'
        },
        {
            label: '$(symbol-color) Severidade técnica',
            description: settings.severity || 'Original da regra',
            detail: 'Personaliza a severidade usada nos agrupamentos e totais técnicos.',
            action: 'severity'
        },
        {
            label: '$(clear-all) Limpar ajustes desta regra',
            detail: 'Restaura ativação, confiança e severidade aos valores do preset.',
            action: 'clear'
        },
        {
            label: '$(list-selection) Escolher outra regra',
            detail: 'Mantém os ajustes atuais e volta à lista de regras.',
            action: 'another-category'
        },
        {
            label: '$(check) Concluir ajustes da regra',
            detail: 'Mantém o rascunho e volta ao resumo antes de salvar.',
            action: 'summary'
        }
    ];
    const selected = await api.window.showQuickPick(items, {
        title: wizardTitle(scopeLabel, category.label),
        placeHolder: categoryStatus(draft, categoryId),
        ignoreFocusOut: true,
        matchOnDescription: true,
        matchOnDetail: true
    });
    return selected?.action;
}

async function pickConfidence(
    draft: ProfileDraft,
    categoryId: ProfileCategoryId,
    scopeLabel: string | undefined,
    api: VscodeApi
): Promise<ConfidenceChoice | undefined> {
    const current = getEffectiveCategorySettings(draft, categoryId).minimumConfidence;
    const preset = getProfilePreset(draft.preset);
    const items: ConfidenceItem[] = [
        {
            label: `Padrão do preset (${preset.minimumConfidence})`,
            description: draft.categories[categoryId]?.minimumConfidence === undefined ? 'Atual' : undefined,
            detail: `Acompanhar o preset ${preset.label.toLocaleLowerCase('pt-BR')}.`,
            value: 'default'
        },
        {
            label: 'ALTA',
            description: current === 'ALTA' ? 'Efetiva agora' : undefined,
            detail: 'Aceitar somente indícios de confiança alta.',
            value: 'ALTA'
        },
        {
            label: 'MÉDIA',
            description: current === 'MEDIA' ? 'Efetiva agora' : undefined,
            detail: 'Aceitar indícios de confiança alta e média.',
            value: 'MEDIA'
        },
        {
            label: 'BAIXA',
            description: current === 'BAIXA' ? 'Efetiva agora' : undefined,
            detail: 'Aceitar indícios de todas as faixas de confiança.',
            value: 'BAIXA'
        },
        {
            label: '$(arrow-left) Voltar',
            detail: 'Não altera a confiança mínima.',
            value: 'back'
        }
    ];
    const selected = await api.window.showQuickPick(items, {
        title: wizardTitle(scopeLabel, `${getProfileCategory(categoryId).label}: confiança`),
        placeHolder: 'Escolha a confiança mínima desta regra.',
        ignoreFocusOut: true,
        matchOnDescription: true,
        matchOnDetail: true
    });
    return selected?.value;
}

async function pickSeverity(
    draft: ProfileDraft,
    categoryId: ProfileCategoryId,
    scopeLabel: string | undefined,
    api: VscodeApi
): Promise<SeverityChoice | undefined> {
    const proceed = await api.window.showWarningMessage(
        'Personalizar a severidade técnica altera agrupamentos, totais e o indicador técnico. Isso não representa conclusão jurídica de conformidade ou desconformidade.',
        { modal: true },
        'Ajustar severidade'
    );
    if (proceed !== 'Ajustar severidade') {
        return 'back';
    }
    const current = getEffectiveCategorySettings(draft, categoryId).severity;
    const items: SeverityItem[] = [
        {
            label: 'Original da regra',
            description: current === undefined ? 'Atual' : undefined,
            detail: 'Não substituir a severidade produzida pelo analisador.',
            value: 'default'
        },
        {
            label: 'ALTO',
            description: current === 'ALTO' ? 'Atual' : undefined,
            detail: 'Classificar os achados desta regra como risco técnico alto.',
            value: 'ALTO'
        },
        {
            label: 'MÉDIO',
            description: current === 'MEDIO' ? 'Atual' : undefined,
            detail: 'Classificar os achados desta regra como risco técnico médio.',
            value: 'MEDIO'
        },
        {
            label: 'BAIXO',
            description: current === 'BAIXO' ? 'Atual' : undefined,
            detail: 'Classificar os achados desta regra como risco técnico baixo.',
            value: 'BAIXO'
        },
        {
            label: '$(arrow-left) Voltar',
            detail: 'Não altera a severidade técnica.',
            value: 'back'
        }
    ];
    const selected = await api.window.showQuickPick(items, {
        title: wizardTitle(scopeLabel, `${getProfileCategory(categoryId).label}: severidade`),
        placeHolder: 'Escolha a severidade técnica desta regra.',
        ignoreFocusOut: true,
        matchOnDescription: true,
        matchOnDetail: true
    });
    return selected?.value;
}

async function adjustCategories(
    originalDraft: ProfileDraft,
    scopeLabel: string | undefined,
    api: VscodeApi
): Promise<ProfileDraft | undefined> {
    let draft = originalDraft;
    let categoryId = await pickCategory(draft, scopeLabel, api);
    while (categoryId !== undefined && categoryId !== null) {
        let chooseAnotherCategory = false;
        while (!chooseAnotherCategory) {
            const action = await pickCategoryAdjustment(draft, categoryId, scopeLabel, api);
            if (!action) {
                return undefined;
            }
            switch (action) {
                case 'toggle-enabled':
                    draft = setDraftCategoryEnabled(
                        draft,
                        categoryId,
                        !getEffectiveCategorySettings(draft, categoryId).enabled
                    );
                    break;
                case 'confidence': {
                    const confidence = await pickConfidence(draft, categoryId, scopeLabel, api);
                    if (confidence === undefined) {
                        return undefined;
                    }
                    if (confidence !== 'back') {
                        draft = setDraftCategoryConfidence(
                            draft,
                            categoryId,
                            confidence === 'default' ? undefined : confidence
                        );
                    }
                    break;
                }
                case 'severity': {
                    const severity = await pickSeverity(draft, categoryId, scopeLabel, api);
                    if (severity === undefined) {
                        return undefined;
                    }
                    if (severity !== 'back') {
                        draft = setDraftCategorySeverity(
                            draft,
                            categoryId,
                            severity === 'default' ? undefined : severity
                        );
                    }
                    break;
                }
                case 'clear':
                    draft = clearDraftCategory(draft, categoryId);
                    break;
                case 'another-category':
                    chooseAnotherCategory = true;
                    break;
                case 'summary':
                    return draft;
            }
        }
        categoryId = await pickCategory(draft, scopeLabel, api);
    }
    return categoryId === null ? draft : undefined;
}

/**
 * Abre o assistente nativo. Todo o trabalho anterior ao clique em “Salvar perfil”
 * acontece apenas em memória; Esc e “Cancelar sem salvar” não chamam onSave.
 */
export async function showProfileWizard(
    options: ProfileWizardOptions,
    vscodeApi: VscodeApi = loadVscodeApi()
): Promise<AnalysisProfile | undefined> {
    let draft = createProfileDraft(options.initialProfile);

    let action = await pickMainAction(draft, options.scopeLabel, vscodeApi);
    while (action && action !== 'cancel') {
        switch (action) {
            case 'preset': {
                const preset = await pickPreset(draft, options.scopeLabel, vscodeApi);
                if (preset === undefined) {
                    return undefined;
                }
                if (preset !== null) {
                    draft = changeDraftPreset(draft, preset);
                }
                break;
            }
            case 'enabled-categories': {
                const enabled = await pickEnabledCategories(draft, options.scopeLabel, vscodeApi);
                if (!enabled) {
                    return undefined;
                }
                draft = setDraftEnabledCategories(draft, enabled);
                break;
            }
            case 'adjust-category': {
                const adjusted = await adjustCategories(draft, options.scopeLabel, vscodeApi);
                if (!adjusted) {
                    return undefined;
                }
                draft = adjusted;
                break;
            }
            case 'clear':
                draft = clearDraftCustomizations(draft);
                break;
            case 'reset':
                draft = resetProfileDraft();
                break;
            case 'save': {
                const profile = normalizeProfileDraft(draft);
                await options.onSave(profile);
                return profile;
            }
        }
        action = await pickMainAction(draft, options.scopeLabel, vscodeApi);
    }
    return undefined;
}

export const runProfileWizard = showProfileWizard;

import * as fs from 'fs';
import * as path from 'path';

export type Confidence = 'ALTA' | 'MEDIA' | 'BAIXA';
export type Preset = 'conservador' | 'equilibrado' | 'completo';
export type Risk = 'ALTO' | 'MEDIO' | 'BAIXO';

export interface CategoryProfile {
    enabled?: boolean;
    minimumConfidence?: Confidence;
    severity?: Risk;
}

export interface AnalysisProfile {
    schemaVersion: 1;
    preset: Preset;
    categories: Record<string, CategoryProfile>;
}

export const DEFAULT_PROFILE: AnalysisProfile = {
    schemaVersion: 1,
    preset: 'conservador',
    categories: {}
};

const KNOWN_CATEGORIES = new Set([
    'DADO_HARDCODED', 'DADO_SEM_CRIPTOGRAFIA', 'CRIPTOGRAFIA_FRACA',
    'DADO_EM_LOG', 'TRANSFERENCIA_SEM_BASE_LEGAL', 'COLETA_EXCESSIVA',
    'AUSENCIA_EXCLUSAO', 'CAMPO_SEM_HASH', 'AUSENCIA_SOFT_DELETE',
    'AUSENCIA_RETENCAO', 'MISTURA_DADOS', 'AUSENCIA_CONSENTIMENTO',
    'DADO_SENSIVEL_COMO_PK'
]);

export class ProfileError extends Error {
    constructor(message: string, public readonly filePath?: string) {
        super(message);
        this.name = 'ProfileError';
    }
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
}

export function validateProfile(value: unknown, filePath?: string): AnalysisProfile {
    if (!isRecord(value)) {
        throw new ProfileError('A configuracao deve ser um objeto JSON.', filePath);
    }
    const unknownRoot = Object.keys(value).filter(
        key => !['schemaVersion', 'preset', 'categories'].includes(key)
    );
    if (unknownRoot.length) {
        throw new ProfileError(`Opcoes desconhecidas: ${unknownRoot.join(', ')}.`, filePath);
    }
    if ((value.schemaVersion ?? 1) !== 1) {
        throw new ProfileError('schemaVersion deve ser 1.', filePath);
    }
    const preset = value.preset ?? 'conservador';
    if (!['conservador', 'equilibrado', 'completo'].includes(String(preset))) {
        throw new ProfileError('preset deve ser conservador, equilibrado ou completo.', filePath);
    }
    const rawCategories = value.categories ?? {};
    if (!isRecord(rawCategories)) {
        throw new ProfileError('categories deve ser um objeto.', filePath);
    }

    const categories: Record<string, CategoryProfile> = {};
    for (const [name, rawOptions] of Object.entries(rawCategories)) {
        if (!name.trim() || !isRecord(rawOptions)) {
            throw new ProfileError(`Categoria invalida: ${name || '<vazia>'}.`, filePath);
        }
        if (!KNOWN_CATEGORIES.has(name)) {
            throw new ProfileError(`Categoria desconhecida: ${name}.`, filePath);
        }
        const unknown = Object.keys(rawOptions).filter(
            key => !['enabled', 'minimumConfidence', 'severity'].includes(key)
        );
        if (unknown.length) {
            throw new ProfileError(`Opcoes desconhecidas em ${name}: ${unknown.join(', ')}.`, filePath);
        }
        if (rawOptions.enabled !== undefined && typeof rawOptions.enabled !== 'boolean') {
            throw new ProfileError(`enabled de ${name} deve ser booleano.`, filePath);
        }
        if (
            rawOptions.minimumConfidence !== undefined
            && !['ALTA', 'MEDIA', 'BAIXA'].includes(String(rawOptions.minimumConfidence))
        ) {
            throw new ProfileError(`minimumConfidence invalido em ${name}.`, filePath);
        }
        if (
            rawOptions.severity !== undefined
            && !['ALTO', 'MEDIO', 'BAIXO'].includes(String(rawOptions.severity))
        ) {
            throw new ProfileError(`severity invalido em ${name}.`, filePath);
        }
        categories[name] = rawOptions as CategoryProfile;
    }
    return { schemaVersion: 1, preset: preset as Preset, categories };
}

export function profileFilePath(workspaceRoot: string): string {
    return path.join(workspaceRoot, '.privacy-scanner.json');
}

export function loadProfile(workspaceRoot?: string): AnalysisProfile {
    if (!workspaceRoot) {
        return DEFAULT_PROFILE;
    }
    const filePath = profileFilePath(workspaceRoot);
    if (!fs.existsSync(filePath)) {
        return DEFAULT_PROFILE;
    }
    try {
        return validateProfile(JSON.parse(fs.readFileSync(filePath, 'utf8')), filePath);
    } catch (error) {
        if (error instanceof ProfileError) {
            throw error;
        }
        throw new ProfileError(
            `JSON invalido: ${error instanceof Error ? error.message : String(error)}`,
            filePath
        );
    }
}

export function serializeProfile(profile: AnalysisProfile): string {
    return `${JSON.stringify(profile, null, 2)}\n`;
}

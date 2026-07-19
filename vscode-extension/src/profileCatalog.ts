import type { Confidence, Preset } from './profile';

export type ProfileCategoryGroup = 'code' | 'sqlite';

export const PROFILE_CATEGORY_IDS = [
    'DADO_HARDCODED',
    'DADO_SEM_CRIPTOGRAFIA',
    'CRIPTOGRAFIA_FRACA',
    'DADO_EM_LOG',
    'TRANSFERENCIA_SEM_BASE_LEGAL',
    'COLETA_EXCESSIVA',
    'AUSENCIA_EXCLUSAO',
    'CAMPO_SEM_HASH',
    'AUSENCIA_SOFT_DELETE',
    'AUSENCIA_RETENCAO',
    'MISTURA_DADOS',
    'AUSENCIA_CONSENTIMENTO',
    'DADO_SENSIVEL_COMO_PK',
    'DADO_SENSIVEL_COMO_INDICE_UNICO'
] as const;

export type ProfileCategoryId = typeof PROFILE_CATEGORY_IDS[number];

export interface ProfileCategoryGroupDescriptor {
    readonly id: ProfileCategoryGroup;
    readonly label: string;
    readonly description: string;
}

export interface ProfileCategoryDescriptor {
    readonly id: ProfileCategoryId;
    readonly group: ProfileCategoryGroup;
    readonly label: string;
    readonly description: string;
}

export interface ProfilePresetDescriptor {
    readonly id: Preset;
    readonly label: string;
    readonly minimumConfidence: Confidence;
    readonly description: string;
}

export const PROFILE_CATEGORY_GROUPS: readonly ProfileCategoryGroupDescriptor[] = [
    {
        id: 'code',
        label: 'Código',
        description: 'Regras aplicadas a arquivos Python e Java.'
    },
    {
        id: 'sqlite',
        label: 'SQLite',
        description: 'Regras aplicadas à estrutura de bancos SQLite.'
    }
];

export const PROFILE_CATEGORIES: readonly ProfileCategoryDescriptor[] = [
    {
        id: 'DADO_HARDCODED',
        group: 'code',
        label: 'Possível dado pessoal literal no código',
        description: 'Procura atribuições literais a identificadores classificados.'
    },
    {
        id: 'DADO_SEM_CRIPTOGRAFIA',
        group: 'code',
        label: 'Proteção no armazenamento não evidenciada',
        description: 'Procura fluxos de armazenamento sem proteção evidenciada localmente.'
    },
    {
        id: 'CRIPTOGRAFIA_FRACA',
        group: 'code',
        label: 'Algoritmo criptográfico potencialmente fraco',
        description: 'Procura usos de algoritmos classificados tecnicamente como fracos.'
    },
    {
        id: 'DADO_EM_LOG',
        group: 'code',
        label: 'Possível dado pessoal em log',
        description: 'Procura possíveis registros de dados pessoais em mecanismos de log.'
    },
    {
        id: 'TRANSFERENCIA_SEM_BASE_LEGAL',
        group: 'code',
        label: 'Transferência sem marcador técnico de base legal',
        description: 'Procura envios externos sem marcador técnico local de base legal.'
    },
    {
        id: 'COLETA_EXCESSIVA',
        group: 'code',
        label: 'Possível coleta acima do mínimo necessário',
        description: 'Procura concentração de campos classificados em uma mesma entrada.'
    },
    {
        id: 'AUSENCIA_EXCLUSAO',
        group: 'code',
        label: 'Exclusão ou anonimização não evidenciada',
        description: 'Procura modelos sem mecanismo local evidenciado de exclusão ou anonimização.'
    },
    {
        id: 'CAMPO_SEM_HASH',
        group: 'sqlite',
        label: 'Proteção do campo não evidenciada',
        description: 'Verifica se o schema evidencia proteção para campos classificados.'
    },
    {
        id: 'AUSENCIA_SOFT_DELETE',
        group: 'sqlite',
        label: 'Exclusão lógica ou anonimização não evidenciada',
        description: 'Verifica se o schema evidencia exclusão lógica ou anonimização.'
    },
    {
        id: 'AUSENCIA_RETENCAO',
        group: 'sqlite',
        label: 'Retenção ou expurgo não evidenciado',
        description: 'Verifica se o schema evidencia controle de retenção ou expurgo.'
    },
    {
        id: 'MISTURA_DADOS',
        group: 'sqlite',
        label: 'Separação entre dados requer revisão',
        description: 'Aponta estruturas que concentram campos classificados e operacionais.'
    },
    {
        id: 'AUSENCIA_CONSENTIMENTO',
        group: 'sqlite',
        label: 'Proteção/base legal não evidenciada',
        description: 'Verifica marcadores técnicos de consentimento ou de outra base legal.'
    },
    {
        id: 'DADO_SENSIVEL_COMO_PK',
        group: 'sqlite',
        label: 'Identificador pessoal usado como chave primária',
        description: 'Aponta o uso de campo classificado como identificador primário.'
    },
    {
        id: 'DADO_SENSIVEL_COMO_INDICE_UNICO',
        group: 'sqlite',
        label: 'Identificador pessoal em índice único',
        description: 'Aponta identificadores pessoais expostos como índices únicos correlacionáveis.'
    }
];

export const PROFILE_PRESETS: readonly ProfilePresetDescriptor[] = [
    {
        id: 'conservador',
        label: 'Conservador',
        minimumConfidence: 'ALTA',
        description: 'Mostra somente indícios de confiança alta e reduz o ruído.'
    },
    {
        id: 'equilibrado',
        label: 'Equilibrado',
        minimumConfidence: 'MEDIA',
        description: 'Mostra indícios de confiança alta e média.'
    },
    {
        id: 'completo',
        label: 'Completo',
        minimumConfidence: 'BAIXA',
        description: 'Mostra indícios de todas as faixas de confiança para maior cobertura.'
    }
];

const CATEGORY_IDS = new Set<string>(PROFILE_CATEGORY_IDS);

export function isProfileCategoryId(value: string): value is ProfileCategoryId {
    return CATEGORY_IDS.has(value);
}

export function getProfileCategory(id: ProfileCategoryId): ProfileCategoryDescriptor {
    const descriptor = PROFILE_CATEGORIES.find(category => category.id === id);
    if (!descriptor) {
        throw new Error(`Categoria de perfil desconhecida: ${id}.`);
    }
    return descriptor;
}

export function getProfilePreset(preset: Preset): ProfilePresetDescriptor {
    const descriptor = PROFILE_PRESETS.find(candidate => candidate.id === preset);
    if (!descriptor) {
        throw new Error(`Preset de perfil desconhecido: ${preset}.`);
    }
    return descriptor;
}

export function presetMinimumConfidence(preset: Preset): Confidence {
    return getProfilePreset(preset).minimumConfidence;
}

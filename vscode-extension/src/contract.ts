/**
 * Contrato normalizado entre a extensao e o backend do Privacy Scanner.
 *
 * Este modulo nao depende da API do VS Code para que suas regras possam ser
 * testadas com Node puro. Campos legados continuam sendo lidos apenas como
 * compatibilidade; todo estado novo da extensao usa os nomes canonicos.
 */

export type Risk = 'ALTO' | 'MEDIO' | 'BAIXO';
export type Confidence = 'ALTA' | 'MEDIA' | 'BAIXA';

export interface Finding {
    finding_id?: string;
    finding_id_legacy?: string;
    arquivo: string;
    linha: number;
    categoria: string;
    risco: Risk;
    risco_base?: Risk;
    confianca?: Confidence;
    artigo_lgpd: string;
    /** Evidencia curta e segura para exibicao; nunca o codigo-fonte bruto. */
    evidencia_segura: string;
    recomendacao?: string;
}

export interface RiskCounts {
    ALTO: number | null;
    MEDIO: number | null;
    BAIXO: number | null;
}

export interface AnalysisSummary {
    total: number | null;
    por_risco: RiskCounts;
    /** Nulo quando o backend nao pode calcular o indicador para o escopo. */
    indicador_tecnico: number | null;
    criterio_indicador?: string;
    aviso_escopo?: string;
}

export interface ScopeMetadata {
    status?: string;
    arquivos_elegiveis?: number;
    arquivos_analisados?: number;
    arquivos_ignorados?: number;
    arquivos_falhos?: number;
    erros_por_arquivo?: unknown;
}

export interface AnalysisResponse {
    success: boolean;
    status?: string;
    aviso_escopo?: string;
    achados: Finding[];
    resumo?: AnalysisSummary;
    escopo?: ScopeMetadata;
    message?: string;
    perfil_analise?: AnalysisProfileMetadata;
}

export interface AnalysisProfileMetadata {
    preset?: string;
    origem?: string;
    hash?: string;
}

export interface BackendHealth {
    valid: boolean;
    reason?: string;
    service?: string;
    version?: string;
}

export function aggregateAnalysisResponses(responses: AnalysisResponse[]): AnalysisResponse {
    const successful = responses.filter(item => item.success);
    if (successful.length === 0) {
        return responses[responses.length - 1] ?? { success: false, status: 'invalid', achados: [] };
    }
    const riskCounts = successful.reduce(
        (acc, item) => {
            for (const risk of ['ALTO', 'MEDIO', 'BAIXO'] as const) {
                acc[risk] += item.resumo?.por_risco[risk] ?? 0;
            }
            return acc;
        },
        { ALTO: 0, MEDIO: 0, BAIXO: 0 }
    );
    const scope = responses.reduce<ScopeMetadata>((acc, item) => ({
        status: acc.status,
        arquivos_elegiveis: (acc.arquivos_elegiveis ?? 0) + (item.escopo?.arquivos_elegiveis ?? 0),
        arquivos_analisados: (acc.arquivos_analisados ?? 0) + (item.escopo?.arquivos_analisados ?? 0),
        arquivos_ignorados: (acc.arquivos_ignorados ?? 0) + (item.escopo?.arquivos_ignorados ?? 0),
        arquivos_falhos: (acc.arquivos_falhos ?? 0) + (item.escopo?.arquivos_falhos ?? 0)
    }), { status: 'complete' });
    const partial = responses.some(
        item => !item.success || item.status === 'partial' || item.escopo?.status === 'partial'
    );
    scope.status = partial ? 'partial' : 'complete';
    const findings = successful.flatMap(item => item.achados);
    return {
        success: true,
        status: scope.status,
        achados: findings,
        aviso_escopo: successful[0]?.aviso_escopo,
        resumo: {
            total: findings.length,
            por_risco: riskCounts,
            indicador_tecnico: Math.max(
                0,
                100 - riskCounts.ALTO * 10 - riskCounts.MEDIO * 5 - riskCounts.BAIXO * 2
            )
        },
        escopo: scope,
        perfil_analise: successful.length === 1 ? successful[0].perfil_analise : undefined
    };
}

type UnknownRecord = Record<string, unknown>;

function asRecord(value: unknown): UnknownRecord | undefined {
    return value !== null && typeof value === 'object' && !Array.isArray(value)
        ? value as UnknownRecord
        : undefined;
}

function stringValue(...values: unknown[]): string | undefined {
    for (const value of values) {
        if (typeof value === 'string' && value.trim().length > 0) {
            return value.trim();
        }
    }
    return undefined;
}

function numberValue(...values: unknown[]): number | undefined {
    for (const value of values) {
        if (typeof value === 'number' && Number.isFinite(value)) {
            return value;
        }
        if (typeof value === 'string' && value.trim().length > 0) {
            const parsed = Number(value);
            if (Number.isFinite(parsed)) {
                return parsed;
            }
        }
    }
    return undefined;
}

function firstArray(record: UnknownRecord, names: string[]): unknown[] {
    for (const name of names) {
        const candidate = record[name];
        if (Array.isArray(candidate)) {
            return candidate;
        }
    }
    return [];
}

function normalizeRisk(value: unknown): Risk {
    const normalized = stringValue(value)?.toUpperCase().normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');

    if (normalized === 'ALTO' || normalized === 'HIGH') {
        return 'ALTO';
    }
    if (normalized === 'MEDIO' || normalized === 'MEDIUM') {
        return 'MEDIO';
    }
    return 'BAIXO';
}

/**
 * Descarta campos que possam conter o codigo-fonte bruto. `trecho` e aceito
 * apenas como alias legado porque o backend o entrega redigido nesta versao.
 */
export function normalizeFinding(value: unknown): Finding | undefined {
    const record = asRecord(value);
    if (!record) {
        return undefined;
    }

    const arquivo = stringValue(record.arquivo, record.file, record.filepath, record.path);
    const categoria = stringValue(record.categoria, record.category);
    if (!arquivo || !categoria) {
        return undefined;
    }

    const linha = Math.max(0, Math.floor(numberValue(
        record.linha,
        record.line,
        record.line_number
    ) ?? 0));
    const evidenciaSegura = stringValue(
        record.evidencia_segura,
        record.safe_evidence,
        record.trecho,
        record.descricao,
        record.description
    ) ?? 'Evidencia tecnica disponivel; revise o achado no backend.';

    return {
        finding_id: stringValue(record.finding_id, record.id),
        finding_id_legacy: stringValue(record.finding_id_legacy),
        arquivo,
        linha,
        categoria,
        risco: normalizeRisk(record.risco ?? record.risk),
        risco_base: normalizeRisk(record.risco_base ?? record.base_risk ?? record.risco ?? record.risk),
        confianca: normalizeConfidence(record.confianca ?? record.confidence),
        artigo_lgpd: stringValue(record.artigo_lgpd, record.lgpd_article, record.artigo) ?? '',
        evidencia_segura: evidenciaSegura,
        recomendacao: stringValue(record.recomendacao, record.recommendation)
    };
}

function normalizeConfidence(value: unknown): Confidence {
    const normalized = stringValue(value)?.toUpperCase();
    return normalized === 'MEDIA' || normalized === 'BAIXA' ? normalized : 'ALTA';
}

function normalizeRiskCounts(value: unknown): RiskCounts {
    const record = asRecord(value) ?? {};
    return {
        ALTO: numberValue(record.ALTO, record.alto, record.HIGH) ?? null,
        MEDIO: numberValue(record.MEDIO, record['MÉDIO'], record.medio, record.medium, record.MEDIUM) ?? null,
        BAIXO: numberValue(record.BAIXO, record.baixo, record.low, record.LOW) ?? null
    };
}

export function normalizeSummary(value: unknown): AnalysisSummary | undefined {
    const record = asRecord(value);
    if (!record) {
        return undefined;
    }

    return {
        total: numberValue(record.total, record.total_achados, record.count) ?? null,
        por_risco: normalizeRiskCounts(record.por_risco ?? record.by_risk),
        indicador_tecnico: numberValue(
            record.indicador_tecnico,
            record.score_conformidade
        ) ?? null,
        criterio_indicador: stringValue(record.criterio_indicador, record.indicator_criterion),
        aviso_escopo: stringValue(record.aviso_escopo, record.scope_notice)
    };
}

function normalizeScope(value: unknown, status?: string): ScopeMetadata | undefined {
    const record = asRecord(value);
    if (!record && !status) {
        return undefined;
    }

    const source = record ?? {};
    return {
        status: stringValue(source.status) ?? status,
        arquivos_elegiveis: numberValue(source.arquivos_elegiveis, source.eligible_files),
        arquivos_analisados: numberValue(source.arquivos_analisados, source.analyzed_files),
        arquivos_ignorados: numberValue(source.arquivos_ignorados, source.ignored_files),
        arquivos_falhos: numberValue(source.arquivos_falhos, source.failed_files),
        erros_por_arquivo: source.erros_por_arquivo ?? source.errors_by_file ?? source.erros
    };
}

/** Normaliza o contrato canonico e os aliases de versoes anteriores. */
export function normalizeAnalysisResponse(value: unknown): AnalysisResponse {
    const record = asRecord(value) ?? {};
    const status = stringValue(record.status);
    const normalizedStatus = status?.toLowerCase().normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');
    const summarySource = record.resumo
        ?? record.summary
        ?? record.sumario
        ?? (
            record.indicador_tecnico !== undefined
            || record.score_conformidade !== undefined
            || record.criterio_indicador !== undefined
            || record.total !== undefined
                ? record
                : undefined
        );
    const resumo = normalizeSummary(summarySource);
    const successfulStatuses = new Set([
        'ok',
        'success',
        'complete',
        'completo',
        'completed',
        'concluido',
        'concluida',
        'partial',
        'parcial'
    ]);

    return {
        success: record.success === true
            || record.sucesso === true
            || (normalizedStatus !== undefined && successfulStatuses.has(normalizedStatus)),
        status,
        aviso_escopo: stringValue(record.aviso_escopo, record.scope_notice),
        achados: firstArray(record, ['achados', 'vulnerabilities', 'vulnerabilidades', 'findings'])
            .map(normalizeFinding)
            .filter((finding): finding is Finding => finding !== undefined),
        resumo,
        escopo: normalizeScope(record.escopo ?? record.scope ?? record, status),
        message: stringValue(record.message, record.mensagem, record.error)
        ,perfil_analise: normalizeProfileMetadata(record.perfil_analise ?? record.analysis_profile)
    };
}

function normalizeProfileMetadata(value: unknown): AnalysisProfileMetadata | undefined {
    const record = asRecord(value);
    if (!record) {
        return undefined;
    }
    return {
        preset: stringValue(record.preset, record.name),
        origem: stringValue(record.origem, record.source),
        hash: stringValue(record.hash, record.config_hash)
    };
}

/**
 * O gate impede que uma resposta antiga substitua o estado da analise mais
 * recente. O AbortController da extensao reduz trabalho; este gate e a defesa
 * final para respostas que ja estavam em transito.
 */
export class LatestRequestGate {
    private current = 0;

    begin(): number {
        this.current += 1;
        return this.current;
    }

    isCurrent(requestId: number): boolean {
        return requestId === this.current;
    }

    invalidate(): void {
        this.current += 1;
    }
}

function normalizedServiceName(value: string): string {
    return value.toLowerCase().replace(/[^a-z0-9]/g, '');
}

/** Valida que a porta pertence ao backend esperado e que ele declara versao compativel. */
export function validateBackendHealth(value: unknown): BackendHealth {
    const record = asRecord(value);
    if (!record || stringValue(record.status)?.toLowerCase() !== 'ok') {
        return { valid: false, reason: 'O endpoint /health nao retornou status ok.' };
    }

    const service = stringValue(
        record.service,
        record.servico,
        record.service_name,
        record.nome_servico,
        record.name
    );
    if (!service) {
        return { valid: false, reason: 'O backend nao informou sua identidade.' };
    }

    const knownServices = new Set(['privacyscanner', 'privacyscannerlgpd']);
    if (!knownServices.has(normalizedServiceName(service))) {
        return { valid: false, reason: `Servico inesperado na porta configurada: ${service}.`, service };
    }

    if (numberValue(record.api_version, record.apiVersion) !== 1) {
        return { valid: false, reason: 'Versao de protocolo da API incompativel.', service };
    }

    const version = stringValue(record.version, record.versao);
    const match = version?.match(/^v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$/);
    if (!match) {
        return { valid: false, reason: 'O backend nao informou uma versao semver valida.', service, version };
    }
    if (Number(match[1]) !== 1) {
        return { valid: false, reason: `Versao de backend incompativel: ${version}.`, service, version };
    }

    return { valid: true, service, version };
}

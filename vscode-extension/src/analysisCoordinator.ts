import { LatestRequestGate } from './contract';
import * as path from 'path';

export interface CoordinatedAnalysisSession {
    requestId: number;
    controller: AbortController;
    startedAt: number;
    label: string;
}

export type CanonicalAnalysisOrigin = 'workspace' | 'single';

export interface AnalysisTarget {
    origin: CanonicalAnalysisOrigin;
    paths: readonly string[];
    label: string;
}

/** Compara caminhos completos, sem confundir pastas irmãs como app e app-extra. */
export function isPathInAnalysisTarget(target: AnalysisTarget, filePath: string): boolean {
    const normalize = (value: string): string => {
        const resolved = path.resolve(value);
        return process.platform === 'win32' ? resolved.toLowerCase() : resolved;
    };
    const candidate = normalize(filePath);
    return target.paths.some(root => {
        const relative = path.relative(normalize(root), candidate);
        return relative === '' || (target.origin === 'workspace'
            && relative !== '..' && !relative.startsWith(`..${path.sep}`)
            && !path.isAbsolute(relative));
    });
}

/** Identifica a varredura do resumo sem recalcular os valores do backend. */
export class AnalysisSnapshot {
    completedAt?: number;
    stale = false;

    constructor(readonly target: AnalysisTarget) {}

    markChanged(filePath: string): boolean {
        if (!isPathInAnalysisTarget(this.target, filePath)) {
            return false;
        }
        this.stale = true;
        return true;
    }

    complete(completedAt: number = Date.now()): void {
        // Uma edição durante a requisição continua tornando o resultado antigo.
        this.completedAt = completedAt;
    }
}

export interface AnalysisDocument {
    uri: { scheme: string; fsPath: string };
    isUntitled: boolean;
    isDirty: boolean;
    version?: number;
}

export interface SavableAnalysisDocument extends AnalysisDocument {
    save(): PromiseLike<boolean>;
}

export function shouldAutomaticallyAnalyze(document: AnalysisDocument, enabled: boolean): boolean {
    return enabled && document.uri.scheme === 'file' && !document.isUntitled && !document.isDirty
        && /\.(py|java|db|sqlite|sqlite3)$/i.test(document.uri.fsPath);
}

export function documentChangedSinceRequest(version: number | undefined, document?: AnalysisDocument): boolean {
    return Boolean(document && (document.isDirty || (version !== undefined && document.version !== version)));
}

export function discardQueuedAnalysesInTarget<T extends { fsPath: string }>(
    pending: Map<string, T>, target: AnalysisTarget
): void {
    for (const [key, uri] of pending) {
        if (isPathInAnalysisTarget(target, uri.fsPath)) {
            pending.delete(key);
        }
    }
}

export function dirtyDocumentsInRoots<T extends AnalysisDocument>(
    documents: readonly T[], roots: readonly string[]
): T[] {
    return documents.filter(document => document.uri.scheme === 'file'
        && !document.isUntitled && document.isDirty
        && /\.(py|java)$/i.test(document.uri.fsPath)
        && isPathInAnalysisTarget({ origin: 'workspace', paths: roots, label: '' }, document.uri.fsPath));
}

/** A confirmação autoriza apenas os documentos modificados do escopo escolhido. */
export async function saveDirtyAnalysisDocuments(
    documents: () => readonly SavableAnalysisDocument[],
    roots: readonly string[],
    confirm: (count: number) => PromiseLike<boolean>
): Promise<'ready' | 'cancelled' | 'unsaved'> {
    const dirty = dirtyDocumentsInRoots(documents(), roots);
    if (dirty.length === 0) {
        return 'ready';
    }
    if (!await confirm(dirty.length)) {
        return 'cancelled';
    }
    for (const document of dirty) {
        if (document.isDirty && !await document.save()) {
            return 'unsaved';
        }
    }
    return dirtyDocumentsInRoots(documents(), roots).length === 0 ? 'ready' : 'unsaved';
}

/** Preserva o resumo do projeto quando um arquivo é analisado automaticamente. */
export function shouldPreserveCanonicalWorkspaceState(
    currentOrigin: CanonicalAnalysisOrigin | undefined,
    automaticFileAnalysis: boolean
): boolean {
    return automaticFileAnalysis && currentOrigin === 'workspace';
}

export class AnalysisCoordinator {
    private active?: CoordinatedAnalysisSession;
    private readonly gate = new LatestRequestGate();

    get isActive(): boolean {
        return this.active !== undefined;
    }

    begin(label: string): CoordinatedAnalysisSession {
        this.active?.controller.abort();
        const session = {
            requestId: this.gate.begin(),
            controller: new AbortController(),
            startedAt: Date.now(),
            label
        };
        this.active = session;
        return session;
    }

    isCurrent(session: CoordinatedAnalysisSession): boolean {
        return this.active === session && this.gate.isCurrent(session.requestId);
    }

    finish(session: CoordinatedAnalysisSession): boolean {
        if (!this.isCurrent(session)) {
            return false;
        }
        this.active = undefined;
        return true;
    }

    cancel(): void {
        this.active?.controller.abort();
        this.active = undefined;
        this.gate.invalidate();
    }
}

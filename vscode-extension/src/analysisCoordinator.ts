import { LatestRequestGate } from './contract';

export interface CoordinatedAnalysisSession {
    requestId: number;
    controller: AbortController;
    startedAt: number;
    label: string;
}

export type CanonicalAnalysisOrigin = 'workspace' | 'single';

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

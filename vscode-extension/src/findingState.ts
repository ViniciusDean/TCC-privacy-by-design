import * as path from 'path';
import { Finding } from './contract';

export class FindingStateStore {
    readonly byFile = new Map<string, Finding[]>();
    readonly ignoredKeys = new Set<string>();

    replaceIgnored(keys: Iterable<string>): void {
        this.ignoredKeys.clear();
        for (const key of keys) {
            this.ignoredKeys.add(key);
        }
    }

    key(finding: Finding): string {
        if (finding.finding_id) {
            return `finding:${finding.finding_id}`;
        }
        return this.legacyLocationKey(finding);
    }

    legacyLocationKey(finding: Finding): string {
        return [
            path.normalize(finding.arquivo).toLowerCase(),
            finding.linha,
            finding.categoria,
            finding.risco_base || finding.risco
        ].join('|');
    }

    isIgnored(finding: Finding): boolean {
        if (this.ignoredKeys.has(this.key(finding))) {
            return true;
        }
        if (
            finding.finding_id_legacy
            && this.ignoredKeys.has(`finding:${finding.finding_id_legacy}`)
        ) {
            return true;
        }
        return this.ignoredKeys.has(this.legacyLocationKey(finding));
    }

    visible(): Finding[] {
        return Array.from(this.byFile.values()).flat().filter(item => !this.isIgnored(item));
    }

    ignoredCount(): number {
        return Array.from(this.byFile.values()).flat().filter(item => this.isIgnored(item)).length;
    }
}

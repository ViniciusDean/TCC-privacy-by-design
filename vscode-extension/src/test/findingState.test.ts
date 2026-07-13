import * as assert from 'assert';
import { FindingStateStore } from '../findingState';
import { Finding } from '../contract';

function finding(overrides: Partial<Finding> = {}): Finding {
    return {
        finding_id: 'new-id',
        finding_id_legacy: 'old-id',
        arquivo: 'C:/workspace/model.py',
        linha: 10,
        categoria: 'DADO_EM_LOG',
        risco: 'BAIXO',
        risco_base: 'ALTO',
        artigo_lgpd: 'Art. 46',
        evidencia_segura: 'evidencia redigida',
        ...overrides
    };
}

const state = new FindingStateStore();
const item = finding();
state.byFile.set(item.arquivo, [item]);
assert.strictEqual(state.visible().length, 1);

state.replaceIgnored(['finding:old-id']);
assert.strictEqual(state.isIgnored(item), true);
assert.strictEqual(state.ignoredCount(), 1);

const withoutIds = finding({ finding_id: undefined, finding_id_legacy: undefined });
state.replaceIgnored([state.legacyLocationKey(withoutIds)]);
assert.strictEqual(state.isIgnored(withoutIds), true);

console.log('ok - estado migra IDs legados e severidade-base');

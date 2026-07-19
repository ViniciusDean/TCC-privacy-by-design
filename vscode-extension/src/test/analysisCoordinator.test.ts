import * as assert from 'assert';
import {
    AnalysisCoordinator,
    shouldPreserveCanonicalWorkspaceState
} from '../analysisCoordinator';

const coordinator = new AnalysisCoordinator();
const first = coordinator.begin('primeira');
const second = coordinator.begin('segunda');

assert.strictEqual(first.controller.signal.aborted, true);
assert.strictEqual(coordinator.isCurrent(first), false);
assert.strictEqual(coordinator.isCurrent(second), true);
assert.strictEqual(coordinator.finish(second), true);
assert.strictEqual(coordinator.isActive, false);

assert.strictEqual(shouldPreserveCanonicalWorkspaceState('workspace', true), true);
assert.strictEqual(shouldPreserveCanonicalWorkspaceState('workspace', false), false);
assert.strictEqual(shouldPreserveCanonicalWorkspaceState('single', true), false);
assert.strictEqual(shouldPreserveCanonicalWorkspaceState(undefined, true), false);

console.log('ok - coordenador protege ordem e preserva resumo do workspace');

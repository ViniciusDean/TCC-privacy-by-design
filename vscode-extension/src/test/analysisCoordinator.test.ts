import * as assert from 'assert';
import { AnalysisCoordinator } from '../analysisCoordinator';

const coordinator = new AnalysisCoordinator();
const first = coordinator.begin('primeira');
const second = coordinator.begin('segunda');

assert.strictEqual(first.controller.signal.aborted, true);
assert.strictEqual(coordinator.isCurrent(first), false);
assert.strictEqual(coordinator.isCurrent(second), true);
assert.strictEqual(coordinator.finish(second), true);
assert.strictEqual(coordinator.isActive, false);

console.log('ok - coordenador cancela respostas fora de ordem');

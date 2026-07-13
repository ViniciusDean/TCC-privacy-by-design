import * as assert from 'assert';
import {
    BackendEndpointDependencies,
    HealthCheckResult,
    normalizeServerPort,
    selectBackendPort
} from '../backendEndpoint';

function dependencies(
    health: HealthCheckResult,
    available: boolean = true,
    freePort: number = 54321
): BackendEndpointDependencies {
    return {
        checkHealth: async () => health,
        isPortAvailable: async () => available,
        findAvailablePort: async () => freePort
    };
}

async function main(): Promise<void> {
    assert.strictEqual(normalizeServerPort(5000), 5000);
    assert.strictEqual(normalizeServerPort(0), 5000);
    assert.strictEqual(normalizeServerPort(70000), 5000);
    assert.strictEqual(normalizeServerPort('5000'), 5000);

    const compatible = await selectBackendPort(
        5000,
        dependencies({ reachable: true, valid: true, version: '1.1.0' })
    );
    assert.strictEqual(compatible.action, 'reuse');
    assert.strictEqual(compatible.port, 5000);

    const free = await selectBackendPort(
        5000,
        dependencies({ reachable: false, valid: false }, true)
    );
    assert.strictEqual(free.action, 'start');
    assert.strictEqual(free.port, 5000);

    const incompatibleHttp = await selectBackendPort(
        5000,
        dependencies({ reachable: true, valid: false, reason: 'servico inesperado' })
    );
    assert.strictEqual(incompatibleHttp.action, 'relocate');
    assert.strictEqual(incompatibleHttp.port, 54321);
    assert.strictEqual(incompatibleHttp.occupiedPort, 5000);

    const occupiedWithoutHttp = await selectBackendPort(
        5000,
        dependencies({ reachable: false, valid: false }, false, 54322)
    );
    assert.strictEqual(occupiedWithoutHttp.action, 'relocate');
    assert.strictEqual(occupiedWithoutHttp.port, 54322);

    console.log('backendEndpoint.test.ts: 13 verificacoes ok');
}

void main();

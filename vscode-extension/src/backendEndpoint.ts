import axios from 'axios';
import * as net from 'net';
import { validateBackendHealth } from './contract';

export interface HealthCheckResult {
    reachable: boolean;
    valid: boolean;
    reason?: string;
    version?: string;
}

export type BackendPortAction = 'reuse' | 'start' | 'relocate';

export interface BackendPortDecision {
    action: BackendPortAction;
    port: number;
    occupiedPort?: number;
    health: HealthCheckResult;
}

export interface BackendEndpointDependencies {
    checkHealth: (port: number) => Promise<HealthCheckResult>;
    isPortAvailable: (port: number) => Promise<boolean>;
    findAvailablePort: () => Promise<number>;
}

export function normalizeServerPort(value: unknown, fallback: number = 5000): number {
    return typeof value === 'number'
        && Number.isInteger(value)
        && value >= 1
        && value <= 65535
        ? value
        : fallback;
}

export async function checkBackendHealth(
    port: number,
    timeoutMs: number = 2000
): Promise<HealthCheckResult> {
    try {
        const response = await axios.get<unknown>(
            `http://localhost:${port}/health`,
            {
                timeout: timeoutMs,
                // Qualquer resposta HTTP prova que a porta esta ocupada. O
                // corpo ainda precisa satisfazer o contrato do Privacy Scanner.
                validateStatus: () => true
            }
        );
        const health = validateBackendHealth(response.data);
        return {
            reachable: true,
            valid: health.valid,
            reason: health.reason,
            version: health.version
        };
    } catch {
        return { reachable: false, valid: false };
    }
}

export function isPortAvailable(port: number): Promise<boolean> {
    return new Promise(resolve => {
        const server = net.createServer();
        server.unref();
        server.once('error', () => resolve(false));
        server.listen(port, '127.0.0.1', () => {
            server.close(() => resolve(true));
        });
    });
}

export function findAvailablePort(): Promise<number> {
    return new Promise((resolve, reject) => {
        const server = net.createServer();
        server.unref();
        server.once('error', reject);
        server.listen(0, '127.0.0.1', () => {
            const address = server.address();
            const available = typeof address === 'object' && address ? address.port : 0;
            server.close(() => available
                ? resolve(available)
                : reject(new Error('Porta livre nao encontrada.')));
        });
    });
}

export async function selectBackendPort(
    configuredPort: number,
    dependencies: BackendEndpointDependencies = {
        checkHealth: checkBackendHealth,
        isPortAvailable,
        findAvailablePort
    }
): Promise<BackendPortDecision> {
    const health = await dependencies.checkHealth(configuredPort);
    if (health.valid) {
        return { action: 'reuse', port: configuredPort, health };
    }

    const available = health.reachable
        ? false
        : await dependencies.isPortAvailable(configuredPort);
    if (available) {
        return { action: 'start', port: configuredPort, health };
    }

    return {
        action: 'relocate',
        port: await dependencies.findAvailablePort(),
        occupiedPort: configuredPort,
        health
    };
}

import * as assert from 'assert';
import {
    LatestRequestGate,
    aggregateAnalysisResponses,
    normalizeAnalysisResponse,
    validateBackendHealth
} from '../contract';

function run(name: string, test: () => void): void {
    try {
        test();
        console.log(`ok - ${name}`);
    } catch (error) {
        console.error(`not ok - ${name}`);
        throw error;
    }
}

run('normaliza o contrato canonico sem recalcular o indicador', () => {
    const result = normalizeAnalysisResponse({
        success: true,
        achados: [{
            finding_id: 'abc',
            arquivo: '/tmp/exemplo.py',
            linha: 7,
            categoria: 'DADO_SENSIVEL',
            risco: 'ALTO',
            evidencia_segura: 'Campo sensivel identificado',
            trecho: 'nao deve prevalecer'
        }],
        resumo: {
            total: 18,
            por_risco: { ALTO: 2, MEDIO: 3, BAIXO: 13 },
            indicador_tecnico: 61,
            criterio_indicador: 'criterio do backend'
        }
    });

    assert.strictEqual(result.achados.length, 1);
    assert.strictEqual(result.achados[0].evidencia_segura, 'Campo sensivel identificado');
    assert.strictEqual(result.resumo?.indicador_tecnico, 61);
    assert.strictEqual(result.resumo?.total, 18);
});

run('aceita aliases legados sem substituir campos canonicos', () => {
    const result = normalizeAnalysisResponse({
        success: true,
        achados: [],
        vulnerabilities: [{ arquivo: '/tmp/legado.py', linha: 4, categoria: 'IGNORADO' }],
        summary: {
            total: 4,
            por_risco: { ALTO: 1, MEDIO: 2, BAIXO: 1 },
            score_conformidade: 79
        }
    });

    assert.deepStrictEqual(result.achados, []);
    assert.strictEqual(result.resumo?.indicador_tecnico, 79);
});

run('usa aliases legados quando os campos canonicos nao existem', () => {
    const result = normalizeAnalysisResponse({
        sucesso: true,
        vulnerabilidades: [{
            file: '/tmp/legado.py',
            line: '8',
            category: 'LOG_SENSIVEL',
            risk: 'medium',
            description: 'Descricao segura do backend'
        }],
        summary: { score_conformidade: 88 }
    });

    assert.strictEqual(result.success, true);
    assert.strictEqual(result.achados[0].risco, 'MEDIO');
    assert.strictEqual(result.achados[0].linha, 8);
    assert.strictEqual(result.achados[0].evidencia_segura, 'Descricao segura do backend');
    assert.strictEqual(result.resumo?.indicador_tecnico, 88);
});

run('mantem indicador nulo para escopo sem indicador', () => {
    const result = normalizeAnalysisResponse({ success: true, achados: [], resumo: { total: 0 } });
    assert.strictEqual(result.resumo?.indicador_tecnico, null);
    assert.strictEqual(result.resumo?.por_risco.ALTO, null);
});

run('aceita status e metadados canonicos no nivel raiz', () => {
    const result = normalizeAnalysisResponse({
        status: 'complete',
        achados: [],
        total: 12,
        por_risco: { ALTO: 1, MEDIO: 4, BAIXO: 7 },
        indicador_tecnico: 68,
        criterio_indicador: 'critério canônico',
        arquivos_elegiveis: 20,
        arquivos_analisados: 19,
        arquivos_falhos: 1
    });

    assert.strictEqual(result.success, true);
    assert.strictEqual(result.resumo?.indicador_tecnico, 68);
    assert.strictEqual(result.resumo?.criterio_indicador, 'critério canônico');
    assert.strictEqual(result.escopo?.arquivos_elegiveis, 20);
    assert.strictEqual(result.escopo?.arquivos_falhos, 1);
});

run('descarta respostas fora de ordem', () => {
    const gate = new LatestRequestGate();
    const first = gate.begin();
    const second = gate.begin();
    assert.strictEqual(gate.isCurrent(first), false);
    assert.strictEqual(gate.isCurrent(second), true);
    gate.invalidate();
    assert.strictEqual(gate.isCurrent(second), false);
});

run('valida identidade e versao do backend', () => {
    assert.strictEqual(validateBackendHealth({
        status: 'ok',
        service: 'privacy-scanner',
        version: '1.1.0',
        api_version: 1
    }).valid, true);
    assert.strictEqual(validateBackendHealth({
        status: 'ok',
        service: 'outro-servico',
        version: '1.1.0',
        api_version: 1
    }).valid, false);
    assert.strictEqual(validateBackendHealth({
        status: 'ok',
        service: 'privacy-scanner',
        version: '2.0.0',
        api_version: 1
    }).valid, false);
    assert.strictEqual(validateBackendHealth({
        status: 'ok', service: 'privacy-scanner', version: '1.1.0', api_version: 2
    }).valid, false);
});

run('multi-root preserva estado parcial e soma escopos', () => {
    const result = aggregateAnalysisResponses([
        {
            success: true,
            status: 'complete',
            achados: [],
            resumo: { total: 0, por_risco: { ALTO: 0, MEDIO: 0, BAIXO: 0 }, indicador_tecnico: 100 },
            escopo: { status: 'complete', arquivos_analisados: 2, arquivos_falhos: 0 }
        },
        {
            success: false,
            status: 'partial',
            achados: [],
            escopo: { status: 'partial', arquivos_analisados: 1, arquivos_falhos: 1 }
        }
    ]);

    assert.strictEqual(result.success, true);
    assert.strictEqual(result.status, 'partial');
    assert.strictEqual(result.escopo?.arquivos_analisados, 3);
});

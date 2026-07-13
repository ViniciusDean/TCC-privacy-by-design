const fs = require('fs');
const http = require('http');
const path = require('path');
const { runTests } = require('@vscode/test-electron');

function listen(server) {
    return new Promise((resolve, reject) => {
        server.once('error', reject);
        server.listen(0, '127.0.0.1', () => resolve(server.address().port));
    });
}

function close(server) {
    return new Promise(resolve => server.close(() => resolve()));
}

async function main() {
    const extensionDevelopmentPath = path.resolve(__dirname, '..');
    const extensionTestsPath = path.resolve(extensionDevelopmentPath, 'out', 'test', 'integration');
    const fixtureWorkspace = path.resolve(extensionDevelopmentPath, 'src', 'test', 'fixtures', 'workspace');
    const testWorkspace = path.resolve(extensionDevelopmentPath, '.vscode-test', 'integration-workspace');
    let healthRequests = 0;
    const incompatibleServer = http.createServer((request, response) => {
        if (request.url === '/health') {
            healthRequests += 1;
        }
        response.writeHead(404, { 'Content-Type': 'application/json' });
        response.end(JSON.stringify({ service: 'outro-servico', status: 'not-found' }));
    });
    const occupiedPort = await listen(incompatibleServer);

    fs.rmSync(testWorkspace, { recursive: true, force: true });
    fs.cpSync(fixtureWorkspace, testWorkspace, { recursive: true });
    fs.mkdirSync(path.join(testWorkspace, '.vscode'), { recursive: true });
    fs.writeFileSync(
        path.join(testWorkspace, '.vscode', 'settings.json'),
        JSON.stringify({ 'privacy-scanner.serverPort': occupiedPort }, null, 2)
    );

    try {
        await runTests({
            extensionDevelopmentPath,
            extensionTestsPath,
            version: process.env.VSCODE_TEST_VERSION || '1.128.0',
            launchArgs: [testWorkspace, '--disable-extensions']
        });
        if (healthRequests === 0) {
            throw new Error('A extensao nao verificou o servico incompatível na porta configurada.');
        }
        console.log(`Conflito de porta validado com ${healthRequests} consulta(s) ao servico incompatível.`);
    } finally {
        await close(incompatibleServer);
        fs.rmSync(testWorkspace, { recursive: true, force: true });
    }
}

main().catch(error => {
    console.error('Falha nos testes de integracao do VS Code:', error);
    process.exitCode = 1;
});

import * as assert from 'assert';
import * as vscode from 'vscode';

export async function run(): Promise<void> {
    const extension = vscode.extensions.getExtension('fatec-tcc.privacy-scanner-lgpd');
    assert.ok(extension, 'A extensao deve ser descoberta pelo Extension Host.');
    await extension.activate();
    assert.strictEqual(extension.isActive, true);

    const commands = new Set(await vscode.commands.getCommands(true));
    for (const command of [
        'privacy-scanner.analyzeNow',
        'privacy-scanner.createProfile',
        'privacy-scanner.selectProfile',
        'privacy-scanner.validateProfile',
        'privacy-scanner.restartBackend',
        'privacy-scanner.setupBackend',
        'privacy-scanner.showLogs'
    ]) {
        assert.ok(commands.has(command), `Comando nao registrado: ${command}`);
    }

    await vscode.commands.executeCommand('privacy-scanner.restartBackend');
    await vscode.commands.executeCommand('privacy-scanner.restartBackend');
    await vscode.commands.executeCommand('privacy-scanner.clearResults');
    assert.strictEqual(
        vscode.languages.getDiagnostics().flatMap(([, items]) => items).length,
        0,
        'A verificacao deve partir de estado limpo.'
    );
    try {
        await vscode.commands.executeCommand('privacy-scanner.analyzeNow');
    } catch (error) {
        console.error('Falha detalhada em analyzeNow:', error);
        throw error;
    }

    const diagnostics = vscode.languages.getDiagnostics().flatMap(([, items]) => items);
    assert.ok(diagnostics.length > 0, 'Uma analise real deve produzir diagnosticos na fixture.');
    assert.ok(
        diagnostics.every(item => item.source === 'Privacy Scanner'),
        'Os diagnosticos devem pertencer ao Privacy Scanner.'
    );
}

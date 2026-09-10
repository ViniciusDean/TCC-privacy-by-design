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
        'privacy-scanner.analyze',
        'privacy-scanner.analyzeAll',
        'privacy-scanner.analyzeDatabase',
        'privacy-scanner.clearResults',
        'privacy-scanner.exportReport',
        'privacy-scanner.exportHTML',
        'privacy-scanner.exportJSON',
        'privacy-scanner.showSidebar',
        'privacy-scanner.ignoreVulnerability',
        'privacy-scanner.restoreIgnoredVulnerabilities',
        'privacy-scanner.configureProfile',
        'privacy-scanner.createProfile',
        'privacy-scanner.selectProfile',
        'privacy-scanner.validateProfile',
        'privacy-scanner.restartBackend',
        'privacy-scanner.setupBackend',
        'privacy-scanner.showLogs'
    ]) {
        assert.ok(commands.has(command), `Comando nao registrado: ${command}`);
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    assert.ok(workspaceFolder, 'A fixture deve abrir como workspace.');
    const sampleUri = vscode.Uri.joinPath(workspaceFolder.uri, 'sample.py');
    const notesUri = vscode.Uri.joinPath(workspaceFolder.uri, 'notes.txt');
    const databaseUri = vscode.Uri.joinPath(workspaceFolder.uri, 'empty.sqlite');

    // Mantem um documento diferente ativo para provar que o URI recebido pelo
    // menu do Explorer prevalece sobre o editor atual.
    const notesDocument = await vscode.workspace.openTextDocument(notesUri);
    await vscode.window.showTextDocument(notesDocument);
    assert.notStrictEqual(vscode.window.activeTextEditor?.document.uri.fsPath, sampleUri.fsPath);

    await vscode.commands.executeCommand('privacy-scanner.showSidebar');
    await vscode.commands.executeCommand('privacy-scanner.showLogs');
    await vscode.commands.executeCommand('privacy-scanner.validateProfile');
    await vscode.commands.executeCommand('privacy-scanner.restoreIgnoredVulnerabilities');
    await vscode.commands.executeCommand('privacy-scanner.restartBackend');
    await vscode.commands.executeCommand('privacy-scanner.restartBackend');
    await vscode.commands.executeCommand('privacy-scanner.clearResults');
    assert.strictEqual(
        vscode.languages.getDiagnostics().flatMap(([, items]) => items).length,
        0,
        'A verificacao deve partir de estado limpo.'
    );
    try {
        await vscode.commands.executeCommand('privacy-scanner.analyze', sampleUri);
    } catch (error) {
        console.error('Falha detalhada em analyze com URI:', error);
        throw error;
    }

    const diagnostics = vscode.languages.getDiagnostics(sampleUri);
    assert.ok(diagnostics.length > 0, 'Uma analise real deve produzir diagnosticos na fixture.');
    assert.ok(
        diagnostics.every(item => item.source === 'Privacy Scanner'),
        'Os diagnosticos devem pertencer ao Privacy Scanner.'
    );

    // O arquivo vazio exercita tambem a recuperacao de uma recusa do backend.
    // As duas formas de argumento devem concluir sem abrir o seletor de arquivos.
    await vscode.workspace.fs.writeFile(databaseUri, new Uint8Array());
    await vscode.commands.executeCommand('privacy-scanner.analyzeDatabase', databaseUri);
    await vscode.commands.executeCommand('privacy-scanner.analyzeDatabase', [databaseUri]);

    await vscode.commands.executeCommand('privacy-scanner.clearResults');
    await vscode.commands.executeCommand('privacy-scanner.analyzeNow');
    assert.ok(
        vscode.languages.getDiagnostics(sampleUri).length > 0,
        'O comando legado analyzeNow deve continuar analisando o workspace.'
    );

    const sampleDocument = await vscode.workspace.openTextDocument(sampleUri);
    await vscode.window.showTextDocument(sampleDocument);
    const edit = new vscode.WorkspaceEdit();
    edit.replace(sampleUri, new vscode.Range(
        sampleDocument.positionAt(0), sampleDocument.positionAt(sampleDocument.getText().length)
    ), 'print("Operacao concluida")\n');
    await vscode.workspace.applyEdit(edit);
    assert.strictEqual(sampleDocument.isDirty, true);
    await vscode.window.showTextDocument(notesDocument);
    await vscode.window.showTextDocument(sampleDocument);
    // O debounce automático é 500 ms; a troca de editor não pode analisar o buffer sujo.
    await new Promise(resolve => setTimeout(resolve, 1200));
    assert.ok(vscode.languages.getDiagnostics(sampleUri).length > 0,
        'Editar sem salvar deve manter somente os diagnósticos da versão salva.');
    assert.strictEqual(sampleDocument.isDirty, true, 'A análise automática não pode salvar o arquivo.');
    assert.strictEqual(await sampleDocument.save(), true);
    const deadline = Date.now() + 10000;
    while (vscode.languages.getDiagnostics(sampleUri).length > 0 && Date.now() < deadline) {
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    assert.strictEqual(vscode.languages.getDiagnostics(sampleUri).length, 0,
        'Salvar a correção deve disparar nova análise e retirar os diagnósticos antigos.');
    await vscode.commands.executeCommand('privacy-scanner.analyzeAll');
    assert.strictEqual(vscode.languages.getDiagnostics(sampleUri).length, 0);
    console.log('Fluxo real validado: analisar, editar sem salvar, salvar e reanalisar.');
}

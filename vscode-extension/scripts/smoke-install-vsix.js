const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const {
    downloadAndUnzipVSCode,
    resolveCliPathFromVSCodeExecutablePath
} = require('@vscode/test-electron');

async function main() {
    const root = path.resolve(__dirname, '..');
    const manifest = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
    const vsix = `${manifest.name}-${manifest.version}.vsix`;
    if (!fs.existsSync(path.join(root, vsix))) {
        throw new Error(`Pacote VSIX esperado nao encontrado: ${vsix}.`);
    }
    const version = process.env.VSCODE_TEST_VERSION || '1.128.0';
    const executable = await downloadAndUnzipVSCode(version);
    const cli = resolveCliPathFromVSCodeExecutablePath(executable);
    const extensionsDir = path.join(root, '.vscode-test', 'smoke-extensions');
    const userDataDir = path.join(root, '.vscode-test', 'smoke-user-data');
    fs.rmSync(extensionsDir, { recursive: true, force: true });
    fs.rmSync(userDataDir, { recursive: true, force: true });
    const cliArgs = [
        '--install-extension', path.join(root, vsix),
        '--force',
        '--extensions-dir', extensionsDir,
        '--user-data-dir', userDataDir
    ];
    const result = spawnSync(cli, cliArgs, {
        encoding: 'utf8',
        // code.cmd exige shell no Windows; todos os argumentos sao caminhos
        // locais controlados por este script de CI.
        shell: process.platform === 'win32'
    });
    if (result.status !== 0) {
        throw new Error(result.stderr || result.stdout || 'Falha ao instalar VSIX.');
    }
    const installed = fs.existsSync(extensionsDir)
        ? fs.readdirSync(extensionsDir, { withFileTypes: true })
            .filter(entry => entry.isDirectory())
            .map(entry => path.join(extensionsDir, entry.name, 'package.json'))
            .filter(candidate => fs.existsSync(candidate))
            .map(candidate => ({
                packagePath: candidate,
                manifest: JSON.parse(fs.readFileSync(candidate, 'utf8'))
            }))
        : [];
    const expectedInstalled = installed.find(candidate =>
        candidate.manifest.name === manifest.name
        && candidate.manifest.version === manifest.version
        && candidate.manifest.publisher === manifest.publisher
    );
    if (!expectedInstalled) {
        throw new Error(`O pacote instalado nao corresponde a ${manifest.publisher}.${manifest.name}@${manifest.version}.`);
    }
    const installedMain = path.resolve(
        path.dirname(expectedInstalled.packagePath),
        expectedInstalled.manifest.main
    );
    const installedSource = fs.readFileSync(installedMain, 'utf8');
    if (
        !installedSource.includes('activate: () => activate')
        || !installedSource.includes('deactivate: () => deactivate')
    ) {
        throw new Error('O JavaScript empacotado nao exporta activate e deactivate para o VS Code.');
    }
    console.log(`VSIX ${vsix} instalado com sucesso em ambiente isolado.`);
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});

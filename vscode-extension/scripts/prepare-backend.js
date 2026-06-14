const fs = require('fs');
const path = require('path');

const extensionRoot = path.resolve(__dirname, '..');
const projectRoot = path.resolve(extensionRoot, '..');
const backendTarget = path.join(extensionRoot, 'python_backend');

const backendFiles = [
    'server.py',
    'code_analyzer.py',
    'java_analyzer.py',
    'db_analyzer.py',
    'reporter.py',
    'requirements.txt'
];

fs.rmSync(backendTarget, { recursive: true, force: true });
fs.mkdirSync(backendTarget, { recursive: true });

for (const file of backendFiles) {
    const source = path.join(projectRoot, file);
    if (!fs.existsSync(source)) {
        throw new Error(`Arquivo obrigatório do backend não encontrado: ${source}`);
    }
    fs.copyFileSync(source, path.join(backendTarget, file));
}

console.log(`Backend preparado em ${backendTarget}`);

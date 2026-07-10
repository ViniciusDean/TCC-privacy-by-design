#!/usr/bin/env node

/*
 * Garante que o VSIX não anuncie uma versão diferente do backend que ele
 * empacota. A fonte de verdade é ../VERSION, espelhada em
 * reporter.VERSAO_FERRAMENTA. O modo --bundled-only é usado após
 * prepare-backend, quando python_backend já foi copiado.
 */

const fs = require('fs');
const path = require('path');

const extensionRoot = path.resolve(__dirname, '..');
const packagePath = path.join(extensionRoot, 'package.json');
const projectRoot = path.resolve(extensionRoot, '..');
const rootVersionPath = path.join(projectRoot, 'VERSION');
const rootReporterPath = path.join(projectRoot, 'reporter.py');
const rootBackendPath = path.join(projectRoot, 'server.py');
const bundledBackendPath = path.join(extensionRoot, 'python_backend', 'server.py');
const bundledReporterPath = path.join(extensionRoot, 'python_backend', 'reporter.py');
const bundledOnly = process.argv.includes('--bundled-only');
const expectedVersion = JSON.parse(fs.readFileSync(packagePath, 'utf8')).version;

function fail(message) {
    console.error(message);
    process.exit(1);
}

function readRequired(filePath) {
    if (!fs.existsSync(filePath)) {
        fail(`Arquivo obrigatório não encontrado para validação: ${filePath}`);
    }
    return fs.readFileSync(filePath, 'utf8');
}

function assertVersion(version, sourceName) {
    if (version !== expectedVersion) {
        fail(`Versão incompatível: extensão ${expectedVersion}; ${sourceName} ${version}`);
    }
}

function reporterVersion(source, sourceName) {
    const match = source.match(/^VERSAO_FERRAMENTA\s*=\s*['"]([^'"]+)['"]/m);
    if (!match) {
        fail(`VERSAO_FERRAMENTA não declarada em ${sourceName}`);
    }
    return match[1];
}

if (bundledOnly) {
    const backendSource = readRequired(bundledBackendPath);
    const reporterSource = readRequired(bundledReporterPath);
    if (!backendSource.includes('VERSAO_FERRAMENTA')) {
        fail(`O backend empacotado não usa VERSAO_FERRAMENTA: ${bundledBackendPath}`);
    }
    assertVersion(reporterVersion(reporterSource, bundledReporterPath), 'reporter empacotado');
} else {
    const declaredVersion = readRequired(rootVersionPath).trim();
    assertVersion(declaredVersion, 'VERSION');
    assertVersion(reporterVersion(readRequired(rootReporterPath), rootReporterPath), 'reporter.VERSAO_FERRAMENTA');
    const backendSource = readRequired(rootBackendPath);
    if (!backendSource.includes('VERSAO_FERRAMENTA')) {
        fail(`O servidor deve expor a versão de reporter.VERSAO_FERRAMENTA: ${rootBackendPath}`);
    }
}

console.log(`Versão do backend compatível com a extensão: ${expectedVersion}`);

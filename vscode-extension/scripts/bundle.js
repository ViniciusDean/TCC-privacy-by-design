'use strict';

const path = require('path');
const fs = require('fs');
const { builtinModules } = require('module');
const esbuild = require('esbuild');

const extensionRoot = path.resolve(__dirname, '..');

esbuild.build({
    absWorkingDir: extensionRoot,
    // Usar o módulo da extensão como entrada preserva os exports activate e
    // deactivate exigidos pelo VS Code. Um import apenas por efeito colateral
    // executava o arquivo, mas gerava um VSIX sem função de ativação exportada.
    entryPoints: [path.join(extensionRoot, 'src', 'extension.ts')],
    bundle: true,
    platform: 'node',
    format: 'cjs',
    external: ['vscode'],
    plugins: [{
        name: 'workspace-relative-paths',
        setup(build) {
            build.onResolve({ filter: /^\./ }, args => {
                const base = path.resolve(args.resolveDir, args.path);
                const candidates = [
                    base,
                    `${base}.ts`,
                    `${base}.tsx`,
                    `${base}.js`,
                    `${base}.json`,
                    path.join(base, 'index.ts'),
                    path.join(base, 'index.js')
                ];
                const resolved = candidates.find(candidate => (
                    fs.existsSync(candidate) && fs.statSync(candidate).isFile()
                ));
                return resolved ? { path: resolved } : undefined;
            });
            build.onResolve({ filter: /^[^./]/ }, args => {
                if (
                    args.path === 'vscode'
                    || builtinModules.includes(args.path)
                    || args.path.startsWith('node:')
                ) {
                    return { path: args.path, external: true };
                }
                return { path: require.resolve(args.path, { paths: [args.resolveDir, extensionRoot] }) };
            });
        }
    }],
    outfile: path.join(extensionRoot, 'out', 'extension.js'),
    sourcemap: true
}).catch(error => {
    console.error(error);
    process.exitCode = 1;
});

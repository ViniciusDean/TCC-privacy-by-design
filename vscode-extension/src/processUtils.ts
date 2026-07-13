import { spawn, spawnSync } from 'child_process';

export interface PythonCommand {
    command: string;
    prefixArgs: string[];
}

export function resolvePythonCommand(configured: string): PythonCommand | undefined {
    const candidates: PythonCommand[] = [
        { command: configured, prefixArgs: [] },
        ...(process.platform === 'win32'
            ? [{ command: 'py', prefixArgs: ['-3'] }, { command: 'python', prefixArgs: [] }]
            : [{ command: 'python3', prefixArgs: [] }, { command: 'python', prefixArgs: [] }])
    ];
    const seen = new Set<string>();
    for (const candidate of candidates) {
        const key = `${candidate.command}\0${candidate.prefixArgs.join('\0')}`;
        if (seen.has(key)) {
            continue;
        }
        seen.add(key);
        const probe = spawnSync(candidate.command, [...candidate.prefixArgs, '--version'], {
            windowsHide: true,
            timeout: 3000
        });
        if (!probe.error && probe.status === 0) {
            return candidate;
        }
    }
    return undefined;
}

export async function runProcess(command: string, args: string[], cwd: string): Promise<void> {
    await new Promise<void>((resolve, reject) => {
        const child = spawn(command, args, { cwd, windowsHide: true });
        let stderr = '';
        child.stderr.on('data', data => {
            stderr += data.toString();
        });
        child.once('error', reject);
        child.once('exit', code => {
            if (code === 0) {
                resolve();
            } else {
                reject(new Error(stderr.trim() || `Processo encerrou com codigo ${code}.`));
            }
        });
    });
}

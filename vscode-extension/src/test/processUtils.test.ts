import * as assert from 'assert';
import { resolvePythonCommand, runProcess } from '../processUtils';

async function main(): Promise<void> {
    const resolved = resolvePythonCommand(process.execPath);
    assert.ok(resolved);
    assert.strictEqual(resolved.command, process.execPath);

    await runProcess(process.execPath, ['-e', 'process.exit(0)'], process.cwd());
    await assert.rejects(
        runProcess(process.execPath, ['-e', 'process.exit(3)'], process.cwd())
    );
    console.log('ok - utilitarios de processo sao previsiveis');
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});

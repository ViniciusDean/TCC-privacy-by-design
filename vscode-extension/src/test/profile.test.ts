import * as assert from 'assert';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import {
    DEFAULT_PROFILE,
    ProfileError,
    loadProfile,
    serializeProfile,
    validateProfile
} from '../profile';

function run(name: string, test: () => void): void {
    try {
        test();
        console.log(`ok - ${name}`);
    } catch (error) {
        console.error(`not ok - ${name}`);
        throw error;
    }
}

run('usa perfil conservador quando arquivo nao existe', () => {
    assert.deepStrictEqual(loadProfile(path.join(os.tmpdir(), 'workspace-inexistente')), DEFAULT_PROFILE);
});

run('valida e serializa perfil versionado', () => {
    const profile = validateProfile({
        schemaVersion: 1,
        preset: 'equilibrado',
        categories: { DADO_EM_LOG: { minimumConfidence: 'MEDIA', severity: 'ALTO' } }
    });
    assert.strictEqual(profile.preset, 'equilibrado');
    assert.ok(serializeProfile(profile).endsWith('\n'));
});

run('rejeita configuracao desconhecida', () => {
    assert.throws(
        () => validateProfile({ preset: 'conservador', categories: {}, extra: true }),
        ProfileError
    );
});

run('carrega perfil do workspace', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'privacy-profile-'));
    try {
        fs.writeFileSync(
            path.join(root, '.privacy-scanner.json'),
            serializeProfile({ ...DEFAULT_PROFILE, preset: 'completo' })
        );
        assert.strictEqual(loadProfile(root).preset, 'completo');
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});

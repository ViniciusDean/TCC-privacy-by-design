import * as assert from 'assert';
import * as path from 'path';
import {
    AnalysisCoordinator,
    AnalysisSnapshot,
    AnalysisTarget,
    SavableAnalysisDocument,
    dirtyDocumentsInRoots,
    discardQueuedAnalysesInTarget,
    documentChangedSinceRequest,
    isPathInAnalysisTarget,
    saveDirtyAnalysisDocuments,
    shouldAutomaticallyAnalyze,
    shouldPreserveCanonicalWorkspaceState
} from '../analysisCoordinator';

const coordinator = new AnalysisCoordinator();
const first = coordinator.begin('primeira');
const second = coordinator.begin('segunda');

assert.strictEqual(first.controller.signal.aborted, true);
assert.strictEqual(coordinator.isCurrent(first), false);
assert.strictEqual(coordinator.isCurrent(second), true);
assert.strictEqual(coordinator.finish(second), true);
assert.strictEqual(coordinator.isActive, false);

assert.strictEqual(shouldPreserveCanonicalWorkspaceState('workspace', true), true);
assert.strictEqual(shouldPreserveCanonicalWorkspaceState('workspace', false), false);
assert.strictEqual(shouldPreserveCanonicalWorkspaceState('single', true), false);
assert.strictEqual(shouldPreserveCanonicalWorkspaceState(undefined, true), false);

console.log('ok - coordenador protege ordem e preserva resumo do workspace');

const root = path.resolve('test-workspaces', 'app');
const otherRoot = path.resolve('test-workspaces', 'outro');
const sibling = path.resolve('test-workspaces', 'app-extra');
const workspaceTarget: AnalysisTarget = { origin: 'workspace', paths: [root, otherRoot], label: 'Projeto' };
const singleTarget: AnalysisTarget = { origin: 'single', paths: [path.join(root, 'main.py')], label: 'Arquivo' };

assert.strictEqual(isPathInAnalysisTarget(workspaceTarget, path.join(root, 'src', 'main.py')), true);
assert.strictEqual(isPathInAnalysisTarget(workspaceTarget, path.join(otherRoot, 'Main.java')), true);
assert.strictEqual(isPathInAnalysisTarget(workspaceTarget, path.join(sibling, 'main.py')), false);
assert.strictEqual(isPathInAnalysisTarget(workspaceTarget, path.join(root, '..', 'fora.py')), false);
assert.strictEqual(isPathInAnalysisTarget(singleTarget, path.join(root, 'main.py')), true);
assert.strictEqual(isPathInAnalysisTarget(singleTarget, path.join(root, 'main.py.bak')), false);
assert.strictEqual(isPathInAnalysisTarget(singleTarget, path.join(root, 'main.py', 'child.py')), false);
if (process.platform === 'win32') {
    assert.strictEqual(isPathInAnalysisTarget(workspaceTarget, path.join(root.toUpperCase(), 'MAIN.PY')), true);
}
console.log('ok - escopo respeita multiplas raizes e limites entre caminhos');

const snapshot = new AnalysisSnapshot(workspaceTarget);
assert.strictEqual(snapshot.markChanged(path.join(sibling, 'main.py')), false);
assert.strictEqual(snapshot.stale, false);
assert.strictEqual(snapshot.markChanged(path.join(otherRoot, 'Main.java')), true);
snapshot.complete(12345);
assert.strictEqual(snapshot.completedAt, 12345);
assert.strictEqual(snapshot.stale, true, 'concluir a requisicao nao apaga edicoes ocorridas durante a analise');
const freshSnapshot = new AnalysisSnapshot(singleTarget);
freshSnapshot.complete(12346);
assert.strictEqual(freshSnapshot.stale, false);
assert.strictEqual(freshSnapshot.markChanged(path.join(root, 'outro.py')), false);
assert.strictEqual(freshSnapshot.markChanged(path.join(root, 'main.py')), true);
console.log('ok - resumo mantem alteracoes feitas durante e depois da requisicao');

function makeDocument(filePath: string, dirty = true): SavableAnalysisDocument & { saves: number } {
    return {
        uri: { scheme: 'file', fsPath: filePath },
        isUntitled: false,
        isDirty: dirty,
        version: 1,
        saves: 0,
        async save() {
            this.saves++;
            this.isDirty = false;
            return true;
        }
    };
}

const automaticDocument = makeDocument(path.join(root, 'main.py'), false);
assert.strictEqual(shouldAutomaticallyAnalyze(automaticDocument, true), true);
assert.strictEqual(shouldAutomaticallyAnalyze(automaticDocument, false), false);
for (const extension of ['JAVA', 'db', 'sqlite', 'sqlite3']) {
    assert.strictEqual(shouldAutomaticallyAnalyze(makeDocument(path.join(root, `data.${extension}`), false), true), true);
}
assert.strictEqual(shouldAutomaticallyAnalyze({ ...automaticDocument, isDirty: true }, true), false);
assert.strictEqual(shouldAutomaticallyAnalyze({ ...automaticDocument, isUntitled: true }, true), false);
assert.strictEqual(shouldAutomaticallyAnalyze({ ...automaticDocument, uri: { scheme: 'git', fsPath: automaticDocument.uri.fsPath } }, true), false);
assert.strictEqual(shouldAutomaticallyAnalyze(makeDocument(path.join(root, 'README.md'), false), true), false);
assert.strictEqual(documentChangedSinceRequest(1, automaticDocument), false);
assert.strictEqual(documentChangedSinceRequest(1, { ...automaticDocument, version: 2 }), true);
assert.strictEqual(documentChangedSinceRequest(1, { ...automaticDocument, isDirty: true }), true);
assert.strictEqual(documentChangedSinceRequest(undefined, automaticDocument), false);
assert.strictEqual(documentChangedSinceRequest(1, undefined), false);
console.log('ok - analise automatica exige documento salvo e rejeita versao alterada');

const pending = new Map([
    ['main', { fsPath: path.join(root, 'main.py') }],
    ['second-file', { fsPath: path.join(root, 'outro.py') }],
    ['other-root', { fsPath: path.join(otherRoot, 'Main.java') }],
    ['sibling', { fsPath: path.join(sibling, 'main.py') }]
]);
discardQueuedAnalysesInTarget(pending, singleTarget);
assert.deepStrictEqual([...pending.keys()], ['second-file', 'other-root', 'sibling']);
discardQueuedAnalysesInTarget(pending, { ...workspaceTarget, paths: [root] });
assert.deepStrictEqual([...pending.keys()], ['other-root', 'sibling']);
discardQueuedAnalysesInTarget(pending, workspaceTarget);
assert.deepStrictEqual([...pending.keys()], ['sibling']);
console.log('ok - fila descarta somente arquivos cobertos pela analise escolhida');

async function testSaving(): Promise<void> {
    const selected = makeDocument(path.join(root, 'main.py'));
    const secondRoot = makeDocument(path.join(otherRoot, 'Main.java'));
    const outside = makeDocument(path.join(sibling, 'main.py'));
    const ignored = makeDocument(path.join(root, 'README.md'));
    const database = makeDocument(path.join(root, 'data.sqlite'));
    const clean = makeDocument(path.join(root, 'clean.py'), false);
    const untitled = { ...makeDocument(path.join(root, 'untitled.py')), isUntitled: true };
    const virtual = { ...makeDocument(path.join(root, 'virtual.py')), uri: { scheme: 'git', fsPath: path.join(root, 'virtual.py') } };
    const documents = [selected, secondRoot, outside, ignored, database, clean, untitled, virtual];
    assert.deepStrictEqual(dirtyDocumentsInRoots(documents, [root, otherRoot]), [selected, secondRoot]);

    let confirmations = 0;
    assert.strictEqual(await saveDirtyAnalysisDocuments(() => documents, [root, otherRoot], async count => {
        confirmations++;
        assert.strictEqual(count, 2);
        return false;
    }), 'cancelled');
    assert.strictEqual(documents.every(document => document.saves === 0), true);

    assert.strictEqual(await saveDirtyAnalysisDocuments(() => documents, [root, otherRoot], async count => {
        confirmations++;
        assert.strictEqual(count, 2);
        return true;
    }), 'ready');
    assert.strictEqual(selected.saves, 1);
    assert.strictEqual(secondRoot.saves, 1);
    assert.strictEqual(documents.slice(2).every(document => document.saves === 0), true);
    assert.strictEqual(await saveDirtyAnalysisDocuments(() => documents, [root, otherRoot], async () => {
        throw new Error('nao deve pedir confirmacao quando nao ha arquivos elegiveis modificados');
    }), 'ready');
    assert.strictEqual(confirmations, 2);

    const failed = makeDocument(path.join(root, 'failed.py'));
    failed.save = async () => { failed.saves++; return false; };
    const following = makeDocument(path.join(root, 'following.py'));
    assert.strictEqual(await saveDirtyAnalysisDocuments(() => [failed, following], [root], async () => true), 'unsaved');
    assert.strictEqual(failed.saves, 1);
    assert.strictEqual(following.saves, 0);

    const editedDuringSave = makeDocument(path.join(root, 'race.py'));
    editedDuringSave.save = async () => true;
    assert.strictEqual(await saveDirtyAnalysisDocuments(() => [editedDuringSave], [root], async () => true), 'unsaved');

    const newDirty = makeDocument(path.join(root, 'new.py'));
    const initial = makeDocument(path.join(root, 'initial.py'));
    const changingDocuments = [initial];
    initial.save = async () => { initial.isDirty = false; changingDocuments.push(newDirty); return true; };
    assert.strictEqual(await saveDirtyAnalysisDocuments(() => changingDocuments, [root], async () => true), 'unsaved');
    assert.strictEqual(newDirty.saves, 0, 'documento novo nao foi incluido na confirmacao de salvamento');
    console.log('ok - salvamento trata cancelamento, falha e mudancas concorrentes dentro do escopo');
}

testSaving().catch(error => {
    console.error(error);
    process.exitCode = 1;
});

import * as assert from 'assert';
import axios from 'axios';
import { postWithSingleRecovery } from '../httpClient';

async function main(): Promise<void> {
    const originalPost = axios.post;
    try {
        let attempts = 0;
        let recoveries = 0;
        (axios.post as typeof axios.post) = (async () => {
            attempts += 1;
            if (attempts === 1) {
                throw new Error('connection refused');
            }
            return { data: { ok: true } };
        }) as typeof axios.post;
        const response = await postWithSingleRecovery<{ ok: boolean }>(
            '/test',
            {},
            { timeout: 100 },
            {
                baseUrl: () => 'http://localhost:1',
                recover: async () => {
                    recoveries += 1;
                    return true;
                },
                log: () => undefined
            }
        );
        assert.strictEqual(response.data.ok, true);
        assert.strictEqual(attempts, 2);
        assert.strictEqual(recoveries, 1);

        const applicationError = Object.assign(new Error('bad request'), {
            isAxiosError: true,
            response: { status: 400 }
        });
        (axios.post as typeof axios.post) = (async () => {
            throw applicationError;
        }) as typeof axios.post;
        recoveries = 0;
        await assert.rejects(postWithSingleRecovery(
            '/test', {}, { timeout: 100 }, {
                baseUrl: () => 'http://localhost:1',
                recover: async () => {
                    recoveries += 1;
                    return true;
                },
                log: () => undefined
            }
        ));
        assert.strictEqual(recoveries, 0);
        console.log('ok - cliente HTTP repete apenas falhas de conexao');
    } finally {
        axios.post = originalPost;
    }
}

main().catch(error => {
    console.error(error);
    process.exitCode = 1;
});

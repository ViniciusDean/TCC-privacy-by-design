import axios from 'axios';

export interface BackendRequestOptions {
    timeout: number;
    signal?: AbortSignal;
}

export interface BackendRecovery {
    baseUrl: () => string;
    recover: () => Promise<boolean>;
    log: (message: string) => void;
}

export async function postWithSingleRecovery<T>(
    endpoint: string,
    payload: unknown,
    options: BackendRequestOptions,
    recovery: BackendRecovery
): Promise<{ data: T }> {
    const request = () => axios.post<T>(
        `${recovery.baseUrl()}${endpoint}`,
        payload,
        options
    );
    try {
        return await request();
    } catch (error) {
        if (axios.isCancel(error) || (axios.isAxiosError(error) && error.response)) {
            throw error;
        }
        recovery.log(`Falha de conexao em ${endpoint}; recuperando backend uma vez.`);
        if (!await recovery.recover()) {
            throw error;
        }
        return request();
    }
}

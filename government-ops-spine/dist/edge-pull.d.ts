import { type OpportunitySink } from './foundry-bridge.js';
export interface EdgePullOptions {
    accountId: string;
    databaseId: string;
    apiToken: string;
    sink: OpportunitySink;
    fetchImpl?: typeof fetch;
    limit?: number;
    now?: () => Date;
}
export interface EdgePullSummary {
    claimed: number;
    published: number;
    results: Array<{
        id: number;
        externalId?: string;
        disposition?: string;
    }>;
    errors: Array<{
        id?: number;
        message: string;
    }>;
}
export declare function pullEdgeOutbox(options: EdgePullOptions): Promise<EdgePullSummary>;

import type { Pool } from 'pg';
import type { CapabilityRegistry } from './capability-indexer.js';
import type { CapabilityIndexingWorker } from './indexing-worker.js';
import type { PostgresEngineeringProgramService } from './engineering-postgres.js';
import { type GmailDraftProvider } from './gmail-drafts.js';
export interface ControlRequest {
    method: string;
    path: string;
    body?: unknown;
}
export interface ControlResponse {
    status: number;
    body: unknown;
}
export declare class ControlPlaneRuntime {
    private readonly pool;
    private readonly registry;
    private readonly indexer;
    private readonly engineeringPrograms;
    private readonly gmailProvider;
    private readonly reviews;
    private readonly releases;
    private readonly documents;
    private readonly receipts;
    private readonly gmail;
    private readonly collaboration;
    constructor(pool: Pool, registry: CapabilityRegistry, indexer: CapabilityIndexingWorker, engineeringPrograms: PostgresEngineeringProgramService, gmailProvider?: GmailDraftProvider);
    handle(request: ControlRequest): Promise<ControlResponse | undefined>;
    private createDraft;
    private approve;
}

import { type IntakeSql, type PersistReceipt } from './store.js';
export interface IntakeBindings {
    DB: IntakeSql;
    SAM_GOV_API_KEY?: string;
    INGEST_TOKEN?: string;
    FOUNDRY_INGEST_NAICS?: string;
    FOUNDRY_INGEST_DISPOSITIONS?: string;
    FOUNDRY_INGEST_LOOKBACK_DAYS?: string;
    FOUNDRY_INGEST_LIMIT?: string;
    SAM_GOV_MAX_PAGES?: string;
}
export interface IntakeSummary {
    sourceRunId: string;
    loaded: number;
    selected: number;
    skipped: Array<{
        externalId?: string;
        title?: string;
        reason: string;
    }>;
    results: PersistReceipt[];
    errors: Array<{
        externalId?: string;
        message: string;
    }>;
}
declare const _default: {
    fetch(request: Request, env: IntakeBindings): Promise<Response>;
    scheduled(_controller: {
        cron: string;
    }, env: IntakeBindings): Promise<void>;
};
export default _default;
export declare function handleIntakeRequest(request: Request, env: IntakeBindings): Promise<Response>;
export declare function handleScheduledIntake(env: IntakeBindings, options?: {
    fetchImpl?: typeof fetch;
    now?: Date;
}): Promise<IntakeSummary>;

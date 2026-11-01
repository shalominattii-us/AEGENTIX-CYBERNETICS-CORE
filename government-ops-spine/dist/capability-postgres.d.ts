import type { Pool } from 'pg';
import type { CapabilityMatch } from './types.js';
import type { CapabilityAsset, CapabilityRegistry } from './capability-indexer.js';
export declare class PostgresCapabilityRegistry implements CapabilityRegistry {
    private readonly pool;
    constructor(pool: Pool);
    upsert(a: CapabilityAsset): Promise<void>;
    list(): Promise<CapabilityAsset[]>;
    saveMatches(opportunityId: string, matches: CapabilityMatch[]): Promise<void>;
}

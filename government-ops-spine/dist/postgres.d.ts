import type { Pool } from 'pg';
import type { BrainPlan, BuildSpecification, PublicOpportunity, TreasuryAnalysis } from './types.js';
import type { IngestResult, OpportunityRepository, StoredOpportunity } from './repository.js';
export declare class PostgresOpportunityRepository implements OpportunityRepository {
    private readonly pool;
    constructor(pool: Pool);
    getByEventId(eventId: string): Promise<StoredOpportunity | undefined>;
    getBySourceIdentity(sourceSystem: string, externalId: string): Promise<StoredOpportunity | undefined>;
    ingest(opportunity: PublicOpportunity, canonicalHash: string): Promise<IngestResult>;
    saveAnalysis(analysis: TreasuryAnalysis): Promise<void>;
    saveSpecification(specification: BuildSpecification): Promise<void>;
    saveBrainPlan(plan: BrainPlan): Promise<void>;
    appendEvent(eventType: string, aggregateId: string, payload: unknown): Promise<void>;
    private getBySourceIdentityTx;
}

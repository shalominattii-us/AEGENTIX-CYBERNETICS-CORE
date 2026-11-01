import { BrainPlan, BuildSpecification, PublicOpportunity, TreasuryAnalysis } from './types.js';
export type IngestDisposition = 'created' | 'unchanged' | 'amended' | 'cancelled' | 'awarded';
export interface StoredOpportunity {
    opportunity: PublicOpportunity;
    canonicalHash: string;
    revision: number;
    status: 'active' | 'cancelled' | 'awarded' | 'closed';
}
export interface IngestResult {
    disposition: IngestDisposition;
    stored: StoredOpportunity;
    changedFields: string[];
}
export interface OpportunityRepository {
    getByEventId(eventId: string): Promise<StoredOpportunity | undefined>;
    getBySourceIdentity(sourceSystem: string, externalId: string): Promise<StoredOpportunity | undefined>;
    ingest(opportunity: PublicOpportunity, canonicalHash: string): Promise<IngestResult>;
    saveAnalysis(analysis: TreasuryAnalysis): Promise<void>;
    saveSpecification(specification: BuildSpecification): Promise<void>;
    saveBrainPlan(plan: BrainPlan): Promise<void>;
    appendEvent(eventType: string, aggregateId: string, payload: unknown): Promise<void>;
}
export declare class MemoryOpportunityRepository implements OpportunityRepository {
    private readonly opportunities;
    private readonly sourceIndex;
    getByEventId(eventId: string): Promise<StoredOpportunity | undefined>;
    getBySourceIdentity(sourceSystem: string, externalId: string): Promise<StoredOpportunity | undefined>;
    ingest(opportunity: PublicOpportunity, canonicalHash: string): Promise<IngestResult>;
    saveAnalysis(_: TreasuryAnalysis): Promise<void>;
    saveSpecification(_: BuildSpecification): Promise<void>;
    saveBrainPlan(_: BrainPlan): Promise<void>;
    appendEvent(_: string, __: string, ___: unknown): Promise<void>;
}

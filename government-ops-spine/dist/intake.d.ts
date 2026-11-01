import { PublicOpportunity } from './types.js';
import { IngestResult, OpportunityRepository } from './repository.js';
export interface IntakeEnvelope {
    sourceRunId: string;
    receivedAt: string;
    opportunity: PublicOpportunity;
}
export interface IntakeReceipt {
    sourceRunId: string;
    eventId: string;
    canonicalHash: string;
    result: IngestResult;
}
export declare class OpportunityIntakeService {
    private readonly repository;
    constructor(repository: OpportunityRepository);
    ingest(envelope: IntakeEnvelope): Promise<IntakeReceipt>;
}
export declare function normalizeOpportunity(input: PublicOpportunity): PublicOpportunity;
export declare function hashOpportunity(input: PublicOpportunity): string;

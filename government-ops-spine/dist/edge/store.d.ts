import type { PublicOpportunity } from '../types.js';
import type { IngestDisposition } from '../repository.js';
export interface BoundStatement {
    first<T = Record<string, unknown>>(): Promise<T | null>;
    run(): Promise<unknown>;
}
export interface IntakeSql {
    prepare(query: string): {
        bind(...values: unknown[]): BoundStatement;
    };
    batch(statements: BoundStatement[]): Promise<unknown>;
}
export interface PersistReceipt {
    eventId: string;
    externalId: string;
    disposition: IngestDisposition;
    canonicalHash: string;
    revision: number;
}
export declare function persistOpportunity(db: IntakeSql, input: {
    sourceRunId: string;
    receivedAt: string;
    opportunity: PublicOpportunity;
}): Promise<PersistReceipt>;

import type { Pool } from 'pg';
export interface EventPublisher {
    publish(eventType: string, aggregateId: string, payload: unknown): Promise<void>;
}
export declare class CybercoreHttpPublisher implements EventPublisher {
    private readonly endpoint;
    private readonly fetchImpl;
    constructor(endpoint: string, fetchImpl?: typeof fetch);
    publish(eventType: string, aggregateId: string, payload: unknown): Promise<void>;
}
export declare class OutboxWorker {
    private readonly pool;
    private readonly publisher;
    private readonly batchSize;
    constructor(pool: Pool, publisher: EventPublisher, batchSize?: number);
    runOnce(): Promise<number>;
}

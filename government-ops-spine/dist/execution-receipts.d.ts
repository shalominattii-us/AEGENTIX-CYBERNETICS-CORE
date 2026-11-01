import type { Pool } from 'pg';
export interface ExecutionReceipt {
    receiptId: string;
    eventType: string;
    aggregateId: string;
    status: 'recorded' | 'published' | 'failed';
    occurredAt: string;
    payloadHash: string;
    payload: unknown;
}
export interface ExecutionDashboard {
    generatedAt: string;
    totals: {
        recorded: number;
        published: number;
        failed: number;
    };
    recent: ExecutionReceipt[];
    externalActionsBlocked: true;
}
export declare class ExecutionReceiptService {
    private readonly pool;
    constructor(pool: Pool);
    record(eventType: string, aggregateId: string, payload: unknown, status?: ExecutionReceipt['status']): Promise<ExecutionReceipt>;
    dashboard(limit?: number): Promise<ExecutionDashboard>;
}

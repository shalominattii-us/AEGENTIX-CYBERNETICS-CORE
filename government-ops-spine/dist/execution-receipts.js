import { createHash } from 'node:crypto';
export class ExecutionReceiptService {
    pool;
    constructor(pool) {
        this.pool = pool;
    }
    async record(eventType, aggregateId, payload, status = 'recorded') {
        const occurredAt = new Date().toISOString();
        const payloadHash = hash(payload);
        const receiptId = `EXEC-${hash({ eventType, aggregateId, payloadHash, occurredAt }).slice(0, 20)}`;
        const receipt = { receiptId, eventType, aggregateId, status, occurredAt, payloadHash, payload };
        await this.pool.query(`insert into execution_receipts(receipt_id,event_type,aggregate_id,status,occurred_at,payload_hash,payload_json) values($1,$2,$3,$4,$5,$6,$7)`, [receiptId, eventType, aggregateId, status, occurredAt, payloadHash, payload]);
        return receipt;
    }
    async dashboard(limit = 50) {
        const totalsResult = await this.pool.query(`select status,count(*)::int as count from execution_receipts group by status`);
        const totals = { recorded: 0, published: 0, failed: 0 };
        for (const row of totalsResult.rows)
            totals[row.status] = Number(row.count);
        const recentResult = await this.pool.query(`select * from execution_receipts order by occurred_at desc limit $1`, [Math.min(Math.max(limit, 1), 200)]);
        const recent = recentResult.rows.map(row => ({ receiptId: row.receipt_id, eventType: row.event_type, aggregateId: row.aggregate_id, status: row.status, occurredAt: new Date(row.occurred_at).toISOString(), payloadHash: row.payload_hash, payload: row.payload_json }));
        return { generatedAt: new Date().toISOString(), totals, recent, externalActionsBlocked: true };
    }
}
function hash(value) { return createHash('sha256').update(JSON.stringify(value)).digest('hex'); }

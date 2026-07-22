import type { Pool } from 'pg';

export interface EventPublisher { publish(eventType: string, aggregateId: string, payload: unknown): Promise<void>; }

export class CybercoreHttpPublisher implements EventPublisher {
  constructor(private readonly endpoint: string, private readonly fetchImpl: typeof fetch = fetch) {}
  async publish(eventType: string, aggregateId: string, payload: unknown): Promise<void> {
    const response = await this.fetchImpl(this.endpoint, {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ type: eventType, aggregateId, payload })
    });
    if (!response.ok) throw new Error(`Cybercore publish failed: ${response.status}`);
  }
}

export class OutboxWorker {
  constructor(private readonly pool: Pool, private readonly publisher: EventPublisher, private readonly batchSize = 50) {}
  async runOnce(): Promise<number> {
    const client = await this.pool.connect();
    try {
      await client.query('begin');
      const result = await client.query(
        `select id,event_type,aggregate_id,payload_json from cybercore_outbox where published_at is null order by id for update skip locked limit $1`,
        [this.batchSize]
      );
      for (const row of result.rows) {
        await this.publisher.publish(row.event_type, row.aggregate_id, row.payload_json);
        await client.query('update cybercore_outbox set published_at=now(), attempts=attempts+1 where id=$1', [row.id]);
      }
      await client.query('commit');
      return result.rowCount ?? 0;
    } catch (error) {
      await client.query('rollback');
      throw error;
    } finally { client.release(); }
  }
}

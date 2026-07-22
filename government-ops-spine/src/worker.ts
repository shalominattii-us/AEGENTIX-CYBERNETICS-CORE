import { Pool } from 'pg';
import { CybercoreHttpPublisher, OutboxWorker } from './outbox.js';

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const endpoint = process.env.CYBERCORE_EVENT_ENDPOINT ?? 'http://127.0.0.1:8000/api/bus';
const intervalMs = Number(process.env.OUTBOX_INTERVAL_MS ?? 5000);
const maxBackoffMs = Number(process.env.OUTBOX_MAX_BACKOFF_MS ?? 60000);
const worker = new OutboxWorker(pool, new CybercoreHttpPublisher(endpoint), Number(process.env.OUTBOX_BATCH_SIZE ?? 50));
let stopped = false;
let failures = 0;

async function loop(): Promise<void> {
  while (!stopped) {
    try {
      const published = await worker.runOnce();
      failures = 0;
      console.log(JSON.stringify({ event: 'outbox.cycle', published, endpoint }));
      await sleep(intervalMs);
    } catch (error) {
      failures += 1;
      const delay = Math.min(maxBackoffMs, intervalMs * 2 ** Math.min(failures, 6));
      console.error(JSON.stringify({ event: 'outbox.error', failures, retryInMs: delay, error: error instanceof Error ? error.message : String(error) }));
      await sleep(delay);
    }
  }
}

const shutdown = async () => { stopped = true; await pool.end(); process.exit(0); };
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
void loop();

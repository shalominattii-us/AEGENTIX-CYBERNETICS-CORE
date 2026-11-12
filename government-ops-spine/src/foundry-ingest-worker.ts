import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Pool } from 'pg';
import { PostgresOpportunityRepository } from './postgres.js';
import { GovernmentOpsRuntime } from './runtime.js';
import type { OpportunityRepository } from './repository.js';
import { redactSecrets } from './sam-gov.js';
import { foundryRequestFromEnv, runFoundryIngest, runtimeSink, type FoundryIngestSummary } from './foundry-bridge.js';

export class FoundryIngestScheduler {
  private timer?: ReturnType<typeof setInterval>;
  private running = false;
  private pending: Promise<void> = Promise.resolve();
  constructor(private readonly intervalMs: number, private readonly task: () => Promise<void>) {}

  runOnce(): Promise<void> {
    if (this.running) return this.pending;
    this.running = true;
    this.pending = (async () => {
      try {
        await this.task();
      } finally {
        this.running = false;
      }
    })();
    return this.pending;
  }

  start(): void {
    if (this.timer) return;
    const launch = () => { void this.runOnce().catch((error) => this.reportFailure(error)); };
    launch();
    this.timer = setInterval(launch, this.intervalMs);
  }

  stop(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = undefined;
  }

  whenSettled(): Promise<void> {
    return this.pending;
  }

  private reportFailure(error: unknown): void {
    const message = error instanceof Error ? error.message : String(error);
    console.error(JSON.stringify({ event: 'foundry_ingest.scheduler_error', error: message }));
  }
}

export function startEmbeddedFoundryIngest(repository: OpportunityRepository, env: NodeJS.ProcessEnv = process.env): { stop: () => void; whenSettled: () => Promise<void> } | undefined {
  if (env.FOUNDRY_INGEST_ENABLED !== 'true') return undefined;
  const pathValue = env.FOUNDRY_INGEST_PATH?.trim();
  const apiKey = env.SAM_GOV_API_KEY?.trim();
  if (!pathValue && !apiKey) {
    console.error(JSON.stringify({ event: 'foundry_ingest.disabled', reason: 'Set FOUNDRY_INGEST_PATH or SAM_GOV_API_KEY' }));
    return undefined;
  }
  let intervalMs: number;
  try {
    intervalMs = positiveInteger(env.FOUNDRY_INGEST_INTERVAL_MS, 3_600_000);
  } catch (error) {
    console.error(JSON.stringify({ event: 'foundry_ingest.disabled', reason: error instanceof Error ? error.message : String(error) }));
    return undefined;
  }
  const runtime = new GovernmentOpsRuntime(repository);
  const scheduler = new FoundryIngestScheduler(intervalMs, async () => {
    try {
      const summary = await runFoundryIngest(runtimeSink(runtime), foundryRequestFromEnv(env, { pull: Boolean(apiKey), path: pathValue || undefined }));
      console.log(JSON.stringify({ event: 'foundry_ingest.cycle', ...publicIngestCounts(summary) }));
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      console.error(JSON.stringify({ event: 'foundry_ingest.error', error: redactSecrets(message, apiKey ? [apiKey] : []) }));
    }
  });
  scheduler.start();
  return { stop: () => scheduler.stop(), whenSettled: () => scheduler.whenSettled() };
}

export function publicIngestCounts(summary: FoundryIngestSummary): Record<string, unknown> {
  const dispositions: Record<string, number> = {};
  for (const result of summary.results) dispositions[result.disposition] = (dispositions[result.disposition] ?? 0) + 1;
  return {
    sourceRunId: summary.sourceRunId,
    dryRun: summary.dryRun,
    loaded: summary.loaded,
    selected: summary.selected,
    skipped: summary.skipped.length,
    dispositions,
    errors: summary.errors.map((error) => ({ externalId: error.externalId, message: error.message }))
  };
}

function positiveInteger(value: string | undefined, fallback: number): number {
  if (!value?.trim()) return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 1) throw new Error(`Invalid interval: ${value}`);
  return Math.trunc(parsed);
}

const workerPath = fileURLToPath(import.meta.url);
const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === workerPath;
if (invokedDirectly) {
  const connectionString = process.env.DATABASE_URL;
  if (!connectionString) {
    console.error(JSON.stringify({ event: 'foundry_ingest.error', error: 'DATABASE_URL is required' }));
    process.exit(2);
  }
  const pool = new Pool({ connectionString });
  const repository = new PostgresOpportunityRepository(pool);
  const scheduler = startEmbeddedFoundryIngest(repository, { ...process.env, FOUNDRY_INGEST_ENABLED: 'true' });
  if (!scheduler) process.exit(2);
  const shutdown = async () => {
    scheduler.stop();
    await pool.end();
    process.exit(0);
  };
  process.on('SIGINT', () => void shutdown());
  process.on('SIGTERM', () => void shutdown());
}

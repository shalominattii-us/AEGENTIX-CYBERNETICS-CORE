import type { OpportunityRepository } from './repository.js';
import { type FoundryIngestSummary } from './foundry-bridge.js';
export declare class FoundryIngestScheduler {
    private readonly intervalMs;
    private readonly task;
    private timer?;
    private running;
    private pending;
    constructor(intervalMs: number, task: () => Promise<void>);
    runOnce(): Promise<void>;
    start(): void;
    stop(): void;
    whenSettled(): Promise<void>;
    private reportFailure;
}
export declare function startEmbeddedFoundryIngest(repository: OpportunityRepository, env?: NodeJS.ProcessEnv): {
    stop: () => void;
    whenSettled: () => Promise<void>;
} | undefined;
export declare function publicIngestCounts(summary: FoundryIngestSummary): Record<string, unknown>;

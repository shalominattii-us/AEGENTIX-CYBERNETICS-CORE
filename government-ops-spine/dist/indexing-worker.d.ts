import type { CapabilityCollector } from './live-collectors.js';
import type { CapabilityRegistry } from './capability-indexer.js';
export interface IndexingHealth {
    running: boolean;
    lastStartedAt?: string;
    lastCompletedAt?: string;
    lastAssetCount: number;
    lastError?: string;
}
export declare class CapabilityIndexingWorker {
    private readonly registry;
    private readonly collectors;
    private readonly intervalMs;
    private timer?;
    readonly health: IndexingHealth;
    constructor(registry: CapabilityRegistry, collectors: CapabilityCollector[], intervalMs?: number);
    runOnce(): Promise<number>;
    start(): void;
    stop(): void;
}

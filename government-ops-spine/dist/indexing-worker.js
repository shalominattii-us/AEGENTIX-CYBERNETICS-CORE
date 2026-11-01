export class CapabilityIndexingWorker {
    registry;
    collectors;
    intervalMs;
    timer;
    health = { running: false, lastAssetCount: 0 };
    constructor(registry, collectors, intervalMs = 15 * 60_000) {
        this.registry = registry;
        this.collectors = collectors;
        this.intervalMs = intervalMs;
    }
    async runOnce() {
        if (this.health.running)
            throw new Error('Capability indexing is already running.');
        this.health.running = true;
        this.health.lastStartedAt = new Date().toISOString();
        this.health.lastError = undefined;
        try {
            let count = 0;
            for (const collector of this.collectors) {
                for (const asset of await collector.collect()) {
                    await this.registry.upsert(asset);
                    count++;
                }
            }
            this.health.lastAssetCount = count;
            this.health.lastCompletedAt = new Date().toISOString();
            return count;
        }
        catch (error) {
            this.health.lastError = error instanceof Error ? error.message : String(error);
            throw error;
        }
        finally {
            this.health.running = false;
        }
    }
    start() { if (this.timer)
        return; void this.runOnce().catch(() => { }); this.timer = setInterval(() => void this.runOnce().catch(() => { }), this.intervalMs); }
    stop() { if (this.timer)
        clearInterval(this.timer); this.timer = undefined; }
}

import { createHash } from 'node:crypto';
import { matchCapabilities } from './pipeline.js';
const zones = ['OpenClaw', 'Nemotron', 'Hermes', 'Docker', 'Manus'];
const hash = (value) => createHash('sha256').update(JSON.stringify(value)).digest('hex');
const tags = (...values) => Array.from(new Set(values.flatMap(v => v.toLowerCase().match(/[a-z0-9][a-z0-9-]{2,}/g) ?? []))).sort();
export class StaticCapabilitySource {
    name;
    assets;
    constructor(name, assets) {
        this.name = name;
        this.assets = assets;
    }
    async scan() { return this.assets.map(a => ({ ...a, contentHash: hash(a), discoveredAt: new Date().toISOString() })); }
}
export function githubAsset(input) {
    const evidence = [input.url];
    const metadata = { language: input.language, defaultBranch: input.defaultBranch, topics: input.topics ?? [] };
    return { id: `github:${input.fullName}`, name: input.fullName, tags: tags(input.fullName, input.description ?? '', ...(input.topics ?? []), input.language ?? ''), maturity: 'repository', evidence, executionZones: zones, sourceType: 'github', sourceUri: input.url, description: input.description ?? '', metadata, contentHash: hash({ input, metadata }), discoveredAt: new Date().toISOString() };
}
export function dockerAsset(input) {
    const sourceUri = `docker://${input.image}${input.container ? `/${input.container}` : ''}`;
    const metadata = { container: input.container, status: input.status, ports: input.ports ?? [], labels: input.labels ?? {} };
    return { id: `docker:${hash(sourceUri).slice(0, 20)}`, name: input.container ?? input.image, tags: tags(input.image, input.container ?? '', input.status ?? '', ...(input.ports ?? []), ...Object.values(input.labels ?? {})), maturity: input.status?.toLowerCase().includes('running') ? 'deployed' : 'image', evidence: [sourceUri], executionZones: zones, sourceType: 'docker', sourceUri, description: `Docker capability from ${input.image}`, metadata, contentHash: hash({ input, metadata }), discoveredAt: new Date().toISOString() };
}
export function documentAsset(input) {
    return { id: `document:${hash(input.path).slice(0, 20)}`, name: input.title, tags: tags(input.title, input.text), maturity: 'documented', evidence: [input.path], executionZones: zones, sourceType: input.kind ?? 'document', sourceUri: input.path, description: input.text.slice(0, 500), metadata: { path: input.path }, contentHash: hash(input), discoveredAt: new Date().toISOString() };
}
export class CapabilityIndexer {
    registry;
    sources;
    constructor(registry, sources) {
        this.registry = registry;
        this.sources = sources;
    }
    async run() { let scanned = 0, upserted = 0; const sourceCounts = {}; for (const source of this.sources) {
        const assets = await source.scan();
        sourceCounts[source.name] = assets.length;
        scanned += assets.length;
        for (const asset of assets) {
            await this.registry.upsert(asset);
            upserted++;
        }
    } return { scanned, upserted, sourceCounts }; }
    async planWithCapabilities(opportunityId, analysis, plan) { const capabilities = await this.registry.list(); const matches = matchCapabilities(analysis, capabilities); await this.registry.saveMatches(opportunityId, matches); return { plan: { ...plan, capabilityMatches: matches }, matches }; }
}
export class MemoryCapabilityRegistry {
    assets = new Map();
    matches = new Map();
    async upsert(asset) { this.assets.set(asset.id, asset); }
    async list() { return [...this.assets.values()]; }
    async saveMatches(opportunityId, matches) { this.matches.set(opportunityId, matches); }
    getMatches(opportunityId) { return this.matches.get(opportunityId) ?? []; }
}

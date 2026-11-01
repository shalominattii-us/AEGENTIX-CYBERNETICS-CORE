import type { CapabilityRecord, TreasuryAnalysis, CapabilityMatch, BrainPlan } from './types.js';
export type CapabilitySourceType = 'github' | 'docker' | 'document' | 'service' | 'cad' | 'patent' | 'test' | 'manual';
export interface CapabilityAsset extends CapabilityRecord {
    sourceType: CapabilitySourceType;
    sourceUri: string;
    description: string;
    metadata: Record<string, unknown>;
    contentHash: string;
    discoveredAt: string;
}
export interface CapabilitySource {
    name: string;
    scan(): Promise<CapabilityAsset[]>;
}
export interface CapabilityRegistry {
    upsert(asset: CapabilityAsset): Promise<void>;
    list(): Promise<CapabilityAsset[]>;
    saveMatches(opportunityId: string, matches: CapabilityMatch[]): Promise<void>;
}
export declare class StaticCapabilitySource implements CapabilitySource {
    readonly name: string;
    private readonly assets;
    constructor(name: string, assets: Omit<CapabilityAsset, 'contentHash' | 'discoveredAt'>[]);
    scan(): Promise<CapabilityAsset[]>;
}
export declare function githubAsset(input: {
    fullName: string;
    description?: string;
    topics?: string[];
    language?: string;
    url: string;
    defaultBranch?: string;
}): CapabilityAsset;
export declare function dockerAsset(input: {
    image: string;
    container?: string;
    status?: string;
    ports?: string[];
    labels?: Record<string, string>;
}): CapabilityAsset;
export declare function documentAsset(input: {
    path: string;
    title: string;
    text: string;
    kind?: CapabilitySourceType;
}): CapabilityAsset;
export declare class CapabilityIndexer {
    private readonly registry;
    private readonly sources;
    constructor(registry: CapabilityRegistry, sources: CapabilitySource[]);
    run(): Promise<{
        scanned: number;
        upserted: number;
        sourceCounts: Record<string, number>;
    }>;
    planWithCapabilities(opportunityId: string, analysis: TreasuryAnalysis, plan: BrainPlan): Promise<{
        plan: BrainPlan & {
            capabilityMatches: CapabilityMatch[];
        };
        matches: CapabilityMatch[];
    }>;
}
export declare class MemoryCapabilityRegistry implements CapabilityRegistry {
    private assets;
    private matches;
    upsert(asset: CapabilityAsset): Promise<void>;
    list(): Promise<CapabilityAsset[]>;
    saveMatches(opportunityId: string, matches: CapabilityMatch[]): Promise<void>;
    getMatches(opportunityId: string): CapabilityMatch[];
}

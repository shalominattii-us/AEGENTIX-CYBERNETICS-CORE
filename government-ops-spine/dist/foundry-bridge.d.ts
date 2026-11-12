import type { GovernmentOpsRuntime } from './runtime.js';
import type { IntakeEnvelope, IntakeReceipt } from './intake.js';
import type { IngestDisposition } from './repository.js';
import type { PublicOpportunity } from './types.js';
export declare const DEFAULT_FOUNDRY_DISPOSITIONS: readonly ["HUMAN_REVIEW"];
export declare const DEFAULT_FOUNDRY_NAICS: readonly ["541512", "541715"];
export type FoundryOrigin = 'foundry-run' | 'foundry-report' | 'sam-api';
export interface FoundryIntelligenceLabel {
    stage: string;
    disposition: string;
}
export interface LoadedFoundryRecord {
    origin: FoundryOrigin;
    externalId: string;
    title: string;
    naics: string[];
    intelligence?: FoundryIntelligenceLabel;
    opportunity: PublicOpportunity;
}
export interface FoundrySkip {
    externalId?: string;
    title?: string;
    reason: 'disposition' | 'disposition_missing' | 'naics' | 'naics_missing' | 'duplicate';
}
export interface FoundryIngestError {
    externalId?: string;
    title?: string;
    message: string;
}
export interface FoundryIngestResult {
    eventId: string;
    externalId: string;
    disposition: IngestDisposition;
    canonicalHash: string;
    revision: number;
}
export interface FoundryIngestSummary {
    sourceRunId: string;
    dryRun: boolean;
    loaded: number;
    selected: number;
    selectedExternalIds: string[];
    skipped: FoundrySkip[];
    results: FoundryIngestResult[];
    errors: FoundryIngestError[];
}
export interface OpportunitySink {
    ingest(envelope: IntakeEnvelope): Promise<IntakeReceipt>;
}
export interface FoundryLoadBatch {
    sourceRunId: string;
    receivedAt?: string;
    records: LoadedFoundryRecord[];
    errors: FoundryIngestError[];
}
export interface SamPullOptions {
    apiKey: string;
    postedFrom?: string;
    postedTo?: string;
    lookbackDays?: number;
    limit?: number;
    noticeType?: string;
    title?: string;
    organization?: string;
    endpoint?: string;
    fetchImpl?: typeof fetch;
    now?: () => Date;
    naics: string[];
    maxPages?: number;
}
export interface FoundryIngestRequest {
    path?: string;
    pull?: SamPullOptions;
    dispositions: string[];
    naics: string[];
    sourceRunId?: string;
    receivedAt?: string;
    dryRun?: boolean;
    secrets?: string[];
}
export declare function parseFilterList(value: string | undefined, fallback: readonly string[]): string[];
export declare function parseDispositionList(value: string | undefined, fallback?: readonly string[]): string[];
export declare function parseNaicsList(value: string | undefined, fallback?: readonly string[]): string[];
export declare function runtimeSink(runtime: GovernmentOpsRuntime): OpportunitySink;
export declare function httpSink(endpoint: string, fetchImpl?: typeof fetch, secrets?: readonly string[]): OpportunitySink;
export declare function loadFoundryInput(inputPath: string): Promise<FoundryLoadBatch>;
export declare function opportunityFromFoundry(input: unknown, options: {
    origin: FoundryOrigin;
    retrievedAt?: string;
}): LoadedFoundryRecord;
export declare function selectFoundryRecords(records: LoadedFoundryRecord[], options: {
    dispositions: string[];
    naics: string[];
}): {
    selected: LoadedFoundryRecord[];
    skipped: FoundrySkip[];
};
export declare function ingestFoundryRecords(sink: OpportunitySink, records: LoadedFoundryRecord[], options: {
    sourceRunId: string;
    receivedAt: string;
    secrets?: string[];
}): Promise<{
    results: FoundryIngestResult[];
    errors: FoundryIngestError[];
}>;
export declare function runFoundryIngest(sink: OpportunitySink, request: FoundryIngestRequest): Promise<FoundryIngestSummary>;
export declare function foundryRequestFromEnv(env: NodeJS.ProcessEnv, options?: {
    pull?: boolean;
    path?: string;
    now?: () => Date;
    fetchImpl?: typeof fetch;
}): FoundryIngestRequest;
export declare function recordsFromFoundryDocument(json: unknown, options?: {
    sourceRunId?: string;
    receivedAt?: string;
}): FoundryLoadBatch;
export declare function extractNaicsCodes(value: unknown): string[];

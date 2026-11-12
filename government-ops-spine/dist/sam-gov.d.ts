export interface SamGovSearchRequest {
    apiKey: string;
    postedFrom: string;
    postedTo: string;
    limit?: number;
    offset?: number;
    naics?: string;
    title?: string;
    noticeType?: string;
    organization?: string;
    endpoint?: string;
    timeoutMs?: number;
    maxPages?: number;
    fetchImpl?: typeof fetch;
}
export declare function redactSecrets(text: string, secrets: readonly string[]): string;
export declare function assertOfficialSamEndpoint(endpoint: string): URL;
export declare function formatSamDate(date: Date): string;
export declare function assertSamDate(value: string, label: string): string;
export declare function searchSamGov(request: SamGovSearchRequest): Promise<Record<string, unknown>[]>;

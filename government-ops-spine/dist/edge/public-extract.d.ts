import { type LoadedFoundryRecord } from '../foundry-bridge.js';
export declare const SAM_PUBLIC_OPPORTUNITIES_CSV = "https://sam.gov/api/prod/fileextractservices/v1/api/download/Contract%20Opportunities/datagov/ContractOpportunitiesFullCSV.csv?privacy=Public";
export interface PublicExtractStats {
    records: LoadedFoundryRecord[];
    scannedRows: number;
    matched: number;
    bytes: number;
    stopped: 'eof' | 'matches' | 'bytes' | 'window';
}
export declare function pullSamPublicExtract(options: {
    naics: string[];
    windowStartMs: number;
    limit: number;
    maxBytes: number;
    retrievedAt: string;
    fetchImpl?: typeof fetch;
    csvText?: string;
    url?: string;
}): Promise<PublicExtractStats>;

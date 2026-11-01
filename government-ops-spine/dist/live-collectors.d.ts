import type { CapabilityAsset } from './capability-indexer.js';
export interface CapabilityCollector {
    collect(): Promise<CapabilityAsset[]>;
}
export declare class DockerCapabilityCollector implements CapabilityCollector {
    collect(): Promise<CapabilityAsset[]>;
}
export declare class GitHubWorkspaceCollector implements CapabilityCollector {
    private readonly roots;
    constructor(roots: string[]);
    collect(): Promise<CapabilityAsset[]>;
}
export declare class FilesystemDocumentCollector implements CapabilityCollector {
    private readonly roots;
    private readonly maxFiles;
    constructor(roots: string[], maxFiles?: number);
    collect(): Promise<CapabilityAsset[]>;
}

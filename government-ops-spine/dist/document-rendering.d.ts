import type { Pool } from 'pg';
export type BinaryDocumentFormat = 'pdf' | 'docx';
export interface BinaryDocumentPackage {
    packageId: string;
    artifactId: string;
    format: BinaryDocumentFormat;
    filename: string;
    mediaType: string;
    contentBase64: string;
    contentHash: string;
    createdAt: string;
    releaseState: 'internal_review' | 'release_candidate';
    externalActionBlocked: true;
}
export declare class ControlledDocumentRenderer {
    private readonly pool;
    constructor(pool: Pool);
    render(artifactId: string, format: BinaryDocumentFormat): Promise<BinaryDocumentPackage>;
}

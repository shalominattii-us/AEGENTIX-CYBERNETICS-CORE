import type { Pool } from 'pg';
export type ReviewerRole = 'technical' | 'legal' | 'compliance' | 'manufacturing' | 'executive';
export type ReviewDecision = 'approve' | 'request_changes' | 'reject';
export interface ReviewerIdentity {
    reviewerId: string;
    displayName: string;
    role: ReviewerRole;
    organization: string;
    email?: string;
}
export interface ArtifactReviewInput {
    reviewer: ReviewerIdentity;
    decision: ReviewDecision;
    comments: string;
    reviewedAt: string;
}
export interface ArtifactReviewReceipt extends ArtifactReviewInput {
    receiptId: string;
    artifactId: string;
    artifactHash: string;
    receiptHash: string;
}
export interface RenderedArtifactPackage {
    packageId: string;
    artifactId: string;
    format: 'markdown' | 'json';
    filename: string;
    mediaType: string;
    content: string;
    contentHash: string;
    createdAt: string;
    releaseState: 'internal_review' | 'release_candidate';
    externalActionBlocked: true;
}
export declare class ArtifactReviewService {
    private readonly pool;
    constructor(pool: Pool);
    review(artifactId: string, input: ArtifactReviewInput): Promise<ArtifactReviewReceipt>;
    render(artifactId: string, format?: 'markdown' | 'json'): Promise<RenderedArtifactPackage>;
    listReviews(artifactId: string): Promise<any[]>;
}

import type { Pool } from 'pg';
import type { EngineeringArtifact, EngineeringArtifactType } from './engineering-program.js';
import type { ReviewerRole, ReviewDecision } from './artifact-review.js';
export interface ReviewSnapshot {
    artifactId: string;
    artifactHash: string;
    reviewerRole: ReviewerRole;
    reviewerId: string;
    decision: ReviewDecision;
    reviewedAt: string;
}
export interface ReleasePolicyResult {
    artifactId: string;
    artifactHash: string;
    requiredRoles: ReviewerRole[];
    approvedRoles: ReviewerRole[];
    missingRoles: ReviewerRole[];
    blockingDecisions: ReviewSnapshot[];
    releaseState: 'internal_review' | 'role_review_complete';
    externalActionBlocked: true;
}
export interface ExportManifestEntry {
    artifactId: string;
    artifactType: EngineeringArtifactType;
    artifactHash: string;
    approvalState: string;
    exportPackageIds: string[];
    releasePolicy: ReleasePolicyResult;
}
export interface EngineeringExportManifest {
    manifestId: string;
    programId: string;
    opportunityId: string;
    generatedAt: string;
    entries: ExportManifestEntry[];
    manifestHash: string;
    releaseState: 'internal_review' | 'role_review_complete';
    externalActionBlocked: true;
}
export declare function requiredRolesFor(type: EngineeringArtifactType): ReviewerRole[];
export declare function evaluateReleasePolicy(artifact: EngineeringArtifact, reviews: ReviewSnapshot[]): ReleasePolicyResult;
export declare class ReleasePolicyService {
    private readonly pool;
    constructor(pool: Pool);
    evaluateArtifact(artifactId: string): Promise<ReleasePolicyResult>;
    createProgramManifest(programId: string): Promise<EngineeringExportManifest>;
    getManifest(manifestId: string): Promise<EngineeringExportManifest | undefined>;
}

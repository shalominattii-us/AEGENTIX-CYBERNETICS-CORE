import type { Pool } from 'pg';
import type { ReviewerRole } from './artifact-review.js';
export type ReviewItemType = 'artifact_review' | 'correspondence_review' | 'gmail_draft_review' | 'submission_package_review';
export type ReviewItemStatus = 'pending' | 'approved' | 'denied' | 'changes_requested';
export interface OrganizationContact {
    organizationId: string;
    name: string;
    submissionEmail: string;
    cc: string[];
    address?: string;
    jurisdiction?: string;
    sectors: string[];
    verifiedAt: string;
    source: string;
}
export interface ReviewQueueItem {
    reviewId: string;
    itemType: ReviewItemType;
    aggregateId: string;
    opportunityId?: string;
    title: string;
    summary: string;
    requiredRole: ReviewerRole | 'executive';
    status: ReviewItemStatus;
    dueAt?: string;
    createdAt: string;
    payload: Record<string, unknown>;
}
export interface ReviewDecisionInput {
    decision: 'approve' | 'deny' | 'request_changes';
    decidedBy: string;
    role: ReviewerRole | 'executive';
    comments: string;
    authorizationToken: string;
    decidedAt: string;
}
export interface SubmissionAttachment {
    packageId: string;
    filename: string;
    mediaType: string;
    contentBase64: string;
    contentHash: string;
    artifactId: string;
}
export interface CompleteSubmissionPackage {
    packageId: string;
    opportunityId: string;
    programId: string;
    organization: OrganizationContact;
    subject: string;
    body: string;
    attachments: SubmissionAttachment[];
    manifestId: string;
    createdAt: string;
    packageHash: string;
    status: 'pending_review' | 'approved' | 'denied';
    externalActionBlocked: true;
}
export declare class CollaborationFlowService {
    private readonly pool;
    constructor(pool: Pool);
    upsertOrganization(contact: OrganizationContact): Promise<OrganizationContact>;
    listOrganizations(): Promise<any[]>;
    reviewInbox(status?: ReviewItemStatus): Promise<{
        status: ReviewItemStatus;
        count: number;
        items: any[];
    }>;
    enqueue(input: Omit<ReviewQueueItem, 'reviewId' | 'status' | 'createdAt'>): Promise<ReviewQueueItem>;
    decide(reviewId: string, input: ReviewDecisionInput): Promise<any>;
    assembleCompletePackage(input: {
        opportunityId: string;
        programId: string;
        organizationId: string;
        manifestId: string;
        subject?: string;
        body?: string;
    }): Promise<CompleteSubmissionPackage>;
    getPackage(packageId: string): Promise<any>;
}

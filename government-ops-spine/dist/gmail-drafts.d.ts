import type { Pool } from 'pg';
export interface GmailAttachment {
    filename: string;
    mediaType: string;
    contentBase64: string;
    contentHash: string;
}
export interface GmailDraftProvider {
    createDraft(input: {
        from: string;
        to: string[];
        cc: string[];
        subject: string;
        body: string;
        attachments: GmailAttachment[];
    }): Promise<{
        providerDraftId: string;
        createdAt: string;
        displayUrl?: string;
    }>;
}
export interface GmailDraftReceipt {
    receiptId: string;
    correspondenceId: string;
    packageId?: string;
    providerDraftId: string;
    mailbox: string;
    createdAt: string;
    status: 'draft_created';
    attachmentCount: number;
    recipientCount: number;
    displayUrl?: string;
    sendBlocked: true;
}
export declare class GmailDraftIntegration {
    private readonly pool;
    constructor(pool: Pool);
    createReviewableDraft(correspondenceId: string, provider: GmailDraftProvider): Promise<GmailDraftReceipt>;
    createFromApprovedPackage(packageId: string, mailbox: string, provider: GmailDraftProvider): Promise<GmailDraftReceipt>;
    private resolveAttachments;
    private create;
}
export declare class DisabledGmailDraftProvider implements GmailDraftProvider {
    createDraft(): Promise<{
        providerDraftId: string;
        createdAt: string;
    }>;
}

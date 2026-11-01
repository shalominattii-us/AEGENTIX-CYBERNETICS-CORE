export type CorrespondencePurpose = 'proposal' | 'patent' | 'partnership' | 'clarification' | 'general';
export interface OrganizationalMailbox {
    displayName: string;
    address: string;
    authorizedDomains?: string[];
}
export interface CorrespondenceDraft {
    id: string;
    purpose: CorrespondencePurpose;
    mailbox: OrganizationalMailbox;
    to: string[];
    cc: string[];
    subject: string;
    body: string;
    attachments: string[];
    opportunityId?: string;
    createdAt: string;
    status: 'draft' | 'approved' | 'sent' | 'rejected';
    approval?: ApprovalReceipt;
}
export interface ApprovalReceipt {
    approvedBy: string;
    approvedAt: string;
    scope: 'single_message';
    authorizationToken: string;
}
export interface CorrespondenceTransport {
    send(draft: CorrespondenceDraft): Promise<{
        providerMessageId: string;
        sentAt: string;
    }>;
}
export declare class CorrespondenceQueue {
    private readonly drafts;
    create(input: Omit<CorrespondenceDraft, 'id' | 'createdAt' | 'status'>): CorrespondenceDraft;
    approve(id: string, receipt: ApprovalReceipt): CorrespondenceDraft;
    send(id: string, transport: CorrespondenceTransport): Promise<CorrespondenceDraft>;
    get(id: string): CorrespondenceDraft | undefined;
    list(): CorrespondenceDraft[];
    private require;
}

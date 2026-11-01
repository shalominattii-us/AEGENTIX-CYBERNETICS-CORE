export class CorrespondenceQueue {
    drafts = new Map();
    create(input) {
        validateMailbox(input.mailbox);
        const id = `CORR-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
        const draft = { id, createdAt: new Date().toISOString(), status: 'draft', ...input };
        this.drafts.set(id, draft);
        return draft;
    }
    approve(id, receipt) {
        if (!receipt.authorizationToken.startsWith('AEGENTIX-AUTH-'))
            throw new Error('Explicit AEGENTIX authorization token required.');
        const draft = this.require(id);
        const approved = { ...draft, status: 'approved', approval: receipt };
        this.drafts.set(id, approved);
        return approved;
    }
    async send(id, transport) {
        const draft = this.require(id);
        if (draft.status !== 'approved' || !draft.approval)
            throw new Error('Correspondence blocked: approved single-message authorization required.');
        if (draft.purpose === 'proposal' || draft.purpose === 'patent')
            assertSubmissionAuthorized(draft.approval.authorizationToken);
        await transport.send(draft);
        const sent = { ...draft, status: 'sent' };
        this.drafts.set(id, sent);
        return sent;
    }
    get(id) { return this.drafts.get(id); }
    list() { return [...this.drafts.values()]; }
    require(id) { const draft = this.drafts.get(id); if (!draft)
        throw new Error('Correspondence draft not found.'); return draft; }
}
function validateMailbox(mailbox) { if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(mailbox.address))
    throw new Error('A valid organizational mailbox is required.'); }
function assertSubmissionAuthorized(token) { if (!token.startsWith('AEGENTIX-AUTH-'))
    throw new Error('Proposal or patent submission blocked.'); }

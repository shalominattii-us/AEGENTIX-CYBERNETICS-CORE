import { createHash } from 'node:crypto';
export class GmailDraftIntegration {
    pool;
    constructor(pool) {
        this.pool = pool;
    }
    async createReviewableDraft(correspondenceId, provider) {
        const result = await this.pool.query('select * from correspondence_drafts where id=$1', [correspondenceId]);
        if (!result.rowCount)
            throw new Error('Correspondence draft not found.');
        const row = result.rows[0];
        if (row.status !== 'approved')
            throw new Error('Gmail draft creation requires an approved single-message correspondence record.');
        const approval = await this.pool.query('select draft_id from correspondence_approvals where draft_id=$1', [correspondenceId]);
        if (!approval.rowCount)
            throw new Error('Approval receipt not found.');
        const draft = { id: row.id, purpose: row.purpose, mailbox: row.mailbox_json, to: row.to_json, cc: row.cc_json, subject: row.subject, body: row.body, attachments: row.attachments_json, opportunityId: row.opportunity_id ?? undefined, createdAt: new Date(row.created_at).toISOString(), status: row.status };
        const attachments = await this.resolveAttachments(draft.attachments);
        return this.create(provider, { correspondenceId, from: draft.mailbox.address, to: draft.to, cc: draft.cc, subject: draft.subject, body: draft.body, attachments });
    }
    async createFromApprovedPackage(packageId, mailbox, provider) {
        const result = await this.pool.query('select p.*,o.submission_email,o.cc_json from complete_submission_packages p join organization_directory o on o.organization_id=p.organization_id where p.package_id=$1', [packageId]);
        if (!result.rowCount)
            throw new Error('Complete submission package not found.');
        const row = result.rows[0];
        const review = await this.pool.query(`select review_id from human_review_queue where aggregate_id=$1 and item_type='submission_package_review' and status='approved'`, [packageId]);
        if (!review.rowCount)
            throw new Error('Complete package requires explicit one-click approval before Gmail draft creation.');
        const pkg = { packageId: row.package_id, opportunityId: row.opportunity_id, programId: row.program_id, organization: { organizationId: row.organization_id, name: '', submissionEmail: row.submission_email, cc: row.cc_json, sectors: [], verifiedAt: new Date().toISOString(), source: '' }, subject: row.subject, body: row.body, attachments: row.attachments_json, manifestId: row.manifest_id, createdAt: new Date(row.created_at).toISOString(), packageHash: row.package_hash, status: 'approved', externalActionBlocked: true };
        const attachments = pkg.attachments.map(toGmailAttachment);
        const correspondenceId = `PKG-${packageId}`;
        return this.create(provider, { correspondenceId, packageId, from: mailbox, to: [row.submission_email], cc: row.cc_json, subject: pkg.subject, body: pkg.body, attachments });
    }
    async resolveAttachments(ids) { if (!ids.length)
        return []; const r = await this.pool.query('select filename,media_type,content_base64,content_hash from binary_artifact_exports where package_id=any($1::text[])', [ids]); return r.rows.map(x => ({ filename: x.filename, mediaType: x.media_type, contentBase64: x.content_base64, contentHash: x.content_hash })); }
    async create(provider, input) {
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(input.from))
            throw new Error('A valid organizational mailbox is required.');
        if (!input.to.length)
            throw new Error('At least one recipient is required.');
        const providerResult = await provider.createDraft({ from: input.from, to: input.to, cc: input.cc, subject: input.subject, body: input.body, attachments: input.attachments });
        const receiptBase = { correspondenceId: input.correspondenceId, packageId: input.packageId, providerDraftId: providerResult.providerDraftId, mailbox: input.from, createdAt: providerResult.createdAt, status: 'draft_created', attachmentCount: input.attachments.length, recipientCount: input.to.length + input.cc.length, displayUrl: providerResult.displayUrl, sendBlocked: true };
        const receipt = { ...receiptBase, receiptId: `GMAIL-${hash(receiptBase).slice(0, 20)}` };
        await this.pool.query(`insert into gmail_draft_receipts(receipt_id,correspondence_id,provider_draft_id,mailbox,created_at,status,send_blocked) values($1,$2,$3,$4,$5,'draft_created',true) on conflict(correspondence_id) do update set provider_draft_id=excluded.provider_draft_id,mailbox=excluded.mailbox,created_at=excluded.created_at`, [receipt.receiptId, input.correspondenceId, receipt.providerDraftId, receipt.mailbox, receipt.createdAt]);
        await this.pool.query(`insert into cybercore_outbox(event_type,aggregate_id,payload_json) values('correspondence.gmail_draft.created',$1,$2)`, [input.correspondenceId, { ...receipt, attachments: input.attachments.map(a => ({ filename: a.filename, contentHash: a.contentHash })) }]);
        return receipt;
    }
}
export class DisabledGmailDraftProvider {
    async createDraft() { throw new Error('Gmail provider is not configured. Draft creation remains blocked.'); }
}
function toGmailAttachment(a) { return { filename: a.filename, mediaType: a.mediaType, contentBase64: a.contentBase64, contentHash: a.contentHash }; }
function hash(value) { return createHash('sha256').update(JSON.stringify(value)).digest('hex'); }

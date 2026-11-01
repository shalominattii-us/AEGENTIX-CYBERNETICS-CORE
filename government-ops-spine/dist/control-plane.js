import { createHash } from 'node:crypto';
import { ArtifactReviewService } from './artifact-review.js';
import { ReleasePolicyService } from './release-policy.js';
import { ControlledDocumentRenderer } from './document-rendering.js';
import { ExecutionReceiptService } from './execution-receipts.js';
import { DisabledGmailDraftProvider, GmailDraftIntegration } from './gmail-drafts.js';
import { CollaborationFlowService } from './collaboration-flow.js';
export class ControlPlaneRuntime {
    pool;
    registry;
    indexer;
    engineeringPrograms;
    gmailProvider;
    reviews;
    releases;
    documents;
    receipts;
    gmail;
    collaboration;
    constructor(pool, registry, indexer, engineeringPrograms, gmailProvider = new DisabledGmailDraftProvider()) {
        this.pool = pool;
        this.registry = registry;
        this.indexer = indexer;
        this.engineeringPrograms = engineeringPrograms;
        this.gmailProvider = gmailProvider;
        this.reviews = new ArtifactReviewService(pool);
        this.releases = new ReleasePolicyService(pool);
        this.documents = new ControlledDocumentRenderer(pool);
        this.receipts = new ExecutionReceiptService(pool);
        this.gmail = new GmailDraftIntegration(pool);
        this.collaboration = new CollaborationFlowService(pool);
    }
    async handle(request) {
        if (request.method === 'GET' && request.path === '/api/capabilities')
            return { status: 200, body: await this.registry.list() };
        if (request.method === 'GET' && request.path === '/api/indexing/health')
            return { status: 200, body: this.indexer.health };
        if (request.method === 'POST' && request.path === '/api/indexing/run')
            return { status: 202, body: { assetCount: await this.indexer.runOnce(), health: this.indexer.health } };
        if (request.method === 'GET' && request.path === '/api/execution-receipts/dashboard')
            return { status: 200, body: await this.receipts.dashboard() };
        if (request.method === 'GET' && request.path === '/api/reviews/inbox')
            return { status: 200, body: await this.collaboration.reviewInbox('pending') };
        if (request.method === 'GET' && request.path === '/api/organizations')
            return { status: 200, body: await this.collaboration.listOrganizations() };
        if (request.method === 'POST' && request.path === '/api/organizations')
            return { status: 201, body: await this.collaboration.upsertOrganization(request.body) };
        const decision = request.path.match(/^\/api\/reviews\/([^/]+)\/(approve|deny|request-changes)$/);
        if (request.method === 'POST' && decision) {
            const body = request.body;
            const verb = decision[2];
            const mapped = verb === 'request-changes' ? 'request_changes' : verb;
            return { status: 200, body: await this.collaboration.decide(decodeURIComponent(decision[1]), { ...body, decision: mapped }) };
        }
        const generate = request.path.match(/^\/api\/opportunities\/([^/]+)\/engineering-programs$/);
        if (request.method === 'POST' && generate)
            return { status: 201, body: await this.engineeringPrograms.generateForOpportunity(decodeURIComponent(generate[1])) };
        if (request.method === 'GET' && generate)
            return { status: 200, body: await this.engineeringPrograms.listByOpportunity(decodeURIComponent(generate[1])) };
        const program = request.path.match(/^\/api\/engineering-programs\/([^/]+)$/);
        if (request.method === 'GET' && program) {
            const found = await this.engineeringPrograms.get(decodeURIComponent(program[1]));
            return found ? { status: 200, body: found } : { status: 404, body: { error: 'Engineering program not found' } };
        }
        const manifest = request.path.match(/^\/api\/engineering-programs\/([^/]+)\/export-manifests$/);
        if (request.method === 'POST' && manifest)
            return { status: 201, body: await this.releases.createProgramManifest(decodeURIComponent(manifest[1])) };
        const packageRoute = request.path.match(/^\/api\/engineering-programs\/([^/]+)\/complete-package$/);
        if (request.method === 'POST' && packageRoute) {
            const b = request.body;
            return { status: 201, body: await this.collaboration.assembleCompletePackage({ ...b, programId: decodeURIComponent(packageRoute[1]) }) };
        }
        const getPackage = request.path.match(/^\/api\/complete-packages\/([^/]+)$/);
        if (request.method === 'GET' && getPackage) {
            const found = await this.collaboration.getPackage(decodeURIComponent(getPackage[1]));
            return found ? { status: 200, body: found } : { status: 404, body: { error: 'Complete package not found' } };
        }
        const packageGmail = request.path.match(/^\/api\/complete-packages\/([^/]+)\/gmail-draft$/);
        if (request.method === 'POST' && packageGmail) {
            const mailbox = request.body.mailbox;
            return { status: 201, body: await this.gmail.createFromApprovedPackage(decodeURIComponent(packageGmail[1]), mailbox, this.gmailProvider) };
        }
        const getManifest = request.path.match(/^\/api\/export-manifests\/([^/]+)$/);
        if (request.method === 'GET' && getManifest) {
            const found = await this.releases.getManifest(decodeURIComponent(getManifest[1]));
            return found ? { status: 200, body: found } : { status: 404, body: { error: 'Export manifest not found' } };
        }
        const review = request.path.match(/^\/api\/engineering-artifacts\/([^/]+)\/reviews$/);
        if (request.method === 'POST' && review)
            return { status: 201, body: await this.reviews.review(decodeURIComponent(review[1]), request.body) };
        if (request.method === 'GET' && review)
            return { status: 200, body: await this.reviews.listReviews(decodeURIComponent(review[1])) };
        const policy = request.path.match(/^\/api\/engineering-artifacts\/([^/]+)\/release-policy$/);
        if (request.method === 'GET' && policy)
            return { status: 200, body: await this.releases.evaluateArtifact(decodeURIComponent(policy[1])) };
        const render = request.path.match(/^\/api\/engineering-artifacts\/([^/]+)\/render$/);
        if (request.method === 'POST' && render) {
            const format = request.body?.format ?? 'markdown';
            return { status: 201, body: await this.reviews.render(decodeURIComponent(render[1]), format) };
        }
        const binary = request.path.match(/^\/api\/engineering-artifacts\/([^/]+)\/render-binary$/);
        if (request.method === 'POST' && binary) {
            const format = request.body?.format ?? 'pdf';
            return { status: 201, body: await this.documents.render(decodeURIComponent(binary[1]), format) };
        }
        if (request.method === 'POST' && request.path === '/api/correspondence/drafts')
            return { status: 201, body: await this.createDraft(request.body) };
        const approve = request.path.match(/^\/api\/correspondence\/([^/]+)\/approve$/);
        if (request.method === 'POST' && approve)
            return { status: 200, body: await this.approve(decodeURIComponent(approve[1]), request.body) };
        const gmailDraft = request.path.match(/^\/api\/correspondence\/([^/]+)\/gmail-draft$/);
        if (request.method === 'POST' && gmailDraft)
            return { status: 201, body: await this.gmail.createReviewableDraft(decodeURIComponent(gmailDraft[1]), this.gmailProvider) };
        const get = request.path.match(/^\/api\/correspondence\/([^/]+)$/);
        if (request.method === 'GET' && get) {
            const row = await this.pool.query('select * from correspondence_drafts where id=$1', [decodeURIComponent(get[1])]);
            return row.rowCount ? { status: 200, body: row.rows[0] } : { status: 404, body: { error: 'Correspondence draft not found' } };
        }
        return undefined;
    }
    async createDraft(input) { if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(input.mailbox.address))
        throw new Error('A valid organizational mailbox is required.'); const id = `CORR-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, createdAt = new Date().toISOString(); await this.pool.query(`insert into correspondence_drafts(id,purpose,mailbox_json,to_json,cc_json,subject,body,attachments_json,opportunity_id,status,created_at) values($1,$2,$3,$4,$5,$6,$7,$8,$9,'draft',$10)`, [id, input.purpose, input.mailbox, input.to, input.cc, input.subject, input.body, input.attachments, input.opportunityId ?? null, createdAt]); await this.collaboration.enqueue({ itemType: 'correspondence_review', aggregateId: id, opportunityId: input.opportunityId, title: `Review correspondence: ${input.subject}`, summary: `Recipients: ${input.to.join(', ')}; attachments: ${input.attachments.length}`, requiredRole: 'executive', payload: { correspondenceId: id, subject: input.subject, to: input.to, cc: input.cc, attachments: input.attachments } }); await this.receipts.record('correspondence.draft.created', id, { purpose: input.purpose, mailbox: input.mailbox.address }); return { id, createdAt, status: 'draft', ...input }; }
    async approve(id, receipt) { if (!receipt.authorizationToken.startsWith('AEGENTIX-AUTH-'))
        throw new Error('Explicit AEGENTIX authorization token required.'); const hash = createHash('sha256').update(receipt.authorizationToken).digest('hex'); const client = await this.pool.connect(); try {
        await client.query('begin');
        const updated = await client.query(`update correspondence_drafts set status='approved',updated_at=now() where id=$1 and status='draft' returning *`, [id]);
        if (!updated.rowCount)
            throw new Error('Draft not found or not approvable.');
        await client.query(`insert into correspondence_approvals(draft_id,approved_by,approved_at,scope,authorization_token_hash) values($1,$2,$3,'single_message',$4) on conflict(draft_id) do update set approved_by=excluded.approved_by,approved_at=excluded.approved_at,authorization_token_hash=excluded.authorization_token_hash`, [id, receipt.approvedBy, receipt.approvedAt, hash]);
        await client.query('commit');
        await this.receipts.record('correspondence.approved', id, { approvedBy: receipt.approvedBy, scope: 'single_message' });
        return updated.rows[0];
    }
    catch (error) {
        await client.query('rollback');
        throw error;
    }
    finally {
        client.release();
    } }
}

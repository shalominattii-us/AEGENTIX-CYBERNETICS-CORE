import { createHash } from 'node:crypto';
export class ArtifactReviewService {
    pool;
    constructor(pool) {
        this.pool = pool;
    }
    async review(artifactId, input) {
        validateReviewer(input.reviewer);
        const artifactResult = await this.pool.query('select artifact_json,content_hash,approval_state from engineering_artifacts where artifact_id=$1', [artifactId]);
        if (!artifactResult.rowCount)
            throw new Error('Engineering artifact not found.');
        const row = artifactResult.rows[0];
        const receiptBase = { artifactId, artifactHash: row.content_hash, ...input };
        const receipt = { ...receiptBase, receiptId: `REVIEW-${hash(receiptBase).slice(0, 20)}`, receiptHash: hash(receiptBase) };
        const nextState = input.decision === 'approve' ? 'technical_review' : 'draft';
        const client = await this.pool.connect();
        try {
            await client.query('begin');
            await client.query(`insert into artifact_reviews(receipt_id,artifact_id,artifact_hash,reviewer_json,decision,comments,reviewed_at,receipt_hash) values($1,$2,$3,$4,$5,$6,$7,$8)`, [receipt.receiptId, artifactId, receipt.artifactHash, input.reviewer, input.decision, input.comments, input.reviewedAt, receipt.receiptHash]);
            await client.query(`update engineering_artifacts set approval_state=$2,updated_at=now() where artifact_id=$1`, [artifactId, nextState]);
            await client.query('commit');
            return receipt;
        }
        catch (error) {
            await client.query('rollback');
            throw error;
        }
        finally {
            client.release();
        }
    }
    async render(artifactId, format = 'markdown') {
        const result = await this.pool.query('select artifact_json,content_hash,approval_state from engineering_artifacts where artifact_id=$1', [artifactId]);
        if (!result.rowCount)
            throw new Error('Engineering artifact not found.');
        const artifact = result.rows[0].artifact_json;
        const releaseState = result.rows[0].approval_state === 'technical_review' ? 'release_candidate' : 'internal_review';
        const content = format === 'json' ? JSON.stringify(artifact, null, 2) : renderMarkdown(artifact);
        const createdAt = new Date().toISOString();
        const pkg = { packageId: `EXPORT-${hash({ artifactId, format, content }).slice(0, 20)}`, artifactId, format, filename: `${artifact.type}-${artifact.artifactId}.${format === 'json' ? 'json' : 'md'}`, mediaType: format === 'json' ? 'application/json' : 'text/markdown', content, contentHash: hash(content), createdAt, releaseState, externalActionBlocked: true };
        await this.pool.query(`insert into artifact_exports(package_id,artifact_id,format,filename,media_type,content_text,content_hash,release_state,external_action_blocked,created_at) values($1,$2,$3,$4,$5,$6,$7,$8,true,$9) on conflict(package_id) do nothing`, [pkg.packageId, artifactId, format, pkg.filename, pkg.mediaType, pkg.content, pkg.contentHash, pkg.releaseState, createdAt]);
        return pkg;
    }
    async listReviews(artifactId) { const r = await this.pool.query('select * from artifact_reviews where artifact_id=$1 order by reviewed_at', [artifactId]); return r.rows; }
}
function validateReviewer(reviewer) { if (!reviewer.reviewerId || !reviewer.displayName || !reviewer.organization)
    throw new Error('Named reviewer identity is required.'); }
function renderMarkdown(a) { return `# ${a.title}\n\n- Artifact ID: ${a.artifactId}\n- Opportunity: ${a.opportunityId}\n- Specification: ${a.specificationId}\n- Approval state: ${a.approvalState}\n- External action blocked: ${a.externalActionBlocked}\n\n## Content\n\n\`\`\`json\n${JSON.stringify(a.content, null, 2)}\n\`\`\`\n`; }
function hash(value) { return createHash('sha256').update(typeof value === 'string' ? value : JSON.stringify(value)).digest('hex'); }

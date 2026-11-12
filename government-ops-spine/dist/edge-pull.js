import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Pool } from 'pg';
import { PostgresOpportunityRepository } from './postgres.js';
import { GovernmentOpsRuntime } from './runtime.js';
import { runtimeSink } from './foundry-bridge.js';
const D1_QUERY = 'https://api.cloudflare.com/client/v4/accounts';
export async function pullEdgeOutbox(options) {
    const accountId = options.accountId.trim();
    const databaseId = options.databaseId.trim();
    const apiToken = options.apiToken.trim();
    if (!/^[a-f0-9]{32}$/i.test(accountId))
        throw new Error('CLOUDFLARE_ACCOUNT_ID must be a 32 character account id');
    if (!/^[a-f0-9-]{36}$/i.test(databaseId))
        throw new Error('D1_DATABASE_ID must be a database UUID');
    if (!apiToken)
        throw new Error('CLOUDFLARE_API_TOKEN is required');
    const fetchImpl = options.fetchImpl ?? fetch;
    const limit = options.limit ?? 50;
    const publishedAt = (options.now ?? (() => new Date()))().toISOString();
    const rows = await d1Query(fetchImpl, accountId, databaseId, apiToken, `select id, event_type, aggregate_id, payload_json from intake_outbox where published_at is null order by id limit ?`, [limit]);
    const summary = { claimed: rows.length, published: 0, results: [], errors: [] };
    for (const row of rows) {
        try {
            const envelope = JSON.parse(row.payload_json);
            const receipt = await options.sink.ingest(envelope);
            await d1Query(fetchImpl, accountId, databaseId, apiToken, `update intake_outbox set published_at = ? where id = ? and published_at is null`, [publishedAt, row.id]);
            summary.published += 1;
            summary.results.push({ id: row.id, externalId: envelope.opportunity?.externalId, disposition: receipt.result.disposition });
        }
        catch (error) {
            summary.errors.push({ id: row.id, message: redactToken(error instanceof Error ? error.message : String(error), apiToken) });
        }
    }
    return summary;
}
async function d1Query(fetchImpl, accountId, databaseId, apiToken, sql, params) {
    const url = `${D1_QUERY}/${accountId}/d1/database/${databaseId}/query`;
    let response;
    try {
        response = await fetchImpl(url, {
            method: 'POST',
            headers: { authorization: `Bearer ${apiToken}`, 'content-type': 'application/json' },
            body: JSON.stringify({ sql, params })
        });
    }
    catch (error) {
        throw new Error(redactToken(`D1 query failed: ${error instanceof Error ? error.message : String(error)}`, apiToken));
    }
    const text = await response.text();
    if (!response.ok)
        throw new Error(redactToken(`D1 query failed (${response.status}): ${text.slice(0, 300)}`, apiToken));
    let body;
    try {
        body = JSON.parse(text);
    }
    catch {
        throw new Error('D1 query response was not JSON');
    }
    if (!isRecord(body) || body.success !== true || !Array.isArray(body.result)) {
        throw new Error(redactToken('D1 query was rejected', apiToken));
    }
    const first = body.result[0];
    if (!isRecord(first) || !Array.isArray(first.results))
        return [];
    return first.results;
}
function redactToken(text, token) {
    const trimmed = token.trim();
    return trimmed.length >= 8 ? text.split(trimmed).join('[redacted]') : text;
}
function isRecord(value) {
    return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}
async function main() {
    const accountId = process.env.CLOUDFLARE_ACCOUNT_ID ?? '';
    const databaseId = process.env.D1_DATABASE_ID ?? '';
    const apiToken = process.env.CLOUDFLARE_API_TOKEN ?? '';
    const databaseUrl = process.env.DATABASE_URL;
    if (!databaseUrl) {
        console.error(JSON.stringify({ event: 'edge_pull.error', error: 'DATABASE_URL is required' }));
        return 2;
    }
    const pool = new Pool({ connectionString: databaseUrl });
    try {
        const sink = runtimeSink(new GovernmentOpsRuntime(new PostgresOpportunityRepository(pool)));
        const summary = await pullEdgeOutbox({ accountId, databaseId, apiToken, sink });
        console.log(JSON.stringify({ event: 'edge_pull.completed', claimed: summary.claimed, published: summary.published, errors: summary.errors.length }));
        return summary.errors.length ? 1 : 0;
    }
    catch (error) {
        console.error(JSON.stringify({ event: 'edge_pull.error', error: redactToken(error instanceof Error ? error.message : String(error), apiToken) }));
        return 2;
    }
    finally {
        await pool.end();
    }
}
const pullPath = fileURLToPath(import.meta.url);
if (process.argv[1] && path.resolve(process.argv[1]) === pullPath) {
    main().then((code) => process.exit(code));
}

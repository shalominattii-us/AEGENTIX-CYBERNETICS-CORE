import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { DatabaseSync } from 'node:sqlite';
import { hashOpportunity } from './intake.js';
import { assertExternalActionAuthorized } from './pipeline.js';
import { handleIntakeRequest, handleScheduledIntake } from './edge/index.js';
import { pullEdgeOutbox } from './edge-pull.js';
const migration = readFileSync(path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../edge-intake/migrations/0001_intake.sql'), 'utf8');
const token = 'ingest-token-for-tests';
const apiKey = 'unit-test-sam-key';
function database() {
    const raw = new DatabaseSync(':memory:');
    raw.exec('PRAGMA foreign_keys = ON');
    raw.exec(migration);
    const sql = {
        prepare(query) {
            return {
                bind(...values) {
                    return {
                        async first() {
                            const row = raw.prepare(query).get(...values);
                            return row ?? null;
                        },
                        async run() {
                            raw.prepare(query).run(...values);
                            return { success: true };
                        }
                    };
                }
            };
        },
        async batch(statements) {
            raw.exec('begin');
            try {
                for (const statement of statements)
                    await statement.run();
                raw.exec('commit');
            }
            catch (error) {
                raw.exec('rollback');
                throw error;
            }
        }
    };
    return { sql, raw };
}
function env(sql, extra = {}) {
    return { DB: sql, INGEST_TOKEN: token, FOUNDRY_INGEST_NAICS: '541512,541715', FOUNDRY_INGEST_DISPOSITIONS: 'HUMAN_REVIEW', ...extra };
}
const foundryRecord = {
    external_id: 'NOTICE-EDGE-541512',
    title: 'Edge software solicitation',
    source: 'SAM.gov',
    source_url: 'https://sam.gov/opp/NOTICE-EDGE-541512/view',
    issuer: 'GENERAL SERVICES ADMINISTRATION.FAS',
    jurisdiction: 'United States',
    type: 'Solicitation',
    naics: ['541512'],
    description: 'The contractor shall deliver software.',
    deadline: '2099-06-01T17:00:00Z',
    published_date: '2026-07-21',
    intelligence_output: { maturity: { stage: 'HUMAN_REVIEW', disposition: 'REQUIRES_HUMAN_DECISION' } }
};
const notice = {
    noticeId: 'NOTICE-EDGE-541512',
    title: 'Edge software solicitation',
    type: 'Solicitation',
    naicsCode: '541512',
    fullParentPathName: 'GENERAL SERVICES ADMINISTRATION.FAS',
    uiLink: 'https://sam.gov/opp/NOTICE-EDGE-541512/view',
    description: 'The contractor shall deliver software.',
    responseDeadLine: '2099-06-01T17:00:00Z',
    postedDate: '2026-07-21'
};
test('edge intake stays off the external-action path', () => {
    assert.throws(() => assertExternalActionAuthorized('submit_offer'), /blocked/);
    assert.throws(() => assertExternalActionAuthorized('external_representation'), /blocked/);
});
test('health is public and every other read is closed', async () => {
    const { sql } = database();
    const bindings = env(sql);
    const health = await handleIntakeRequest(new Request('https://intake.example/health'), bindings);
    assert.equal(health.status, 200);
    const healthBody = await health.json();
    assert.equal(healthBody.ok, true);
    assert.equal(healthBody.service, 'opportunity-intake');
    assert.equal(JSON.stringify(healthBody).includes('NOTICE-EDGE'), false);
    for (const pathName of ['/api/opportunities', '/api/opportunities/sam:NOTICE-EDGE-541512/state', '/admin', '/']) {
        const response = await handleIntakeRequest(new Request(`https://intake.example${pathName}`), bindings);
        assert.equal(response.status, 404, pathName);
    }
});
test('ingest requires the bearer token, maps SAM.gov as official, and dedupes by notice id', async () => {
    const { sql, raw } = database();
    const bindings = env(sql);
    const denied = await handleIntakeRequest(new Request('https://intake.example/api/opportunities/ingest', {
        method: 'POST',
        body: JSON.stringify([notice])
    }), bindings);
    assert.equal(denied.status, 401);
    const first = await handleIntakeRequest(authorized(JSON.stringify([foundryRecord])), bindings);
    assert.equal(first.status, 200);
    const created = await first.json();
    const createdResult = created.results[0];
    assert.ok(createdResult);
    assert.equal(createdResult.disposition, 'created');
    assert.equal(createdResult.eventId, 'sam:NOTICE-EDGE-541512');
    const stored = raw.prepare('select canonical_hash, opportunity_json, revision from opportunity_records').get();
    const opportunity = JSON.parse(stored.opportunity_json);
    assert.equal(stored.canonical_hash, hashOpportunity(opportunity));
    assert.equal(stored.canonical_hash, createdResult.canonicalHash);
    assert.equal(opportunity.provenance[0]?.authority, 'official');
    assert.equal(opportunity.provenance[0]?.system, 'SAM.gov');
    assert.equal(opportunity.provenance[0]?.url, 'https://sam.gov/opp/NOTICE-EDGE-541512/view');
    assert.equal(countOf(raw, 'intake_outbox'), 1);
    const second = await handleIntakeRequest(authorized(JSON.stringify([foundryRecord])), bindings);
    const unchanged = await second.json();
    const unchangedResult = unchanged.results[0];
    assert.ok(unchangedResult);
    assert.equal(unchangedResult.disposition, 'unchanged');
    assert.equal(unchangedResult.revision, 1);
    assert.equal(unchangedResult.canonicalHash, createdResult.canonicalHash);
    assert.equal(countOf(raw, 'intake_outbox'), 1);
    assert.equal(countOf(raw, 'opportunity_revisions'), 1);
    const amendedBody = JSON.stringify([{ ...foundryRecord, deadline: '2099-07-01T17:00:00Z' }]);
    const third = await handleIntakeRequest(authorized(amendedBody), bindings);
    const amended = await third.json();
    const amendedResult = amended.results[0];
    assert.ok(amendedResult);
    assert.equal(amendedResult.disposition, 'amended');
    assert.equal(amendedResult.revision, 2);
    assert.equal(countOf(raw, 'intake_outbox'), 2);
    assert.equal(JSON.stringify(created).includes(token), false);
    const uploaded = await handleIntakeRequest(authorized(JSON.stringify({ opportunitiesData: [notice] })), env(database().sql));
    const uploadedBody = await uploaded.json();
    assert.equal(uploadedBody.results.length, 0);
    assert.equal(uploadedBody.skipped[0]?.reason, 'disposition_missing');
});
test('scheduled pull calls only api.sam.gov and does not log the key', async () => {
    const { sql, raw } = database();
    const urls = [];
    const summary = await handleScheduledIntake(env(sql, { SAM_GOV_API_KEY: apiKey, FOUNDRY_INGEST_NAICS: '541512' }), {
        now: new Date('2026-07-22T15:00:00.000Z'),
        fetchImpl: async (input) => {
            const url = String(input);
            urls.push(url);
            if (url.includes('unit-test-sam-key-should-not-echo'))
                throw new Error(url);
            return Response.json({ totalRecords: 1, opportunitiesData: [notice] });
        }
    });
    const cronResult = summary.results[0];
    assert.ok(cronResult);
    assert.equal(cronResult.disposition, 'created');
    assert.ok(urls.every((url) => new URL(url).hostname === 'api.sam.gov'));
    assert.equal(JSON.stringify(summary).includes(apiKey), false);
    assert.equal(countOf(raw, 'opportunity_records'), 1);
    const repeat = await handleScheduledIntake(env(sql, { SAM_GOV_API_KEY: apiKey, FOUNDRY_INGEST_NAICS: '541512' }), {
        now: new Date('2026-08-01T00:00:00.000Z'),
        fetchImpl: async () => Response.json({ totalRecords: 1, opportunitiesData: [notice] })
    });
    const repeatResult = repeat.results[0];
    assert.ok(repeatResult);
    assert.equal(repeatResult.disposition, 'unchanged');
});
test('the spine pulls the edge outbox from the Cloudflare API and does not open a listener', async () => {
    const calls = [];
    const cloudToken = 'cloudflare-api-token-test';
    const opportunity = {
        schemaVersion: '1.0.0',
        eventId: 'sam:NOTICE-EDGE-541512',
        externalId: 'NOTICE-EDGE-541512',
        title: 'Edge software solicitation',
        issuer: 'GENERAL SERVICES ADMINISTRATION.FAS',
        jurisdiction: 'United States',
        opportunityType: 'RFP',
        deadline: '2099-06-01T17:00:00Z',
        eligibility: [],
        requiredRegistrations: ['SAM.gov'],
        summary: 'The contractor shall deliver software.',
        provenance: [{ system: 'SAM.gov', authority: 'official', url: 'https://sam.gov/opp/NOTICE-EDGE-541512/view', retrievedAt: '2026-07-22T15:00:00.000Z' }]
    };
    const fetchImpl = async (input, init) => {
        const url = new URL(String(input));
        calls.push(url.hostname);
        assert.equal(url.hostname, 'api.cloudflare.com');
        const body = JSON.parse(String(init?.body));
        if (body.sql.startsWith('select')) {
            return Response.json({ success: true, result: [{ success: true, results: [{ id: 7, event_type: 'opportunity.created', aggregate_id: opportunity.eventId, payload_json: JSON.stringify({ sourceRunId: 'sam-api', receivedAt: '2026-07-22T15:00:00.000Z', opportunity }) }] }] });
        }
        return Response.json({ success: true, result: [{ success: true, results: [] }] });
    };
    const summary = await pullEdgeOutbox({
        accountId: 'a'.repeat(32),
        databaseId: '00000000-0000-4000-8000-000000000001',
        apiToken: cloudToken,
        fetchImpl,
        sink: {
            async ingest(envelope) {
                assert.equal(envelope.opportunity.externalId, 'NOTICE-EDGE-541512');
                return { sourceRunId: envelope.sourceRunId, eventId: envelope.opportunity.eventId, canonicalHash: 'abc', result: { disposition: 'created', stored: { opportunity: envelope.opportunity, canonicalHash: 'abc', revision: 1, status: 'active' }, changedFields: [] } };
            }
        }
    });
    assert.equal(summary.published, 1);
    assert.deepEqual(calls, ['api.cloudflare.com', 'api.cloudflare.com']);
    assert.equal(JSON.stringify(summary).includes(cloudToken), false);
    await assert.rejects(() => pullEdgeOutbox({ accountId: 'not-an-account', databaseId: '00000000-0000-4000-8000-000000000001', apiToken: cloudToken, sink: { async ingest() { throw new Error('should not ingest'); } } }), /CLOUDFLARE_ACCOUNT_ID/);
});
function authorized(body) {
    return new Request('https://intake.example/api/opportunities/ingest', {
        method: 'POST',
        headers: { authorization: `Bearer ${token}` },
        body
    });
}
function countOf(raw, table) {
    const row = raw.prepare(`select count(*) as count from ${table}`).get();
    return Number(row?.count ?? 0);
}

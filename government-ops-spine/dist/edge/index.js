import { recordsFromFoundryDocument, parseDispositionList, parseNaicsList, selectFoundryRecords, opportunityFromFoundry } from '../foundry-bridge.js';
import { formatSamDate, redactSecrets, searchSamGov } from '../sam-gov.js';
import { ingestAuthorized } from './auth.js';
import { persistOpportunity } from './store.js';
const MAX_BODY_BYTES = 1_048_576;
export default {
    fetch(request, env) {
        return handleIntakeRequest(request, env);
    },
    scheduled(_controller, env) {
        return handleScheduledIntake(env).then(() => undefined);
    }
};
export async function handleIntakeRequest(request, env) {
    const url = new URL(request.url);
    if (request.method === 'GET' && url.pathname === '/health') {
        return json({ ok: true, service: 'opportunity-intake', externalActionsBlocked: true });
    }
    if (url.pathname !== '/api/opportunities/ingest')
        return json({ error: 'Not found' }, 404);
    if (request.method !== 'POST')
        return json({ error: 'Method not allowed' }, 405);
    if (!await ingestAuthorized(request, env.INGEST_TOKEN))
        return json({ error: 'Unauthorized' }, 401);
    const body = await readLimitedBody(request);
    if (!body.ok)
        return json({ error: body.error }, body.status);
    let parsed;
    try {
        parsed = JSON.parse(body.text);
    }
    catch {
        return json({ error: 'Invalid JSON body' }, 400);
    }
    const sourceRunId = request.headers.get('x-source-run-id')?.trim() || 'edge-ingest';
    const receivedAt = new Date().toISOString();
    const loaded = recordsFromFoundryDocument(parsed, { sourceRunId, receivedAt });
    const summary = await persistLoaded(env, loaded.records, loaded.errors.map((error) => ({ message: error.message })), {
        sourceRunId,
        receivedAt,
        secrets: []
    });
    return json(summary, summary.errors.length && !summary.results.length ? 400 : 200);
}
export async function handleScheduledIntake(env, options = {}) {
    const apiKey = env.SAM_GOV_API_KEY?.trim() ?? '';
    const now = options.now ?? new Date();
    const receivedAt = now.toISOString();
    if (!apiKey) {
        console.error(JSON.stringify({ event: 'intake.cron.skipped', reason: 'SAM_GOV_API_KEY is not set' }));
        return { sourceRunId: 'sam-api', loaded: 0, selected: 0, skipped: [], results: [], errors: [{ message: 'SAM_GOV_API_KEY is not set' }] };
    }
    const lookback = positive(env.FOUNDRY_INGEST_LOOKBACK_DAYS, 1);
    const to = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
    const from = new Date(to);
    from.setUTCDate(from.getUTCDate() - lookback);
    const postedFrom = formatSamDate(from);
    const postedTo = formatSamDate(to);
    const naics = parseNaicsList(env.FOUNDRY_INGEST_NAICS);
    const dispositions = parseDispositionList(env.FOUNDRY_INGEST_DISPOSITIONS);
    const records = [];
    const errors = [];
    const seen = new Set();
    const pull = async (code) => {
        try {
            const notices = await searchSamGov({
                apiKey,
                postedFrom,
                postedTo,
                limit: positive(env.FOUNDRY_INGEST_LIMIT, 100),
                maxPages: positive(env.SAM_GOV_MAX_PAGES, 5),
                naics: code,
                fetchImpl: options.fetchImpl
            });
            for (const notice of notices) {
                try {
                    const loaded = opportunityFromFoundry(notice, { origin: 'sam-api', retrievedAt: receivedAt });
                    if (seen.has(loaded.externalId))
                        continue;
                    seen.add(loaded.externalId);
                    records.push(loaded);
                }
                catch (error) {
                    errors.push({ message: redactSecrets(error instanceof Error ? error.message : String(error), [apiKey]) });
                }
            }
        }
        catch (error) {
            errors.push({ message: redactSecrets(`SAM.gov NAICS ${code ?? 'all'}: ${error instanceof Error ? error.message : String(error)}`, [apiKey]) });
        }
    };
    if (!naics.length)
        await pull();
    else
        for (const code of naics)
            await pull(code);
    const summary = await persistLoaded(env, records, errors, {
        sourceRunId: `sam-api:${postedFrom}_to_${postedTo}`,
        receivedAt,
        secrets: [apiKey],
        dispositions,
        naics
    });
    console.log(JSON.stringify({
        event: 'intake.cron.completed',
        sourceRunId: summary.sourceRunId,
        loaded: summary.loaded,
        selected: summary.selected,
        skipped: summary.skipped.length,
        results: summary.results.map((result) => ({ externalId: result.externalId, disposition: result.disposition })),
        errors: summary.errors.length
    }));
    return summary;
}
async function persistLoaded(env, records, preloadErrors, options) {
    const dispositions = options.dispositions ?? parseDispositionList(env.FOUNDRY_INGEST_DISPOSITIONS);
    const naics = options.naics ?? parseNaicsList(env.FOUNDRY_INGEST_NAICS);
    const { selected, skipped } = selectFoundryRecords(records, { dispositions, naics });
    const results = [];
    const errors = [...preloadErrors];
    for (const record of selected) {
        try {
            results.push(await persistOpportunity(env.DB, { sourceRunId: options.sourceRunId, receivedAt: options.receivedAt, opportunity: record.opportunity }));
        }
        catch (error) {
            errors.push({ externalId: record.externalId, message: redactSecrets(error instanceof Error ? error.message : String(error), options.secrets) });
        }
    }
    return { sourceRunId: options.sourceRunId, loaded: records.length, selected: selected.length, skipped, results, errors };
}
async function readLimitedBody(request) {
    if (!request.body)
        return { ok: false, status: 400, error: 'Missing body' };
    const reader = request.body.getReader();
    const chunks = [];
    let total = 0;
    while (true) {
        const next = await reader.read();
        if (next.done)
            break;
        total += next.value.byteLength;
        if (total > MAX_BODY_BYTES)
            return { ok: false, status: 413, error: 'Payload too large' };
        chunks.push(next.value);
    }
    return { ok: true, text: new TextDecoder().decode(concatBytes(chunks)) };
}
function concatBytes(chunks) {
    const out = new Uint8Array(chunks.reduce((sum, chunk) => sum + chunk.byteLength, 0));
    let offset = 0;
    for (const chunk of chunks) {
        out.set(chunk, offset);
        offset += chunk.byteLength;
    }
    return out;
}
function positive(value, fallback) {
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : fallback;
}
function json(body, status = 200) {
    return new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json; charset=utf-8' } });
}

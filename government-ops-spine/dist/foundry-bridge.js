import { readdir, readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { formatSamDate, redactSecrets, searchSamGov } from './sam-gov.js';
export const DEFAULT_FOUNDRY_DISPOSITIONS = ['HUMAN_REVIEW'];
export const DEFAULT_FOUNDRY_NAICS = ['541512', '541715'];
export function parseFilterList(value, fallback) {
    if (value === undefined)
        return [...fallback];
    const trimmed = value.trim();
    if (!trimmed || trimmed === '*' || trimmed.toLowerCase() === 'any')
        return [];
    return [...new Set(trimmed.split(/[\s,]+/).map((part) => part.trim()).filter(Boolean))];
}
export function parseDispositionList(value, fallback = DEFAULT_FOUNDRY_DISPOSITIONS) {
    return parseFilterList(value, fallback).map((item) => item.toUpperCase());
}
export function parseNaicsList(value, fallback = DEFAULT_FOUNDRY_NAICS) {
    const raw = parseFilterList(value, fallback);
    if (!raw.length)
        return [];
    return [...new Set(raw.flatMap((token) => extractNaicsCodes(token)))].sort();
}
export function runtimeSink(runtime) {
    return {
        async ingest(envelope) {
            const response = await runtime.handle({ method: 'POST', path: '/api/opportunities/ingest', body: envelope });
            if (response.status >= 400 || !isReceipt(response.body)) {
                const message = isRecord(response.body) && typeof response.body.error === 'string'
                    ? response.body.error
                    : `Spine ingest failed (${response.status})`;
                throw new Error(message);
            }
            return response.body;
        }
    };
}
export function httpSink(endpoint, fetchImpl = fetch, secrets = []) {
    const url = endpoint.endsWith('/api/opportunities/ingest')
        ? endpoint
        : `${endpoint.replace(/\/$/, '')}/api/opportunities/ingest`;
    return {
        async ingest(envelope) {
            const response = await fetchImpl(url, {
                method: 'POST',
                headers: { 'content-type': 'application/json' },
                body: JSON.stringify(envelope)
            });
            const text = await response.text();
            let body = text;
            try {
                body = JSON.parse(text);
            }
            catch {
                body = text;
            }
            if (!response.ok || !isReceipt(body)) {
                const message = isRecord(body) && typeof body.error === 'string' ? body.error : text.slice(0, 500);
                throw new Error(redactSecrets(`Spine ingest failed (${response.status}): ${message}`, secrets));
            }
            return body;
        }
    };
}
export async function loadFoundryInput(inputPath) {
    const resolved = path.resolve(inputPath);
    const info = await stat(resolved);
    if (info.isDirectory())
        return loadDirectory(resolved);
    if (info.isFile())
        return loadFile(resolved);
    throw new Error(`Foundry input is not a file or directory: ${inputPath}`);
}
export function opportunityFromFoundry(input, options) {
    const intelligence = extractIntelligence(input);
    const intermediate = intermediateFromUnknown(input);
    if (!intermediate.retrievedAt && options.retrievedAt)
        intermediate.retrievedAt = options.retrievedAt;
    const opportunity = toPublicOpportunity(intermediate, options.retrievedAt ?? new Date(0).toISOString());
    return {
        origin: options.origin,
        externalId: opportunity.externalId,
        title: opportunity.title,
        naics: intermediate.naics,
        intelligence: intelligence ?? extractIntelligence(isRecord(input) ? input.metadata : undefined),
        opportunity
    };
}
export function selectFoundryRecords(records, options) {
    const skipped = [];
    const seen = new Map();
    for (const record of records) {
        const disposition = dispositionDecision(record, options.dispositions);
        if (!disposition.ok) {
            skipped.push({ externalId: record.externalId, title: record.title, reason: disposition.reason });
            continue;
        }
        const naics = naicsDecision(record.naics, options.naics);
        if (!naics.ok) {
            skipped.push({ externalId: record.externalId, title: record.title, reason: naics.reason });
            continue;
        }
        const identity = `${record.opportunity.provenance[0]?.system ?? 'unknown'}:${record.externalId}`;
        const previous = seen.get(identity);
        if (previous)
            skipped.push({ externalId: previous.externalId, title: previous.title, reason: 'duplicate' });
        seen.set(identity, record);
    }
    const selected = [...seen.values()].sort((a, b) => a.externalId.localeCompare(b.externalId));
    return { selected, skipped };
}
export async function ingestFoundryRecords(sink, records, options) {
    const results = [];
    const errors = [];
    for (const record of records) {
        try {
            const receipt = await sink.ingest({
                sourceRunId: options.sourceRunId,
                receivedAt: options.receivedAt,
                opportunity: record.opportunity
            });
            results.push({
                eventId: receipt.eventId,
                externalId: record.externalId,
                disposition: receipt.result.disposition,
                canonicalHash: receipt.canonicalHash,
                revision: receipt.result.stored.revision
            });
        }
        catch (error) {
            errors.push({
                externalId: record.externalId,
                title: record.title,
                message: redactSecrets(error instanceof Error ? error.message : String(error), options.secrets ?? [])
            });
        }
    }
    return { results, errors };
}
export async function runFoundryIngest(sink, request) {
    const secrets = request.secrets ?? (request.pull?.apiKey ? [request.pull.apiKey] : []);
    const batches = [];
    const errors = [];
    if (request.path) {
        try {
            batches.push(await loadFoundryInput(request.path));
        }
        catch (error) {
            errors.push({ message: redactSecrets(error instanceof Error ? error.message : String(error), secrets) });
        }
    }
    if (request.pull) {
        const pulled = await loadSamPull(request.pull, secrets);
        batches.push(pulled.batch);
        errors.push(...pulled.errors);
    }
    const records = batches.flatMap((batch) => batch.records);
    errors.push(...batches.flatMap((batch) => batch.errors));
    const { selected, skipped } = selectFoundryRecords(records, { dispositions: request.dispositions, naics: request.naics });
    const sourceRunId = request.sourceRunId ?? batches.find((batch) => batch.records.length)?.sourceRunId ?? batches[0]?.sourceRunId ?? 'foundry-ingest';
    const receivedAt = request.receivedAt ?? batches.find((batch) => batch.receivedAt)?.receivedAt ?? new Date().toISOString();
    const summaryBase = {
        sourceRunId,
        dryRun: Boolean(request.dryRun),
        loaded: records.length,
        selected: selected.length,
        selectedExternalIds: selected.map((record) => record.externalId),
        skipped,
        errors
    };
    if (request.dryRun || !selected.length)
        return { ...summaryBase, results: [] };
    const ingested = await ingestFoundryRecords(sink, selected, { sourceRunId, receivedAt, secrets });
    return { ...summaryBase, results: ingested.results, errors: [...errors, ...ingested.errors] };
}
export function foundryRequestFromEnv(env, options = {}) {
    const pathValue = options.path ?? env.FOUNDRY_INGEST_PATH?.trim() ?? undefined;
    const apiKey = env.SAM_GOV_API_KEY?.trim() ?? '';
    const pull = options.pull && apiKey ? {
        apiKey,
        postedFrom: env.SAM_GOV_POSTED_FROM?.trim() || undefined,
        postedTo: env.SAM_GOV_POSTED_TO?.trim() || undefined,
        lookbackDays: integerEnv(env.FOUNDRY_INGEST_LOOKBACK_DAYS, 1),
        limit: integerEnv(env.FOUNDRY_INGEST_LIMIT, 100),
        noticeType: env.SAM_GOV_NOTICE_TYPE?.trim() || undefined,
        title: env.SAM_GOV_TITLE?.trim() || undefined,
        organization: env.SAM_GOV_ORGANIZATION?.trim() || undefined,
        endpoint: env.SAM_GOV_ENDPOINT?.trim() || undefined,
        fetchImpl: options.fetchImpl,
        now: options.now,
        naics: parseNaicsList(env.FOUNDRY_INGEST_NAICS),
        maxPages: integerEnv(env.SAM_GOV_MAX_PAGES, 5)
    } : undefined;
    if (options.pull && !apiKey)
        throw new Error('SAM_GOV_API_KEY is required');
    return {
        path: pathValue || undefined,
        pull,
        dispositions: parseDispositionList(env.FOUNDRY_INGEST_DISPOSITIONS),
        naics: parseNaicsList(env.FOUNDRY_INGEST_NAICS),
        secrets: apiKey ? [apiKey] : [],
        dryRun: env.FOUNDRY_INGEST_DRY_RUN === 'true'
    };
}
async function loadSamPull(options, secrets) {
    const now = options.now?.() ?? new Date();
    const postedTo = options.postedTo ?? formatSamDate(now);
    const from = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
    from.setUTCDate(from.getUTCDate() - (options.lookbackDays ?? 1));
    const postedFrom = options.postedFrom ?? formatSamDate(from);
    const retrievedAt = now.toISOString();
    const records = [];
    const errors = [];
    const seen = new Set();
    const pullQuery = async (naics) => {
        try {
            const notices = await searchSamGov({
                apiKey: options.apiKey,
                postedFrom,
                postedTo,
                limit: options.limit,
                maxPages: options.maxPages,
                naics,
                title: options.title,
                noticeType: options.noticeType,
                organization: options.organization,
                endpoint: options.endpoint,
                fetchImpl: options.fetchImpl
            });
            for (const notice of notices) {
                try {
                    const loaded = opportunityFromFoundry(notice, { origin: 'sam-api', retrievedAt });
                    if (seen.has(loaded.externalId))
                        continue;
                    seen.add(loaded.externalId);
                    records.push(loaded);
                }
                catch (error) {
                    errors.push({ message: redactSecrets(error instanceof Error ? error.message : String(error), secrets) });
                }
            }
        }
        catch (error) {
            errors.push({ message: redactSecrets(`SAM.gov NAICS ${naics ?? 'all'}: ${error instanceof Error ? error.message : String(error)}`, secrets) });
        }
    };
    if (!options.naics.length)
        await pullQuery();
    else
        for (const code of options.naics)
            await pullQuery(code);
    return {
        batch: { sourceRunId: `sam-api:${postedFrom}_to_${postedTo}`, receivedAt: retrievedAt, records, errors: [] },
        errors
    };
}
async function loadDirectory(directory) {
    const base = path.basename(directory);
    if ((base === 'opportunities' || base === 'bundles') && await isRunDirectory(path.dirname(directory))) {
        return loadRunDirectory(path.dirname(directory));
    }
    if (await isRunDirectory(directory))
        return loadRunDirectory(directory);
    const runsDir = path.join(directory, 'runs');
    if (await isDirectory(runsDir)) {
        const names = (await readdir(runsDir)).sort();
        const runs = [];
        for (const name of names) {
            const candidate = path.join(runsDir, name);
            if (await isRunDirectory(candidate))
                runs.push(candidate);
        }
        if (!runs.length)
            throw new Error(`No Foundry run directories under ${runsDir}`);
        return loadRunDirectory(runs[runs.length - 1]);
    }
    const latestReport = path.join(directory, 'latest-report.json');
    if (await isFile(latestReport))
        return loadFile(latestReport);
    return loadJsonRecords(directory, path.basename(directory), 'foundry-report');
}
async function loadFile(file) {
    const json = await readJson(file);
    if (isRecord(json) && json.schema_version === 'universal-opportunity-run-manifest-v2' && await isRunDirectory(path.dirname(file))) {
        return loadRunDirectory(path.dirname(file));
    }
    if (isRecord(json) && Array.isArray(json.opportunitiesData)) {
        return recordsBatch(path.basename(file), 'sam-api', json.opportunitiesData, receivedAtFrom(json));
    }
    if (Array.isArray(json))
        return recordsBatch(path.basename(file, '.json'), 'foundry-report', json);
    if (isRecord(json) && Array.isArray(json.opportunities) && !json.opportunity_id) {
        return recordsBatch(path.basename(file, '.json'), 'foundry-report', json.opportunities, receivedAtFrom(json));
    }
    if (isRecord(json) && Array.isArray(json.records)) {
        return recordsBatch(path.basename(file, '.json'), 'foundry-report', json.records, receivedAtFrom(json));
    }
    return recordsBatch(path.basename(file, '.json'), 'foundry-report', [json]);
}
async function loadRunDirectory(runDir) {
    const manifest = await readOptionalJson(path.join(runDir, 'manifest.json'));
    const receivedAt = isRecord(manifest) && typeof manifest.generated_at === 'string' ? manifest.generated_at : undefined;
    const opportunityDir = path.join(runDir, 'opportunities');
    const bundleDir = path.join(runDir, 'bundles');
    const sourceDir = await isDirectory(opportunityDir) ? opportunityDir : bundleDir;
    const files = await jsonFiles(sourceDir);
    const intelligenceDir = path.join(runDir, 'intelligence');
    const records = [];
    const errors = [];
    for (const file of files) {
        try {
            const json = await readJson(file);
            const intelligence = extractIntelligence(json) ?? await readSidecarIntelligence(intelligenceDir, opportunityIdOf(json));
            const loaded = opportunityFromFoundry(json, { origin: 'foundry-run', retrievedAt: receivedAt });
            records.push(intelligence ? { ...loaded, intelligence } : loaded);
        }
        catch (error) {
            errors.push({ message: `${path.basename(file)}: ${error instanceof Error ? error.message : String(error)}` });
        }
    }
    return { sourceRunId: path.basename(runDir), receivedAt, records, errors };
}
async function loadJsonRecords(directory, sourceRunId, origin) {
    const files = (await jsonFiles(directory)).filter((file) => !['manifest.json', 'run.json', 'latest-report.json'].includes(path.basename(file)));
    if (!files.length)
        throw new Error(`No Foundry opportunity JSON in ${directory}`);
    const records = [];
    const errors = [];
    for (const file of files) {
        try {
            records.push(opportunityFromFoundry(await readJson(file), { origin }));
        }
        catch (error) {
            errors.push({ message: `${path.basename(file)}: ${error instanceof Error ? error.message : String(error)}` });
        }
    }
    return { sourceRunId, records, errors };
}
function recordsBatch(sourceRunId, origin, items, receivedAt) {
    const records = [];
    const errors = [];
    items.forEach((item, index) => {
        try {
            const itemOrigin = origin === 'foundry-report' && isRawSamNotice(item) ? 'sam-api' : origin;
            records.push(opportunityFromFoundry(item, { origin: itemOrigin, retrievedAt: receivedAt }));
        }
        catch (error) {
            errors.push({ message: `record ${index + 1}: ${error instanceof Error ? error.message : String(error)}` });
        }
    });
    return { sourceRunId, receivedAt, records, errors };
}
function toPublicOpportunity(input, retrievedAtFallback) {
    const sourceName = input.sourceName.trim();
    const official = isSamGovSource(sourceName);
    const system = official ? 'SAM.gov' : (sourceName || 'unknown');
    const externalId = input.externalId.trim();
    const title = collapse(input.title);
    if (!externalId)
        throw new Error(title ? `Missing notice id for "${title}"` : 'Missing notice id');
    if (!title)
        throw new Error(externalId ? `Missing title for ${externalId}` : 'Missing title');
    const url = input.sourceUrl?.trim() || (official ? `https://sam.gov/opp/${encodeURIComponent(externalId)}/view` : '');
    if (!url)
        throw new Error(`Missing source URL for ${externalId}`);
    const issuer = collapse(input.issuer || '') || (official ? 'Unknown agency' : 'Unknown issuer');
    const jurisdiction = collapse(input.jurisdiction || '') || (official ? 'United States' : 'Unknown');
    const description = proseDescription(input.description);
    const typeText = input.typeText || '';
    let summary = description || composeSummary({ title, typeText, issuer, externalId, naics: input.naics, setAside: input.setAside });
    if (/award notice/i.test(typeText) && !/award notice/i.test(`${title} ${summary}`))
        summary = `Award Notice. ${summary}`;
    if (/cancell?ed/i.test(`${input.statusText ?? ''} ${typeText}`) && !/cancell?ed/i.test(`${title} ${summary}`))
        summary = `Cancelled. ${summary}`;
    const provenance = {
        system,
        authority: official ? 'official' : 'aggregator',
        url,
        retrievedAt: input.retrievedAt || retrievedAtFallback,
        ...(input.contentHash ? { contentHash: input.contentHash } : {}),
        ...(input.attachments.length ? { attachmentUrls: [...input.attachments].sort() } : {})
    };
    const registrations = new Set(input.registrations);
    if (official)
        registrations.add('SAM.gov');
    const amount = input.amountMax ?? input.amountMin;
    const opportunity = {
        schemaVersion: '1.0.0',
        eventId: `${sourcePrefix(system)}:${externalId}`,
        externalId,
        title,
        issuer,
        jurisdiction,
        opportunityType: classifyOpportunityType(typeText, title),
        ...(input.publishedDate ? { publicationDate: input.publishedDate } : {}),
        ...(input.updateDate ? { updateDate: input.updateDate } : {}),
        ...(input.deadline ? { deadline: input.deadline } : {}),
        ...(amount !== undefined ? { value: { amount, currency: input.currency || 'USD', ...(rangeText(input) ? { text: rangeText(input) } : {}) } } : {}),
        eligibility: input.eligibility,
        ...(input.setAside ? { setAside: input.setAside } : {}),
        ...(input.location ? { location: input.location } : {}),
        submissionMethod: official ? 'SAM.gov' : undefined,
        requiredRegistrations: [...registrations],
        summary,
        rawText: buildRawText(input, description),
        provenance: [provenance]
    };
    if (!opportunity.submissionMethod)
        delete opportunity.submissionMethod;
    return opportunity;
}
function intermediateFromUnknown(input) {
    const record = unwrapOpportunity(input);
    if (isRawSamNotice(record))
        return intermediateFromRawSam(record);
    return intermediateFromCanonicalOrNormalized(record);
}
function unwrapOpportunity(input) {
    if (!isRecord(input))
        throw new Error('Opportunity JSON must be an object');
    if (isRecord(input.opportunity))
        return input.opportunity;
    return input;
}
function intermediateFromCanonicalOrNormalized(record) {
    const metadata = isRecord(record.metadata) ? record.metadata : record;
    const samRaw = isRecord(metadata.sam_raw) ? metadata.sam_raw : isRawSamNotice(metadata) ? metadata : {};
    const provenance = isRecord(record.provenance) ? record.provenance : {};
    const externalId = text(record.external_id) || text(provenance.source_record_id) || text(metadata.external_id) || text(metadata.record_id) || text(samRaw.noticeId) || text(record.noticeId);
    const sourceName = text(record.source) || text(provenance.source_name) || text(metadata.source) || 'unknown';
    const sourceUrl = text(samRaw.uiLink) || text(metadata.source_url) || text(provenance.source_url) || text(record.source_url) || text(metadata.submission_path);
    const deadline = firstDate(samRaw.responseDeadLine, metadata.deadline, record.deadline);
    const published = firstDate(record.published_date, metadata.published_date, samRaw.postedDate);
    const updated = firstDate(metadata.update_date, samRaw.modifiedDate, record.update_date);
    const naics = uniqueNaics(record.sectors, metadata.naics, metadata.sectors, metadata.naicsCode, samRaw.naicsCode, samRaw.naicsCodes);
    const contacts = contactsFrom(metadata.contact ?? metadata.pointOfContact ?? samRaw.pointOfContact);
    const attachments = uniqueStrings(record.attachments, metadata.attachments, samRaw.resourceLinks);
    return {
        externalId: externalId ?? '',
        title: text(record.title) || text(metadata.title) || '',
        sourceName,
        sourceUrl,
        issuer: text(record.issuer) || text(metadata.issuer) || text(metadata.agency) || text(samRaw.fullParentPathName) || text(samRaw.department),
        jurisdiction: text(record.jurisdiction) || text(metadata.jurisdiction),
        typeText: [text(record.opportunity_type), text(record.type), text(metadata.type), text(metadata.opportunity_type), text(samRaw.type), text(samRaw.baseType)].filter(Boolean).join(' '),
        statusText: text(record.status) || text(metadata.status) || text(samRaw.active),
        publishedDate: published,
        updateDate: updated,
        deadline,
        naics,
        psc: text(metadata.psc) || text(samRaw.classificationCode),
        setAside: text(metadata.set_aside) || text(samRaw.typeOfSetAsideDescription) || text(samRaw.typeOfSetAside),
        description: text(metadata.description) || text(samRaw.description) || text(record.description),
        attachments,
        location: formatLocation(metadata.location ?? samRaw.placeOfPerformance),
        contacts,
        solicitationNumber: text(metadata.solicitation_number) || text(samRaw.solicitationNumber),
        office: text(metadata.office) || text(samRaw.office),
        eligibility: stringList(record.eligibility ?? metadata.eligibility),
        registrations: stringList(metadata.registration_requirements),
        amountMin: amount(record.amount_min ?? metadata.amount_min),
        amountMax: amount(record.amount_max ?? metadata.amount_max ?? awardAmount(samRaw.award)),
        currency: text(record.currency) || text(metadata.currency) || undefined,
        retrievedAt: text(provenance.retrieved_at) || text(metadata.retrieved_at) || text(metadata.source_checked_at),
        contentHash: text(provenance.content_hash) || text(metadata.content_hash),
        activeText: text(samRaw.active) || text(metadata.active)
    };
}
function intermediateFromRawSam(record) {
    const noticeId = text(record.noticeId) ?? '';
    const uiLink = text(record.uiLink) || (noticeId ? `https://sam.gov/opp/${encodeURIComponent(noticeId)}/view` : undefined);
    return intermediateFromCanonicalOrNormalized({
        external_id: noticeId,
        title: text(record.title),
        source: 'SAM.gov',
        source_url: uiLink,
        issuer: text(record.fullParentPathName) || text(record.department),
        jurisdiction: 'United States',
        type: text(record.type) || text(record.baseType),
        status: activeStatus(record.active),
        published_date: text(record.postedDate),
        deadline: text(record.responseDeadLine),
        naics: naicsList(record.naicsCode, record.naicsCodes),
        psc: text(record.classificationCode),
        set_aside: text(record.typeOfSetAsideDescription) || text(record.typeOfSetAside),
        description: text(record.description),
        attachments: stringList(record.resourceLinks),
        solicitation_number: text(record.solicitationNumber),
        office: text(record.office),
        location: record.placeOfPerformance,
        contact: record.pointOfContact,
        amount_max: awardAmount(record.award),
        sam_raw: record
    });
}
function dispositionDecision(record, allow) {
    if (!allow.length || record.origin === 'sam-api')
        return { ok: true };
    if (!record.intelligence)
        return { ok: false, reason: 'disposition_missing' };
    const stage = record.intelligence.stage.toUpperCase();
    const disposition = record.intelligence.disposition.toUpperCase();
    const ok = allow.some((item) => item.toUpperCase() === stage || item.toUpperCase() === disposition);
    return ok ? { ok: true } : { ok: false, reason: 'disposition' };
}
function naicsDecision(codes, allow) {
    if (!allow.length)
        return { ok: true };
    if (!codes.length)
        return { ok: false, reason: 'naics_missing' };
    return codes.some((code) => allow.includes(code)) ? { ok: true } : { ok: false, reason: 'naics' };
}
function extractIntelligence(input) {
    if (!isRecord(input))
        return undefined;
    for (const candidate of [input.intelligence_output, input.intelligence, input]) {
        if (!isRecord(candidate) || !isRecord(candidate.maturity))
            continue;
        const stage = text(candidate.maturity.stage);
        const disposition = text(candidate.maturity.disposition);
        if (!stage && !disposition)
            continue;
        return { stage: stage || disposition || '', disposition: disposition || stage || '' };
    }
    return undefined;
}
function opportunityIdOf(input) {
    const record = unwrapOpportunity(input);
    return text(record.opportunity_id) || (isRecord(input) ? text(input.opportunity_id) : undefined);
}
async function readSidecarIntelligence(directory, opportunityId) {
    if (!opportunityId || opportunityId.includes('/') || opportunityId.includes('\\') || opportunityId.includes('..'))
        return undefined;
    const file = path.join(directory, `${opportunityId}.json`);
    if (!await isFile(file))
        return undefined;
    return extractIntelligence(await readJson(file));
}
function classifyOpportunityType(typeText, title) {
    const blob = `${typeText} ${title}`;
    const rules = [
        [/\bSTTR\b/i, 'STTR'],
        [/\bSBIR\b/i, 'SBIR'],
        [/\bBAA\b|broad agency announcement/i, 'BAA'],
        [/\bCSO\b|commercial solutions opening/i, 'CSO'],
        [/\bOTA\b|other transaction/i, 'OTA'],
        [/\bIFB\b|invitation for bids?/i, 'IFB'],
        [/\bRFQ\b|request for quotations?/i, 'RFQ'],
        [/\bRFI\b|request for information/i, 'RFI'],
        [/sources sought/i, 'SOURCES_SOUGHT'],
        [/cooperative agreement/i, 'COOPERATIVE_AGREEMENT'],
        [/\bgrants?\b/i, 'GRANT'],
        [/\bprizes?\b/i, 'PRIZE'],
        [/\bchallenges?\b/i, 'CHALLENGE'],
        [/forecast|presolicitation/i, 'FORECAST'],
        [/licen[cs]ing/i, 'LICENSING'],
        [/partnership/i, 'PARTNERSHIP'],
        [/subcontract/i, 'SUBCONTRACT'],
        [/solicitation|combined synopsis|\bRFP\b|request for proposals?/i, 'RFP']
    ];
    for (const [pattern, type] of rules)
        if (pattern.test(blob))
            return type;
    return 'OTHER';
}
function buildRawText(input, description) {
    const lines = [
        `Title: ${collapse(input.title)}`,
        `Notice ID: ${input.externalId}`,
        input.solicitationNumber ? `Solicitation: ${input.solicitationNumber}` : undefined,
        input.typeText ? `Type: ${collapse(input.typeText)}` : undefined,
        input.issuer ? `Agency: ${collapse(input.issuer)}` : undefined,
        input.office ? `Office: ${input.office}` : undefined,
        input.naics.length ? `NAICS: ${input.naics.join(', ')}` : undefined,
        input.psc ? `PSC: ${input.psc}` : undefined,
        input.setAside ? `Set-aside: ${input.setAside}` : undefined,
        input.statusText ? `Status: ${input.statusText}` : undefined,
        input.activeText ? `Active: ${input.activeText}` : undefined,
        input.location ? `Location: ${input.location}` : undefined,
        description ? `Description: ${description}` : input.description ? `Description URL: ${input.description}` : undefined,
        ...input.contacts.map((contact) => `Contact: ${[contact.name, contact.type, contact.email, contact.phone].filter(Boolean).join(' | ')}`)
    ];
    return lines.filter((line) => Boolean(line)).join('\n');
}
function composeSummary(input) {
    const typeLabel = collapse(input.typeText) || 'opportunity';
    const naics = input.naics.length ? ` NAICS ${input.naics.join(', ')}.` : '';
    const setAside = input.setAside ? ` Set-aside: ${input.setAside}.` : '';
    return `${input.title}. ${typeLabel} issued by ${input.issuer}. Notice ${input.externalId}.${naics}${setAside}`;
}
function proseDescription(value) {
    if (!value)
        return undefined;
    const trimmed = collapse(value);
    if (/^https?:\/\//i.test(trimmed))
        return undefined;
    return trimmed;
}
function formatLocation(value) {
    if (typeof value === 'string')
        return collapse(value) || undefined;
    if (!isRecord(value))
        return undefined;
    const city = nestedText(value.city, 'name') || text(value.city);
    const state = nestedText(value.state, 'code') || text(value.state);
    const postal = text(value.postal_code) || text(value.zip) || text(value.postalCode);
    const country = nestedText(value.country, 'code') || text(value.country);
    const parts = [city, state, postal, country].map((part) => part?.trim()).filter(Boolean);
    return parts.length ? parts.join(', ') : undefined;
}
function contactsFrom(value) {
    const items = Array.isArray(value) ? value : value ? [value] : [];
    const contacts = items.filter(isRecord).map((item) => ({
        name: text(item.fullname) || text(item.fullName) || text(item.name),
        email: text(item.email),
        phone: text(item.phone),
        type: text(item.type)
    })).filter((contact) => contact.name || contact.email || contact.phone);
    contacts.sort((a, b) => `${a.type ?? ''}:${a.name ?? ''}:${a.email ?? ''}`.localeCompare(`${b.type ?? ''}:${b.name ?? ''}:${b.email ?? ''}`));
    return contacts;
}
function firstDate(...values) {
    for (const value of values) {
        const parsed = dateText(value);
        if (parsed)
            return parsed;
    }
    return undefined;
}
function dateText(value) {
    const raw = text(value);
    if (!raw)
        return undefined;
    const stamp = Date.parse(raw);
    if (Number.isNaN(stamp))
        return undefined;
    return raw;
}
function amount(value) {
    if (typeof value === 'number' && Number.isFinite(value) && value >= 0)
        return value;
    if (typeof value !== 'string')
        return undefined;
    const cleaned = value.replace(/[$,\s]/g, '');
    if (!cleaned)
        return undefined;
    const parsed = Number(cleaned);
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined;
}
function awardAmount(value) {
    if (!isRecord(value))
        return undefined;
    return amount(value.amount);
}
function rangeText(input) {
    if (input.amountMin === undefined || input.amountMax === undefined || input.amountMin === input.amountMax)
        return undefined;
    return `${input.amountMin}-${input.amountMax} ${input.currency || 'USD'}`;
}
function activeStatus(value) {
    if (typeof value === 'boolean')
        return value ? 'open' : 'inactive';
    const raw = text(value);
    if (!raw)
        return 'open';
    if (/^(no|false|inactive|n)$/i.test(raw))
        return 'inactive';
    return 'open';
}
function isSamGovSource(sourceName) {
    const normalized = sourceName.toLowerCase().replace(/[\s._-]+/g, '');
    return normalized === 'samgov' || normalized === 'apisamgov';
}
function sourcePrefix(system) {
    if (system === 'SAM.gov')
        return 'sam';
    const slug = system.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
    return slug || 'source';
}
export function extractNaicsCodes(value) {
    const found = new Set();
    collectNaics(value, found);
    return [...found].sort();
}
function uniqueNaics(...values) {
    return [...new Set(values.flatMap((value) => extractNaicsCodes(value)))].sort();
}
function collectNaics(value, into) {
    if (typeof value === 'number' && Number.isFinite(value)) {
        addNaics(String(Math.trunc(value)), into);
        return;
    }
    if (typeof value === 'string') {
        addNaics(value, into);
        return;
    }
    if (Array.isArray(value)) {
        for (const item of value)
            collectNaics(item, into);
        return;
    }
    if (isRecord(value)) {
        if ('code' in value)
            collectNaics(value.code, into);
        if ('naicsCode' in value)
            collectNaics(value.naicsCode, into);
    }
}
function addNaics(value, into) {
    const trimmed = value.trim();
    if (/^\d{6}$/.test(trimmed)) {
        into.add(trimmed);
        return;
    }
    for (const match of trimmed.matchAll(/\b\d{6}\b/g))
        into.add(match[0]);
}
function naicsList(...values) {
    return uniqueNaics(...values);
}
function stringList(...values) {
    const found = [];
    for (const value of values) {
        if (typeof value === 'string' && value.trim())
            found.push(value.trim());
        else if (Array.isArray(value)) {
            for (const item of value)
                if (typeof item === 'string' && item.trim())
                    found.push(item.trim());
        }
    }
    return [...new Set(found)].sort();
}
function uniqueStrings(...values) {
    return stringList(...values);
}
function nestedText(value, key) {
    if (isRecord(value))
        return text(value[key]);
    return text(value);
}
function text(value) {
    if (typeof value === 'string') {
        const trimmed = value.trim();
        return trimmed || undefined;
    }
    if (typeof value === 'number' && Number.isFinite(value))
        return String(value);
    return undefined;
}
function collapse(value) {
    return value.trim().replace(/\s+/g, ' ');
}
function receivedAtFrom(record) {
    return text(record.generated_at) || text(record.retrieved_at);
}
function isRawSamNotice(value) {
    return isRecord(value) && typeof value.noticeId === 'string' && value.opportunity_id == null && value.external_id == null && !isRecord(value.opportunity);
}
function isReceipt(value) {
    return isRecord(value) && typeof value.eventId === 'string' && typeof value.canonicalHash === 'string' && isRecord(value.result) && typeof value.result.disposition === 'string';
}
function isRecord(value) {
    return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}
function integerEnv(value, fallback) {
    if (!value?.trim())
        return fallback;
    const parsed = Number(value);
    if (!Number.isFinite(parsed))
        throw new Error(`Invalid number: ${value}`);
    return Math.trunc(parsed);
}
async function readJson(file) {
    try {
        return JSON.parse(await readFile(file, 'utf8'));
    }
    catch (error) {
        throw new Error(`Unable to read ${path.basename(file)}: ${error instanceof Error ? error.message : String(error)}`);
    }
}
async function readOptionalJson(file) {
    if (!await isFile(file))
        return undefined;
    return readJson(file);
}
async function jsonFiles(directory) {
    const names = await readdir(directory);
    return names.filter((name) => name.endsWith('.json')).sort().map((name) => path.join(directory, name));
}
async function isRunDirectory(directory) {
    return await isDirectory(path.join(directory, 'opportunities')) || await isDirectory(path.join(directory, 'bundles'));
}
async function isDirectory(file) {
    try {
        return (await stat(file)).isDirectory();
    }
    catch {
        return false;
    }
}
async function isFile(file) {
    try {
        return (await stat(file)).isFile();
    }
    catch {
        return false;
    }
}

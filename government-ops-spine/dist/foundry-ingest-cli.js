import path from 'node:path';
import { parseArgs } from 'node:util';
import { fileURLToPath } from 'node:url';
import { Pool } from 'pg';
import { PostgresOpportunityRepository } from './postgres.js';
import { GovernmentOpsRuntime } from './runtime.js';
import { httpSink, parseDispositionList, parseNaicsList, runFoundryIngest, runtimeSink } from './foundry-bridge.js';
export async function runFoundryIngestCli(argv, io = {}) {
    const stdout = io.stdout ?? ((line) => console.log(line));
    const stderr = io.stderr ?? ((line) => console.error(line));
    const env = io.env ?? process.env;
    let values;
    let positionals;
    try {
        const parsed = parseArgs({
            args: argv,
            allowPositionals: true,
            strict: true,
            options: {
                path: { type: 'string' },
                pull: { type: 'boolean', default: false },
                naics: { type: 'string' },
                dispositions: { type: 'string' },
                'source-run-id': { type: 'string' },
                endpoint: { type: 'string' },
                'dry-run': { type: 'boolean', default: false },
                'posted-from': { type: 'string' },
                'posted-to': { type: 'string' },
                'lookback-days': { type: 'string' },
                limit: { type: 'string' },
                'max-pages': { type: 'string' },
                'notice-type': { type: 'string' },
                title: { type: 'string' },
                organization: { type: 'string' },
                help: { type: 'boolean', default: false }
            }
        });
        values = parsed.values;
        positionals = parsed.positionals;
    }
    catch (error) {
        stderr(error instanceof Error ? error.message : String(error));
        stderr(usage());
        return 2;
    }
    if (values.help) {
        stdout(usage());
        return 0;
    }
    const inputPath = optionString(values.path) ?? positionals[0];
    const pull = values.pull === true;
    if (!inputPath && !pull) {
        stderr(usage());
        return 2;
    }
    if (positionals.length > 1) {
        stderr('Pass one Foundry path.');
        return 2;
    }
    const apiKey = env.SAM_GOV_API_KEY?.trim() ?? '';
    if (pull && !apiKey) {
        stderr('SAM_GOV_API_KEY is required');
        return 2;
    }
    let request;
    try {
        const naics = parseNaicsList(optionString(values.naics) ?? env.FOUNDRY_INGEST_NAICS);
        const dispositions = parseDispositionList(optionString(values.dispositions) ?? env.FOUNDRY_INGEST_DISPOSITIONS);
        request = {
            path: inputPath,
            dispositions,
            naics,
            sourceRunId: optionString(values['source-run-id']),
            dryRun: values['dry-run'] === true,
            secrets: apiKey ? [apiKey] : [],
            pull: pull ? {
                apiKey,
                postedFrom: optionString(values['posted-from']) ?? env.SAM_GOV_POSTED_FROM,
                postedTo: optionString(values['posted-to']) ?? env.SAM_GOV_POSTED_TO,
                lookbackDays: numberOption(optionString(values['lookback-days']) ?? env.FOUNDRY_INGEST_LOOKBACK_DAYS, 1),
                limit: numberOption(optionString(values.limit) ?? env.FOUNDRY_INGEST_LIMIT, 100),
                maxPages: numberOption(optionString(values['max-pages']) ?? env.SAM_GOV_MAX_PAGES, 5),
                noticeType: optionString(values['notice-type']) ?? env.SAM_GOV_NOTICE_TYPE,
                title: optionString(values.title) ?? env.SAM_GOV_TITLE,
                organization: optionString(values.organization) ?? env.SAM_GOV_ORGANIZATION,
                endpoint: env.SAM_GOV_ENDPOINT,
                fetchImpl: io.fetchImpl,
                now: io.now,
                naics
            } : undefined
        };
    }
    catch (error) {
        stderr(error instanceof Error ? error.message : String(error));
        return 2;
    }
    if (!io.sink && !optionString(values.endpoint) && !env.SPINE_INGEST_URL && !env.DATABASE_URL) {
        stderr('No DATABASE_URL or SPINE_INGEST_URL set; posting to http://127.0.0.1:8099/api/opportunities/ingest');
    }
    const opened = io.sink ? undefined : await openSink(env, optionString(values.endpoint), io.fetchImpl, apiKey ? [apiKey] : []);
    const sink = io.sink ?? opened?.sink;
    if (!sink) {
        stderr('No intake sink is configured.');
        return 2;
    }
    try {
        const summary = await runFoundryIngest(sink, request);
        stdout(JSON.stringify(summary, null, 2));
        return summary.errors.length ? 1 : 0;
    }
    finally {
        await opened?.close();
    }
}
async function openSink(env, endpoint, fetchImpl, secrets) {
    const explicitEndpoint = endpoint ?? env.SPINE_INGEST_URL;
    if (explicitEndpoint)
        return { sink: httpSink(explicitEndpoint, fetchImpl, secrets), close: async () => { } };
    if (env.DATABASE_URL) {
        const pool = new Pool({ connectionString: env.DATABASE_URL });
        const runtime = new GovernmentOpsRuntime(new PostgresOpportunityRepository(pool));
        return { sink: runtimeSink(runtime), close: () => pool.end() };
    }
    return { sink: httpSink('http://127.0.0.1:8099', fetchImpl, secrets), close: async () => { } };
}
function optionString(value) {
    return typeof value === 'string' ? value : undefined;
}
function numberOption(value, fallback) {
    if (!value?.trim())
        return fallback;
    const parsed = Number(value);
    if (!Number.isFinite(parsed))
        throw new Error(`Invalid number: ${value}`);
    return Math.trunc(parsed);
}
function usage() {
    return `Usage: npm run ingest:foundry -- <path> [options]

Map Foundry canonical opportunities into the spine intake endpoint.
<path> may be a run directory, the opportunities/ folder, a runs/ parent
(the latest run is used), or latest-report.json.

Options:
  --path <path>              Same as the positional path
  --pull                     Fetch SAM.gov Opportunities API v2 (SAM_GOV_API_KEY)
  --naics <codes>            NAICS allow list (default 541512,541715; "any" disables)
  --dispositions <list>      Foundry maturity stage or disposition (default HUMAN_REVIEW; "any" disables)
  --source-run-id <id>       Override the intake sourceRunId
  --endpoint <url>           POST /api/opportunities/ingest instead of using DATABASE_URL
  --dry-run                  Map and filter without writing
  --posted-from <MM/dd/yyyy> SAM.gov postedFrom
  --posted-to <MM/dd/yyyy>   SAM.gov postedTo
  --lookback-days <n>        Window when posted dates are omitted (default 1)
  --limit <n>                SAM.gov page size (default 100, max 1000)
  --max-pages <n>            SAM.gov pages per query (default 5, max 50)
  --notice-type <ptype>      SAM.gov ptype filter
  --title <text>             SAM.gov title filter
  --organization <name>      SAM.gov organizationName filter
  --help

Direct SAM.gov pulls have no Foundry intelligence label, so the disposition
filter is not applied to them. NAICS filtering still applies.
This command only ingests public notices. It does not submit bids, send email,
or contact anyone.`;
}
const cliPath = fileURLToPath(import.meta.url);
const invokedDirectly = process.argv[1] && path.resolve(process.argv[1]) === cliPath;
if (invokedDirectly) {
    runFoundryIngestCli(process.argv.slice(2)).then((code) => process.exit(code)).catch((error) => {
        console.error(error instanceof Error ? error.message : String(error));
        process.exit(1);
    });
}

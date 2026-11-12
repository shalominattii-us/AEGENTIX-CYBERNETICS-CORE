# AEGENTIX Government Operations Spine

Ports authoritative public opportunities through Cybercore into Treasury Labs and the Infinite Brain OS.

## Implemented

- Canonical opportunity and provenance contracts
- Deterministic normalization, hashing, deduplication, amendment detection, and status classification
- Treasury Labs requirement analysis and build-specification generation
- Infinite Brain task graph across OpenClaw, Nemotron, Docker, Hermes, and Manus
- PostgreSQL persistence migration and concrete repository adapter
- Transactional Cybercore outbox with HTTP publisher
- Framework-neutral runtime handlers for ingest, analyze, and state routes
- Automatic analysis, specification, and planning after active opportunity ingestion
- Capability matching boundary
- Explicit authorization guard for external submissions, filings, commitments, and representations
- Foundry SAM.gov intake bridge: canonical run artifacts and an optional direct Opportunities API v2 pull, filtered and ingested through the existing intake endpoint

## Runtime routes

- `POST /api/opportunities/ingest`
- `POST /api/opportunities/:eventId/analyze`
- `GET /api/opportunities/:eventId/state`

## Run locally

```bash
cd government-ops-spine
npm install
npm test
```

## Foundry SAM.gov intake

[Foundry](https://github.com/eaglecrat/Foundry) stays a separate MIT-licensed repository. This package does not vendor it. Foundry's `foundry-opportunities` command reads the SAM.gov Opportunities API and writes canonical opportunity JSON under `var/opportunities/runs/<run-id>/opportunities/`, Cybercore intelligence labels under `intelligence/`, and a normalized `latest-report.json`. The spine bridge maps those records onto `PublicOpportunity` and posts them through `OpportunityIntakeService` / `POST /api/opportunities/ingest`.

```bash
# In the Foundry checkout. Do not commit the key.
export SAM_GOV_API_KEY="your-sam-gov-key"
foundry-opportunities \
  --output-root var/opportunities/runs \
  --report-path var/opportunities/latest-report.json

# In this package, with DATABASE_URL pointing at the spine database.
cd government-ops-spine
npm run ingest:foundry -- /path/to/Foundry/var/opportunities
```

A path that contains `runs/` uses the latest run directory, because that directory carries intelligence labels. Pass a run directory, its `opportunities/` folder, or `latest-report.json` directly when you want a specific input.

| Foundry / SAM.gov field | Spine field |
| --- | --- |
| `external_id`, `provenance.source_record_id`, or `noticeId` | `externalId` and stable `eventId` (`sam:<noticeId>` for SAM.gov) |
| `title` | `title` |
| `issuer` / `fullParentPathName` | `issuer` |
| `jurisdiction` | `jurisdiction` (`United States` when SAM.gov omits it) |
| `opportunity_type` / `type`, with title keywords | `opportunityType` |
| `published_date` / `postedDate` | `publicationDate` |
| `sam_raw.responseDeadLine`, otherwise `deadline` | `deadline` |
| `modifiedDate` | `updateDate` |
| `amount_min` / `amount_max` or award amount | `value` |
| `eligibility` | `eligibility` |
| `set_aside` / `typeOfSetAsideDescription` | `setAside` |
| `location` / `placeOfPerformance` | `location` |
| SAM.gov source | `submissionMethod` and `requiredRegistrations` include `SAM.gov` |
| prose `description`, or a composed notice line | `summary` |
| notice text, NAICS, PSC, solicitation, office, public contacts | `rawText` |
| SAM.gov `uiLink` or `source_url`, `retrieved_at`, attachments | `provenance` (`system: SAM.gov`, `authority: official`, `url`, `retrievedAt`, `attachmentUrls`) |
| any other source name | `authority: aggregator` |

`authority: official` is set only for SAM.gov API records. `parseOpportunity` then does not add the non-official provenance risk. Other sources stay `aggregator`, so review stays required. Description URLs are kept in `rawText` and are not downloaded.

Filters, both configurable:

- Intelligence disposition defaults to maturity stage `HUMAN_REVIEW`. `FORECAST_MONITOR`, `CLOSED`, and the disposition strings such as `REQUIRES_HUMAN_DECISION` are accepted. Records in a Foundry run or report that have no intelligence label are skipped. Use `--dispositions any` to keep them.
- NAICS defaults to `541512` and `541715`. A record matches when any of its codes is in the list. Use `--naics any` to disable the filter.
- Direct SAM.gov pulls have no Foundry intelligence label, so the disposition filter is not applied to them. The NAICS filter still is.

Re-ingesting the same `noticeId` uses the spine hash. `retrievedAt` is stored and ignored by the hash, and attachment URLs are sorted, so an unchanged notice returns `unchanged` instead of a new row. A real content change, such as a new deadline, increments the revision.

```bash
npm run ingest:foundry -- /path/to/run --dry-run
npm run ingest:foundry -- /path/to/latest-report.json --dispositions any
npm run ingest:foundry -- --pull --naics 541512,541715
npm run ingest:foundry:schedule
```

`npm run ingest:foundry:schedule` repeats that ingest in its own process. It needs `DATABASE_URL` and uses `FOUNDRY_INGEST_INTERVAL_MS` (default one hour). Set `FOUNDRY_INGEST_ENABLED=true` to run the same loop inside `server.js` instead. Direct pulls read `SAM_GOV_API_KEY` from the environment. Each NAICS query stops after `SAM_GOV_MAX_PAGES` pages (default 5, 100 notices per page) so a broad window cannot page without a bound. Raise it with `--max-pages` or `SAM_GOV_MAX_PAGES` when a window is larger than that. The key is not written to source, fixtures, or logs. If neither `DATABASE_URL` nor `SPINE_INGEST_URL` is set, the CLI says so and posts to `http://127.0.0.1:8099/api/opportunities/ingest`.

Live intake does not need that local process. The standalone Worker in `edge-intake/` pulls SAM.gov on a Cloudflare cron and stores notices in D1. The spine pulls the outbox outbound with `npm run ingest:edge`. See DEPLOYMENT.md for the network boundary and deploy steps. Leave the local scheduler off once the Worker is deployed.

## Next

- Bind handlers to the deployed Cybercore HTTP framework
- Schedule and supervise the outbox worker
- Add GitHub, Docker, deployment, document, CAD, and patent capability indexers
- Add durable approval records and reviewer identities
- Add patent and proposal workbenches behind approval gates

## Safety boundary

This package may generate internal drafts, specifications, simulations, and execution plans. It must not submit bids, grants, patent filings, financial commitments, or external representations without explicit human authorization. The Foundry bridge only calls the internal ingest path. It does not submit offers, send email, or contact contracting officers. `assertExternalActionAuthorized` is unchanged.

Still blocked after this bridge:

- Bid, grant, patent, and other external submissions
- Correspondence delivery and any outreach
- Downloading SAM.gov description or attachment bodies, so official notices whose description is only a URL can still be flagged for attachment review
- Live SAM.gov calls in CI; those need an operator-supplied `SAM_GOV_API_KEY` and were not executed here

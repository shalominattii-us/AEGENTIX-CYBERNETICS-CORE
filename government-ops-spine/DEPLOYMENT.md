# Deployment Integration

## Start

```bash
cd government-ops-spine
cp .env.example .env
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:8099/health
```

## Opportunity endpoints

- `POST /api/opportunities/ingest`
- `POST /api/opportunities/{eventId}/analyze`
- `GET /api/opportunities/{eventId}/state`

## Capability and indexing endpoints

- `GET /api/capabilities`
- `GET /api/indexing/health`
- `POST /api/indexing/run`

The API container mounts the Docker socket read-only and mounts `${AEGENTIX_WORKSPACE:-..}` at `/workspace` read-only. Set `CAPABILITY_INDEX_ENABLED`, `CAPABILITY_INDEX_INTERVAL_MS`, and `CAPABILITY_MAX_FILES` to control scheduled discovery.

## Controlled correspondence endpoints

- `POST /api/correspondence/drafts`
- `GET /api/correspondence/{draftId}`
- `POST /api/correspondence/{draftId}/approve`

A valid organizational mailbox is required. Approval requires a single-message `AEGENTIX-AUTH-...` token. Tokens are stored only as SHA-256 hashes. This slice intentionally does not expose a send endpoint; provider delivery remains blocked until a separately authorized transport is configured.

## Foundry SAM.gov bridge

Foundry remains a separate checkout. The spine reads its artifacts or, when Foundry is not running, pulls the SAM.gov Opportunities API v2 directly. Neither path submits bids, sends email, or contacts anyone.

```bash
# Foundry checkout
export SAM_GOV_API_KEY="your-sam-gov-key"   # shell or secret store only; never commit it
foundry-opportunities \
  --output-root var/opportunities/runs \
  --report-path var/opportunities/latest-report.json

# Spine database already up
cd government-ops-spine
export DATABASE_URL="postgresql://aegentix:${POSTGRES_PASSWORD}@127.0.0.1:5432/aegentix"
npm run ingest:foundry -- /path/to/Foundry/var/opportunities
```

`var/opportunities` selects the latest run under `runs/`, which is the input that includes Cybercore intelligence labels. `latest-report.json` is the normalized daily report. By default only `HUMAN_REVIEW` records whose NAICS is `541512` or `541715` are ingested. Override with `--dispositions` and `--naics` (`any` disables that filter). Report rows without an intelligence label are skipped unless `--dispositions any` is set.

Direct pull, no Foundry process:

```bash
export SAM_GOV_API_KEY="your-sam-gov-key"
npm run ingest:foundry -- --pull --naics 541512,541715
```

Direct pulls are not Cybercore-scored, so the disposition filter does not apply to them. NAICS filtering still applies. Scheduled ingest uses the same mapping:

```bash
export DATABASE_URL="postgresql://aegentix:${POSTGRES_PASSWORD}@127.0.0.1:5432/aegentix"
export FOUNDRY_INGEST_PATH=/path/to/Foundry/var/opportunities
export FOUNDRY_INGEST_INTERVAL_MS=3600000
npm run ingest:foundry:schedule
```

Set `FOUNDRY_INGEST_ENABLED=true` to run that loop inside the API process instead. Docker Compose keeps it off the default stack and starts it only with the `foundry` profile:

```bash
FOUNDRY_DATA_DIR=/path/to/Foundry/var/opportunities \
FOUNDRY_INGEST_PATH=/foundry \
SAM_GOV_API_KEY="your-sam-gov-key" \
docker compose --profile foundry up -d --build
```

The key is interpolated from the environment into the `foundry-ingest` container. Do not commit `.env` with a real key. `.env.example` leaves `SAM_GOV_API_KEY` empty. The profile process exits until `FOUNDRY_INGEST_PATH` or `SAM_GOV_API_KEY` is set. Point `FOUNDRY_INGEST_PATH` at `/foundry` when the Foundry `var/opportunities` directory is mounted there.

What stays blocked:

- `assertExternalActionAuthorized` still rejects unauthenticated `submit_offer`, `file_patent`, `commit_funds`, and `external_representation`
- The bridge has no send, bid, or contact path
- SAM.gov description and attachment files are not fetched, so requirement extraction can still require human review when the description is only a URL
- A live SAM.gov call is not part of `npm test`

## Edge intake worker

Live SAM.gov intake runs in a standalone Cloudflare Worker, `government-ops-spine/edge-intake`. Nothing on the user's machine has to stay up for the pull. The Worker is TypeScript, not Rust. The mapping, NAICS filter, provenance rules, and canonical hash are the same modules the Node bridge uses (`foundry-bridge.ts`, `sam-gov.ts`, `intake.ts`). A second Rust port would drift from those tests. Workers TypeScript also has the supported D1, Cron Trigger, and Wrangler test path.

### Network boundary

```text
Internet
  |  GET /health                         public, no records
  |  POST /api/opportunities/ingest      Bearer INGEST_TOKEN only
  v
opportunity-intake Worker
  |  cron, hourly                        outbound HTTPS to api.sam.gov only
  |  D1 binding                          private; not an HTTP route
  v
D1 database opportunity-intake

Node spine (optional, on a private network)
  |  outbound HTTPS to api.cloudflare.com  D1 query API
  v
local Postgres
```

The Worker does not open a route to Postgres, the Node process, or any admin or record-listing API. There is no Cloudflare Tunnel and no published database port. The spine, when used, dials Cloudflare. Cloudflare does not dial the spine. Hyperdrive is not used, because it would require Postgres to be reachable from Cloudflare. A Queue consumer is not used, because a consumer Worker would still have to call inward to reach the Node pipeline. Downstream parsing, specifications, matching, and rendering stay in the Node spine.

`assertExternalActionAuthorized` is unchanged. The Worker does not submit bids, send email, or contact anyone. Its only outbound call is the SAM.gov Opportunities API during the cron.

### Create resources and deploy

Do this in the Cloudflare account. This repository does not create the resources.

```bash
cd government-ops-spine/edge-intake
npm install
npx wrangler login
npx wrangler d1 create opportunity-intake
```

Copy the printed `database_id` into `wrangler.jsonc`, replacing `00000000-0000-4000-8000-000000000001`. Then:

```bash
npx wrangler d1 migrations apply opportunity-intake --remote
printf '%s' 'your-sam-gov-key' | npx wrangler secret put SAM_GOV_API_KEY
printf '%s' 'a-long-random-ingest-token' | npx wrangler secret put INGEST_TOKEN
npx wrangler deploy
```

Secrets are not in `wrangler.jsonc` or git. Cron is `0 * * * *` (hourly). NAICS defaults to `541512,541715` and the Foundry disposition filter defaults to `HUMAN_REVIEW`. Direct SAM.gov rows have no Foundry label, so that filter does not drop them. Change the non-secret filters in the `vars` block.

Local development uses a simulated D1 and does not touch the account:

```bash
cp .dev.vars.example .dev.vars   # fill SAM_GOV_API_KEY and INGEST_TOKEN locally; do not commit .dev.vars
npx wrangler d1 migrations apply opportunity-intake --local
npm run dev
curl http://127.0.0.1:8787/health
curl -X POST http://127.0.0.1:8787/api/opportunities/ingest \
  -H "authorization: Bearer $INGEST_TOKEN" \
  -H "content-type: application/json" \
  --data @../fixtures/foundry/workspace/latest-report.json
```

Foundry, or any webhook, posts a run directory's JSON (a canonical record, an array, or `latest-report.json`) to `POST /api/opportunities/ingest` with `Authorization: Bearer <INGEST_TOKEN>`. Optional header `x-source-run-id` labels the batch. `npm run deploy` refuses to run while `database_id` is still the placeholder `00000000-0000-4000-8000-000000000001`. A posted SAM.gov `opportunitiesData` dump is not a live API pull: without a Foundry intelligence label it is skipped by the `HUMAN_REVIEW` filter. The cron pull is the path that ingests official API notices without that label.

### Hand off to the Node spine

The Worker writes an outbox row only when the canonical hash changes. The spine pulls those rows outbound:

```bash
cd government-ops-spine
export DATABASE_URL="postgresql://aegentix:${POSTGRES_PASSWORD}@127.0.0.1:5432/aegentix"
export CLOUDFLARE_ACCOUNT_ID="your-32-hex-account-id"
export D1_DATABASE_ID="the-database-uuid"
export CLOUDFLARE_API_TOKEN="token-with-d1-edit-on-this-database"
npm run ingest:edge
```

The token stays on the spine. The D1 HTTP API is rate limited and is the right shape for this periodic pull, not a hot query path. `npm run ingest:edge` feeds each envelope through the existing intake service, so analysis still happens in Postgres, and then marks the outbox row published.

### Local scheduler

Once the Worker cron is deployed, leave `FOUNDRY_INGEST_ENABLED` unset or `false` and do not run `npm run ingest:foundry:schedule` or the Compose `foundry` profile. Those remain available for a one-off file ingest into local Postgres. Running both writes the same notice twice; the hash keeps the spine row unchanged, but the local scheduler is no longer the live intake.

## Cybercore binding

Set `CYBERCORE_EVENT_ENDPOINT` to the live Cybercore event receiver. The locked local default is `http://host.docker.internal:8000/api/bus`.

## Active execution zones

Build plans route across OpenClaw, Nemotron, Hermes, Docker, and Manus. No zone may submit offers, file patents, commit funds, or make external representations without explicit authorization.

## Operations

```bash
docker compose logs -f api outbox-worker
docker compose restart api outbox-worker
docker compose down
docker compose down -v  # destructive: removes PostgreSQL data
```

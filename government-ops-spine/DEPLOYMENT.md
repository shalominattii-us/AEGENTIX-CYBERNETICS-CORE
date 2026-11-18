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

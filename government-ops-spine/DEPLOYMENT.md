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

# Deployment Integration

## Start

```bash
cd government-ops-spine
cp .env.example .env
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:8099/health
```

## Endpoints

- `GET /health`
- `POST /api/opportunities/ingest`
- `POST /api/opportunities/{eventId}/analyze`
- `GET /api/opportunities/{eventId}/state`

## Cybercore binding

Set `CYBERCORE_EVENT_ENDPOINT` to the live Cybercore event receiver. The locked local default is `http://host.docker.internal:8000/api/bus`. If the deployed Cybercore accepts events through another route, change only this environment variable.

## Active execution zones

Build plans continue to route across OpenClaw, Nemotron, Hermes, Docker, and Manus. This deployment does not grant any zone authority to submit offers, file patents, commit funds, or make external representations.

## Operations

```bash
docker compose logs -f api outbox-worker
docker compose restart api outbox-worker
docker compose down
docker compose down -v  # destructive: also removes PostgreSQL data
```

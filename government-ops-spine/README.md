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

## Next

- Bind handlers to the deployed Cybercore HTTP framework
- Schedule and supervise the outbox worker
- Add GitHub, Docker, deployment, document, CAD, and patent capability indexers
- Add durable approval records and reviewer identities
- Add patent and proposal workbenches behind approval gates

## Safety boundary

This package may generate internal drafts, specifications, simulations, and execution plans. It must not submit bids, grants, patent filings, financial commitments, or external representations without explicit human authorization.

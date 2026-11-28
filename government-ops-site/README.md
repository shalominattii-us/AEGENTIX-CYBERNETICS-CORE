# Government Ops Site

Public, read-only field guide for the Government Ops Spine (`government-ops-spine/` in this repository) and the companion Foundry intake repo ([eaglecrat/Foundry](https://github.com/eaglecrat/Foundry)). It is a Cloudflare Worker with static assets. It is not the spine server, not Foundry, and not the edge intake worker.

The organization has no verified SAM.gov registration, UEI, CAGE code, FedRAMP authorization, ATO, certification, past performance, or named personnel. This site does not claim any of those.

## What the site contains

- **Pipeline explorer** (`/`). Seven stages: public intake, requirement extraction, build specification, capability matching, the TASK-001..005 plan, controlled PDF/DOCX rendering, and the authorization gate. Copy follows the code. Stages that need Postgres, Foundry, or the intake worker are marked described only.
- **Sample demo** (`/demo/`). A visitor picks a labeled sample or pastes text. `POST /api/demo/analyze` runs `parseOpportunity`, `generateBuildSpecification`, `matchCapabilities`, and `createBrainPlan` from `government-ops-spine/src/pipeline.ts`, then SHA-256 hashes that JSON. The capability catalog is fictional. The gate is called with no token. Results are not stored.
- **Sample opportunities** (`/opportunities/`). Rows come from `public/snapshot/opportunities.json`. The Worker validates the file and returns it. The raw file is also at `/snapshot/opportunities.json`.
- **Boundary** (`/boundary/`). The network limit, response headers, and the snapshot update rule.

There is no admin route, no sign-in form, and no secret.

## Intake description (accurate, not live here)

Live intake does **not** depend on a SAM.gov API key. The edge intake path pulls SAM.gov’s public Contract Opportunities CSV extract (`pullSamPublicExtract`) and uses Grants.gov for grant notices. Foundry remains the companion opportunity-intelligence platform. An Opportunities API key is optional and is not required for the public-extract path. This public site does not call SAM.gov, Grants.gov, Foundry, or the intake worker.

## Network boundary

Allowed:

- The browser and this Worker.
- Static assets in `public/`.
- The pure functions bundled from `government-ops-spine/src/pipeline.ts` and `zones.ts`.

Not connected, and not configured:

- Postgres, Hyperdrive, or the spine HTTP server.
- SAM.gov, Grants.gov, Foundry, or the edge intake worker’s storage.
- Submission, outbox, or email tooling.

`wrangler.jsonc` has no KV, R2, D1, service, Hyperdrive, route, or secret. The only binding besides assets is a Worker rate-limit configuration (`20` requests / `60` seconds) for the demo. If the binding throws, the demo returns 503.

## Local development

```bash
cd government-ops-site
npm install
npm test
npm run dev
```

`npm run dev` starts Wrangler on `http://127.0.0.1:8787`.

## Checks

```bash
npm test
npm run typecheck
npm run deploy:dry-run
```

`deploy:dry-run` bundles the Worker and assets and does not upload them.

## Deploy

This repository does not deploy the site and does not create Cloudflare resources. An operator with an account does that:

```bash
cd government-ops-site
npx wrangler login
npx wrangler deploy
```

Wrangler publishes the Worker named `government-ops-site` to the logged-in account’s `workers.dev` subdomain unless you add a route yourself. No `wrangler secret` is required. Do not put an API key in `vars`.

## Accuracy notes

Requirement confidence is the spine’s keyword heuristic. Match scores use tag overlap. The PDF/DOCX renderer lives in the spine and hashes file bytes with SHA-256. The demo hashes JSON instead, and says so. Default plan zones are KERNEL, TREASURY, AI, SECURITY, and XR.

# AEGENTIX Edge Gateway (Cloudflare Worker)

Public 24/7 entry point for the AEGENTIX sovereign machine economy.

## What it does

- **`/health`, `/status`, `/`** — aggregated system health (no auth). Reports overall operational/degraded/down across origin services.
- **`/api/*`** — authenticated proxy to the Tunnel-protected origin. Public read-only treasury/rewards/vault endpoints pass without a token; everything else requires a Bearer capability token.
- **`/sovereign/*`** — elevated actions (kill-switch) gated behind `SOVEREIGN_TOKEN`.
- **Cron Trigger** — stub for 30s settlement batches and 15-minute on-chain reconciliation witnesses.

Every response carries `X-AEGENTIX-Value-Policy: SIMULATED_NEVER_PRESENTED_AS_SETTLED` and `X-AEGENTIX-Edge: cloudflare-worker` headers.

## Deploy

```bash
cd edge/cloudflare-worker
npx wrangler secret put ORIGIN_API
npx wrangler secret put SOVEREIGN_TOKEN
npx wrangler secret put CAPABILITY_SECRET
npx wrangler deploy
```

## Prerequisites

1. `cloudflared` Tunnel running on the machine hosting the Docker stack (CyberCore gRPC :50051, treasury API, Prometheus :9090).
2. Tunnel hostname set as `ORIGIN_API` secret.
3. Optional: custom domain (e.g. `edge.aegentixcybernetics.com`) routed to this Worker in the Cloudflare dashboard.
4. Optional: Cloudflare Load Balancing + health checks in front of the Tunnel for multi-origin failover.

## Doctrine compliance

- Human authorization above autonomous execution: sovereign actions require the master token; value-moving paths require capability tokens.
- Simulated ≠ settled: policy header on every response; promotion gates live in the origin type system.
- Self-hosted: origin stays behind the Tunnel; no inbound ports opened.
- Audit trail: every proxied request is timestamped and edge-tagged for hash-chain receipt logging on the origin side.

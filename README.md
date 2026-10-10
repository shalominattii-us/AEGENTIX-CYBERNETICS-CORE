# AEGENTIX-CYBERNETICS-CORE

Consolidated AEGENTIX enterprise repository with sovereign cybernetics architecture.

## Architecture Overview

### Core Components

**CyberCore** — Zero-storage deterministic key vault with gRPC signing oracle
- 300-shard deterministic derivations (BIP32/SLIP-0010)
- Multi-backend entropy (Argon2id, TPM2.0, HSM PKCS#11, Shamir 3-of-5)
- Jurisdictional exclusion (UAE/Dubai/Sharia-compliant zones blocked)
- Stateless vault with automatic memory zeroization
- gRPC signing oracle on port 50051 with capability tokens

**Hermes Message Bus** — NATS + JetStream integration
- Event streaming for signing operations, key derivations, audit logs
- JetStream persistence with 24h retention, 100MB limit
- Subject hierarchy: `cybercore.*`, `hermes.*`
- Sync and async client interfaces

**Treasury & Rewards** — Native AEGENTIX cyber-genetic stablecoin
- 5 minimal node treasuries across EVM, XRPL, Solana, Cosmos, Bitcoin L2
- 9-chain stablecoin deployment (EVM×5, XRPL, Solana, Cosmos, Stacks)
- Dynamic pricing tiers (MICRO → CRITICAL) with shard bonuses
- Autonomous batch settlement every 30s

**Observability** — Prometheus metrics + structured audit logging
- Metrics on port 9090 (`/metrics`)
- Merkle-tree audit log with Merkle integrity verification
- Jurisdictional compliance reporting

### Docker-First Deployment

```bash
cd sources/sovereign-os
docker compose up -d --build
```

Services: `cybercore`, `nats`, `kernel-event-bus`, `treasury`, `ai-runtime`, `xr-quest-backend`, `security-threat-monitor`, `orbital-observer`, `data-vector-memory`, `cloud-event-stream`

Ports: 50051 (gRPC), 9090 (metrics), 4222 (NATS), 8080 (kernel), 8081 (treasury)

### API Endpoints (Wallet Server on :3000)

| Endpoint | Description |
|----------|-------------|
| `GET /api/cybercore/treasury/status` | US-SQTE $7.3B reserves, 5 treasuries with RPC endpoints |
| `GET /api/cybercore/rewards/summary` | AEGENTIX stablecoin, pricing tiers, settlement engine |
| `GET /api/cybercore/vault/shards` | 300-shard topology, deterministic derivations |

### Treasury Pipelines (Live)

| Network | Treasury Address | RPC Endpoints |
|---------|------------------|---------------|
| EVM | `0x71C865d4fC35E2a188B67B7A98AcB921098A1904` | ethereum, base, arbitrum, optimism, polygon |
| XRPL | `rZamanXRPLMainnetVaultAddr9948271` | websocket, http |
| Solana | `SolanaMinimalTreasuryVault111111111111111111` | http |
| Cosmos | `cosmos1aegentixminimaltreasuryvault99999` | rest, grpc |
| Bitcoin L2 | `bc1qaegentixminimalnodebtc2026vault999` | stacks |

### Stablecoin Contracts (AEGENTIX)

| Chain | Contract |
|-------|----------|
| Ethereum | `0xAEGENTIX...` |
| Base | `0xAEGENTIX...` |
| Arbitrum | `0xAEGENTIX...` |
| Optimism | `0xAEGENTIX...` |
| Polygon | `0xAEGENTIX...` |
| XRPL | `AEGENTIX` (IOU) |
| Solana | `AEGENTIX...` (SPL) |
| Cosmos | `ibc/AEGENTIX...` (IBC) |
| Stacks | `SP...AEGENTIX` (SIP-010) |

### Quick Start

```bash
# Start gRPC oracle locally
cd C:\AEGENTIX-WORKSPACE\github-repos\AEGENTIX-CYBERNETICS-CORE
python start_oracle.py --with-hermes --enable-metrics

# Run wallet API server
cd C:\Users\eagle\antigravity\Aegentix-Super-Agent-Wallet
npx tsx server.ts

# Verify endpoints
curl http://localhost:3000/api/cybercore/treasury/status
curl http://localhost:3000/api/cybercore/rewards/summary
curl http://localhost:3000/api/cybercore/vault/shards
```

## Source Structure

```
sources/
├── sovereign-os/           # Base OS, kernel, Docker Compose orchestration
│   ├── KERNEL/             # Event bus, identity OS, agent runtime
│   ├── TREASURY/           # Autonomous agents, swap aggregation
│   ├── AI/                 # Multi-LLM runtime
│   ├── XR/                 # Quest backend, VR backend
│   ├── SECURITY/           # Threat monitor, orbital observer
│   ├── DATA/               # Vector memory
│   └── CLOUD/              # Event streaming
├── sovereign-prime/
├── SOVEREIGN/              # Starship law, legal proctor briefs
├── Sovereign-System/
├── sovereign-os-9-core/
├── SovereignOS-Core/
├── SovereignOS-Runtime/
├── SovereignOS-Mesh/
└── SovereignOS-Memory/
```

## Status

**Production-ready components:** CyberCore gRPC oracle, Hermes NATS integration, Treasury APIs, Docker Compose orchestration, Prometheus metrics, mTLS certificates.

**In development:** Full on-chain treasury verification, Shamir entropy provider, HSM PKCS#11 integration.

## License

Proprietary — AEGENTIX Cybernetics
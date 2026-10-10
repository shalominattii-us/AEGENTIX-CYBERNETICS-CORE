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

## C:\ Root Structure (Post-Reorganization)

```
C:\
├── .cursor/                    # Cursor IDE config
├── AEGENTIX-CYBERNETICS-CORE/  # Main cybernetics repo (git)
│   ├── .github/workflows/      # CI/CD pipelines
│   ├── cybercore/              # Core vault, oracle, hermes, metrics
│   ├── sources/sovereign-os/   # Docker Compose orchestration
│   ├── c-drive-map/            # C:\ drive mapping artifacts
│   ├── monitoring/             # Prometheus, Grafana, Alertmanager configs
│   ├── orchestrator/           # Event orchestration logs
│   ├── start_oracle.py         # gRPC oracle entrypoint
│   ├── generate_certs.py       # TLS certificate generator
│   ├── cybercore_cli.py        # CLI for vault operations
│   ├── cybercore_daemon.py     # Daemon entrypoint
│   ├── cybercore_parity_test.py # Migration parity tests
│   ├── requirements-cybercore.txt
│   ├── Dockerfile.cybercore
│   ├── docker-entrypoint.sh
│   └── README.md
├── AEGENTIX-WORKSPACE/         # Primary workspace (git)
│   ├── github-repos/           # Git repositories
│   ├── AE_HUB/                 # AE Hub (moved from AEGENTIS_WORKSPACE)
│   ├── ASSR/                   # Autonomous System for Sovereign Records
│   ├── linux-distros/          # Linux ISO acquisition
│   ├── gdrive_ingest/          # Google Drive ingestion
│   ├── omnicyberdex/           # OmniCyberDex
│   ├── logs/                   # Workspace logs
│   ├── src/                    # Source code
│   ├── pnpm-store/             # pnpm cache
│   ├── AE-Hub-v2/              # AE Hub v2 (moved from root)
│   ├── governor.js             # Governor script
│   └── server.js               # Server entrypoint
├── Aegentix/                   # Legacy (archived - contents merged)
├── AE-Hub-v2/                  # Moved to AEGENTIX-WORKSPACE/AE-Hub-v2
├── AI_Ingest_Books/            # Moved to data/books/
├── AE-Hub-v2/                  # Moved to AEGENTIX-WORKSPACE/
├── archive/                    # Archived staging dirs
│   └── AEGENTIX_STAGING_20260907.zip
├── BlockchainData/             # Moved to data/blockchain/
├── BlockchainData/             # Moved to data/blockchain/
├── catalog/                    # Moved to data/catalog/
├── data/                       # Unified data lake
│   ├── blockchain/             # Blockchain node configs, RPC nodes
│   ├── books/                  # AI ingested books
│   ├── catalog/                # Data catalogs (NASA, NSF, etc.)
│   ├── legacy/                 # Archived legacy dirs
│   │   ├── hedera-starter/
│   │   ├── PURE-ISO-UPSTREAM/
│   │   └── var/
│   ├── models/                 # ML models
│   ├── policy/                 # Policy definitions
│   ├── provenance/             # Provenance tracking
│   ├── reflection/             # Reflection data
│   └── schemas/                # Schema definitions
├── eSupport/                   # Dell support tools
├── events/                     # Event logs
├── hedera-starter/             # Moved to data/legacy/
├── inetpub/                    # IIS web root
├── Linux_ISOs/                 # Linux ISO storage
├── LLVM/                       # LLVM compiler infrastructure
├── manifests/                  # Deployment manifests
├── MinimalNodes/               # 300-chain minimal node registry
├── models/                     # Moved to data/models/
├── policy/                     # Moved to data/policy/
├── PURE-ISO-UPSTREAM/          # Moved to data/legacy/
├── provenance/                 # Moved to data/provenance/
├── production/                 # Production configs
├── provenance/                 # Moved to data/provenance/
├── reflection/                 # Moved to data/reflection/
├── schemas/                    # Moved to data/schemas/
├── Sovereign/                  # Unified sovereign core (git)
│   ├── AE-Hub/                 # AE Hub core
│   ├── Config/                 # Configuration
│   ├── core/                   # Core sovereign modules
│   ├── Data/                   # Sovereign data
│   ├── Deploy/                 # Deployment configs
│   ├── envs/                   # Environment configs
│   ├── governance/             # Governance policies
│   ├── halo-ce-universal/      # HALO CE universal
│   ├── ledger/                 # Ledger/ledger state
│   ├── logs/                   # Sovereign logs
│   ├── OllamaModels/           # Ollama model storage
│   ├── processed/              # Processed ingestion data
│   ├── SovereignOS-Portal/     # Portal frontend
│   ├── workflows/              # Workflow definitions
│   ├── anythingllm_ingest_queue/
│   ├── OllamaModels/
│   ├── workflows/
│   ├── AnythingLLMSetup.exe
│   ├── CalibreSetup.msi
│   ├── INSTALLATION_GUIDE.txt
│   ├── inventory_manifest.json
│   └── OllamaSetup.exe
├── tmp/                        # Temp directory
├── UWP_Backup/                 # UWP app backups
├── var/                        # Moved to data/legacy/
├── vfcompat.dll                # Windows system file
├── Windows/                    # Windows system directory
├── XboxGames/                  # Xbox games
├── xboxsetup/                  # Xbox setup
└── .cursor/                    # Cursor IDE config
```

## Source Structure (AEGENTIX-CYBERNETICS-CORE)

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

## Naming Conventions

- **Repositories**: `kebab-case` (e.g., `AEGENTIX-CYBERNETICS-CORE`)
- **Workspaces**: `kebab-case` with `WORKSPACE` suffix (e.g., `AEGENTIX-WORKSPACE`)
- **Directories**: `kebab-case` for projects, `PascalCase` for system components
- **Data directories**: `kebab-case` under `C:\data\`
- **Legacy/archived**: `data/legacy/` or `archive/`
- **Git repos**: Standard GitHub naming

## Status

**Production-ready components:** CyberCore gRPC oracle, Hermes NATS integration, Treasury APIs, Docker Compose orchestration, Prometheus metrics, mTLS certificates.

**In development:** Full on-chain treasury verification, Shamir entropy provider, HSM PKCS#11 integration.

## Post-Reorganization Cleanup Required (Run as Administrator)

```powershell
# Remove locked root files
takeown /f C:\WRP6793.tmp /a
icacls C:\WRP6793.tmp /grant administrators:F
Remove-Item C:\WRP6793.tmp -Force

Remove-Item C:\release.yml, C:\server.js, C:\governor.js, C:\d, C:\DumpStack.log -Force
```

## License

Proprietary — AEGENTIX Cybernetics
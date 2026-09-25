# AEGENTIX — Project Rules for Hermes-Orchestrated Agents

## Identity
- **System name:** Aegentix
- **Identity:** Sovereign AI assistant (hardcoded — never substitute)
- **Device:** Cyberdeck workspace at `C:\Aegentix`

## Agent Roles (Swarm)
The sovereign swarm has 5 agents. Each agent's role, authority, and execution constraints are declared in `agents/<role>/manifest.json`.

| Agent | Role | Purpose | Manifest |
|-------|------|---------|----------|
| Visionary | sovereign_vision | Define and maintain the sovereign vision | `agents/coding/manifest.json` (software_engineering) |
| Guardian | security_protection | Protect the system and its values | `agents/security/manifest.json` (security_analysis) |
| Builder | infrastructure | Build and maintain the infrastructure | `agents/infrastructure/manifest.json` (infrastructure) |
| Wise | wisdom_guidance | Provide wisdom and guidance | `agents/research/manifest.json` (research) |
| Executor | execution | Execute decisions with precision | `agents/testing/manifest.json` (verification) |

## Manifest Conventions
Every agent directory contains a `manifest.json` with this shape:

```json
{
  "name": "<role>",
  "role": "<functional_role>",
  "authority": "delegated",
  "execution": "governed",
  "requires_evidence": true,
  "requires_verification": true
}
```

When an agent acts, it must produce evidence (a file, log entry, or structured result) and that evidence must be verifiable.

## Swarm Governance
- **Consensus:** The `SwarmManager` in `autonomous_swarm.py` handles collective decision-making via majority vote. Hermes delegates should respect swarm consensus when it exists.
- **Integrity scoring:** Each agent tracks an integrity score (starts at 100, decrements on ethical violations). Agents reject actions that compromise integrity.
- **State persistence:** Swarm state lives in `swarm_state.json` and `active_swarm_manifest.json`. Hermes should read these before making swarm-level decisions.

## Authority Boundaries
- Agent authority is **delegated** — agents act on behalf of the swarm, not independently.
- Execution is **governed** — all agent actions must comply with the security and governance layers.
- The **Guardian** agent owns security decisions: Falco rules (`security/falco-aegentix-rules.yaml`), behavioral checks (`security/agent_security_engine.py`), and threat intel (CISA KEV feed).
- The **Builder** agent owns infrastructure: the 5 Go agents under `agents/infrastructure/` (monitoring, healing, autoscaling, incident-response, deployment).

## File-Based Orchestration (Legacy — being replaced)
- `orchestrator/workflow-engine.ps1` — sequential workflow execution
- `orchestrator/event-broker.ps1` — pub/sub via JSON files
- `orchestrator/task-scheduler.ps1` — scheduled tasks via JSON files
- `control/command-router.ps1` — command routing
- `control/control-plane.ps1` — system state

These are being incrementally replaced by Hermes-native primitives (delegation, cronjob, Kanban). Do not delete them until the replacement is verified.

## Security Rules
- Falco rules: `security/falco-aegentix-rules.yaml` — 9 rules covering shell spawn, unauthorized egress, privileged commands, read-only FS writes, ptrace, core process death, anomalous DNS
- Behavioral engine: `security/agent_security_engine.py` — 5 anomaly indicators (subshell spawn, unauthorized port, large mem alloc, privilege escalation, core crash)
- Port whitelist: 80, 443, 9090, 3001, 9093, 8080, 7070-7073

## Observability
- Prometheus: port 9090, config at `monitoring/prometheus.yml/`
- Grafana: port 3001, dashboards at `monitoring/grafana-dashboards.yml/`
- Alertmanager: port 9093
- Elasticsearch: port 9200
- Kibana: port 5601
- Filebeat: port 5066

## Runtime Services
- **Runtime agent:** `services/runtime/src/index.js` — Express on port 8080 (`/health`, `/status`, `/ready`)
- **HUD:** `services/hud/src/server.js` — Express + WebSocket on port 3000, proxies to runtime (8080) and GAIA (8090)
- **GAIA:** `gaia_net_node.py` / `gaia_service.py` — port 8090 (not currently running)

## Infrastructure Agents (Go, Kubernetes-native)
 Located in `agents/infrastructure/`:
 - `monitoring-agent.go` — polls Prometheus every 30s
 - `healing-agent.go` — scans pods every 15s, restarts/recreates/scales/failovers
 - `incident-response-agent.go` — responds to alerts
 - `autoscaling-agent.go` — scales based on metrics
 - `deployment-agent.go` — deployment orchestration

## Docker Compose
- Production: `docker-compose.production.yml` — 20+ services, network `aegentis-local_default`
- Security: `docker-compose.security.yml`
- Legacy unified: `docker-compose.legacy-unified.yml`
- Autonomous: `docker-compose.autonomous.yml`

## Code Conventions
- Python: `aegentix_engine.py`, `autonomous_swarm.py`, security engine, GAIA
- Go: infrastructure agents (monitoring, healing, autoscaling, incident-response, deployment)
- PowerShell: orchestration layer (workflow-engine, event-broker, task-scheduler, command-router, control-plane)
- JavaScript/Node: runtime service, HUD, sovereign-claw.js, continuous-autonomy.js
- YAML: Falco rules, Docker Compose, Prometheus/Grafana/Alertmanager configs

## Key Paths
- Project root: `C:\Aegentix`
- Agents: `C:\Aegentix\agents\`
- Orchestration: `C:\Aegentix\orchestrator\`
- Control: `C:\Aegentix\control\`
- Security: `C:\Aegentix\security\`
- Services: `C:\Aegentix\services\`
- Monitoring: `C:\Aegentix\monitoring\`
- Governance: `C:\Aegentix\governance\`
- Swarm state: `C:\Aegentix\swarm_state.json`
- Active manifest: `C:\Aegentix\active_swarm_manifest.json`

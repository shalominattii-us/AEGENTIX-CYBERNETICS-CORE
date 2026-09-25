# AEGENTIX Swarm Binding — Hermes Delegate Manifest

## Overview
This file binds the 5-agent sovereign swarm (`autonomous_swarm.py`) to Hermes orchestration. Each agent becomes a Hermes delegate role with a defined lane on the Kanban board.

## Swarm Identity
- **Swarm manager:** `autonomous_swarm.py` — `SwarmManager` class
- **Swarm state:** `swarm_state.json` (per-agent state), `active_swarm_manifest.json` (cluster manifest: target_cluster=aegentis-local_default, active_nodes=6, total_indexed_playbooks=136, status=AUTONOMY_ACTIVE)
- **Consensus:** Majority vote across 5 agents. Recorded in `SwarmManager.consensus_log`.
- **Integrity scoring:** Per-agent, starts at 100, decrements on ethical violations, agent stops below 50.

## Hermes Binding — Agent to Delegate Role Map

| Swarm Agent | Hermes Delegate Role | Role File | Kanban Lane | Manifest |
|-------------|---------------------|-----------|-------------|----------|
| Visionary | visionary | `swarm-roles/visionary.md` | Swarm Consensus | `agents/coding/manifest.json` |
| Guardian | guardian | `swarm-roles/guardian.md` | Security | `agents/security/manifest.json` |
| Builder | builder | `swarm-roles/builder.md` | Execution | `agents/infrastructure/manifest.json` |
| Wise | wise | `swarm-roles/wise.md` | Swarm Consensus | `agents/research/manifest.json` |
| Executor | executor | `swarm-roles/executor.md` | Execution/Verification | `agents/testing/manifest.json` |

## Delegate Spawn Order
1. **Visionary** — sets strategic context for all other agents
2. **Guardian** — establishes security gates
3. **Wise** — provides research/analysis capacity
4. **Builder** — builds infrastructure (requires Visionary direction + Guardian approval)
5. **Executor** — executes and verifies (requires all approvals)

## Delegate Communication
- All delegates read `swarm_state.json` and `active_swarm_manifest.json` before acting.
- Delegates post evidence to Kanban card comments.
- Cross-agent decisions route through the Swarm Consensus lane (Visionary + Wise vote, Guardian approves security, Executor verifies).
- The Kanban board is the durable shared state replacing the legacy `orchestrator/` JSON files.

## delegate_task Configuration
- **Model:** `upstage/solar-pro4:free` (inherited from parent config)
- **Provider:** `nous` (inherited)
- **max_concurrent_children:** 10 (enough for all 5 swarm agents + ad-hoc tasks)
- **max_iterations:** 250 per delegate
- **Workdir:** `C:\Aegentix` (all delegates operate in the project root)
- **Toolset:** terminal, file, code_execution, delegation (no browser/computer_use unless explicitly granted)

## Swarm Consensus Protocol (Hermes-mediated)
When a cross-agent decision is needed:
1. A Kanban card is created in the **Swarm Consensus** lane
2. Visionary and Wise are spawned as delegates to evaluate the decision
3. Guardian evaluates security implications
4. Visionary posts a vote, Wise posts analysis, Guardian posts security verdict
5. If consensus is reached (majority proceed + Guardian approval if security-relevant), the card moves to **Execution**
6. Executor spawns to carry out the decision
7. After execution, card moves to **Verification** for Executor self-check, then **Done**

## Integrity Monitoring
- Each delegate's integrity score is tracked in `swarm_state.json`.
- If any delegate's integrity score drops below 50, the Visionary delegate is notified and that agent is suspended from further execution until reviewed.
- Hermes cronjob runs a periodic integrity check (see `.hermes.md` — cronjob integration).

## Evidence and Verification
- Every delegate action must produce evidence (a file, log entry, or structured result).
- Evidence is posted to the Kanban card as a comment or attachment.
- The Executor delegate verifies evidence before moving a card to Done.
- Manifest declarations (`requires_evidence: true`, `requires_verification: true`) are enforced by Hermes policy (`.hermes.md`).

## Source References
- Swarm: `autonomous_swarm.py` (lines 96-188 — SwarmManager), `swarm_state.json`, `active_swarm_manifest.json`
- Roles: `swarm-roles/visionary.md`, `swarm-roles/guardian.md`, `swarm-roles/builder.md`, `swarm-roles/wise.md`, `swarm-roles/executor.md`
- Manifests: `agents/coding/manifest.json`, `agents/security/manifest.json`, `agents/infrastructure/manifest.json`, `agents/research/manifest.json`, `agents/testing/manifest.json`
- Policy: `.hermes.md`, `AGENTS.md`

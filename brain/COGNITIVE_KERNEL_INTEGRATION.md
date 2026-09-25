# AEGENTIX Cognitive / Kernel Integration Contract

## Actual architecture

The authoritative runtime state layer is the PowerShell kernel:

- `Kernel/State/state-core.ps1`
- `Kernel/State/state-runtime.ps1`
- `Kernel/State/state-ops.ps1`

Supporting runtime:

- `Kernel/Recovery/recovery.ps1`
- `Kernel/Heartbeat/heartbeat.ps1`
- `AgentLoop/agent-loop.ps1`

Cognitive layer:

- `brain/jarvis/planner.py`
- `brain/infinite/manifest.json`
- `brain/router/model_router.py`
- `brain/router/model_registry.json`
- `brain/cognitive_bus.py`

## Authority

The PowerShell kernel remains authoritative.

JARVIS is cognitive.

Infinite Brain is cognitive.

The model router is cognitive.

Cognitive components may observe state and produce requests.

They do not become the authoritative state store.

## Causal invariant

Event first. State second.

A cognitive request becomes an event.

The kernel determines whether and how that request changes authoritative state.

## Gateway

`brain/cognitive_gateway.ps1`

The gateway provides:

- status
- model registry inspection
- planning boundary
- cognitive intent submission

## Direct state mutation

Disabled.

The cognitive gateway does not write `runtime/state.json`.

## External actions

Fail closed.

The cognitive layer cannot authorize merely by producing an intent:

- deployment
- financial operations
- live trading
- withdrawals
- contract execution
- destructive operations

## Reality invariant

AEGENTIX SHALL NOT FABRICATE REALITY.

A capability is not considered operational merely because a manifest declares it.

A kernel interface is not considered available merely because a filename was expected.

The system must verify the actual implementation before treating it as authoritative.
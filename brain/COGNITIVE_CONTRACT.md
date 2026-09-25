# AEGENTIX Cognitive Integration Contract

## Actual Authority

The existing AEGENTIX kernel remains authoritative.

The current kernel is PowerShell-based:

- Kernel/State/state-core.ps1
- Kernel/State/state-runtime.ps1
- Kernel/State/state-ops.ps1
- Kernel/State/state-health.ps1
- Kernel/Recovery/recovery.ps1
- Kernel/Heartbeat/heartbeat.ps1
- Kernel/Watchdogs/watchdog.ps1

`brain/cognitive_bus.py` is the existing cognitive event/state interface.

No fictional `StateAuthority.py` or `EventBus.py` is introduced.

## Causal Order

Event first. State second.

Cognitive components emit intent through the existing cognitive bus.

The bridge does not directly modify `runtime/state.json`.

## Cognitive Components

JARVIS:

    brain/jarvis/planner.py

Infinite Brain:

    brain/infinite/manifest.json

Model Router:

    brain/router/model_router.py

Model Registry:

    brain/router/model_registry.json

## External Action Boundary

Cognitive planning does not grant authority for:

- deployments
- financial operations
- live trading
- withdrawals
- contracts
- destructive filesystem operations

Those remain governed by the existing governance/runtime boundary.

## Failure Rule

If the real event implementation cannot be invoked safely:

    FAIL CLOSED

If canonical state cannot be read:

    FAIL CLOSED

If model routing cannot be resolved:

    FAIL CLOSED

AEGENTIX SHALL NOT FABRICATE REALITY.
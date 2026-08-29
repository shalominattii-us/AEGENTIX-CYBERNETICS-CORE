# AEGENTIX CyberDAW Integration Package

CyberDAW is the AEGENTIX live-performance integration layer for Ableton Live, Max for Live, OBS Studio, audio routing, recording, streaming, and Swarm/Orbital supervision.

## Truth boundary

The current Ableton Live Trial installation is a development target only. It MUST NOT satisfy the production Ableton gate. Production readiness requires an explicitly verified Ableton Live Suite + Max for Live environment and a verified AEGENTIX Max-for-Live bridge.

`ONLINE` is reachability. `CONNECTED` is protocol connectivity. `VERIFIED` is functional verification. Only the complete acceptance gate can produce `LIVE_PA_READY`.

## Quick verification

```powershell
python -m cyberdaw verify --json
```

The verifier is offline-first and never treats missing production dependencies as success. It reports `PRODUCTION_BLOCKED` rather than fabricating readiness.

## Acceptance chain

```text
AEGENTIX BOOT
  -> Orbital ONLINE
  -> Ableton CONNECTED
  -> Max Bridge CONNECTED
  -> OBS CONNECTED
  -> Audio Interface LOCKED
  -> PA ROUTING VERIFIED
  -> Recording VERIFIED
  -> Stream Path VERIFIED
  -> Swarm CUE TEST
  -> EMERGENCY STOP TEST
  -> WATCHDOG TEST
  -> LIVE PA READY
```

## Package layout

- `cyberdaw/` — deterministic production gate and adapter contracts
- `maxforlive/` — bridge protocol reference implementation for a Max-for-Live device
- `config/` — explicit capability policy
- `docs/` — Ableton-facing architecture, safety, and validation documents
- `tests/` — offline acceptance tests
- `.github/workflows/cyberdaw-integrity.yml` — CI validation

## Status semantics

Unknown, stale, absent, or contradictory required evidence fails closed.

```text
DEMO_VERIFIED != PRODUCTION_READY != LIVE_PA_READY
```

This package is designed to be demonstrated to Ableton as a proof-of-concept and then validated in the proper production environment.

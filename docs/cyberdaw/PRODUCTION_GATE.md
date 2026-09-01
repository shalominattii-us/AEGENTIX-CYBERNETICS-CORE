# CyberDAW production gate

The gate is intentionally fail-closed.

## State rules

- `ONLINE`: process/service can be reached.
- `CONNECTED`: protocol connection established.
- `VERIFIED`: required functional test has passed.
- `PRODUCTION_BLOCKED`: one or more production requirements are absent or unverified.
- `LIVE_PA_READY`: every required gate has current positive evidence and the emergency stop is not latched.

## Ableton Trial boundary

Ableton Live Trial is permitted as a development/test target. It is never evidence for `ableton_production`. Production requires explicit verification of Live Suite, Max for Live, and the AEGENTIX Max-for-Live bridge in the actual production environment.

## Fail-closed behavior

Unknown, stale, missing, contradictory, or unreachable required evidence is treated as false. The system must not infer readiness from an API returning `ONLINE`.

## Emergency stop

Emergency stop is an overriding safety state. It prevents `LIVE_PA_READY` until an explicit reset occurs and all other gates remain verified.

# AEGENTIX Service Registry

This directory is the Git-authoritative inventory for AEGENTIX operational services and execution zones.

## Files

- `registry.json` — reconciled service inventory.
- `schema/registry.schema.json` — registry document contract.
- `schema/service-manifest.schema.json` — canonical service manifest contract.

## Operating model

Git defines intended identity, governance, capabilities, dependencies, and known endpoints. Runtime adapters later reconcile live state from AWS ECS, Docker/PowerShell, Hermes, Azure, OpenClaw, Nemotron, and Manus.

Health values have the following meaning:

- `healthy` — the service and required dependencies were verified.
- `degraded` — the service responds but a required dependency or capability is unavailable.
- `offline` — the runtime is known to be stopped or unreachable.
- `unknown` — the service is registered but requires a new live observation.

The registry must never infer `healthy` only because a container or task is running. Dependency health is part of service health.

## Governance boundary

Registry automation may inspect, validate, reconcile, and report. It must not submit bids, file patents, place orders, move money, perform withdrawals, make external representations, or run destructive operations without explicit user authorization.

## Current checkpoint

Government Operations Spine is deployed and publicly reachable on AWS ECS/Fargate, but remains `degraded` until its PostgreSQL connection is changed from `127.0.0.1:5432` to an available database endpoint. ECS and public networking do not need to be re-investigated unless the architecture changes.

## Validation

The GitHub Actions workflow `service-registry.yml` validates `registry.json` against the JSON Schemas and checks that every `serviceId` is unique.

## Next adapters

1. PowerShell Docker discovery for the Windows estate.
2. AWS ECS/CloudWatch discovery for deployed cloud services.
3. Hermes/OpenClaw/Nemotron/Manus heartbeat manifests.
4. Reconciliation that updates observations without overwriting governance or intended-state fields.

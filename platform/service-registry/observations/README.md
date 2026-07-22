# Runtime Observations

This directory contains machine-generated snapshots of deployed AEGENTIX services.

The authoritative desired-state inventory remains `../registry.json`. Observation files describe what an execution zone actually reported at a specific time and must not silently replace desired state.

## Docker discovery

From the repository root on the Windows/Docker host:

```powershell
pwsh -NoProfile -File .\platform\service-registry\scripts\discover-docker-services.ps1 -IncludeStopped
```

Default output:

```text
platform/service-registry/observations/docker-runtime.json
```

Use a custom path when collecting evidence without changing the working tree:

```powershell
pwsh -NoProfile -File .\platform\service-registry\scripts\discover-docker-services.ps1 -IncludeStopped -OutputPath "$env:TEMP\aegentix-docker-runtime.json"
```

## Safety and reconciliation

- Discovery is read-only against Docker.
- Secrets and environment-variable values are not collected.
- Container labels are collected because they are operational metadata; do not store credentials in labels.
- Observations must be validated against `../schema/runtime-observation.schema.json`.
- Reconciliation should create an explicit diff or review artifact before changing `registry.json`.
- No restart, deployment, submission, financial action, or destructive action is authorized by an observation.

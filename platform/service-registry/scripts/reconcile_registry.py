#!/usr/bin/env python3
"""Reconcile the Git-authoritative service registry with runtime observations."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SEVERITY = {"info": 0, "warning": 1, "error": 2}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize(value: str | None) -> str:
    return (value or "").lower().replace("_", "-")


def observation_keys(service: dict[str, Any]) -> set[str]:
    labels = service.get("labels") or {}
    keys = {
        normalize(service.get("name")),
        normalize(labels.get("com.docker.compose.project")),
        normalize(labels.get("com.docker.compose.service")),
        normalize(labels.get("aegentix.service-id")),
    }
    return {key for key in keys if key}


def matches(declared: dict[str, Any], observed: dict[str, Any]) -> bool:
    service_id = normalize(declared.get("serviceId"))
    container = normalize((declared.get("runtime") or {}).get("container"))
    keys = observation_keys(observed)
    return service_id in keys or container in keys or any(service_id in key for key in keys)


def finding(code: str, severity: str, service_id: str | None, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "serviceId": service_id,
        "message": message,
        "details": details or {},
    }


def reconcile(registry: dict[str, Any], observations: list[dict[str, Any]], stale_hours: int) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    observed_services: list[dict[str, Any]] = []
    observed_at_values: list[str] = []

    for observation in observations:
        observed_at = observation.get("observedAt")
        if observed_at:
            observed_at_values.append(observed_at)
        for service in observation.get("services", []):
            item = dict(service)
            item["_source"] = observation.get("source", "unknown")
            item["_observedAt"] = observed_at
            observed_services.append(item)

    matched_runtime_ids: set[str] = set()

    for declared in registry.get("services", []):
        service_id = declared["serviceId"]
        runtime_kind = (declared.get("runtime") or {}).get("kind")
        candidates = [item for item in observed_services if matches(declared, item)]

        if not candidates:
            severity = "warning" if runtime_kind in {"docker", "docker-compose"} else "info"
            findings.append(finding("DECLARED_BUT_NOT_OBSERVED", severity, service_id, "Declared service was not present in supplied runtime observations.", {"runtimeKind": runtime_kind}))
            continue

        observed = candidates[0]
        matched_runtime_ids.add(observed.get("runtimeId", observed.get("name", "")))
        state = normalize(observed.get("state"))
        health = normalize(observed.get("health"))
        declared_health = normalize((declared.get("health") or {}).get("status"))

        findings.append(finding("DECLARED_AND_OBSERVED", "info", service_id, "Declared service matched a runtime observation.", {"runtimeName": observed.get("name"), "source": observed.get("_source")}))

        if state and state != "running":
            findings.append(finding("RUNTIME_NOT_RUNNING", "error", service_id, "Observed runtime is not running.", {"state": observed.get("state"), "exitCode": observed.get("exitCode"), "error": observed.get("error")}))

        if health in {"unhealthy", "starting"} or (declared_health == "healthy" and health not in {"healthy", "none", ""}):
            findings.append(finding("HEALTH_MISMATCH", "warning", service_id, "Observed health does not match the declared healthy state.", {"declared": declared_health, "observed": health}))

        declared_port = (declared.get("runtime") or {}).get("port")
        observed_ports = {entry.get("publicPort") for entry in observed.get("ports", []) if entry.get("publicPort") is not None}
        if declared_port and observed_ports and declared_port not in observed_ports:
            findings.append(finding("PORT_MISMATCH", "warning", service_id, "Declared port was not found in observed published ports.", {"declared": declared_port, "observed": sorted(observed_ports)}))

        if observed.get("restartCount", 0) > 3:
            findings.append(finding("EXCESSIVE_RESTARTS", "warning", service_id, "Runtime restart count exceeds the default threshold.", {"restartCount": observed.get("restartCount")}))

    for observed in observed_services:
        runtime_id = observed.get("runtimeId", observed.get("name", ""))
        if runtime_id not in matched_runtime_ids:
            findings.append(finding("OBSERVED_BUT_UNREGISTERED", "warning", None, "Runtime service is not represented in the authoritative registry.", {"runtimeName": observed.get("name"), "image": observed.get("image"), "source": observed.get("_source")}))

    now = datetime.now(timezone.utc)
    for observed_at in observed_at_values:
        try:
            timestamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
            age_hours = (now - timestamp).total_seconds() / 3600
            if age_hours > stale_hours:
                findings.append(finding("STALE_OBSERVATION", "warning", None, "Runtime observation is older than the configured threshold.", {"observedAt": observed_at, "ageHours": round(age_hours, 2), "thresholdHours": stale_hours}))
        except ValueError:
            findings.append(finding("INVALID_OBSERVATION_TIME", "error", None, "Runtime observation timestamp is invalid.", {"observedAt": observed_at}))

    counts = {level: sum(1 for item in findings if item["severity"] == level) for level in SEVERITY}
    conclusion = "error" if counts["error"] else "warning" if counts["warning"] else "clean"

    return {
        "schemaVersion": "1.0.0",
        "generatedAt": iso_now(),
        "registryVersion": registry.get("registryVersion"),
        "conclusion": conclusion,
        "summary": {"findingCount": len(findings), **counts},
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="platform/service-registry/registry.json")
    parser.add_argument("--observations", nargs="*", default=[])
    parser.add_argument("--output", default="platform/service-registry/reports/reconciliation.json")
    parser.add_argument("--stale-hours", type=int, default=24)
    parser.add_argument("--fail-on", choices=["never", "error", "warning"], default="error")
    args = parser.parse_args()

    registry = load_json(Path(args.registry))
    observations = [load_json(Path(path)) for path in args.observations if Path(path).exists()]
    report = reconcile(registry, observations, args.stale_hours)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Conclusion: {report['conclusion']}")
    print(f"Report: {output}")

    if args.fail_on == "warning" and report["conclusion"] in {"warning", "error"}:
        return 1
    if args.fail_on == "error" and report["conclusion"] == "error":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

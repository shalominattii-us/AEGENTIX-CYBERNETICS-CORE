#!/usr/bin/env python3
"""Reconcile the Git-authoritative service registry with runtime observations."""
from __future__ import annotations
import argparse, json
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

def finding(code: str, severity: str, service_id: str | None, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"code": code, "severity": severity, "serviceId": service_id, "message": message, "details": details or {}}

def docker_keys(service: dict[str, Any]) -> set[str]:
    labels = service.get("labels") or {}
    values = [service.get("name"), labels.get("com.docker.compose.project"), labels.get("com.docker.compose.service"), labels.get("aegentix.service-id")]
    return {normalize(v) for v in values if v}

def matches_docker(declared: dict[str, Any], observed: dict[str, Any]) -> bool:
    service_id = normalize(declared.get("serviceId"))
    container = normalize((declared.get("runtime") or {}).get("container"))
    keys = docker_keys(observed)
    return service_id in keys or (container and container in keys) or any(service_id in key for key in keys)

def matches_ecs(declared: dict[str, Any], observed: dict[str, Any]) -> bool:
    runtime = declared.get("runtime") or {}
    declared_service = normalize(runtime.get("service"))
    observed_service = normalize(observed.get("serviceId"))
    declared_container = normalize(runtime.get("container"))
    container_names = {normalize(c.get("name")) for c in observed.get("containers", [])}
    return bool(declared_service and declared_service == observed_service) or bool(declared_container and declared_container in container_names)

def reconcile_docker(declared: dict[str, Any], observed: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    service_id = declared["serviceId"]
    state = normalize(observed.get("state")); health = normalize(observed.get("health"))
    declared_health = normalize((declared.get("health") or {}).get("status"))
    findings.append(finding("DECLARED_AND_OBSERVED", "info", service_id, "Declared service matched a Docker runtime observation.", {"runtimeName": observed.get("name"), "source": "docker"}))
    if state and state != "running": findings.append(finding("RUNTIME_NOT_RUNNING", "error", service_id, "Observed runtime is not running.", {"state": observed.get("state"), "exitCode": observed.get("exitCode"), "error": observed.get("error")}))
    if health in {"unhealthy", "starting"} or (declared_health == "healthy" and health not in {"healthy", "none", ""}): findings.append(finding("HEALTH_MISMATCH", "warning", service_id, "Observed health does not match the declared healthy state.", {"declared": declared_health, "observed": health}))
    declared_port = (declared.get("runtime") or {}).get("port")
    observed_ports = {p.get("publicPort") for p in observed.get("ports", []) if p.get("publicPort") is not None}
    if declared_port and observed_ports and declared_port not in observed_ports: findings.append(finding("PORT_MISMATCH", "warning", service_id, "Declared port was not found in observed published ports.", {"declared": declared_port, "observed": sorted(observed_ports)}))
    if observed.get("restartCount", 0) > 3: findings.append(finding("EXCESSIVE_RESTARTS", "warning", service_id, "Runtime restart count exceeds the default threshold.", {"restartCount": observed.get("restartCount")}))

def reconcile_ecs(declared: dict[str, Any], observed: dict[str, Any], findings: list[dict[str, Any]]) -> None:
    service_id = declared["serviceId"]
    findings.append(finding("DECLARED_AND_OBSERVED", "info", service_id, "Declared service matched an AWS ECS observation.", {"ecsService": observed.get("serviceId"), "cluster": observed.get("cluster"), "source": "aws-ecs"}))
    desired = observed.get("desiredCount", 0); running = observed.get("runningCount", 0); pending = observed.get("pendingCount", 0)
    if running < desired: findings.append(finding("ECS_TASK_COUNT_DRIFT", "error", service_id, "ECS running task count is below desired count.", {"desired": desired, "running": running, "pending": pending}))
    if normalize(observed.get("status")) != "active": findings.append(finding("ECS_SERVICE_NOT_ACTIVE", "error", service_id, "ECS service is not ACTIVE.", {"status": observed.get("status")}))
    failed = [d for d in observed.get("deployments", []) if normalize(d.get("rolloutState")) in {"failed", "rollback-failed"}]
    if failed: findings.append(finding("ECS_DEPLOYMENT_FAILED", "error", service_id, "An ECS deployment reports a failed rollout state.", {"deployments": failed}))
    task_failures = []
    for task in observed.get("tasks", []):
        if normalize(task.get("lastStatus")) != "running" or normalize(task.get("desiredStatus")) != "running": task_failures.append({"taskArn": task.get("taskArn"), "lastStatus": task.get("lastStatus"), "desiredStatus": task.get("desiredStatus"), "stoppedReason": task.get("stoppedReason")})
        for container in task.get("containers", []):
            if normalize(container.get("lastStatus")) != "running" or container.get("exitCode") not in (None, 0): task_failures.append({"taskArn": task.get("taskArn"), "container": container.get("name"), "lastStatus": container.get("lastStatus"), "exitCode": container.get("exitCode")})
    if task_failures: findings.append(finding("ECS_CONTAINER_NOT_RUNNING", "error", service_id, "One or more ECS tasks or containers are not running.", {"failures": task_failures}))
    declared_port = (declared.get("runtime") or {}).get("port")
    observed_ports = {p.get("containerPort") for c in observed.get("containers", []) for p in c.get("ports", []) if p.get("containerPort") is not None}
    if declared_port and observed_ports and declared_port not in observed_ports: findings.append(finding("PORT_MISMATCH", "warning", service_id, "Declared port was not found in ECS container ports.", {"declared": declared_port, "observed": sorted(observed_ports)}))
    declared_repo = (declared.get("runtime") or {}).get("repository")
    observed_images = {c.get("image") for c in observed.get("containers", []) if c.get("image")}
    if declared_repo and observed_images and not any(normalize(declared_repo.split("/")[-1]) in normalize(img) for img in observed_images): findings.append(finding("IMAGE_DRIFT", "warning", service_id, "Observed ECS image does not appear to match the declared repository identity.", {"declaredRepository": declared_repo, "observedImages": sorted(observed_images)}))

def reconcile(registry: dict[str, Any], observations: list[dict[str, Any]], stale_hours: int) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []; observed_at_values: list[str] = []
    docker_services: list[dict[str, Any]] = []; ecs_services: list[dict[str, Any]] = []
    for observation in observations:
        observed_at = observation.get("observedAt")
        if observed_at: observed_at_values.append(observed_at)
        target = ecs_services if observation.get("source") == "aws-ecs" else docker_services
        for service in observation.get("services", []):
            item = dict(service); item["_observedAt"] = observed_at; target.append(item)
    matched_docker: set[str] = set(); matched_ecs: set[str] = set()
    for declared in registry.get("services", []):
        kind = (declared.get("runtime") or {}).get("kind")
        if kind == "ecs-fargate":
            candidates = [x for x in ecs_services if matches_ecs(declared, x)]
            if candidates:
                obs = candidates[0]; matched_ecs.add(obs.get("serviceArn", obs.get("serviceId", ""))); reconcile_ecs(declared, obs, findings)
            else: findings.append(finding("DECLARED_BUT_NOT_OBSERVED", "warning", declared["serviceId"], "Declared ECS service was not present in supplied AWS observations.", {"runtimeKind": kind}))
        else:
            candidates = [x for x in docker_services if matches_docker(declared, x)]
            if candidates:
                obs = candidates[0]; matched_docker.add(obs.get("runtimeId", obs.get("name", ""))); reconcile_docker(declared, obs, findings)
            else: findings.append(finding("DECLARED_BUT_NOT_OBSERVED", "warning" if kind in {"docker", "docker-compose"} else "info", declared["serviceId"], "Declared service was not present in supplied runtime observations.", {"runtimeKind": kind}))
    for obs in docker_services:
        key = obs.get("runtimeId", obs.get("name", ""))
        if key not in matched_docker: findings.append(finding("OBSERVED_BUT_UNREGISTERED", "warning", None, "Docker runtime service is not represented in the authoritative registry.", {"runtimeName": obs.get("name"), "image": obs.get("image"), "source": "docker"}))
    for obs in ecs_services:
        key = obs.get("serviceArn", obs.get("serviceId", ""))
        if key not in matched_ecs: findings.append(finding("OBSERVED_BUT_UNREGISTERED", "warning", None, "ECS service is not represented in the authoritative registry.", {"ecsService": obs.get("serviceId"), "cluster": obs.get("cluster"), "source": "aws-ecs"}))
    now = datetime.now(timezone.utc)
    for observed_at in observed_at_values:
        try:
            timestamp = datetime.fromisoformat(observed_at.replace("Z", "+00:00")); age_hours = (now - timestamp).total_seconds() / 3600
            if age_hours > stale_hours: findings.append(finding("STALE_OBSERVATION", "warning", None, "Runtime observation is older than the configured threshold.", {"observedAt": observed_at, "ageHours": round(age_hours, 2), "thresholdHours": stale_hours}))
        except ValueError: findings.append(finding("INVALID_OBSERVATION_TIME", "error", None, "Runtime observation timestamp is invalid.", {"observedAt": observed_at}))
    counts = {level: sum(1 for item in findings if item["severity"] == level) for level in SEVERITY}
    conclusion = "error" if counts["error"] else "warning" if counts["warning"] else "clean"
    return {"schemaVersion": "1.0.0", "generatedAt": iso_now(), "registryVersion": registry.get("registryVersion"), "conclusion": conclusion, "summary": {"findingCount": len(findings), **counts}, "findings": findings}

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--registry", default="platform/service-registry/registry.json"); parser.add_argument("--observations", nargs="*", default=[]); parser.add_argument("--output", default="platform/service-registry/reports/reconciliation.json"); parser.add_argument("--stale-hours", type=int, default=24); parser.add_argument("--fail-on", choices=["never", "error", "warning"], default="error"); args = parser.parse_args()
    report = reconcile(load_json(Path(args.registry)), [load_json(Path(p)) for p in args.observations if Path(p).exists()], args.stale_hours)
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True); output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2)); print(f"Conclusion: {report['conclusion']}"); print(f"Report: {output}")
    if args.fail_on == "warning" and report["conclusion"] in {"warning", "error"}: return 1
    if args.fail_on == "error" and report["conclusion"] == "error": return 1
    return 0

if __name__ == "__main__": raise SystemExit(main())
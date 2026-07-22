#!/usr/bin/env bash
set -euo pipefail

REGION="${AWS_REGION:-us-west-1}"
OUTPUT="${1:-platform/service-registry/observations/aws-ecs-runtime.json}"
CLUSTER_FILTER="${AEGENTIX_ECS_CLUSTER:-}"
mkdir -p "$(dirname "$OUTPUT")"

command -v aws >/dev/null 2>&1 || { echo "aws CLI is required" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 2; }
aws sts get-caller-identity --region "$REGION" >/dev/null

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 - "$REGION" "$OUTPUT" "$CLUSTER_FILTER" <<'PY'
import datetime
import json
import re
import subprocess
import sys

region, output, cluster_filter = sys.argv[1:]
warnings = []


def aws(action, *args, default=None, required=False):
    command = ["aws", *action.split(":"), *args, "--region", region, "--output", "json"]
    process = subprocess.run(command, text=True, capture_output=True)
    if process.returncode == 0:
        return json.loads(process.stdout or "{}")

    stderr = (process.stderr or "").strip()
    match = re.search(r"\(([^)]+)\)", stderr)
    error_code = match.group(1) if match else "AwsCliError"
    warnings.append({
        "operation": action,
        "status": error_code,
        "message": stderr or f"aws {action} failed",
        "recoverable": not required,
    })
    if required:
        raise SystemExit(stderr or f"aws {action} failed")
    return default if default is not None else {}


identity = aws("sts:get-caller-identity", required=True)
clusters = aws("ecs:list-clusters", default={}).get("clusterArns", [])
if cluster_filter:
    clusters = [c for c in clusters if c == cluster_filter or c.endswith("/" + cluster_filter)]

services_out = []
for cluster in clusters:
    service_arns = aws("ecs:list-services", "--cluster", cluster, default={}).get("serviceArns", [])
    for index in range(0, len(service_arns), 10):
        batch = service_arns[index:index + 10]
        if not batch:
            continue
        description = aws(
            "ecs:describe-services", "--cluster", cluster, "--services", *batch, default={}
        )
        for service in description.get("services", []):
            task_definition_arn = service.get("taskDefinition")
            task_definition = {}
            if task_definition_arn:
                task_definition = aws(
                    "ecs:describe-task-definition",
                    "--task-definition",
                    task_definition_arn,
                    default={},
                ).get("taskDefinition", {})

            task_arns = aws(
                "ecs:list-tasks",
                "--cluster",
                cluster,
                "--service-name",
                service.get("serviceName", ""),
                default={},
            ).get("taskArns", [])
            tasks = []
            for task_index in range(0, len(task_arns), 100):
                part = task_arns[task_index:task_index + 100]
                if part:
                    tasks.extend(
                        aws(
                            "ecs:describe-tasks",
                            "--cluster",
                            cluster,
                            "--tasks",
                            *part,
                            default={},
                        ).get("tasks", [])
                    )

            containers = [
                {
                    "name": container.get("name"),
                    "image": container.get("image"),
                    "essential": container.get("essential", True),
                    "ports": container.get("portMappings", []),
                    "logConfiguration": container.get("logConfiguration", {}),
                }
                for container in task_definition.get("containerDefinitions", [])
            ]

            services_out.append({
                "serviceId": service.get("serviceName"),
                "cluster": cluster.split("/")[-1],
                "clusterArn": cluster,
                "serviceArn": service.get("serviceArn"),
                "status": service.get("status"),
                "launchType": service.get("launchType") or (service.get("capacityProviderStrategy") or [{}])[0].get("capacityProvider"),
                "desiredCount": service.get("desiredCount", 0),
                "runningCount": service.get("runningCount", 0),
                "pendingCount": service.get("pendingCount", 0),
                "taskDefinition": task_definition_arn,
                "taskDefinitionObserved": bool(task_definition),
                "platformVersion": service.get("platformVersion"),
                "deployments": [
                    {key: deployment.get(key) for key in (
                        "id", "status", "rolloutState", "desiredCount", "runningCount",
                        "pendingCount", "createdAt", "updatedAt"
                    )}
                    for deployment in service.get("deployments", [])
                ],
                "networkConfiguration": service.get("networkConfiguration", {}),
                "loadBalancers": service.get("loadBalancers", []),
                "containers": containers,
                "tasks": [
                    {
                        "taskArn": task.get("taskArn"),
                        "lastStatus": task.get("lastStatus"),
                        "desiredStatus": task.get("desiredStatus"),
                        "healthStatus": task.get("healthStatus"),
                        "startedAt": task.get("startedAt"),
                        "stoppedReason": task.get("stoppedReason"),
                        "containers": [
                            {
                                "name": container.get("name"),
                                "image": container.get("image"),
                                "imageDigest": container.get("imageDigest"),
                                "lastStatus": container.get("lastStatus"),
                                "healthStatus": container.get("healthStatus"),
                                "exitCode": container.get("exitCode"),
                            }
                            for container in task.get("containers", [])
                        ],
                    }
                    for task in tasks
                ],
            })

now = datetime.datetime.now(datetime.timezone.utc)
payload = {
    "schemaVersion": "1.1.0",
    "observationId": "aws-ecs-" + now.strftime("%Y%m%d%H%M%S"),
    "source": "aws-ecs",
    "observedAt": now.isoformat().replace("+00:00", "Z"),
    "region": region,
    "accountId": identity.get("Account"),
    "partial": bool(warnings),
    "warnings": warnings,
    "services": services_out,
}
with open(output, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2, default=str)

print(f"Wrote {len(services_out)} ECS service observations to {output}")
if warnings:
    print(f"Completed with {len(warnings)} recoverable AWS permission/API warning(s).", file=sys.stderr)
    for warning in warnings:
        print(f"- {warning['operation']}: {warning['status']}", file=sys.stderr)
PY
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

aws ecs list-clusters --region "$REGION" --output json > "$TMP/clusters.json"

python3 - "$REGION" "$OUTPUT" "$CLUSTER_FILTER" "$TMP" <<'PY'
import json, subprocess, sys, os, datetime
region, output, cluster_filter, tmp = sys.argv[1:]

def aws(*args):
    p = subprocess.run(["aws", *args, "--region", region, "--output", "json"], text=True, capture_output=True)
    if p.returncode:
        raise SystemExit(p.stderr.strip() or f"aws {' '.join(args)} failed")
    return json.loads(p.stdout or "{}")

clusters = aws("ecs", "list-clusters").get("clusterArns", [])
if cluster_filter:
    clusters = [c for c in clusters if c == cluster_filter or c.endswith('/' + cluster_filter)]
services_out = []
for cluster in clusters:
    service_arns = aws("ecs", "list-services", "--cluster", cluster).get("serviceArns", [])
    for i in range(0, len(service_arns), 10):
        batch = service_arns[i:i+10]
        if not batch: continue
        desc = aws("ecs", "describe-services", "--cluster", cluster, "--services", *batch)
        for svc in desc.get("services", []):
            td_arn = svc.get("taskDefinition")
            td = aws("ecs", "describe-task-definition", "--task-definition", td_arn).get("taskDefinition", {}) if td_arn else {}
            task_arns = aws("ecs", "list-tasks", "--cluster", cluster, "--service-name", svc.get("serviceName", "")).get("taskArns", [])
            tasks = []
            for j in range(0, len(task_arns), 100):
                part = task_arns[j:j+100]
                if part:
                    tasks.extend(aws("ecs", "describe-tasks", "--cluster", cluster, "--tasks", *part).get("tasks", []))
            containers = []
            for c in td.get("containerDefinitions", []):
                containers.append({
                    "name": c.get("name"), "image": c.get("image"),
                    "essential": c.get("essential", True),
                    "ports": c.get("portMappings", []),
                    "logConfiguration": c.get("logConfiguration", {})
                })
            services_out.append({
                "serviceId": svc.get("serviceName"),
                "cluster": cluster.split('/')[-1],
                "clusterArn": cluster,
                "serviceArn": svc.get("serviceArn"),
                "status": svc.get("status"),
                "launchType": svc.get("launchType") or (svc.get("capacityProviderStrategy") or [{}])[0].get("capacityProvider"),
                "desiredCount": svc.get("desiredCount", 0),
                "runningCount": svc.get("runningCount", 0),
                "pendingCount": svc.get("pendingCount", 0),
                "taskDefinition": td_arn,
                "platformVersion": svc.get("platformVersion"),
                "deployments": [{k:d.get(k) for k in ("id","status","rolloutState","desiredCount","runningCount","pendingCount","createdAt","updatedAt")} for d in svc.get("deployments", [])],
                "networkConfiguration": svc.get("networkConfiguration", {}),
                "loadBalancers": svc.get("loadBalancers", []),
                "containers": containers,
                "tasks": [{
                    "taskArn": t.get("taskArn"), "lastStatus": t.get("lastStatus"), "desiredStatus": t.get("desiredStatus"),
                    "healthStatus": t.get("healthStatus"), "startedAt": t.get("startedAt"), "stoppedReason": t.get("stoppedReason"),
                    "containers": [{"name": c.get("name"), "image": c.get("image"), "imageDigest": c.get("imageDigest"), "lastStatus": c.get("lastStatus"), "healthStatus": c.get("healthStatus"), "exitCode": c.get("exitCode")} for c in t.get("containers", [])]
                } for t in tasks]
            })

payload = {
  "schemaVersion": "1.0.0",
  "observationId": "aws-ecs-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S"),
  "source": "aws-ecs",
  "observedAt": datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
  "region": region,
  "accountId": aws("sts", "get-caller-identity").get("Account"),
  "services": services_out
}
with open(output, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, default=str)
print(f"Wrote {len(services_out)} ECS service observations to {output}")
PY

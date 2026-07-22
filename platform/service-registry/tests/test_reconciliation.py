import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "reconcile_registry.py"
SPEC = importlib.util.spec_from_file_location("reconcile_registry", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

class ReconciliationTests(unittest.TestCase):
    def test_matches_declared_service_and_detects_port_drift(self):
        registry = {"registryVersion": "1.0.0", "services": [{"serviceId": "grove-hedera-orchards", "runtime": {"kind": "docker-compose", "port": 8087}, "health": {"status": "healthy"}}]}
        observation = {"source": "docker", "observedAt": MODULE.iso_now(), "services": [{"runtimeId": "abc", "name": "grove-hedera-orchards-api", "state": "running", "health": "healthy", "ports": [{"publicPort": 9000}], "labels": {"com.docker.compose.project": "grove-hedera-orchards"}, "restartCount": 0}]}
        report = MODULE.reconcile(registry, [observation], 24)
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("DECLARED_AND_OBSERVED", codes)
        self.assertIn("PORT_MISMATCH", codes)
        self.assertEqual("warning", report["conclusion"])

    def test_detects_unregistered_and_stopped_runtime(self):
        registry = {"registryVersion": "1.0.0", "services": [{"serviceId": "known-service", "runtime": {"kind": "docker"}, "health": {"status": "healthy"}}]}
        observation = {"source": "docker", "observedAt": MODULE.iso_now(), "services": [{"runtimeId": "1", "name": "known-service", "state": "exited", "health": "unhealthy", "ports": [], "labels": {}, "restartCount": 4}, {"runtimeId": "2", "name": "shadow-service", "state": "running", "health": "healthy", "ports": [], "labels": {}, "restartCount": 0}]}
        report = MODULE.reconcile(registry, [observation], 24)
        codes = {item["code"] for item in report["findings"]}
        self.assertTrue({"RUNTIME_NOT_RUNNING", "HEALTH_MISMATCH", "EXCESSIVE_RESTARTS", "OBSERVED_BUT_UNREGISTERED"}.issubset(codes))
        self.assertEqual("error", report["conclusion"])

    def test_matches_ecs_service_and_detects_task_count_drift(self):
        registry = {"registryVersion": "1.0.0", "services": [{"serviceId": "government-ops-spine", "runtime": {"kind": "ecs-fargate", "service": "aegentix-govops", "container": "government-ops-spine", "port": 8099, "repository": "aegentix-government-ops-spine"}, "health": {"status": "degraded"}}]}
        observation = {"source": "aws-ecs", "observedAt": MODULE.iso_now(), "services": [{"serviceId": "aegentix-govops", "serviceArn": "arn:service", "cluster": "AEGENTIX-Cluster", "status": "ACTIVE", "desiredCount": 2, "runningCount": 1, "pendingCount": 1, "deployments": [], "containers": [{"name": "government-ops-spine", "image": "123.dkr.ecr.us-west-1.amazonaws.com/aegentix-government-ops-spine:latest", "ports": [{"containerPort": 8099}]}], "tasks": [{"taskArn": "arn:task", "lastStatus": "RUNNING", "desiredStatus": "RUNNING", "containers": [{"name": "government-ops-spine", "lastStatus": "RUNNING", "exitCode": None}]}]}]}
        report = MODULE.reconcile(registry, [observation], 24)
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("DECLARED_AND_OBSERVED", codes)
        self.assertIn("ECS_TASK_COUNT_DRIFT", codes)
        self.assertEqual("error", report["conclusion"])

    def test_detects_failed_ecs_deployment_and_container(self):
        registry = {"registryVersion": "1.0.0", "services": [{"serviceId": "government-ops-spine", "runtime": {"kind": "ecs-fargate", "service": "aegentix-govops", "container": "government-ops-spine"}, "health": {"status": "degraded"}}]}
        observation = {"source": "aws-ecs", "observedAt": MODULE.iso_now(), "services": [{"serviceId": "aegentix-govops", "serviceArn": "arn:service", "cluster": "AEGENTIX-Cluster", "status": "DRAINING", "desiredCount": 1, "runningCount": 0, "pendingCount": 0, "deployments": [{"rolloutState": "FAILED"}], "containers": [{"name": "government-ops-spine", "ports": []}], "tasks": [{"taskArn": "arn:task", "lastStatus": "STOPPED", "desiredStatus": "RUNNING", "stoppedReason": "Essential container exited", "containers": [{"name": "government-ops-spine", "lastStatus": "STOPPED", "exitCode": 1}]}]}]}
        report = MODULE.reconcile(registry, [observation], 24)
        codes = {item["code"] for item in report["findings"]}
        self.assertTrue({"ECS_TASK_COUNT_DRIFT", "ECS_SERVICE_NOT_ACTIVE", "ECS_DEPLOYMENT_FAILED", "ECS_CONTAINER_NOT_RUNNING"}.issubset(codes))
        self.assertEqual("error", report["conclusion"])

if __name__ == "__main__":
    unittest.main()

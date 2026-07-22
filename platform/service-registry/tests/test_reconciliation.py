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
        registry = {
            "registryVersion": "1.0.0",
            "services": [{
                "serviceId": "grove-hedera-orchards",
                "runtime": {"kind": "docker-compose", "port": 8087},
                "health": {"status": "healthy"}
            }]
        }
        observation = {
            "source": "docker",
            "observedAt": MODULE.iso_now(),
            "services": [{
                "runtimeId": "abc",
                "name": "grove-hedera-orchards-api",
                "state": "running",
                "health": "healthy",
                "ports": [{"publicPort": 9000}],
                "labels": {"com.docker.compose.project": "grove-hedera-orchards"},
                "restartCount": 0
            }]
        }
        report = MODULE.reconcile(registry, [observation], 24)
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("DECLARED_AND_OBSERVED", codes)
        self.assertIn("PORT_MISMATCH", codes)
        self.assertEqual("warning", report["conclusion"])

    def test_detects_unregistered_and_stopped_runtime(self):
        registry = {
            "registryVersion": "1.0.0",
            "services": [{
                "serviceId": "known-service",
                "runtime": {"kind": "docker"},
                "health": {"status": "healthy"}
            }]
        }
        observation = {
            "source": "docker",
            "observedAt": MODULE.iso_now(),
            "services": [
                {"runtimeId": "1", "name": "known-service", "state": "exited", "health": "unhealthy", "ports": [], "labels": {}, "restartCount": 4},
                {"runtimeId": "2", "name": "shadow-service", "state": "running", "health": "healthy", "ports": [], "labels": {}, "restartCount": 0}
            ]
        }
        report = MODULE.reconcile(registry, [observation], 24)
        codes = {item["code"] for item in report["findings"]}
        self.assertIn("RUNTIME_NOT_RUNNING", codes)
        self.assertIn("HEALTH_MISMATCH", codes)
        self.assertIn("EXCESSIVE_RESTARTS", codes)
        self.assertIn("OBSERVED_BUT_UNREGISTERED", codes)
        self.assertEqual("error", report["conclusion"])


if __name__ == "__main__":
    unittest.main()

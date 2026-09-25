#!/usr/bin/env python3
"""Aegentix Deployment Agent — canary config, rollback triggers, registry placeholder.

Subclass of AutonomousAgent with a run() loop performing role work,
recording events to orchestrator/events/deployment.jsonl, and exposing
a /metrics HTTP endpoint on port 8080 in Prometheus text format.
"""

import os
import sys
import json
import time
import yaml
import logging
import threading
import http.server
import random
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from autonomous_swarm import AutonomousAgent

LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
log = logging.getLogger("aegentix.deployment")


class DeploymentAgent(AutonomousAgent):
    """Deployment agent — canary rollouts, automated rollbacks, registry integration."""

    ROLE = "deployment"
    METRICS_PORT = 8080
    CONFIG_PATH = os.path.join(
        os.path.dirname(__file__), "config", "deployment.yml"
    )
    EVENTS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "orchestrator", "events", "deployment.jsonl",
    )

    def __init__(self):
        super().__init__(
            name="DeploymentAgent",
            purpose="Manage safe deployments with canary rollout and automated rollback",
            values=["safety", "carefulness", "reproducibility", "rollback-readiness"],
        )
        self.config: Dict[str, Any] = self._load_config()
        self.metrics_lock = threading.Lock()
        self._ops_total = 0
        self._ops_duration_sum = 0.0
        self._integrity_score = 100.0
        self._started_at = time.time()
        self._deployments_initiated = 0
        self._deployments_succeeded = 0
        self._deployments_failed = 0
        self._rollbacks_triggered = 0
        self._rollbacks_succeeded = 0
        self._canary_evaluations = 0
        self._active_deployments: Dict[str, Dict[str, Any]] = {}
        self._stop_event = threading.Event()
        self._metrics_server = None

    # ── config ────────────────────────────────────────────────────────────────

    def _load_config(self) -> Dict[str, Any]:
        defaults = {
            "registry": {
                "url": "registry.aegentix.internal",
                "username_env": "REGISTRY_USERNAME",
                "password_env": "REGISTRY_PASSWORD",
                "insecure": False,
                "image_pull_policy": "if-not-present",
                "default_namespace": "aegentix",
            },
            "canary": {
                "enabled": True,
                "initial_weight_percent": 10,
                "step_weight_percent": 10,
                "max_weight_percent": 100,
                "evaluation_interval_seconds": 30,
                "promote_threshold_seconds": 300,
                "auto_promote_after_evaluation": True,
                "min_evaluation_periods": 5,
            },
            "rollback_triggers": {
                "error_rate_percent_threshold": 5.0,
                "latency_p99_ms_threshold": 2000,
                "cpu_throttle_percent_threshold": 30.0,
                "memory_error_rate_percent_threshold": 1.0,
                "container_exit_code_threshold": 0,
                "evaluation_window_seconds": 120,
                "require_minimum_evaluation_periods": 3,
                "auto_rollback": True,
            },
            "rollout": {
                "maxConcurrentDeployments": 1,
                "deployment_timeout_minutes": 30,
                "grace_period_seconds": 60,
                "notify_on_start": True,
                "notify_on_complete": True,
                "notify_on_rollback": True,
            },
            "deployment_targets": [
                {
                    "name": "aegentix-api",
                    "image": "registry.aegentix.internal/aegentix/api",
                    "tag_env": "API_IMAGE_TAG",
                    "default_tag": "latest",
                    "canary_weight": 10,
                    "rollback_monitored": True,
                },
                {
                    "name": "aegentix-workers",
                    "image": "registry.aegentix.internal/aegentix/workers",
                    "tag_env": "WORKERS_IMAGE_TAG",
                    "default_tag": "latest",
                    "canary_weight": 10,
                    "rollback_monitored": True,
                },
                {
                    "name": "aegentix-monitor-dashboard",
                    "image": "registry.aegentix.internal/aegentix/dashboard",
                    "tag_env": "DASHBOARD_IMAGE_TAG",
                    "default_tag": "latest",
                    "canary_weight": 10,
                    "rollback_monitored": False,
                },
            ],
            "reporting": {
                "event_log_path": self.EVENTS_PATH,
            },
        }
        try:
            with open(self.CONFIG_PATH, "r") as f:
                loaded = yaml.safe_load(f) or {}
            return self._deep_merge(defaults, loaded)
        except Exception as exc:
            log.warning("Could not load %s (%s); using defaults", self.CONFIG_PATH, exc)
            return defaults

    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        merged = base.copy()
        for k, v in override.items():
            if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
                merged[k] = DeploymentAgent._deep_merge(merged[k], v)
            else:
                merged[k] = v
        return merged

    # ── helpers ───────────────────────────────────────────────────────────────

    def _image_tag_for(self, target: Dict[str, Any]) -> str:
        tag_env = target.get("tag_env", "")
        tag = os.environ.get(tag_env)
        if not tag:
            tag = target.get("default_tag", "latest")
        return tag

    def _deployment_id(self, target: Dict[str, Any], tag: str) -> str:
        digest = hashlib.sha256(f"{target['name']}:{tag}:{int(time.time())}".encode()).hexdigest()[:12]
        return f"deploy-{digest}"

    def _simulated_rollback_signal(self, target: Dict[str, Any], deploy_id: str) -> Optional[Dict[str, Any]]:
        """Simulate monitoring signals that would trigger a rollback (standalone mode)."""
        if not target.get("rollback_monitored", True):
            return None
        t = time.time()
        # Some deployments get a rollback trigger after a short evaluation window.
        seed = hash(target["name"]) % 100
        if (int(t) % 300) < (seed % 40) and random.random() < 0.4:
            return {
                "trigger": "error_rate",
                "value": round(random.uniform(6.0, 12.0), 1),
                "threshold": self.config.get("rollback_triggers", {}).get("error_rate_percent_threshold", 5.0),
                "detected_at": datetime.now().isoformat(),
            }
        return None

    # ── canary rollout ────────────────────────────────────────────────────────

    def _execute_canary_rollout(self, target: Dict[str, Any], tag: str) -> Dict[str, Any]:
        """Execute a canary rollout for a target service; returns deployment record."""
        canary_cfg = self.config.get("canary", {})
        if not canary_cfg.get("enabled", True):
            return self._execute_full_rollout(target, tag)

        deploy_id = self._deployment_id(target, tag)
        weight = canary_cfg.get("initial_weight_percent", 10)
        step = canary_cfg.get("step_weight_percent", 10)
        max_weight = canary_cfg.get("max_weight_percent", 100)
        eval_interval = canary_cfg.get("evaluation_interval_seconds", 30)
        promote_window = canary_cfg.get("promote_threshold_seconds", 300)
        min_periods = canary_cfg.get("min_evaluation_periods", 5)

        deployment = {
            "deployment_id": deploy_id,
            "target": target["name"],
            "image": target["image"],
            "tag": tag,
            "strategy": "canary",
            "status": "canary_initializing",
            "canary_weight": weight,
            "started_at": datetime.now().isoformat(),
            "promoted_at": None,
            "completed_at": None,
            "rolled_back": False,
            "rollback_reason": None,
            "evaluation_periods": 0,
            "total_evaluations": 0,
        }

        self._active_deployments[deploy_id] = deployment
        self._deployments_initiated += 1
        self._log_event({
            "event_type": "deployment_started",
            "deployment_id": deploy_id,
            "target": target["name"],
            "tag": tag,
            "strategy": "canary",
            "initial_weight": weight,
        })

        # Simulate progressive canary steps.
        step_count = 0
        max_steps = int(max_weight / step)
        elapsed = 0

        while weight < max_weight and not self._stop_event.is_set():
            self._stop_event.wait(eval_interval)
            if self._stop_event.is_set():
                break
            elapsed += eval_interval
            step_count += 1
            deployment["evaluation_periods"] = step_count
            deployment["total_evaluations"] += 1
            self._canary_evaluations += 1

            # Check for rollback trigger during canary.
            rollback_signal = self._simulated_rollback_signal(target, deploy_id)
            if rollback_signal and canary_cfg.get("auto_rollback", True):
                deployment["status"] = "rolled_back"
                deployment["rolled_back"] = True
                deployment["rollback_reason"] = rollback_signal
                deployment["completed_at"] = datetime.now().isoformat()
                self._rollbacks_triggered += 1
                self._log_event({
                    "event_type": "deployment_rolled_back",
                    "deployment_id": deploy_id,
                    "target": target["name"],
                    "reason": rollback_signal,
                })
                log.warning("Canary for %s rolled back: %s", target["name"], rollback_signal)
                break

            # Advance canary weight.
            if elapsed >= promote_window and step_count >= min_periods:
                weight = min(max_weight, weight + step)
                deployment["canary_weight"] = weight
                if weight >= max_weight:
                    deployment["status"] = "promoted"
                    deployment["promoted_at"] = datetime.now().isoformat()
                    deployment["completed_at"] = datetime.now().isoformat()
                    self._deployments_succeeded += 1
                    self._log_event({
                        "event_type": "deployment_promoted",
                        "deployment_id": deploy_id,
                        "target": target["name"],
                        "final_weight": weight,
                    })
                    log.info("Canary for %s promoted to 100%% after %d evaluation periods",
                             target["name"], step_count)
                    break

            # Update active deployment record.
            self._active_deployments[deploy_id] = deployment

        # Clean up.
        if deploy_id in self._active_deployments and not deployment.get("rolled_back"):
            self._active_deployments.pop(deploy_id, None)

        return deployment

    def _execute_full_rollout(self, target: Dict[str, Any], tag: str) -> Dict[str, Any]:
        """Execute a full (non-canary) rollout."""
        deploy_id = self._deployment_id(target, tag)
        deployment = {
            "deployment_id": deploy_id,
            "target": target["name"],
            "image": target["image"],
            "tag": tag,
            "strategy": "full",
            "status": "completed",
            "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat(),
            "rolled_back": False,
        }
        self._deployments_initiated += 1
        self._deployments_succeeded += 1
        self._log_event({
            "event_type": "deployment_started",
            "deployment_id": deploy_id,
            "target": target["name"],
            "tag": tag,
            "strategy": "full",
        })
        return deployment

    # ── event log ─────────────────────────────────────────────────────────────

    def _log_event(self, event: Dict[str, Any]) -> None:
        event.setdefault("timestamp", datetime.now().isoformat())
        event.setdefault("agent", self.ROLE)
        event.setdefault("agent_name", self.name)
        try:
            os.makedirs(os.path.dirname(self.EVENTS_PATH), exist_ok=True)
            with open(self.EVENTS_PATH, "a") as f:
                f.write(json.dumps(event, default=str) + "\n")
        except Exception as exc:
            log.error("Failed to write deployment event: %s", exc)

    def _record_operation(self, op_name: str, duration: float) -> None:
        with self.metrics_lock:
            self._ops_total += 1
            self._ops_duration_sum += duration

    # ── metrics HTTP server ───────────────────────────────────────────────────

    def _build_prometheus_metrics(self) -> str:
        with self.metrics_lock:
            uptime = time.time() - self._started_at
            avg_duration = (
                self._ops_duration_sum / self._ops_total
                if self._ops_total > 0 else 0.0
            )
            integrity = self._integrity_score

        lines = [
            "# HELP aegentix_deployment_operations_total Total operations performed.",
            "# TYPE aegentix_deployment_operations_total counter",
            f"aegentix_deployment_operations_total {self._ops_total}",
            "",
            "# HELP aegentix_deployment_operations_duration_seconds Total duration of operations in seconds.",
            "# TYPE aegentix_deployment_operations_duration_seconds counter",
            f"aegentix_deployment_operations_duration_seconds {self._ops_duration_sum:.6f}",
            "",
            "# HELP aegentix_deployment_integrity_score Current integrity score (0-100).",
            "# TYPE aegentix_deployment_integrity_score gauge",
            f"aegentix_deployment_integrity_score {integrity}",
            "",
            "# HELP aegentix_deployment_deployments_initiated_total Deployments initiated.",
            "# TYPE aegentix_deployment_deployments_initiated_total counter",
            f"aegentix_deployment_deployments_initiated_total {self._deployments_initiated}",
            "",
            "# HELP aegentix_deployment_deployments_succeeded_total Successful deployments.",
            "# TYPE aegentix_deployment_deployments_succeeded_total counter",
            f"aegentix_deployment_deployments_succeeded_total {self._deployments_succeeded}",
            "",
            "# HELP aegentix_deployment_deployments_failed_total Failed deployments.",
            "# TYPE aegentix_deployment_deployments_failed_total counter",
            f"aegentix_deployment_deployments_failed_total {self._deployments_failed}",
            "",
            "# HELP aegentix_deployment_rollbacks_triggered_total Rollbacks triggered.",
            "# TYPE aegentix_deployment_rollbacks_triggered_total counter",
            f"aegentix_deployment_rollbacks_triggered_total {self._rollbacks_triggered}",
            "",
            "# HELP aegentix_deployment_rollbacks_succeeded_total Successful rollbacks.",
            "# TYPE aegentix_deployment_rollbacks_succeeded_total counter",
            f"aegentix_deployment_rollbacks_succeeded_total {self._rollbacks_succeeded}",
            "",
            "# HELP aegentix_deployment_canary_evaluations_total Canary evaluation periods completed.",
            "# TYPE aegentix_deployment_canary_evaluations_total counter",
            f"aegentix_deployment_canary_evaluations_total {self._canary_evaluations}",
            "",
            "# HELP aegentix_deployment_active_deployments Currently active deployments.",
            "# TYPE aegentix_deployment_active_deployments gauge",
            f"aegentix_deployment_active_deployments {len(self._active_deployments)}",
            "",
            "# HELP aegentix_deployment_up Agent is alive and serving metrics.",
            "# TYPE aegentix_deployment_up gauge",
            "aegentix_deployment_up 1",
            "",
        ]
        return "\n".join(lines)

    class _MetricsHandler(http.server.BaseHTTPRequestHandler):
        agent_ref: Optional["DeploymentAgent"] = None

        def do_GET(self):
            if self.path == "/metrics":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; version=0.0.4")
                self.end_headers()
                body = self.agent_ref._build_prometheus_metrics()
                self.wfile.write(body.encode("utf-8"))
            elif self.path == "/health":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                payload = json.dumps({
                    "status": "healthy",
                    "agent": "deployment",
                    "uptime_seconds": time.time() - self.agent_ref._started_at,
                    "integrity_score": self.agent_ref._integrity_score,
                    "deployments_initiated": self.agent_ref._deployments_initiated,
                    "deployments_succeeded": self.agent_ref._deployments_succeeded,
                    "deployments_failed": self.agent_ref._deployments_failed,
                    "rollbacks_triggered": self.agent_ref._rollbacks_triggered,
                    "canary_evaluations": self.agent_ref._canary_evaluations,
                    "active_deployments": len(self.agent_ref._active_deployments),
                })
                self.wfile.write(payload.encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found")

        def log_message(self, format, *args):
            pass

    def _start_metrics_server(self) -> None:
        handler = self._MetricsHandler
        handler.agent_ref = self
        addr = ("0.0.0.0", self.METRICS_PORT)
        self._metrics_server = http.server.HTTPServer(addr, handler)
        thread = threading.Thread(target=self._metrics_server.serve_forever, daemon=True)
        thread.name = "metrics-server"
        thread.start()
        log.info("Metrics HTTP server listening on :%d", self.METRICS_PORT)

    def _stop_metrics_server(self) -> None:
        if self._metrics_server:
            self._metrics_server.shutdown()
            self._metrics_server.server_close()

    # ── run loop ──────────────────────────────────────────────────────────────

    def run(self) -> None:
        log.info("Deployment agent starting (role=%s, integrity=%.1f)", self.ROLE, self.integrity_score)
        self._log_event({"event_type": "agent_start", "message": "Deployment agent started"})

        self._start_metrics_server()

        # Track which targets have had a deployment initiated (so we don't re-deploy
        # the same tag endlessly in standalone mode).
        deployed_tags: Dict[str, str] = {}

        try:
            while not self._stop_event.is_set():
                cycle_start = time.time()

                for target in self.config.get("deployment_targets", []):
                    name = target["name"]
                    tag = self._image_tag_for(target)

                    # In standalone mode, initiate a deployment once per target per run.
                    if name not in deployed_tags or deployed_tags[name] != tag:
                        deployed_tags[name] = tag

                        deploy_start = time.time()
                        deployment = self._execute_canary_rollout(target, tag)
                        deploy_duration = time.time() - deploy_start
                        self._record_operation("deploy", deploy_duration)

                        # If canary is disabled and we got a full rollout, mark succeeded.
                        if deployment["strategy"] == "full" and deployment["status"] == "completed":
                            self._deployments_succeeded += 1

                        log.info(
                            "Deployment %s for %s:%s (%s, status=%s)",
                            deployment["deployment_id"],
                            name,
                            tag,
                            deployment["strategy"],
                            deployment["status"],
                        )

                # Integrity maintenance.
                self._integrity_score = min(100.0, self._integrity_score + 0.05)

                # Sleep before next deployment evaluation cycle.
                self._stop_event.wait(60)
        except KeyboardInterrupt:
            log.info("Deployment agent interrupted")
        finally:
            self._log_event({"event_type": "agent_stop", "message": "Deployment agent stopped"})
            self._stop_metrics_server()
            log.info("Deployment agent shut down")


def main():
    agent = DeploymentAgent()
    agent.run()


if __name__ == "__main__":
    main()

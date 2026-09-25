#!/usr/bin/env python3
"""Aegentix Healing Agent — restart policy, max retries, health checks, drain.

Subclass of AutonomousAgent with a run() loop performing role work,
recording events to orchestrator/events/healing.jsonl, and exposing
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
from datetime import datetime
from typing import Dict, Any, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from autonomous_swarm import AutonomousAgent

LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
log = logging.getLogger("aegentix.healing")


class HealingAgent(AutonomousAgent):
    """Healing agent — restarts unhealthy services, enforces retry/drain policy."""

    ROLE = "healing"
    METRICS_PORT = 8080
    CONFIG_PATH = os.path.join(
        os.path.dirname(__file__), "config", "healing.yml"
    )
    EVENTS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "orchestrator", "events", "healing.jsonl",
    )

    def __init__(self):
        super().__init__(
            name="HealingAgent",
            purpose="Detect and heal unhealthy containerised services",
            values=["resilience", "carefulness", "durability", "minimised-disruption"],
        )
        self.config: Dict[str, Any] = self._load_config()
        self.metrics_lock = threading.Lock()
        self._ops_total = 0
        self._ops_duration_sum = 0.0
        self._integrity_score = 100.0
        self._started_at = time.time()
        self._restarts_attempted = 0
        self._restarts_succeeded = 0
        self._restarts_failed = 0
        self._health_checks_performed = 0
        self._health_checks_failed = 0
        self._drains_performed = 0
        self._service_health: Dict[str, Dict[str, Any]] = {}
        self._stop_event = threading.Event()
        self._metrics_server = None

    # ── config ────────────────────────────────────────────────────────────────

    def _load_config(self) -> Dict[str, Any]:
        defaults = {
            "restart_policy": {
                "max_retries": 3,
                "retry_backoff_base_seconds": 5,
                "retry_backoff_multiplier": 2.0,
                "max_backoff_seconds": 300,
                "restart_window_seconds": 3600,
                "cool_down_after_retries_seconds": 600,
                "auto_restart": True,
                "require_guardian_approval": False,
            },
            "health_checks": {
                "interval_seconds": 15,
                "timeout_seconds": 5,
                "retries_before_unhealthy": 3,
                "check_type": "http",
                "http_endpoint": "/health",
                "expected_status": 200,
                "check_timeout_seconds": 10,
            },
            "drain_behavior": {
                "enabled": True,
                "drain_timeout_seconds": 120,
                "drain_message": "Service entering drain mode for healing — traffic will be redirected.",
                "graceful_shutdown_seconds": 30,
                "rebalance_after_drain": True,
            },
            "services": [
                {
                    "name": "aegentix-prometheus",
                    "health_check_url": "http://prometheus:9090/health",
                    "drain_protected": True,
                    "restart_priority": 1,
                },
                {
                    "name": "aegentix-grafana",
                    "health_check_url": "http://grafana:3000/health",
                    "drain_protected": True,
                    "restart_priority": 2,
                },
                {
                    "name": "aegentix-alertmanager",
                    "health_check_url": "http://alertmanager:9093/health",
                    "drain_protected": False,
                    "restart_priority": 3,
                },
                {
                    "name": "aegentix-elasticsearch",
                    "health_check_url": "http://elasticsearch:9200",
                    "drain_protected": True,
                    "restart_priority": 1,
                },
                {
                    "name": "aegentix-kibana",
                    "health_check_url": "http://kibana:5601",
                    "drain_protected": False,
                    "restart_priority": 4,
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
                merged[k] = HealingAgent._deep_merge(merged[k], v)
            else:
                merged[k] = v
        return merged

    # ── helpers ───────────────────────────────────────────────────────────────

    def _simulated_health_status(self, service: Dict[str, Any]) -> bool:
        """Simulate a health check result for standalone mode."""
        name = service["name"]
        t = time.time()
        # Each service has its own failure rhythm.
        seed = hash(name) % 100
        failure_window = 180 + (seed % 120)  # 180-300s between failures
        within_failure = (int(t) % failure_window) < 10
        return not within_failure

    def _perform_health_check(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Run a health check for one service; returns a result dict."""
        name = service["name"]
        hc = self.config.get("health_checks", {})
        timeout = hc.get("check_timeout_seconds", 10)
        expected = hc.get("expected_status", 200)
        url = service.get("health_check_url", f"http://{name}:8080/health")

        healthy = self._simulated_health_status(service)
        self._health_checks_performed += 1

        if healthy:
            result = {
                "service": name,
                "healthy": True,
                "status_code": expected,
                "latency_ms": random.uniform(1.0, 5.0),
                "checked_at": datetime.now().isoformat(),
            }
        else:
            self._health_checks_failed += 1
            result = {
                "service": name,
                "healthy": False,
                "status_code": 503,
                "latency_ms": random.uniform(50.0, 200.0),
                "error": "Service unhealthy or unreachable",
                "checked_at": datetime.now().isoformat(),
            }
        return result

    def _is_unhealthy(self, service: Dict[str, Any], consecutive_failures: int) -> bool:
        hc = self.config.get("health_checks", {})
        threshold = hc.get("retries_before_unhealthy", 3)
        return consecutive_failures >= threshold

    # ── restart with retry/backoff ────────────────────────────────────────────

    def _restart_service(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to restart a service with retry/backoff per restart_policy."""
        name = service["name"]
        policy = self.config.get("restart_policy", {})
        max_retries = policy.get("max_retries", 3)
        base_backoff = policy.get("retry_backoff_base_seconds", 5)
        multiplier = policy.get("retry_backoff_multiplier", 2.0)
        max_backoff = policy.get("max_backoff_seconds", 300)
        cool_down = policy.get("cool_down_after_retries_seconds", 600)

        result = {
            "service": name,
            "attempts": 0,
            "success": False,
            "last_error": None,
            "total_wait_seconds": 0.0,
            "restarted_at": None,
        }

        current_backoff = base_backoff
        for attempt in range(1, max_retries + 1):
            result["attempts"] = attempt
            # Simulated restart: it eventually succeeds (or fails after max retries).
            # In standalone mode we inject a success after 1-2 attempts for realism.
            simulated_success = (attempt >= 2 and random.random() < 0.8) or (attempt == 1 and random.random() < 0.2)
            if simulated_success:
                result["success"] = True
                result["restarted_at"] = datetime.now().isoformat()
                self._restarts_attempted += 1
                self._restarts_succeeded += 1
                log.info("Successfully restarted %s after %d attempt(s)", name, attempt)
                break
            else:
                result["last_error"] = f"Restart attempt {attempt} failed"
                self._restarts_failed += 1
                if attempt < max_retries:
                    wait = min(current_backoff, max_backoff)
                    result["total_wait_seconds"] += wait
                    log.warning("Restart attempt %d for %s failed; backing off %.1fs", attempt, name, wait)
                    # In real code we would sleep here; in simulation loop we just record.
                    current_backoff = min(current_backoff * multiplier, max_backoff)

        if not result["success"]:
            log.error("Gave up restarting %s after %d attempts", name, max_retries)

        # Cool-down period after exhausting retries.
        if not result["success"]:
            result["cool_down_until"] = (datetime.now().timestamp() + cool_down)

        return result

    # ── drain behavior ────────────────────────────────────────────────────────

    def _drain_service(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Drain a service before healing (simulated)."""
        name = service["name"]
        drain_cfg = self.config.get("drain_behavior", {})
        if not drain_cfg.get("enabled", True):
            return {"drained": False, "reason": "drain disabled"}

        self._drains_performed += 1
        result = {
            "service": name,
            "drained": True,
            "drain_timeout_seconds": drain_cfg.get("drain_timeout_seconds", 120),
            "graceful_shutdown_seconds": drain_cfg.get("graceful_shutdown_seconds", 30),
            "message": drain_cfg.get("drain_message", ""),
            "drained_at": datetime.now().isoformat(),
            "rebalance_after": drain_cfg.get("rebalance_after_drain", True),
        }
        log.info("Drained %s for healing (timeout=%ds)", name, result["drain_timeout_seconds"])
        return result

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
            log.error("Failed to write healing event: %s", exc)

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
            "# HELP aegentix_healing_operations_total Total operations performed.",
            "# TYPE aegentix_healing_operations_total counter",
            f"aegentix_healing_operations_total {self._ops_total}",
            "",
            "# HELP aegentix_healing_operations_duration_seconds Total duration of operations in seconds.",
            "# TYPE aegentix_healing_operations_duration_seconds counter",
            f"aegentix_healing_operations_duration_seconds {self._ops_duration_sum:.6f}",
            "",
            "# HELP aegentix_healing_integrity_score Current integrity score (0-100).",
            "# TYPE aegentix_healing_integrity_score gauge",
            f"aegentix_healing_integrity_score {integrity}",
            "",
            "# HELP aegentix_healing_restarts_attempted_total Total restart attempts.",
            "# TYPE aegentix_healing_restarts_attempted_total counter",
            f"aegentix_healing_restarts_attempted_total {self._restarts_attempted}",
            "",
            "# HELP aegentix_healing_restarts_succeeded_total Successful restarts.",
            "# TYPE aegentix_healing_restarts_succeeded_total counter",
            f"aegentix_healing_restarts_succeeded_total {self._restarts_succeeded}",
            "",
            "# HELP aegentix_healing_restarts_failed_total Failed restarts.",
            "# TYPE aegentix_healing_restarts_failed_total counter",
            f"aegentix_healing_restarts_failed_total {self._restarts_failed}",
            "",
            "# HELP aegentix_healing_health_checks_performed_total Health checks performed.",
            "# TYPE aegentix_healing_health_checks_performed_total counter",
            f"aegentix_healing_health_checks_performed_total {self._health_checks_performed}",
            "",
            "# HELP aegentix_healing_health_checks_failed_total Failed health checks.",
            "# TYPE aegentix_healing_health_checks_failed_total counter",
            f"aegentix_healing_health_checks_failed_total {self._health_checks_failed}",
            "",
            "# HELP aegentix_healing_drains_performed_total Drains performed.",
            "# TYPE aegentix_healing_drains_performed_total counter",
            f"aegentix_healing_drains_performed_total {self._drains_performed}",
            "",
            "# HELP aegentix_healing_unhealthy_services_count Currently unhealthy services.",
            "# TYPE aegentix_healing_unhealthy_services_count gauge",
            f"aegentix_healing_unhealthy_services_count {sum(1 for s in self._service_health.values() if not s.get('healthy'))}",
            "",
            "# HELP aegentix_healing_up Agent is alive and serving metrics.",
            "# TYPE aegentix_healing_up gauge",
            "aegentix_healing_up 1",
            "",
        ]
        return "\n".join(lines)

    class _MetricsHandler(http.server.BaseHTTPRequestHandler):
        agent_ref: Optional["HealingAgent"] = None

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
                    "agent": "healing",
                    "uptime_seconds": time.time() - self.agent_ref._started_at,
                    "integrity_score": self.agent_ref._integrity_score,
                    "restarts_attempted": self.agent_ref._restarts_attempted,
                    "restarts_succeeded": self.agent_ref._restarts_succeeded,
                    "restarts_failed": self.agent_ref._restarts_failed,
                    "health_checks_failed": self.agent_ref._health_checks_failed,
                    "drains_performed": self.agent_ref._drains_performed,
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
        log.info("Healing agent starting (role=%s, integrity=%.1f)", self.ROLE, self.integrity_score)
        self._log_event({"event_type": "agent_start", "message": "Healing agent started"})

        self._start_metrics_server()

        # Track consecutive failure counts per service.
        consecutive_failures: Dict[str, int] = {}
        service_retry_counts: Dict[str, int] = {}

        try:
            while not self._stop_event.is_set():
                cycle_start = time.time()
                hc = self.config.get("health_checks", {})
                interval = hc.get("interval_seconds", 15)

                for service in self.config.get("services", []):
                    name = service["name"]
                    check_start = time.time()

                    result = self._perform_health_check(service)
                    self._service_health[name] = result
                    check_duration = time.time() - check_start
                    self._record_operation("health_check", check_duration)

                    # Track consecutive failures.
                    if result["healthy"]:
                        consecutive_failures[name] = 0
                        service_retry_counts[name] = 0
                    else:
                        consecutive_failures[name] = consecutive_failures.get(name, 0) + 1

                    # If unhealthy for enough consecutive checks, trigger healing.
                    if self._is_unhealthy(service, consecutive_failures.get(name, 0)):
                        log.warning("Service %s is unhealthy (%d consecutive failures) — initiating healing",
                                    name, consecutive_failures[name])

                        # 1. Drain (if enabled and not protected).
                        if service.get("drain_protected", False):
                            log.info("Skipping drain for protected service %s", name)
                            drain_result = {"drained": False, "reason": "protected"}
                        else:
                            drain_result = self._drain_service(service)

                        # 2. Restart with retry/backoff.
                        restart_result = self._restart_service(service)

                        service_retry_counts[name] = service_retry_counts.get(name, 0) + 1
                        if service_retry_counts[name] >= self.config.get("restart_policy", {}).get("max_retries", 3):
                            # Reset retry counter after a full cycle.
                            pass

                        self._log_event({
                            "event_type": "healing_cycle",
                            "service": name,
                            "consecutive_failures": consecutive_failures[name],
                            "drain_result": drain_result,
                            "restart_result": restart_result,
                        })

                        # Reset failure counter after a healing attempt.
                        consecutive_failures[name] = 0

                # Integrity maintenance.
                self._integrity_score = min(100.0, self._integrity_score + 0.05)

                # Sleep until next health-check cycle.
                self._stop_event.wait(interval)
        except KeyboardInterrupt:
            log.info("Healing agent interrupted")
        finally:
            self._log_event({"event_type": "agent_stop", "message": "Healing agent stopped"})
            self._stop_metrics_server()
            log.info("Healing agent shut down")


def main():
    agent = HealingAgent()
    agent.run()


if __name__ == "__main__":
    main()

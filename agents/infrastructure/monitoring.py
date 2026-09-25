#!/usr/bin/env python3
"""Aegentix Monitoring Agent — infrastructure health observability.

Subclass of AutonomousAgent with a run() loop performing role work,
recording events to orchestrator/events/monitoring.jsonl, and exposing
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
from datetime import datetime
from typing import Dict, Any, Optional

# ── Pull AutonomousAgent from the project's swarm engine ──────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from autonomous_swarm import AutonomousAgent

LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
log = logging.getLogger("aegentix.monitoring")


class MonitoringAgent(AutonomousAgent):
    """Infrastructure monitoring agent — scrapes, thresholds, alerts."""

    ROLE = "monitoring"
    METRICS_PORT = 8080
    CONFIG_PATH = os.path.join(
        os.path.dirname(__file__), "config", "monitoring.yml"
    )
    EVENTS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "orchestrator", "events", "monitoring.jsonl",
    )

    def __init__(self):
        super().__init__(
            name="MonitoringAgent",
            purpose="Observe infrastructure health and emit alerts",
            values=["reliability", "observability", "fast-detection", "accuracy"],
        )
        self.config: Dict[str, Any] = self._load_config()
        self.metrics_lock = threading.Lock()
        self._ops_total = 0
        self._ops_duration_sum = 0.0
        self._integrity_score = 100.0
        self._started_at = time.time()
        self._scrape_count = 0
        self._alert_count = 0
        self._runbooks_checked = 0
        self._last_health_check = None
        self._health_check_failures = 0
        self._stop_event = threading.Event()
        self._metrics_server = None

    # ── config ────────────────────────────────────────────────────────────────

    def _load_config(self) -> Dict[str, Any]:
        """Load monitoring.yml; fall back to embedded defaults if missing."""
        defaults = {
            "scrape": {
                "interval_seconds": 15,
                "targets": ["localhost:9090", "localhost:3001", "localhost:9200"],
                "timeout_seconds": 10,
            },
            "alert_thresholds": {
                "cpu_percent": 85.0,
                "memory_percent": 90.0,
                "disk_percent": 80.0,
                "response_latency_ms": 5000,
                "error_rate_percent": 5.0,
                "container_restart_count": 3,
            },
            "grafana": {
                "dashboard_url": "http://grafana:3000/d/aegentix-fleet/agents",
                "refresh_seconds": 30,
                "panels": [
                    "aegentix_agent_uptime",
                    "aegentix_agent_integrity",
                    "aegentix_agent_operations_total",
                ],
            },
            "reporting": {
                "event_log_path": self.EVENTS_PATH,
                "max_events_per_file": 10000,
                "rotate_daily": True,
            },
        }
        try:
            with open(self.CONFIG_PATH, "r") as f:
                loaded = yaml.safe_load(f) or {}
            # deep-merge: env config wins over defaults
            return self._deep_merge(defaults, loaded)
        except Exception as exc:
            log.warning("Could not load %s (%s); using defaults", self.CONFIG_PATH, exc)
            return defaults

    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        merged = base.copy()
        for k, v in override.items():
            if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
                merged[k] = MonitoringAgent._deep_merge(merged[k], v)
            else:
                merged[k] = v
        return merged

    # ── event log ─────────────────────────────────────────────────────────────

    def _log_event(self, event: Dict[str, Any]) -> None:
        """Append a JSONL record to the monitoring event log."""
        event.setdefault("timestamp", datetime.now().isoformat())
        event.setdefault("agent", self.ROLE)
        event.setdefault("agent_name", self.name)
        try:
            os.makedirs(os.path.dirname(self.EVENTS_PATH), exist_ok=True)
            with open(self.EVENTS_PATH, "a") as f:
                f.write(json.dumps(event, default=str) + "\n")
        except Exception as exc:
            log.error("Failed to write monitoring event: %s", exc)

    # ── role work ─────────────────────────────────────────────────────────────

    def _scrape_targets(self) -> Dict[str, Any]:
        """Simulate scraping monitored targets and collect health data."""
        scrape = self.config.get("scrape", {})
        interval = scrape.get("interval_seconds", 15)
        targets = scrape.get("targets", [])
        timeout = scrape.get("timeout_seconds", 10)

        results = {}
        for target in targets:
            try:
                # In real deployment this would be an HTTP/TCP health check.
                # For standalone operation we record a synthetic healthy value.
                results[target] = {
                    "status": "healthy",
                    "latency_ms": 2.4,
                    "scraped_at": datetime.now().isoformat(),
                }
                self._scrape_count += 1
            except Exception as exc:
                results[target] = {
                    "status": "error",
                    "error": str(exc),
                    "scraped_at": datetime.now().isoformat(),
                }
                self._health_check_failures += 1
        self._last_health_check = datetime.now().isoformat()
        return results

    def _evaluate_thresholds(self, scrape_results: Dict[str, Any]) -> list:
        """Return a list of triggered alerts based on threshold config."""
        thresholds = self.config.get("alert_thresholds", {})
        triggered = []

        # CPU alert (simulated: use a small periodic spike for demo purposes)
        cpu = (time.time() % 60) / 60.0 * 100.0  # 0-100 sawtooth
        if cpu > thresholds.get("cpu_percent", 85.0):
            triggered.append({
                "severity": "warning",
                "metric": "cpu_percent",
                "value": round(cpu, 1),
                "threshold": thresholds["cpu_percent"],
                "message": f"CPU usage {cpu:.1f}% exceeds threshold {thresholds['cpu_percent']}%",
            })
            self._alert_count += 1

        # Memory alert (simulated)
        mem = 70.0 + (time.time() % 30) / 30.0 * 25.0  # 70-95%
        if mem > thresholds.get("memory_percent", 90.0):
            triggered.append({
                "severity": "critical",
                "metric": "memory_percent",
                "value": round(mem, 1),
                "threshold": thresholds["memory_percent"],
                "message": f"Memory usage {mem:.1f}% exceeds threshold {thresholds['memory_percent']}%",
            })
            self._alert_count += 1

        # Disk alert (stable low for demo)
        disk = 55.0
        if disk > thresholds.get("disk_percent", 80.0):
            triggered.append({
                "severity": "warning",
                "metric": "disk_percent",
                "value": disk,
                "threshold": thresholds["disk_percent"],
                "message": f"Disk usage {disk}% exceeds threshold {thresholds['disk_percent']}%",
            })

        # Check for container restart storms from scrape results
        for target, data in scrape_results.items():
            if data.get("status") == "error":
                triggered.append({
                    "severity": "critical",
                    "metric": "target_unreachable",
                    "target": target,
                    "message": f"Target {target} unreachable during scrape",
                })
                self._alert_count += 1

        return triggered

    def _emit_alerts(self, alerts: list) -> None:
        """Record triggered alerts to the event log."""
        for alert in alerts:
            self._log_event({
                "event_type": "alert",
                "severity": alert.get("severity", "info"),
                "metric": alert.get("metric", "unknown"),
                "message": alert.get("message", ""),
                "details": alert,
            })

    def _record_operation(self, op_name: str, duration: float) -> None:
        """Track a completed operation for Prometheus metrics."""
        with self.metrics_lock:
            self._ops_total += 1
            self._ops_duration_sum += duration

    # ── metrics HTTP server ───────────────────────────────────────────────────

    def _build_prometheus_metrics(self) -> str:
        """Return the full Prometheus text format exposition."""
        with self.metrics_lock:
            uptime = time.time() - self._started_at
            avg_duration = (
                self._ops_duration_sum / self._ops_total
                if self._ops_total > 0 else 0.0
            )
            integrity = self._integrity_score

        lines = [
            "# HELP aegentix_monitoring_operations_total Total operations performed.",
            "# TYPE aegentix_monitoring_operations_total counter",
            f"aegentix_monitoring_operations_total {self._ops_total}",
            "",
            "# HELP aegentix_monitoring_operations_duration_seconds Total duration of operations in seconds.",
            "# TYPE aegentix_monitoring_operations_duration_seconds counter",
            f"aegentix_monitoring_operations_duration_seconds {self._ops_duration_sum:.6f}",
            "",
            "# HELP aegentix_monitoring_integrity_score Current integrity score (0-100).",
            "# TYPE aegentix_monitoring_integrity_score gauge",
            f"aegentix_monitoring_integrity_score {integrity}",
            "",
            "# HELP aegentix_monitoring_scrape_count Total scrape operations performed.",
            "# TYPE aegentix_monitoring_scrape_count counter",
            f"aegentix_monitoring_scrape_count {self._scrape_count}",
            "",
            "# HELP aegentix_monitoring_alert_count Total alerts triggered.",
            "# TYPE aegentix_monitoring_alert_count counter",
            f"aegentix_monitoring_alert_count {self._alert_count}",
            "",
            "# HELP aegentix_monitoring_health_check_failures Total failed health checks.",
            "# TYPE aegentix_monitoring_health_check_failures counter",
            f"aegentix_monitoring_health_check_failures {self._health_check_failures}",
            "",
            "# HELP aegentix_monitoring_up Agent is alive and serving metrics.",
            "# TYPE aegentix_monitoring_up gauge",
            "aegentix_monitoring_up 1",
            "",
        ]
        return "\n".join(lines)

    class _MetricsHandler(http.server.BaseHTTPRequestHandler):
        """HTTP handler serving Prometheus /metrics and /health."""

        agent_ref: Optional["MonitoringAgent"] = None

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
                    "agent": "monitoring",
                    "uptime_seconds": time.time() - self.agent_ref._started_at,
                    "integrity_score": self.agent_ref._integrity_score,
                    "scrapes": self.agent_ref._scrape_count,
                    "alerts": self.agent_ref._alert_count,
                })
                self.wfile.write(payload.encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not found")

        def log_message(self, format, *args):
            # Suppress default HTTP request logs; agent logs handle observability.
            pass

    def _start_metrics_server(self) -> None:
        """Start the metrics HTTP server on port 8080 in a daemon thread."""
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
        """Main run loop: scrape, evaluate, alert, sleep."""
        log.info("Monitoring agent starting (role=%s, integrity=%.1f)", self.ROLE, self.integrity_score)
        self._log_event({"event_type": "agent_start", "message": "Monitoring agent started"})

        self._start_metrics_server()

        try:
            while not self._stop_event.is_set():
                cycle_start = time.time()

                # 1. Scrape targets
                scrape_results = self._scrape_targets()
                duration_scrape = time.time() - cycle_start
                self._record_operation("scrape", duration_scrape)
                self._log_event({
                    "event_type": "scrape_cycle",
                    "targets_scraped": len(scrape_results),
                    "duration_seconds": round(duration_scrape, 4),
                    "results": scrape_results,
                })

                # 2. Evaluate thresholds
                alerts = self._evaluate_thresholds(scrape_results)
                duration_eval = time.time() - cycle_start - duration_scrape
                self._record_operation("evaluate_thresholds", duration_eval)

                # 3. Emit alerts
                if alerts:
                    self._emit_alerts(alerts)
                    self._log_event({
                        "event_type": "alert_cycle",
                        "alerts_count": len(alerts),
                    })

                # 4. Integrity maintenance
                self._integrity_score = min(100.0, self._integrity_score + 0.1)

                # 5. Sleep until next scrape
                sleep_for = self.config.get("scrape", {}).get("interval_seconds", 15)
                self._stop_event.wait(sleep_for)
        except KeyboardInterrupt:
            log.info("Monitoring agent interrupted")
        finally:
            self._log_event({"event_type": "agent_stop", "message": "Monitoring agent stopped"})
            self._stop_metrics_server()
            log.info("Monitoring agent shut down")


def main():
    agent = MonitoringAgent()
    agent.run()


if __name__ == "__main__":
    main()

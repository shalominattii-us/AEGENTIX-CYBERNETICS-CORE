#!/usr/bin/env python3
"""Aegentix Incident Response Agent — severity escalation, runbooks, Slack.

Subclass of AutonomousAgent with a run() loop performing role work,
recording events to orchestrator/events/incident_response.jsonl, and exposing
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
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from autonomous_swarm import AutonomousAgent

LOG_LEVEL = os.environ.get("LOG_LEVEL", "info").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
)
log = logging.getLogger("aegentix.incident_response")


class IncidentResponseAgent(AutonomousAgent):
    """Incident response — escalate, execute runbooks, notify Slack."""

    ROLE = "incident-response"
    METRICS_PORT = 8080
    CONFIG_PATH = os.path.join(
        os.path.dirname(__file__), "config", "incident-response.yml"
    )
    EVENTS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "orchestrator", "events", "incident_response.jsonl",
    )

    # Severity ordering for escalation decisions.
    SEVERITY_ORDER = ["info", "warning", "critical", "disaster"]

    def __init__(self):
        super().__init__(
            name="IncidentResponseAgent",
            purpose="Respond to infrastructure incidents with runbooks and escalation",
            values=["responsiveness", "clarity", "accountability", "escalation"],
        )
        self.config: Dict[str, Any] = self._load_config()
        self.metrics_lock = threading.Lock()
        self._ops_total = 0
        self._ops_duration_sum = 0.0
        self._integrity_score = 100.0
        self._started_at = time.time()
        self._escalations_total = 0
        self._runbooks_executed = 0
        self._incidents_acknowledged = 0
        self._incidents_resolved = 0
        self._pending_incidents: List[Dict[str, Any]] = []
        self._stop_event = threading.Event()
        self._metrics_server = None

    # ── config ────────────────────────────────────────────────────────────────

    def _load_config(self) -> Dict[str, Any]:
        defaults = {
            "severity_escalation_matrix": {
                "info": {
                    "auto_escalate_to": None,
                    "notification_channels": ["log"],
                    "response_timeout_minutes": 60,
                },
                "warning": {
                    "auto_escalate_to": "critical",
                    "notification_channels": ["log", "slack"],
                    "response_timeout_minutes": 30,
                    "require_acknowledgement": True,
                },
                "critical": {
                    "auto_escalate_to": "disaster",
                    "notification_channels": ["log", "slack", "pagerduty"],
                    "response_timeout_minutes": 10,
                    "require_acknowledgement": True,
                    "auto_runbook": True,
                },
                "disaster": {
                    "auto_escalate_to": None,
                    "notification_channels": ["log", "slack", "pagerduty", "phone"],
                    "response_timeout_minutes": 5,
                    "require_acknowledgement": True,
                    "auto_runbook": True,
                    "activate_countermeasures": True,
                },
            },
            "slack": {
                "webhook_url_env": "SLACK_WEBHOOK_URL",
                "default_channel": "#aegentix-incidents",
                "username": "aegentix-ir-bot",
                "icon_emoji": ":warning:",
                "message_template": (
                    "🚨 *{severity_upper}* incident on *{target}*\n"
                    "```\n{message}\n```\n"
                    "Runbook: {runbook_url}\n"
                    "Escalating to: {escalates_to}"
                ),
            },
            "runbooks": {
                "base_url": "https://runbooks.aegentix.internal/incidents",
                "catalog": {
                    "cpu_spike": "https://runbooks.aegentix.internal/incidents/cpu-spike",
                    "memory_pressure": "https://runbooks.aegentix.internal/incidents/memory-pressure",
                    "disk_full": "https://runbooks.aegentix.internal/incidents/disk-full",
                    "target_unreachable": "https://runbooks.aegentix.internal/incidents/target-unreachable",
                    "container_restart_loop": "https://runbooks.aegentix.internal/incidents/container-restart-loop",
                    "certificate_expiry": "https://runbooks.aegentix.internal/incidents/cert-expiry",
                    "certificate_revoked": "https://runbooks.aegentix.internal/incidents/cert-revoked",
                    "database_connection_pool_exhausted": "https://runbooks.aegentix.internal/incidents/db-pool-exhausted",
                },
                "fallback_runbook": "https://runbooks.aegentix.internal/incidents/generic",
            },
            "deduplication": {
                "window_seconds": 300,
                "hash_fields": ["metric", "target", "message"],
            },
            "acknowledgement": {
                "required_for": ["warning", "critical", "disaster"],
                "timeout_seconds": 600,
            },
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
                merged[k] = IncidentResponseAgent._deep_merge(merged[k], v)
            else:
                merged[k] = v
        return merged

    # ── helpers ───────────────────────────────────────────────────────────────

    def _incident_key(self, incident: Dict[str, Any]) -> str:
        """Deterministic key for deduplication."""
        fields = self.config.get("deduplication", {}).get("hash_fields", [])
        parts = [str(incident.get(f, "")) for f in fields]
        digest = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
        return digest

    def _severity_rank(self, severity: str) -> int:
        try:
            return self.SEVERITY_ORDER.index(severity.lower())
        except ValueError:
            return len(self.SEVERITY_ORDER)

    def _should_escalate(self, incident: Dict[str, Any]) -> Optional[str]:
        matrix = self.config.get("severity_escalation_matrix", {})
        sev = incident.get("severity", "info")
        entry = matrix.get(sev, {})
        return entry.get("auto_escalate_to")

    def _runbook_url_for(self, incident: Dict[str, Any]) -> str:
        catalog = self.config.get("runbooks", {}).get("catalog", {})
        metric = incident.get("metric", "")
        return catalog.get(metric, self.config.get("runbooks", {}).get("fallback_runbook", ""))

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
            log.error("Failed to write incident event: %s", exc)

    # ── Slack notification (placeholder) ──────────────────────────────────────

    def _notify_slack(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Build a Slack webhook payload (posting requires SLACK_WEBHOOK_URL env; stubbed here)."""
        slack_cfg = self.config.get("slack", {})
        webhook_env = slack_cfg.get("webhook_url_env", "SLACK_WEBHOOK_URL")
        webhook_url = os.environ.get(webhook_env)
        template = slack_cfg.get("message_template", "")
        severity_upper = incident.get("severity", "info").upper()
        message = template.format(
            severity_upper=severity_upper,
            target=incident.get("target", "unknown"),
            message=incident.get("message", ""),
            runbook_url=self._runbook_url_for(incident),
            escalates_to=self._should_escalate(incident) or "none",
        )
        result = {
            "channel": slack_cfg.get("default_channel", "#aegentix-incidents"),
            "username": slack_cfg.get("username", "aegentix-ir-bot"),
            "icon_emoji": slack_cfg.get("icon_emoji", ":warning:"),
            "payload": message,
            "webhook_configured": bool(webhook_url),
        }
        if webhook_url:
            # In production this would POST to the webhook URL. Stubbed for standalone.
            log.info("Slack webhook configured (%s); not posting in standalone mode", webhook_env)
        else:
            log.info("No SLACK_WEBHOOK_URL set; incident notification queued for manual dispatch")
        return result

    # ── runbook execution (placeholder) ───────────────────────────────────────

    def _execute_runbook(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Record that a runbook would be executed; in production this invokes infra automation."""
        url = self._runbook_url_for(incident)
        self._runbooks_executed += 1
        result = {
            "runbook_url": url,
            "status": "executed",
            "incident_id": incident.get("incident_id", self._incident_key(incident)),
            "executed_at": datetime.now().isoformat(),
            "actions_taken": ["logged", "notification_queued"],
        }
        self._log_event({
            "event_type": "runbook_executed",
            "runbook_url": url,
            "incident_id": result["incident_id"],
        })
        return result

    # ── core incident handling ─────────────────────────────────────────────────

    def _process_incident(self, incident: Dict[str, Any]) -> None:
        """Handle a single incoming incident through the escalation matrix."""
        now = datetime.now()
        incident.setdefault("incident_id", self._incident_key(incident))
        incident.setdefault("created_at", now.isoformat())
        incident.setdefault("status", "new")
        incident.setdefault("acknowledged", False)
        incident.setdefault("resolved", False)

        severity = incident.get("severity", "info")
        rank = self._severity_rank(severity)
        self._incidents_acknowledged += 1
        incident["acknowledged"] = True
        incident["acknowledged_at"] = now.isoformat()
        incident["status"] = "acknowledged"

        self._log_event({
            "event_type": "incident_acknowledged",
            "incident_id": incident["incident_id"],
            "severity": severity,
            "message": incident.get("message", ""),
        })

        # Determine if the escalation matrix mandates a runbook.
        matrix = self.config.get("severity_escalation_matrix", {})
        entry = matrix.get(severity, {})
        if entry.get("auto_runbook"):
            runbook_result = self._execute_runbook(incident)
            incident["runbook_result"] = runbook_result

        # Notify Slack if configured in the matrix.
        channels = entry.get("notification_channels", [])
        if "slack" in channels:
            slack_result = self._notify_slack(incident)
            incident["slack_notification"] = slack_result

        # Escalate if the matrix says so.
        escalates_to = self._should_escalate(incident)
        if escalates_to:
            self._escalations_total += 1
            escalated = {
                "original_incident_id": incident["incident_id"],
                "original_severity": severity,
                "escalated_to": escalates_to,
                "escalated_at": now.isoformat(),
                "message": incident.get("message", ""),
                "metric": incident.get("metric", ""),
                "target": incident.get("target", "unknown"),
            }
            escalated["severity"] = escalates_to
            self._log_event({
                "event_type": "incident_escalated",
                "from_severity": severity,
                "to_severity": escalates_to,
                "incident_id": incident["incident_id"],
            })
            # Recursively process the escalated incident.
            self._process_incident(escalated)

        # Mark resolved after handling.
        incident["status"] = "resolved"
        incident["resolved_at"] = now.isoformat()
        incident["resolved"] = True
        self._incidents_resolved += 1

    # ── simulate incoming incidents ───────────────────────────────────────────

    def _generate_simulated_incidents(self) -> List[Dict[str, Any]]:
        """Generate a limited set of synthetic incidents for standalone demonstration."""
        incidents = []
        now = datetime.now()

        # CPU spike every ~90 seconds in simulation time.
        if (int(now.timestamp()) % 90) < 5:
            incidents.append({
                "severity": "critical",
                "metric": "cpu_spike",
                "target": "agent-monitoring",
                "message": "CPU usage exceeded 90% on agent-monitoring container",
                "source": "simulated",
            })

        # Memory pressure every ~120 seconds.
        if (int(now.timestamp()) % 120) < 5:
            incidents.append({
                "severity": "warning",
                "metric": "memory_pressure",
                "target": "agent-deployment",
                "message": "Memory usage at 88% on agent-deployment; approaching threshold",
                "source": "simulated",
            })

        # Occasional disk alert.
        if (int(now.timestamp()) % 200) < 5:
            incidents.append({
                "severity": "info",
                "metric": "disk_full",
                "target": "elasticsearch",
                "message": "Disk usage at 72% on elasticsearch data volume",
                "source": "simulated",
            })

        # Target unreachable (simulated network blip).
        if (int(now.timestamp()) % 60) < 2:
            incidents.append({
                "severity": "critical",
                "metric": "target_unreachable",
                "target": "prometheus:9090",
                "message": "Prometheus scrape target unreachable — possible network partition",
                "source": "simulated",
            })

        return incidents

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
            "# HELP aegentix_incident_response_operations_total Total operations performed.",
            "# TYPE aegentix_incident_response_operations_total counter",
            f"aegentix_incident_response_operations_total {self._ops_total}",
            "",
            "# HELP aegentix_incident_response_operations_duration_seconds Total duration of operations in seconds.",
            "# TYPE aegentix_incident_response_operations_duration_seconds counter",
            f"aegentix_incident_response_operations_duration_seconds {self._ops_duration_sum:.6f}",
            "",
            "# HELP aegentix_incident_response_integrity_score Current integrity score (0-100).",
            "# TYPE aegentix_incident_response_integrity_score gauge",
            f"aegentix_incident_response_integrity_score {integrity}",
            "",
            "# HELP aegentix_incident_response_escalations_total Total escalations performed.",
            "# TYPE aegentix_incident_response_escalations_total counter",
            f"aegentix_incident_response_escalations_total {self._escalations_total}",
            "",
            "# HELP aegentix_incident_response_runbooks_executed_total Runbooks executed.",
            "# TYPE aegentix_incident_response_runbooks_executed_total counter",
            f"aegentix_incident_response_runbooks_executed_total {self._runbooks_executed}",
            "",
            "# HELP aegentix_incident_response_incidents_acknowledged_total Incidents acknowledged.",
            "# TYPE aegentix_incident_response_incidents_acknowledged_total counter",
            f"aegentix_incident_response_incidents_acknowledged_total {self._incidents_acknowledged}",
            "",
            "# HELP aegentix_incident_response_incidents_resolved_total Incidents resolved.",
            "# TYPE aegentix_incident_response_incidents_resolved_total counter",
            f"aegentix_incident_response_incidents_resolved_total {self._incidents_resolved}",
            "",
            "# HELP aegentix_incident_response_pending_incidents Currently pending incidents.",
            "# TYPE aegentix_incident_response_pending_incidents gauge",
            f"aegentix_incident_response_pending_incidents {len(self._pending_incidents)}",
            "",
            "# HELP aegentix_incident_response_up Agent is alive and serving metrics.",
            "# TYPE aegentix_incident_response_up gauge",
            "aegentix_incident_response_up 1",
            "",
        ]
        return "\n".join(lines)

    class _MetricsHandler(http.server.BaseHTTPRequestHandler):
        agent_ref: Optional["IncidentResponseAgent"] = None

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
                    "agent": "incident-response",
                    "uptime_seconds": time.time() - self.agent_ref._started_at,
                    "integrity_score": self.agent_ref._integrity_score,
                    "escalations": self.agent_ref._escalations_total,
                    "runbooks": self.agent_ref._runbooks_executed,
                    "pending": len(self.agent_ref._pending_incidents),
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
        log.info("Incident response agent starting (role=%s, integrity=%.1f)", self.ROLE, self.integrity_score)
        self._log_event({"event_type": "agent_start", "message": "Incident response agent started"})

        self._start_metrics_server()

        try:
            while not self._stop_event.is_set():
                cycle_start = time.time()

                # 1. Accept incoming incidents (simulated).
                new_incidents = self._generate_simulated_incidents()
                if new_incidents:
                    for inc in new_incidents:
                        # Deduplication: skip if we've seen this key recently.
                        key = self._incident_key(inc)
                        recent = any(
                            i.get("incident_id") == key
                            for i in self._pending_incidents[-20:]
                        )
                        if not recent:
                            self._pending_incidents.append(inc)
                            self._record_operation("accept_incident", time.time() - cycle_start)
                            self._process_incident(inc)
                            cycle_start = time.time()
                        else:
                            self._log_event({
                                "event_type": "incident_deduped",
                                "incident_key": key,
                            })

                # 2. Reconcile pending incidents (acked but not yet resolved).
                still_pending = [i for i in self._pending_incidents if not i.get("resolved")]
                self._pending_incidents = still_pending[-50:]  # cap backlog

                # 3. Integrity maintenance.
                self._integrity_score = min(100.0, self._integrity_score + 0.05)

                # 4. Sleep.
                self._stop_event.wait(10)
        except KeyboardInterrupt:
            log.info("Incident response agent interrupted")
        finally:
            self._log_event({"event_type": "agent_stop", "message": "Incident response agent stopped"})
            self._stop_metrics_server()
            log.info("Incident response agent shut down")


def main():
    agent = IncidentResponseAgent()
    agent.run()


if __name__ == "__main__":
    main()

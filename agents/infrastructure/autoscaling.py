#!/usr/bin/env python3
"""Aegentix Autoscaling Agent — CPU/mem thresholds, min/max instances, cooldown.

Subclass of AutonomousAgent with a run() loop performing role work,
recording events to orchestrator/events/autoscaling.jsonl, and exposing
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
log = logging.getLogger("aegentix.autoscaling")


class AutoscalingAgent(AutonomousAgent):
    """Autoscaling agent — scale services up/down based on resource thresholds."""

    ROLE = "autoscaling"
    METRICS_PORT = 8080
    CONFIG_PATH = os.path.join(
        os.path.dirname(__file__), "config", "autoscaling.yml"
    )
    EVENTS_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "orchestrator", "events", "autoscaling.jsonl",
    )

    def __init__(self):
        super().__init__(
            name="AutoscalingAgent",
            purpose="Automatically scale infrastructure services based on load",
            values=["efficiency", "responsiveness", "stability", "cost-awareness"],
        )
        self.config: Dict[str, Any] = self._load_config()
        self.metrics_lock = threading.Lock()
        self._ops_total = 0
        self._ops_duration_sum = 0.0
        self._integrity_score = 100.0
        self._started_at = time.time()
        self._scale_ups = 0
        self._scale_downs = 0
        self._scale_operations_total = 0
        self._cooldown_active = False
        self._cooldown_until = 0.0
        self._current_replicas: Dict[str, int] = {}
        self._last_metrics: Dict[str, Dict[str, float]] = {}
        self._stop_event = threading.Event()
        self._metrics_server = None
        # Initialise replica counts from config.
        for svc in self.config.get("services", []):
            self._current_replicas[svc["name"]] = svc.get("initial_replicas", svc.get("min_instances", 1))

    # ── config ────────────────────────────────────────────────────────────────

    def _load_config(self) -> Dict[str, Any]:
        defaults = {
            "services": [
                {
                    "name": "aegentix-api",
                    "metric_source": "simulated",
                    "cpu_threshold_percent": 70.0,
                    "memory_threshold_percent": 80.0,
                    "min_instances": 2,
                    "max_instances": 10,
                    "initial_replicas": 2,
                    "cooldown_seconds": 120,
                    "scale_up_increment": 1,
                    "scale_down_increment": 1,
                    "evaluation_interval_seconds": 30,
                },
                {
                    "name": "aegentix-workers",
                    "metric_source": "simulated",
                    "cpu_threshold_percent": 75.0,
                    "memory_threshold_percent": 85.0,
                    "min_instances": 1,
                    "max_instances": 20,
                    "initial_replicas": 3,
                    "cooldown_seconds": 90,
                    "scale_up_increment": 2,
                    "scale_down_increment": 1,
                    "evaluation_interval_seconds": 30,
                },
                {
                    "name": "aegentix-monitor-stack",
                    "metric_source": "simulated",
                    "cpu_threshold_percent": 80.0,
                    "memory_threshold_percent": 85.0,
                    "min_instances": 1,
                    "max_instances": 5,
                    "initial_replicas": 1,
                    "cooldown_seconds": 180,
                    "scale_up_increment": 1,
                    "scale_down_increment": 1,
                    "evaluation_interval_seconds": 45,
                },
            ],
            "global": {
                "max_scale_up_rate_per_minute": 5,
                "prefer_scale_down_at_night": True,
                "night_start_hour": 22,
                "night_end_hour": 6,
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
                merged[k] = AutoscalingAgent._deep_merge(merged[k], v)
            else:
                merged[k] = v
        return merged

    # ── helpers ───────────────────────────────────────────────────────────────

    def _is_night_time(self) -> bool:
        """Return True if current hour falls in the night window (scale-down preference)."""
        cfg = self.config.get("global", {})
        if not cfg.get("prefer_scale_down_at_night"):
            return False
        hour = datetime.now().hour
        start = cfg.get("night_start_hour", 22)
        end = cfg.get("night_end_hour", 6)
        if start > end:
            return hour >= start or hour < end
        return start <= hour < end

    def _metric_value_for(self, service: Dict[str, Any]) -> Dict[str, float]:
        """Return simulated CPU/memory metrics for a service (standalone mode)."""
        name = service["name"]
        # Deterministic-ish time-based variation so the agent sees scale-up/scale-down opportunities.
        t = time.time()
        cpu = 40.0 + 35.0 * abs(__import__("math").sin(t / 60.0 + hash(name) % 10))
        mem = 50.0 + 30.0 * abs(__import__("math").cos(t / 45.0 + hash(name + "m") % 10))
        # Occasionally spike above threshold.
        if (int(t) % 150) < 8:
            cpu = min(98.0, cpu + 25.0)
        if (int(t) % 200) < 8:
            mem = min(97.0, mem + 20.0)
        return {"cpu_percent": round(cpu, 1), "memory_percent": round(mem, 1)}

    def _in_cooldown(self) -> bool:
        now = time.time()
        if now >= self._cooldown_until:
            self._cooldown_active = False
            return False
        self._cooldown_active = True
        return True

    def _enter_cooldown(self, service_name: str, cooldown_seconds: float) -> None:
        self._cooldown_until = time.time() + cooldown_seconds
        self._cooldown_active = True
        log.info("Cooldown entered for %s until %.1f", service_name, self._cooldown_until)

    # ── scaling decisions ─────────────────────────────────────────────────────

    def _decide_scale(self, service: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Decide whether to scale up or down for a service; returns action dict or None."""
        name = service["name"]
        metrics = self._metric_value_for(service)
        self._last_metrics[name] = metrics

        cpu = metrics["cpu_percent"]
        mem = metrics["memory_percent"]
        cpu_thresh = service.get("cpu_threshold_percent", 70.0)
        mem_thresh = service.get("memory_threshold_percent", 80.0)
        current = self._current_replicas.get(name, service.get("min_instances", 1))
        min_inst = service.get("min_instances", 1)
        max_inst = service.get("max_instances", 10)
        cooldown = service.get("cooldown_seconds", 120)
        scale_up_inc = service.get("scale_up_increment", 1)
        scale_down_inc = service.get("scale_down_increment", 1)

        # Scale-up: either CPU or memory exceeds threshold.
        if (cpu > cpu_thresh or mem > mem_thresh) and current < max_inst:
            if self._in_cooldown():
                log.info("Scale-up for %s skipped: in cooldown", name)
                return None
            new_count = min(max_inst, current + scale_up_inc)
            if new_count > current:
                action = {
                    "service": name,
                    "action": "scale_up",
                    "current_replicas": current,
                    "target_replicas": new_count,
                    "cpu_percent": cpu,
                    "memory_percent": mem,
                    "cpu_threshold": cpu_thresh,
                    "memory_threshold": mem_thresh,
                    "cooldown_seconds": cooldown,
                }
                self._current_replicas[name] = new_count
                self._enter_cooldown(name, cooldown)
                return action

        # Scale-down: both CPU and memory comfortably below threshold, and not at minimum.
        if cpu < cpu_thresh * 0.6 and mem < mem_thresh * 0.6 and current > min_inst:
            if self._in_cooldown():
                log.info("Scale-down for %s skipped: in cooldown", name)
                return None
            # Prefer scale-down at night.
            if self._is_night_time() or current > min_inst + 2:
                new_count = max(min_inst, current - scale_down_inc)
                if new_count < current:
                    action = {
                        "service": name,
                        "action": "scale_down",
                        "current_replicas": current,
                        "target_replicas": new_count,
                        "cpu_percent": cpu,
                        "memory_percent": mem,
                        "cpu_threshold": cpu_thresh,
                        "memory_threshold": mem_thresh,
                        "cooldown_seconds": cooldown,
                    }
                    self._current_replicas[name] = new_count
                    self._enter_cooldown(name, cooldown)
                    return action

        return None

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
            log.error("Failed to write autoscaling event: %s", exc)

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

        replica_lines = []
        for name, count in self._current_replicas.items():
            replica_lines.append(
                f"# HELP aegentix_autoscaling_replicas_service_{name} Current replicas for {name}."
            )
            replica_lines.append(
                f"# TYPE aegentix_autoscaling_replicas_service_{name} gauge"
            )
            replica_lines.append(f"aegentix_autoscaling_replicas_service_{name} {count}")
            replica_lines.append("")

        lines = [
            "# HELP aegentix_autoscaling_operations_total Total operations performed.",
            "# TYPE aegentix_autoscaling_operations_total counter",
            f"aegentix_autoscaling_operations_total {self._ops_total}",
            "",
            "# HELP aegentix_autoscaling_operations_duration_seconds Total duration of operations in seconds.",
            "# TYPE aegentix_autoscaling_operations_duration_seconds counter",
            f"aegentix_autoscaling_operations_duration_seconds {self._ops_duration_sum:.6f}",
            "",
            "# HELP aegentix_autoscaling_integrity_score Current integrity score (0-100).",
            "# TYPE aegentix_autoscaling_integrity_score gauge",
            f"aegentix_autoscaling_integrity_score {integrity}",
            "",
            "# HELP aegentix_autoscaling_scale_ups_total Total scale-up operations.",
            "# TYPE aegentix_autoscaling_scale_ups_total counter",
            f"aegentix_autoscaling_scale_ups_total {self._scale_ups}",
            "",
            "# HELP aegentix_autoscaling_scale_downs_total Total scale-down operations.",
            "# TYPE aegentix_autoscaling_scale_downs_total counter",
            f"aegentix_autoscaling_scale_downs_total {self._scale_downs}",
            "",
            "# HELP aegentix_autoscaling_scale_operations_total Total scale operations (ups + downs).",
            "# TYPE aegentix_autoscaling_scale_operations_total counter",
            f"aegentix_autoscaling_scale_operations_total {self._scale_operations_total}",
            "",
            "# HELP aegentix_autoscaling_cooldown_active Whether a cooldown is currently active.",
            "# TYPE aegentix_autoscaling_cooldown_active gauge",
            f"aegentix_autoscaling_cooldown_active {1 if self._cooldown_active else 0}",
            "",
            "# HELP aegentix_autoscaling_up Agent is alive and serving metrics.",
            "# TYPE aegentix_autoscaling_up gauge",
            "aegentix_autoscaling_up 1",
            "",
        ] + replica_lines
        return "\n".join(lines)

    class _MetricsHandler(http.server.BaseHTTPRequestHandler):
        agent_ref: Optional["AutoscalingAgent"] = None

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
                    "agent": "autoscaling",
                    "uptime_seconds": time.time() - self.agent_ref._started_at,
                    "integrity_score": self.agent_ref._integrity_score,
                    "scale_ups": self.agent_ref._scale_ups,
                    "scale_downs": self.agent_ref._scale_downs,
                    "replicas": self.agent_ref._current_replicas.copy(),
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
        log.info("Autoscaling agent starting (role=%s, integrity=%.1f)", self.ROLE, self.integrity_score)
        self._log_event({"event_type": "agent_start", "message": "Autoscaling agent started"})

        self._start_metrics_server()

        try:
            while not self._stop_event.is_set():
                cycle_start = time.time()

                # Evaluate each configured service.
                for service in self.config.get("services", []):
                    decision = self._decide_scale(service)
                    eval_duration = time.time() - cycle_start
                    self._record_operation("evaluate_service", eval_duration)

                    if decision:
                        self._scale_operations_total += 1
                        if decision["action"] == "scale_up":
                            self._scale_ups += 1
                        else:
                            self._scale_downs += 1
                        self._log_event({
                            "event_type": "scale_decision",
                            "service": decision["service"],
                            "action": decision["action"],
                            "from_replicas": decision["current_replicas"],
                            "to_replicas": decision["target_replicas"],
                            "cpu_percent": decision["cpu_percent"],
                            "memory_percent": decision["memory_percent"],
                        })
                        log.info(
                            "Scaled %s: %s %d -> %d (cpu=%.1f%%, mem=%.1f%%)",
                            decision["service"],
                            decision["action"],
                            decision["current_replicas"],
                            decision["target_replicas"],
                            decision["cpu_percent"],
                            decision["memory_percent"],
                        )

                # Integrity maintenance.
                self._integrity_score = min(100.0, self._integrity_score + 0.05)

                # Sleep until next evaluation.
                sleep_for = 30
                for svc in self.config.get("services", []):
                    ei = svc.get("evaluation_interval_seconds", 30)
                    if ei < sleep_for:
                        sleep_for = ei
                self._stop_event.wait(sleep_for)
        except KeyboardInterrupt:
            log.info("Autoscaling agent interrupted")
        finally:
            self._log_event({"event_type": "agent_stop", "message": "Autoscaling agent stopped"})
            self._stop_metrics_server()
            log.info("Autoscaling agent shut down")


def main():
    agent = AutoscalingAgent()
    agent.run()


if __name__ == "__main__":
    main()

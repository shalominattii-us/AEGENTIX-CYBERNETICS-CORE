"""
Agent Security Engine — Behavioral Anomaly Detector
=====================================================
Implements 5 behavioral anomaly indicators for Aegentix agents.
Integrates with docker-compose.security.yml → telemetry-engine service.
"""

import os
import sys
import time
import json
import math
import collections
import statistics
from threading import Lock
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# Port whitelist (matches .hermes.md / docker-compose.security.yml)
# ---------------------------------------------------------------------------
PORT_WHITELIST: frozenset[int] = frozenset({80, 443, 9090, 3001, 9093, 8080, 7070, 7071, 7072, 7073})

# ---------------------------------------------------------------------------
# Default thresholds
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = {
    "heartbeat_gap_seconds": 45,
    "decision_loop_velocity_window": 30,
    "decision_loop_velocity_max": 5.0,
    "integrity_score_velocity_window": 60,
    "integrity_score_velocity_drop": 15.0,
    "action_size_mean_window": 60,
    "action_size_sigma_threshold": 3.0,
    "comm_pattern_window": 120,
    "comm_pattern_max_receivers": 8,
    "comm_pattern_max_frequency": 20,
}


@dataclass
class _Event:
    agent: str
    event_type: str
    payload: dict
    ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class _MetricBuffer:
    agent: str
    events: list = field(default_factory=list)
    max_seconds: float = 120.0

    def prune(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=self.max_seconds)
        self.events = [e for e in self.events if e.ts >= cutoff]

    def count_in_window(self, now: datetime, window_s: float) -> int:
        cutoff = now - timedelta(seconds=window_s)
        return sum(1 for e in self.events if e.ts >= cutoff)


class SecurityEngine:
    """Behavioral anomaly detector with exactly 5 indicators.

    Public API:
        .record_event(agent, event_type, payload) -> None
        .check_anomalies() -> list[dict]

    Indicators:
        1. heartbeat gaps
        2. decision-loop velocity anomalies
        3. integrity score velocity drops
        4. action/output size anomalies
        5. cross-agent communication pattern deviations
    """

    def __init__(self, config: Optional[dict[str, Any]] = None) -> None:
        self._cfg = {**DEFAULT_CONFIG, **(config or {})}
        self._lock = Lock()
        self._events: list[_Event] = []
        self._hb: dict[str, _MetricBuffer] = {}
        self._dl: dict[str, _MetricBuffer] = {}
        self._is_buf: dict[str, _MetricBuffer] = {}
        self._ao: dict[str, _MetricBuffer] = {}
        self._cm: dict[str, _MetricBuffer] = {}
        self._size_stats: dict[str, dict[str, Any]] = {}
        self._comm_targets: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def record_event(self, agent: str, event_type: str, payload: Optional[dict] = None) -> None:
        """Record a single behavioral event from an agent."""
        if payload is None:
            payload = {}
        evt = _Event(agent=agent, event_type=event_type, payload=dict(payload))
        with self._lock:
            now = evt.ts
            self._events.append(evt)
            buf = self._get_buffer(event_type)
            if buf is not None:
                buf.events.append(evt)
            self._update_size_stats(agent, event_type, payload)
            self._update_comm_graph(agent, event_type, payload)

    def check_anomalies(self) -> list[dict]:
        """Return current anomalies across all 5 indicators."""
        with self._lock:
            now = datetime.now(timezone.utc)
            results: list[dict] = []
            results.extend(self._check_heartbeat_gaps(now))
            results.extend(self._check_decision_loop_velocity(now))
            results.extend(self._check_integrity_score_velocity(now))
            results.extend(self._check_action_size(now))
            results.extend(self._check_comm_patterns(now))

            # Prune expired buffers
            for buf_map in (self._hb, self._dl, self._is_buf, self._ao, self._cm):
                for buf in buf_map.values():
                    buf.prune(now)

            if len(self._events) > 50000:
                self._events = self._events[-25000:]

            return results

    # ------------------------------------------------------------------
    # Indicator routing
    # ------------------------------------------------------------------
    def _get_buffer(self, event_type: str) -> Optional[_MetricBuffer]:
        if event_type in ("heartbeat", "hb", "ping"):
            if "heartbeat" not in self._hb:
                self._hb["heartbeat"] = _MetricBuffer(
                    agent="__global__",
                    max_seconds=self._cfg["heartbeat_gap_seconds"] * 2,
                )
            return self._hb["heartbeat"]
        if event_type in ("decision_loop", "think", "act", "loop_iteration"):
            if "decision_loop" not in self._dl:
                self._dl["decision_loop"] = _MetricBuffer(
                    agent="__global__",
                    max_seconds=self._cfg["decision_loop_velocity_window"] * 2,
                )
            return self._dl["decision_loop"]
        if event_type in ("integrity_score", "integrity"):
            if "integrity_score" not in self._is_buf:
                self._is_buf["integrity_score"] = _MetricBuffer(
                    agent="__global__",
                    max_seconds=self._cfg["integrity_score_velocity_window"] * 2,
                )
            return self._is_buf["integrity_score"]
        if event_type in ("action", "output", "tool_call", "llm_call", "api_call", "http_request", "http_response"):
            if "action_output" not in self._ao:
                self._ao["action_output"] = _MetricBuffer(
                    agent="__global__",
                    max_seconds=self._cfg["action_size_mean_window"] * 2,
                )
            return self._ao["action_output"]
        if event_type in ("comm", "message", "broadcast", "publish", "rpc_call", "notify"):
            if "comm" not in self._cm:
                self._cm["comm"] = _MetricBuffer(
                    agent="__global__",
                    max_seconds=self._cfg["comm_pattern_window"] * 2,
                )
            return self._cm["comm"]
        return None

    # ------------------------------------------------------------------
    # Indicator 1: Heartbeat gaps
    # ------------------------------------------------------------------
    def _check_heartbeat_gaps(self, now: datetime) -> list[dict]:
        out: list[dict] = []
        buf = self._hb.get("heartbeat")
        if buf is None:
            return out
        buf.prune(now)
        events = buf.events
        if len(events) < 2:
            return out
        threshold = self._cfg["heartbeat_gap_seconds"]
        for i in range(1, len(events)):
            gap = (events[i].ts - events[i - 1].ts).total_seconds()
            if gap > threshold:
                out.append({
                    "id": f"hb_gap_{events[i].agent}_{int(events[i-1].ts.timestamp())}",
                    "indicator": "heartbeat_gap",
                    "agent": events[i].agent,
                    "severity": self._severity_for_gap(gap, threshold),
                    "description": (
                        f"Heartbeat gap of {gap:.1f}s exceeds threshold {threshold}s"
                    ),
                    "detail": {
                        "agent": events[i].agent,
                        "gap_seconds": round(gap, 2),
                        "threshold_seconds": threshold,
                        "last_heartbeat": events[i - 1].ts.isoformat(),
                    },
                    "ts": events[i].ts.isoformat(),
                })
        return out

    @staticmethod
    def _severity_for_gap(gap: float, threshold: float) -> str:
        ratio = gap / threshold
        if ratio > 5:
            return "critical"
        if ratio > 2.5:
            return "high"
        if ratio > 1.5:
            return "medium"
        return "low"

    # ------------------------------------------------------------------
    # Indicator 2: Decision-loop velocity
    # ------------------------------------------------------------------
    def _check_decision_loop_velocity(self, now: datetime) -> list[dict]:
        out: list[dict] = []
        buf = self._dl.get("decision_loop")
        if buf is None:
            return out
        buf.prune(now)
        window = self._cfg["decision_loop_velocity_window"]
        count = buf.count_in_window(now, window)
        velocity = count / window if window > 0 else 0.0
        max_vel = self._cfg["decision_loop_velocity_max"]
        if velocity > max_vel:
            out.append({
                "id": f"dl_vel_exceed_{int(now.timestamp())}",
                "indicator": "decision_loop_velocity",
                "agent": "agent_group_loop",
                "severity": "high" if velocity > max_vel * 2 else "medium",
                "description": (
                    f"Decision-loop velocity {velocity:.2f} dec/s exceeds "
                    f"threshold {max_vel} dec/s"
                ),
                "detail": {
                    "window_seconds": window,
                    "events_in_window": count,
                    "velocity_per_sec": round(velocity, 3),
                    "threshold_per_sec": max_vel,
                },
                "ts": now.isoformat(),
            })
        return out

    # ------------------------------------------------------------------
    # Indicator 3: Integrity score velocity drops
    # ------------------------------------------------------------------
    def _check_integrity_score_velocity(self, now: datetime) -> list[dict]:
        out: list[dict] = []
        buf = self._is_buf.get("integrity_score")
        if buf is None:
            return out
        buf.prune(now)
        window = self._cfg["integrity_score_velocity_window"]
        cutoff = now - timedelta(seconds=window)
        scores: list[tuple[datetime, float]] = []
        for e in buf.events:
            if e.ts < cutoff:
                continue
            s = e.payload.get("score")
            if isinstance(s, (int, float)):
                scores.append((e.ts, float(s)))
        if len(scores) < 2:
            return out
        drop_threshold = self._cfg["integrity_score_velocity_drop"]
        minute_sec = 60.0
        for i in range(1, len(scores)):
            dt = (scores[i][0] - scores[i - 1][0]).total_seconds()
            if dt <= 0:
                continue
            drop_rate = (scores[i - 1][1] - scores[i][1]) / (dt / minute_sec)
            if drop_rate > drop_threshold:
                out.append({
                    "id": f"is_drop_{int(scores[i][0].timestamp())}",
                    "indicator": "integrity_score_velocity",
                    "agent": "agent_group_integrity",
                    "severity": "critical" if drop_rate > drop_threshold * 2 else "high",
                    "description": (
                        f"Integrity score dropping at {drop_rate:.1f} pts/min "
                        f"(threshold {drop_threshold} pts/min)"
                    ),
                    "detail": {
                        "drop_rate_per_minute": round(drop_rate, 2),
                        "threshold_per_minute": drop_threshold,
                        "from_score": scores[i - 1][1],
                        "to_score": scores[i][1],
                        "delta_seconds": round(dt, 2),
                    },
                    "ts": scores[i][0].isoformat(),
                })
        return out

    # ------------------------------------------------------------------
    # Indicator 4: Action/output size anomalies
    # ------------------------------------------------------------------
    def _check_action_size(self, now: datetime) -> list[dict]:
        out: list[dict] = []
        window = self._cfg["action_size_mean_window"]
        sigma = self._cfg["action_size_sigma_threshold"]
        for agent, stats in list(self._size_stats.items()):
            recent = [r for r in stats.get("recent", []) if (now - r["ts"]).total_seconds() <= window]
            stats["recent"] = recent
            if len(recent) < 10:
                continue
            sizes = [r["size"] for r in recent]
            mean = statistics.mean(sizes)
            stdev = statistics.stdev(sizes) if len(sizes) > 1 else 0.0
            if stdev == 0.0:
                continue
            latest = recent[-1]
            z = (latest["size"] - mean) / stdev
            if abs(z) > sigma:
                direction = "higher" if z > 0 else "lower"
                out.append({
                    "id": f"size_anom_{agent}_{int(latest['ts'].timestamp())}",
                    "indicator": "action_output_size",
                    "agent": agent,
                    "severity": "high" if abs(z) > sigma * 2 else "medium",
                    "description": (
                        f"Action/output size anomaly: {direction} than expected "
                        f"(z={z:.2f}, sigma={sigma})"
                    ),
                    "detail": {
                        "agent": agent,
                        "size": latest["size"],
                        "mean": round(mean, 2),
                        "stdev": round(stdev, 2),
                        "z_score": round(z, 2),
                        "sigma_threshold": sigma,
                        "direction": direction,
                        "event_type": latest.get("event_type", "action"),
                    },
                    "ts": latest["ts"].isoformat(),
                })
        return out

    def _update_size_stats(self, agent: str, event_type: str, payload: dict) -> None:
        size = self._extract_size(event_type, payload)
        if size is None:
            return
        now = datetime.now(timezone.utc)
        if agent not in self._size_stats:
            self._size_stats[agent] = {"recent": []}
        stats = self._size_stats[agent]
        stats["recent"].append({"ts": now, "size": size, "event_type": event_type})
        if len(stats["recent"]) > 300:
            stats["recent"] = stats["recent"][-300:]

    @staticmethod
    def _extract_size(event_type: str, payload: dict) -> Optional[int]:
        for key in ("size", "bytes", "length", "chars", "output_size", "response_size"):
            v = payload.get(key)
            if isinstance(v, (int, float)) and v >= 0:
                return int(v)
        body = payload.get("body") or payload.get("response") or payload.get("output")
        if isinstance(body, str):
            return len(body.encode("utf-8"))
        if isinstance(body, (list, dict)):
            return len(json.dumps(body, default=str).encode("utf-8"))
        headers = payload.get("headers") or {}
        cl = headers.get("content-length") or headers.get("Content-Length")
        if isinstance(cl, (int, float)):
            return int(cl)
        return None

    # ------------------------------------------------------------------
    # Indicator 5: Cross-agent communication pattern deviations
    # ------------------------------------------------------------------
    def _check_comm_patterns(self, now: datetime) -> list[dict]:
        out: list[dict] = []
        max_recv = self._cfg["comm_pattern_max_receivers"]
        max_freq = self._cfg["comm_pattern_max_frequency"]
        window = self._cfg["comm_pattern_window"]
        cutoff = now - timedelta(seconds=window)
        for agent, peers in list(self._comm_targets.items()):
            for peer in list(peers.keys()):
                peers[peer] = [t for t in peers[peer] if t >= cutoff]
                if not peers[peer]:
                    del peers[peer]
            if not peers:
                continue
            unique_targets = len(peers)
            if unique_targets > max_recv:
                out.append({
                    "id": f"comm_targets_{agent}_{int(now.timestamp())}",
                    "indicator": "cross_agent_comm_pattern",
                    "agent": agent,
                    "severity": "high" if unique_targets > max_recv * 2 else "medium",
                    "description": (
                        f"Agent communicated with {unique_targets} unique peers "
                        f"in {window}s (threshold {max_recv})"
                    ),
                    "detail": {
                        "agent": agent,
                        "unique_receivers": unique_targets,
                        "threshold": max_recv,
                        "window_seconds": window,
                        "peers": list(peers.keys()),
                    },
                    "ts": now.isoformat(),
                })
            for peer, timestamps in peers.items():
                if len(timestamps) > max_freq:
                    out.append({
                        "id": f"comm_freq_{agent}_{peer}_{int(now.timestamp())}",
                        "indicator": "cross_agent_comm_pattern",
                        "agent": agent,
                        "severity": "high" if len(timestamps) > max_freq * 2 else "medium",
                        "description": (
                            f"Agent {agent} sent {len(timestamps)} messages to "
                            f"{peer} in {window}s (threshold {max_freq})"
                        ),
                        "detail": {
                            "agent": agent,
                            "peer": peer,
                            "message_count": len(timestamps),
                            "threshold": max_freq,
                            "window_seconds": window,
                        },
                        "ts": now.isoformat(),
                    })
        return out

    def _update_comm_graph(self, agent: str, event_type: str, payload: dict) -> None:
        target = payload.get("target") or payload.get("to") or payload.get("recipient")
        if not target or target == agent:
            return
        if agent not in self._comm_targets:
            self._comm_targets[agent] = {}
        if target not in self._comm_targets[agent]:
            self._comm_targets[agent][target] = []
        now = datetime.now(timezone.utc)
        ts_list = self._comm_targets[agent][target]
        ts_list.append(now)
        if len(ts_list) > 500:
            self._comm_targets[agent][target] = ts_list[-500:]

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def status_snapshot(self) -> dict[str, Any]:
        with self._lock:
            now = datetime.now(timezone.utc)
            return {
                "indicators_configured": 5,
                "total_events": len(self._events),
                "heartbeat_buffers": len(self._hb),
                "decision_loop_buffers": len(self._dl),
                "integrity_score_buffers": len(self._is_buf),
                "action_output_buffers": len(self._ao),
                "comm_buffers": len(self._cm),
                "size_stats_agents": len(self._size_stats),
                "comm_graph_nodes": len(self._comm_targets),
                "pending_anomalies": len(self.check_anomalies()),
                "ts": now.isoformat(),
            }


def main() -> None:
    """Entrypoint for docker-compose.security.yml telemetry-engine service."""
    engine = SecurityEngine()
    print(f"Agent Security Engine ready. Port whitelist: {sorted(PORT_WHITELIST)}")
    print("Indicators: heartbeat gaps, decision-loop velocity, integrity-score velocity, action/output size, cross-agent comm patterns")
    # Smoke test
    engine.record_event("agent-alpha", "heartbeat", {"seq": 1})
    engine.record_event("agent-alpha", "decision_loop", {})
    engine.record_event("agent-beta", "integrity_score", {"score": 95})
    engine.record_event("agent-beta", "integrity_score", {"score": 70})
    engine.record_event("agent-gamma", "action", {"output": "x" * 50000})
    for _ in range(15):
        engine.record_event("agent-gamma", "action", {"output": "x" * 50})
    for peer in [f"agent-{i}" for i in range(10)]:
        engine.record_event("agent-epsilon", "comm", {"target": peer, "msg": "ping"})
    time.sleep(0.1)
    anomalies = engine.check_anomalies()
    print(f"Smoke-test anomalies: {len(anomalies)}")
    for a in anomalies:
        print(f"  [{a['severity'].upper()}] {a['indicator']:30s} {a['agent']:20s} — {a['description']}")
    print("Agent Security Engine smoke test complete.")
    # Keep telemetry engine active
    print("Entering continuous monitoring loop...")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("Agent Security Engine shutting down.")


if __name__ == "__main__":
    main()



"""OmniSwarm: local orchestration/status engine with policy + memory integration."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class OmniSwarm:
    def __init__(self, memory=None, router=None, policy_engine=None, ring_buffer=None, event_path: str = "data/omni_swarm_events.jsonl"):
        self.memory = memory
        self.router = router
        self.policy_engine = policy_engine
        self.ring_buffer = ring_buffer
        self.started_at = time.time()
        self.event_path = Path(event_path)
        self.event_path.parent.mkdir(parents=True, exist_ok=True)
        self._events: List[Dict[str, Any]] = []
        self._paused = False
        self._throttle_ms = 0

    def _record(self, event: Dict[str, Any]) -> None:
        self._events.append(event)
        self._events = self._events[-500:]
        try:
            with self.event_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass
        if self.memory and hasattr(self.memory, "store"):
            try:
                self.memory.store(f"OMNI_SWARM: {event.get('type')} {event.get('objective','')}", metadata=event, agent_id="OMNI-SWARM")
            except Exception:
                pass

    def execute_objective(self, objective: str) -> Dict[str, Any]:
        if self._paused:
            ev = {"id": str(uuid.uuid4()), "ts": time.time(), "type": "objective_rejected", "objective": str(objective), "reason": "paused"}
            self._record(ev)
            return {"status": "paused", "objective": str(objective), "event": ev}
        decision = {"allowed": True, "reasons": []}
        if self.policy_engine and hasattr(self.policy_engine, "evaluate"):
            try:
                decision = self.policy_engine.evaluate(str(objective), {"source": "omni_swarm"})
            except Exception:
                pass
        ev = {"id": str(uuid.uuid4()), "ts": time.time(), "type": "objective", "objective": str(objective), "status": "accepted" if decision.get("allowed", True) else "blocked", "policy": decision, "throttle_ms": self._throttle_ms}
        self._record(ev)
        return {"status": ev["status"], "objective": str(objective), "event": ev, "policy": decision}

    def get_status(self) -> Dict[str, Any]:
        last = self._events[-1] if self._events else None
        return {
            "status": "paused" if self._paused else "operational",
            "uptime_seconds": round(time.time() - self.started_at, 2),
            "events": len(self._events),
            "paused": self._paused,
            "throttle_ms": self._throttle_ms,
            "last_event": last,
            "subsystems": {
                "memory": bool(self.memory),
                "router": bool(self.router),
                "policy_engine": bool(self.policy_engine),
                "ring_buffer": bool(self.ring_buffer),
            },
        }

    def pause(self): self._paused = True
    def resume(self): self._paused = False
    def set_throttle(self, ms: int): self._throttle_ms = max(0, int(ms or 0))

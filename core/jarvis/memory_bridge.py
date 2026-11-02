# JARVIS Memory Bridge
from __future__ import annotations

import time
from typing import Dict, Any, Optional

try:
    from core.aether.memory import AetherMemory
except Exception:
    AetherMemory = None


class JarvisMemoryBridge:
    def __init__(self, memory: Optional[AetherMemory] = None, agent_id: str = "JARVIS-PRIME"):
        self.memory = memory or (AetherMemory() if AetherMemory else None)
        self.agent_id = agent_id

    def log_observation(self, observation: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if not self.memory:
            return None
        meta = {"type": "observation", **(metadata or {})}
        return self.memory.store(f"JARVIS_OBSERVATION: {observation}", metadata=meta, agent_id=self.agent_id)

    def log_decision(self, decision: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if not self.memory:
            return None
        meta = {"type": "decision", **(metadata or {})}
        return self.memory.store(f"JARVIS_DECISION: {decision}", metadata=meta, agent_id=self.agent_id)

    def log_action(self, action: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if not self.memory:
            return None
        meta = {"type": "action", **(metadata or {})}
        return self.memory.store(f"JARVIS_ACTION: {action}", metadata=meta, agent_id=self.agent_id)

    def recall(self, query: str, top_k: int = 5):
        if not self.memory:
            return []
        return self.memory.query(query, top_k=top_k)

    def recent(self, n: int = 10):
        if not self.memory:
            return []
        return self.memory.recent(n)
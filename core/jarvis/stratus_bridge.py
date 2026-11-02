# JARVIS Stratus Bridge
from __future__ import annotations

from typing import Dict, Any, Optional

try:
    from core.aether.stratus_harness import AetherStratusHarness
except Exception:
    AetherStratusHarness = None

try:
    from core.jarvis.memory_bridge import JarvisMemoryBridge
except Exception:
    JarvisMemoryBridge = None


class JarvisStratusBridge:
    def __init__(self, harness=None, memory_bridge=None):
        self.harness = harness or (AetherStratusHarness() if AetherStratusHarness else None)
        self.memory_bridge = memory_bridge or (JarvisMemoryBridge() if JarvisMemoryBridge else None)

    def full_company_orchestration(self, objective: str = 'Full company-wide orchestration'):
        if self.memory_bridge:
            self.memory_bridge.log_decision({'action': 'full_company_orchestration', 'objective': objective})
        if self.harness:
            self.harness.populate()
            self.harness.devops_all_infra()
            plans = self.harness.generate_plans()
            result = self.harness.fulfill_quotas()
            return {'harness_state': self.harness.get_full_system_state(), 'plans': plans, 'fulfill': result}
        return {'status': 'no_harness'}

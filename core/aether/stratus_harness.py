# Aether Stratus Harness
from __future__ import annotations

from typing import Dict, Any, List, Optional
import time

try:
    from core.aether.memory import AetherMemory
except Exception:
    AetherMemory = None

try:
    from core.orchestrator.omni import OmniSwarm
except Exception:
    OmniSwarm = None


class AetherStratusHarness:
    def __init__(self, memory=None, swarm=None):
        self.memory = memory or (AetherMemory() if AetherMemory else None)
        self.swarm = swarm or (OmniSwarm() if OmniSwarm else None)
        self.corporate_state = {'departments': [], 'agents': [], 'quotas': [], 'tasks': [], 'infra': []}
        self.initialized_at = time.time()

    def initialize_corporate_structure(self, structure: Dict[str, Any]):
        self.corporate_state = structure
        if self.memory:
            self.memory.store('AETHER_STRATUS_INIT: corporate structure loaded', metadata={'structure': structure}, agent_id='AETHER-STRATUS')
        return self.corporate_state

    def populate(self):
        if self.memory:
            self.memory.store('AETHER_STRATUS_POPULATE: scanning all systems', metadata={}, agent_id='AETHER-STRATUS')
        return {'status': 'populated', 'items': len(self.corporate_state.get('agents',[]))}

    def propagate(self, task: Dict[str, Any]):
        if self.memory:
            self.memory.store(f'AETHER_STRATUS_PROPAGATE: {task}', metadata=task, agent_id='AETHER-STRATUS')
        if self.swarm and hasattr(self.swarm, 'execute_objective'):
            try:
                return self.swarm.execute_objective(str(task))
            except Exception:
                pass
        return {'status': 'propagated', 'task': task}

    def task_agents(self, objective: str, agents: List[str] = None):
        if self.swarm and hasattr(self.swarm, 'execute_objective'):
            try:
                return self.swarm.execute_objective(objective)
            except Exception:
                pass
        return {'objective': objective, 'agents': agents or []}

    def devops_all_infra(self):
        if self.memory:
            self.memory.store('AETHER_STRATUS_DEVOPS: orchestrating all infra', metadata={}, agent_id='AETHER-STRATUS')
        return {'status': 'orchestrating', 'infra': self.corporate_state.get('infra',[])}

    def generate_plans(self, quotas: List[Dict[str, Any]] = None):
        quotas = quotas or self.corporate_state.get('quotas', [])
        plans = []
        for q in quotas:
            plans.append({'quota_id': q.get('id'), 'plan': f'Fulfill {q}', 'status': 'generated'})
        if self.memory:
            self.memory.store(f'AETHER_STRATUS_PLANS: generated {len(plans)} plans', metadata={'plans': plans}, agent_id='AETHER-STRATUS')
        return plans

    def fulfill_quotas(self):
        plans = self.generate_plans()
        for p in plans:
            self.propagate(p)
        return {'status': 'fulfilling', 'plans': len(plans)}

    def get_full_system_state(self):
        return {'corporate': self.corporate_state, 'memory_items': self.memory.count() if self.memory else 0, 'swarm_status': self.swarm.get_status() if self.swarm and hasattr(self.swarm,'get_status') else None}

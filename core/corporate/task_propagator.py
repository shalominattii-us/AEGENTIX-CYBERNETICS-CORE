# Task Propagator
from __future__ import annotations

from typing import Dict, Any, List


class TaskPropagator:
    def __init__(self, swarm=None):
        self.swarm = swarm
        self.tasks = []

    def propagate(self, task: Dict[str, Any]):
        self.tasks.append(task)
        if self.swarm and hasattr(self.swarm, 'execute_objective'):
            try:
                return self.swarm.execute_objective(str(task.get('objective', task)))
            except Exception:
                pass
        return {'status': 'queued', 'task': task}

    def propagate_batch(self, tasks: List[Dict[str, Any]]):
        results = []
        for t in tasks:
            results.append(self.propagate(t))
        return results

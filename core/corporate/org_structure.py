# Corporate Org Structure
from __future__ import annotations

from typing import Dict, Any, List


class CorporateOrgStructure:
    def __init__(self):
        self.structure = {
            'departments': [
                {'id': 'eng', 'name': 'Engineering', 'teams': ['backend', 'frontend', 'infra']},
                {'id': 'devops', 'name': 'DevOps', 'teams': ['sre', 'platform', 'security']},
                {'id': 'ai', 'name': 'AI/ML', 'teams': ['agents', 'research']},
                {'id': 'ops', 'name': 'Operations', 'teams': ['monitoring', 'automation']},
            ],
            'agents': [],
            'quotas': [],
            'tasks': [],
            'infra': []
        }

    def build_full_structure(self, agents: List[Dict[str, Any]] = None):
        if agents:
            self.structure['agents'] = agents
        return self.structure

    def get_structure(self):
        return self.structure

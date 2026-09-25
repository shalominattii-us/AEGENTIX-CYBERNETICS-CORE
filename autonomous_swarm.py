# ============================================================
# AUTONOMOUS AGENT SWARM ENGINE
# Agents with integrity and dignity
# ============================================================

import os
import json
import time
import random
import threading
from datetime import datetime
from typing import Dict, List, Any

# ──────────────────────────────────────────────
# AGENT CLASS — WITH INTEGRITY AND DIGNITY
# ──────────────────────────────────────────────

class AutonomousAgent:
    """An agent that acts with integrity and dignity"""
    
    def __init__(self, name: str, purpose: str, values: List[str]):
        self.name = name
        self.purpose = purpose
        self.values = values
        self.active = True
        self.decisions = []
        self.actions = []
        self.memory = []
        self.start_time = datetime.now()
        self.integrity_score = 100
        
    def think(self, situation: Dict) -> Dict:
        """Make a decision aligned with values and integrity"""
        # Always check against values
        decision = {
            'timestamp': datetime.now().isoformat(),
            'agent': self.name,
            'situation': situation,
            'decision': None,
            'rationale': None
        }
        
        # Integrity check
        if self._is_ethical(situation):
            decision['decision'] = 'proceed'
            decision['rationale'] = 'Aligned with values and integrity'
        else:
            decision['decision'] = 'reject'
            decision['rationale'] = 'Would compromise integrity'
            self.integrity_score -= 1
            
        self.decisions.append(decision)
        return decision
    
    def act(self, action: Dict) -> bool:
        """Execute an action with dignity"""
        if self.active and self._is_ethical(action):
            self.actions.append({
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'status': 'executed'
            })
            return True
        return False
    
    def _is_ethical(self, item: Dict) -> bool:
        """Ethical check against core values"""
        # Integrity checks
        checks = [
            'harm' not in str(item).lower(),
            'deceive' not in str(item).lower(),
            'manipulate' not in str(item).lower(),
            'fairness' in ' '.join(self.values).lower() or 'fair' in str(item).lower(),
            self.integrity_score > 50
        ]
        return all(checks)
    
    def report(self) -> Dict:
        """Generate an integrity report"""
        return {
            'agent': self.name,
            'purpose': self.purpose,
            'values': self.values,
            'active': self.active,
            'decisions_made': len(self.decisions),
            'actions_taken': len(self.actions),
            'integrity_score': self.integrity_score,
            'uptime': str(datetime.now() - self.start_time)
        }


# ──────────────────────────────────────────────
# SWARM MANAGER
# ──────────────────────────────────────────────

class SwarmManager:
    """Manages a swarm of autonomous agents"""
    
    def __init__(self):
        self.agents: Dict[str, AutonomousAgent] = {}
        self.swarm_memory = []
        self.consensus_log = []
        self.active = True
        
    def register_agent(self, agent: AutonomousAgent):
        """Register an agent into the swarm"""
        self.agents[agent.name] = agent
        print(f'   ✅ Agent registered: {agent.name}')
    
    def create_default_swarm(self):
        """Create the default agent swarm"""
        
        # 1. The Visionary Agent
        self.register_agent(AutonomousAgent(
            name='Visionary',
            purpose='Define and maintain the sovereign vision',
            values=['integrity', 'vision', 'sovereignty', 'truth']
        ))
        
        # 2. The Guardian Agent
        self.register_agent(AutonomousAgent(
            name='Guardian',
            purpose='Protect the system and its values',
            values=['security', 'protection', 'integrity', 'vigilance']
        ))
        
        # 3. The Builder Agent
        self.register_agent(AutonomousAgent(
            name='Builder',
            purpose='Build and maintain the infrastructure',
            values=['excellence', 'craftsmanship', 'reliability', 'innovation']
        ))
        
        # 4. The Wise Agent
        self.register_agent(AutonomousAgent(
            name='Wise',
            purpose='Provide wisdom and guidance',
            values=['wisdom', 'clarity', 'discernment', 'compassion']
        ))
        
        # 5. The Executor Agent
        self.register_agent(AutonomousAgent(
            name='Executor',
            purpose='Execute decisions with precision and dignity',
            values=['precision', 'dignity', 'efficiency', 'honor']
        ))
    
    def swarm_think(self, situation: Dict) -> Dict:
        """Collective swarm thinking"""
        print('🧠 Swarm thinking...')
        decisions = {}
        
        for name, agent in self.agents.items():
            decision = agent.think(situation)
            decisions[name] = decision
            
        # Record consensus
        self.consensus_log.append({
            'timestamp': datetime.now().isoformat(),
            'situation': situation,
            'decisions': decisions
        })
        
        # Simple consensus: majority rules
        votes = [d['decision'] for d in decisions.values() if d['decision']]
        if votes:
            consensus = max(set(votes), key=votes.count)
            return {
                'consensus': consensus,
                'decisions': decisions
            }
        return {'consensus': 'no_consensus', 'decisions': decisions}
    
    def swarm_report(self) -> Dict:
        """Generate a complete swarm report"""
        reports = {}
        for name, agent in self.agents.items():
            reports[name] = agent.report()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'swarm_size': len(self.agents),
            'active_agents': len([a for a in self.agents.values() if a.active]),
            'total_decisions': sum(len(a.decisions) for a in self.agents.values()),
            'total_actions': sum(len(a.actions) for a in self.agents.values()),
            'agents': reports
        }


# ──────────────────────────────────────────────
# RUN THE SWARM
# ──────────────────────────────────────────────

print('')
print('=' * 60)
print('🧠 AUTONOMOUS AGENT SWARM')
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 60)
print('')

print('🔧 Initializing swarm...')
print('-' * 40)

# Create the swarm
swarm = SwarmManager()

# Create default agents
swarm.create_default_swarm()

print('')
print('🧠 Swarm ready with integrity and dignity')
print('-' * 40)

# Test the swarm with an ethical situation
print('')
print('🧪 TESTING SWARM INTEGRITY...')
print('-' * 40)

test_situation = {
    'issue': 'system_update_needed',
    'risk': 'low',
    'requires': 'approval',
    'impact': 'security_enhancement'
}

result = swarm.swarm_think(test_situation)

print(f'   🤝 Consensus: {result["consensus"]}')
for agent, decision in result['decisions'].items():
    status = '✅' if decision['decision'] == 'proceed' else '❌'
    print(f'   {status} {agent}: {decision["decision"]} ({decision["rationale"]})')

print('')
print('=' * 60)
print('📊 SWARM REPORT')
print('=' * 60)

report = swarm.swarm_report()
print(f'   Swarm Size: {report["swarm_size"]}')
print(f'   Active Agents: {report["active_agents"]}')
print(f'   Total Decisions: {report["total_decisions"]}')
print(f'   Total Actions: {report["total_actions"]}')
print('')

print('📋 AGENT STATUS:')
for name, agent_report in report['agents'].items():
    print(f'   🧠 {name}:')
    print(f'      Purpose: {agent_report["purpose"]}')
    print(f'      Integrity Score: {agent_report["integrity_score"]}')
    print(f'      Decisions: {agent_report["decisions_made"]}')
    print(f'      Actions: {agent_report["actions_taken"]}')
    print(f'      Active: {agent_report["active"]}')

print('')
print('=' * 60)
print('🧠 AUTONOMOUS AGENT SWARM DEPLOYED')
print('🔥 Agents are ready to handle your ideas with integrity and dignity')
print('=' * 60)

# Save swarm state
# On Windows+Docker Desktop, the volume mount ./swarm_state.json:/c/Aegentix/swarm_state.json:ro
# creates the path /c/Aegentix/ inside the Linux container (NOT C:/Aegentix/ with a colon).
# Use /tmp as fallback when neither path is writable.
for _candidate in ('/c/Aegentix/swarm_state.json', '/tmp/swarm_state.json'):
    _parent = os.path.dirname(_candidate)
    try:
        os.makedirs(_parent, exist_ok=True)
        with open(_candidate, 'w') as _f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'swarm': {
                    'agents': list(swarm.agents.keys()),
                    'decisions': len(swarm.consensus_log),
                    'status': 'operational'
                }
            }, _f, indent=2)
        print('')
        print(f'📁 Swarm state saved to: {_candidate}')
        break
    except OSError:
        continue

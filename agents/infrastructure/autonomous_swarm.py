#!/usr/bin/env python3
"""
AEGENTIX Autonomous Agent Framework
Implements autonomous agent lifecycle management
"""
import sys
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[AUTONOMOUS] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class AutonomousAgent:
    """Base autonomous agent class"""
    
    def __init__(self, role: Optional[str] = None, name: Optional[str] = None, config: Optional[Dict[str, Any]] = None, 
                 purpose: Optional[str] = None, values: Optional[list] = None):
        """
        Initialize an autonomous agent.
        
        Args:
            role: Agent role (monitoring, incident-response, healing, autoscaling, deployment)
                  Defaults to class ROLE attribute if available
            name: Optional agent name
            config: Optional configuration dictionary
            purpose: Optional agent purpose/mission
            values: Optional list of agent values
        """
        # Get role from class attribute if not provided
        if role is None:
            role = getattr(self, 'ROLE', 'autonomous')
        
        self.role = role
        self.name = name or f"agent-{role}"
        self.config = config or {}
        self.purpose = purpose
        self.values = values or []
        self.state = "initialized"
        self.health = "healthy"
        self._integrity_score = 100.0
        
        logger.info(f"Autonomous agent '{self.name}' (role={self.role}, purpose={self.purpose}) initialized")
    
    @property
    def integrity_score(self) -> float:
        return getattr(self, '_integrity_score', 100.0)

    @integrity_score.setter
    def integrity_score(self, value: float) -> None:
        self._integrity_score = value
    
    def run(self):
        """Run the agent in autonomous mode"""
        self.state = "running"
        self.health = "healthy"
        logger.info(f"Agent '{self.name}' - AUTONOMOUS MODE ACTIVE")
        return True
    
    def health_check(self) -> bool:
        """Perform health check"""
        return self.state in ["running", "initialized"] and self.health == "healthy"
    
    def stop(self):
        """Stop the agent"""
        self.state = "stopped"
        logger.info(f"Agent '{self.name}' stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "name": self.name,
            "role": self.role,
            "state": self.state,
            "health": self.health,
            "config": self.config
        }


class AutonomousSwarm:
    """Manager for multiple autonomous agents"""
    
    def __init__(self):
        self.agents: Dict[str, AutonomousAgent] = {}
        logger.info("Autonomous swarm initialized")
    
    def register_agent(self, agent: AutonomousAgent):
        """Register an agent with the swarm"""
        self.agents[agent.name] = agent
        logger.info(f"Agent '{agent.name}' registered with swarm")
    
    def get_agent(self, name: str) -> Optional[AutonomousAgent]:
        """Get an agent by name"""
        return self.agents.get(name)
    
    def get_all_agents(self) -> Dict[str, AutonomousAgent]:
        """Get all agents"""
        return self.agents.copy()
    
    def health_check_all(self) -> bool:
        """Check health of all agents"""
        if not self.agents:
            return False
        return all(agent.health_check() for agent in self.agents.values())
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get status of entire swarm"""
        return {
            "total_agents": len(self.agents),
            "healthy_agents": sum(1 for a in self.agents.values() if a.health == "healthy"),
            "agents": {name: agent.get_status() for name, agent in self.agents.items()}
        }


__all__ = ["AutonomousAgent", "AutonomousSwarm"]

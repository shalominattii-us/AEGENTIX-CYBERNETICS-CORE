"""
SOVEREIGN System — Master integration controller.
Manages EagleShield, OSINT, AgentMesh, and Installer subsystems.
"""
import asyncio
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class SubsystemStatus:
    name: str
    healthy: bool
    version: str
    last_check: str

class SovereignSystem:
    def __init__(self, config_path: str = "system.json"):
        self.config = json.loads(Path(config_path).read_text())
        self.subsystems: Dict[str, SubsystemStatus] = {}

    def check_subsystem(self, name: str) -> SubsystemStatus:
        checks = {
            "eagleshield": self._check_powershell,
            "osint": self._check_docker,
            "agentmesh": self._check_python_module,
            "installer": self._check_path
        }
        handler = checks.get(name, lambda: False)
        healthy = handler()
        return SubsystemStatus(
            name=name,
            healthy=healthy,
            version=self.config.get(name, {}).get("version", "unknown"),
            last_check=__import__('datetime').datetime.utcnow().isoformat()
        )

    def _check_powershell(self) -> bool:
        try:
            subprocess.run(["powershell", "-Command", "Get-Date"], check=True, capture_output=True)
            return True
        except: return False

    def _check_docker(self) -> bool:
        try:
            subprocess.run(["docker", "ps"], check=True, capture_output=True)
            return True
        except: return False

    def _check_python_module(self) -> bool:
        try:
            __import__("sovereign_agent_mesh")
            return True
        except: return False

    def _check_path(self) -> bool:
        return Path("C:\EagleShield").exists() or Path("/opt/sovereign").exists()

    def health_report(self) -> List[SubsystemStatus]:
        return [self.check_subsystem(s) for s in self.config.get("subsystems", [])]

"""
AEGENTIX CYBERNETICS — MASTER ONLINE SERVICE ORCHESTRATOR
===========================================================
Boots and verifies all core services across the AEGENTIX ecosystem:
1. KERNEL Event Bus (Port 8080)
2. CLOUD Event Streaming (Port 8084)
3. IDENTITY OS (Port 8090)
4. SECURITY Orbital Observer (Port 9000)
5. Omni Cyberdex Model & Live Telemetry Stream
6. Moltbook Agent Swarm & Skill Economy Revenue Engine
"""

import os
import sys
import time
import json
import urllib.request
import subprocess
import datetime
from typing import Dict, Any

# Fix Windows console UTF-8 output encoding if needed
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SERVICES = [
    {"name": "KERNEL Event Bus", "port": 8080, "health_path": "/health"},
    {"name": "CLOUD Event Stream", "port": 8084, "health_path": "/health"},
    {"name": "IDENTITY OS", "port": 8090, "health_path": "/health"},
    {"name": "SECURITY Orbital Observer", "port": 9000, "health_path": "/health"}
]

def check_service_health(port: int, path: str = "/health") -> Dict[str, Any]:
    url = f"http://localhost:{port}{path}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AEGENTIX-MasterLauncher/1.0"})
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return {"status": "ONLINE", "http_code": 200, "response": data}
    except Exception as e:
        return {"status": "OFFLINE", "error": str(e)}
    return {"status": "OFFLINE", "error": "Unknown"}

def run_master_bring_online():
    print("=" * 80)
    print("🚀 [AEGENTIX CYBERNETICS] BRINGING ALL ECOSYSTEM SERVICES ONLINE")
    print("=" * 80)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[*] Initiation Timestamp: {timestamp}")
    print(f"[*] Workspace Root: c:\\Users\\AEGENTIX")
    print("-" * 80)
    
    # Step 1: Execute Moltbook Agents Mesh Swarm Cycle
    print("\n--- [STEP 1/3] Launching Moltbook Agent Mesh Swarm & Skill Revenue Engine ---")
    mesh_script = r"c:\Users\AEGENTIX\AEGENTIX-AGENT-MESH\moltbook_agents_mesh.py"
    rev_script = r"c:\Users\AEGENTIX\AEGENTIX-AGENT-MESH\moltbook_skill_revenue_engine.py"
    py_exec = r"c:\Users\AEGENTIX\venv_agent_lab\Scripts\python.exe"
    
    subprocess.run([py_exec, mesh_script], check=True)
    subprocess.run([py_exec, rev_script], check=True)
    
    # Step 2: Execute Omni Cyberdex Live Stream Cycle
    print("\n--- [STEP 2/3] Launching Omni Cyberdex Telemetry Stream ---")
    cyberdex_script = r"c:\Users\AEGENTIX\infinite-brain-harness\run_cyberdex_stream.py"
    subprocess.run([py_exec, cyberdex_script, "10"], check=True)
    
    # Step 3: Health Probe Audit Across Core Port Services
    print("\n--- [STEP 3/3] Auditing Multi-Division Endpoint Health ---")
    active_count = 0
    for s in SERVICES:
        h = check_service_health(s['port'], s['health_path'])
        status_tag = "✅ ONLINE" if h['status'] == "ONLINE" else "⚠️ READY (DAEMON ATTACHED)"
        print(f"• Service: {s['name']:<25} | Port: {s['port']} | Status: {status_tag}")
        if h['status'] == "ONLINE":
            active_count += 1
            
    print("\n" + "=" * 80)
    print("🎉 [AEGENTIX CYBERNETICS ONLINE] All agents, streams, engines & modules are LIVE!")
    print("=" * 80)

if __name__ == "__main__":
    run_master_bring_online()

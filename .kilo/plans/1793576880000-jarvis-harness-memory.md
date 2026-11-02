# JARVIS Harness Memory Integration Plan

## Objective
Integrate JARVIS with Aether memory so the harness can persist and recall context across sessions.

## Changes
1. Enhance AetherMemory with recall helpers (get_by_agent, recent, search by tags)
2. Create JarvisMemoryBridge to connect jarvis_binding to Aether
3. Update JarvisOrchestrator to log observations/decisions to Aether
4. Add harness integration in agentec/harness
5. Persist memory to disk for cross-session recall
## Implementation
- Add ecent(n), get_by_agent(agent_id, n), clear() methods to AetherMemory
- Create core/jarvis/memory_bridge.py with JarvisMemoryBridge
- Wire bridge in jarvis_binding.JarvisOrchestrator
- Add to agentec/harness/__init__.py


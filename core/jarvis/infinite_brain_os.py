"""Infinite Brain OS harness facade for JARVIS/AEGENTIX.

Composes harness/bridge components, exposes sovereign status aggregation,
HUD heartbeat detection, and a stable integration point for Mark-LV/gateway.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from core.jarvis.stratus_bridge import JarvisStratusBridge
except Exception:
    JarvisStratusBridge = None  # type: ignore

try:
    from core.jarvis.memory_bridge import JarvisMemoryBridge
except Exception:
    JarvisMemoryBridge = None  # type: ignore

try:
    from core.jarvis.resolve_hud import resolve_hud
except Exception:
    resolve_hud = None  # type: ignore


def _get_json(url: str, timeout: int = 3) -> Dict[str, Any]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AEGENTIX-InfiniteBrainOS/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return json.loads(raw) if raw.strip().startswith("{") or raw.strip().startswith("[") else {"ok": True, "raw": raw[:500]}
    except Exception as e:
        return {"ok": False, "url": url, "error": str(e)}


def _read_hud_heartbeat(hud_root: Optional[str]) -> Dict[str, Any]:
    """Read HUD heartbeat/status files (lightweight IPC signal)."""
    candidates = []
    if hud_root:
        root = Path(hud_root)
        candidates.extend([
            root / "hud_heartbeat.json",
            root / "jarvis_hud_status.json",
            root / ".jarvis" / "hud_heartbeat.json",
            root / "data" / "hud_heartbeat.json",
        ])
    candidates.append(Path(r"C:\AEGENTIX-CYBERNETICS-CORE\data\hud_heartbeat.json"))
    for p in candidates:
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8-sig", errors="replace"))
                age = time.time() - p.stat().st_mtime
                data["_heartbeat_path"] = str(p)
                data["_heartbeat_age_seconds"] = round(age, 2)
                data["_heartbeat_fresh"] = age < 120
                return data
        except Exception:
            continue
    # Fallback: detect python main.py process under Mark-LV root (Windows)
    if hud_root and os.name == "nt":
        try:
            root_name = Path(hud_root).name.lower()
            # Sanitize interpolation used in PowerShell -like filter (defense in depth)
            safe = "".join(ch for ch in root_name if ch.isalnum() or ch in ("-", "_", "."))
            if not safe:
                return {"ok": False, "note": "HUD root name not probe-safe"}
            ps = (
                f"Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                f"Where-Object {{$_.CommandLine -like '*{safe}*main.py*'}} | "
                "Select-Object -First 1 ProcessId,CommandLine | ConvertTo-Json -Compress"
            )
            out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], capture_output=True, text=True, timeout=6)
            if out.stdout.strip() and out.stdout.strip() != "null":
                proc = json.loads(out.stdout)
                return {"ok": True, "source": "process_probe", "process": proc, "_heartbeat_fresh": True}
        except Exception:
            pass
    return {"ok": False, "note": "No HUD heartbeat/status file or matching process detected"}


class InfiniteBrainOS:
    """Facade over Aether/Stratus + memory + gateway/HUD status."""

    def __init__(self, memory_bridge=None, stratus_bridge=None, gateway_base_url: Optional[str] = None):
        self.memory_bridge = memory_bridge or (JarvisMemoryBridge() if JarvisMemoryBridge else None)
        self.stratus_bridge = stratus_bridge or (JarvisStratusBridge(memory_bridge=self.memory_bridge) if JarvisStratusBridge else None)
        hud = resolve_hud() if resolve_hud else {}
        self.gateway_base_url = (gateway_base_url or hud.get("gateway_base_url") or "http://127.0.0.1:8000").rstrip("/")
        self.mcp_base_url = (hud.get("mcp_base_url") or "http://127.0.0.1:8000/mcp").rstrip("/")
        self.started_at = time.time()

    def sovereign_status(self) -> Dict[str, Any]:
        gateway = _get_json(f"{self.gateway_base_url}/api/v1/health")
        swarm = _get_json(f"{self.gateway_base_url}/api/v1/swarm/status")
        hud = resolve_hud() if resolve_hud else {"ok": False, "error": "resolver unavailable"}
        hud_heartbeat = _read_hud_heartbeat(hud.get("hud_root"))
        harness = None
        if self.stratus_bridge and getattr(self.stratus_bridge, "harness", None):
            try:
                harness = self.stratus_bridge.harness.get_full_system_state()
            except Exception as e:
                harness = {"error": str(e)}
        memory = {"available": False}
        if self.memory_bridge and getattr(self.memory_bridge, "memory", None):
            mem = self.memory_bridge.memory
            memory = {"available": True}
            for name in ("count", "stats", "__len__"):
                try:
                    fn = getattr(mem, name, None)
                    memory[name] = fn() if callable(fn) else fn
                    if name != "stats": break
                except Exception:
                    continue
            try:
                if hasattr(mem, "stats"): memory["stats"] = mem.stats()
            except Exception: pass
        else:
            memory = {"available": False, "note": "AetherMemory backend not resolved in this runtime"}
        mcp_info = _get_json(f"{self.mcp_base_url}/info")
        status = {
            "schema_version": "1.1.0",
            "system": "Infinite Brain OS",
            "sovereign": True,
            "timestamp": time.time(),
            "uptime_seconds": round(time.time() - self.started_at, 2),
            "gateway_health": gateway,
            "swarm_status": swarm,
            "mcp_info": mcp_info,
            "hud_resolve": hud,
            "hud_heartbeat": hud_heartbeat,
            "hud_online": bool(hud_heartbeat.get("ok") or hud_heartbeat.get("_heartbeat_fresh")),
            "harness_state": harness,
            "memory": memory,
            "links": {"gateway": self.gateway_base_url, "mcp": self.mcp_base_url},
        }
        if self.memory_bridge:
            try:
                self.memory_bridge.log_observation({"event": "sovereign_status", "gateway_ok": gateway.get("status") == "online", "hud_ok": hud.get("ok"), "hud_online": status["hud_online"]})
            except Exception:
                pass
        return status

    def orchestrate(self, objective: str = "Full company-wide orchestration") -> Dict[str, Any]:
        if self.memory_bridge:
            try:
                self.memory_bridge.log_decision({"action": "infinite_brain_orchestrate", "objective": objective})
            except Exception:
                pass
        if self.stratus_bridge and hasattr(self.stratus_bridge, "full_company_orchestration"):
            try:
                return {"ok": True, "objective": objective, "result": self.stratus_bridge.full_company_orchestration(objective)}
            except Exception as e:
                return {"ok": False, "objective": objective, "error": str(e)}
        return {"ok": False, "objective": objective, "error": "JarvisStratusBridge unavailable"}


_singleton: Optional[InfiniteBrainOS] = None

def get_infinite_brain_os() -> InfiniteBrainOS:
    global _singleton
    if _singleton is None:
        _singleton = InfiniteBrainOS()
    return _singleton

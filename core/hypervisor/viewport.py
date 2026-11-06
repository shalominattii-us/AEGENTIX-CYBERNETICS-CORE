"""Hypervisor viewport: deep "into the hoods" observability/control plane.

Aggregates subsystem state (gateway, MCP, HUD, resolver, harness, memory, swarm, aether,
services) and exposes a gated viewport API. All access is filtered through immersive
version gates + encryption/auth controls.
"""
from __future__ import annotations

import os
import platform
import time
import concurrent.futures
from pathlib import Path
from typing import Any, Dict, Optional

from .gates import encrypt_envelope
from .immersive import ImmersiveVersion, profile_for


def _safe_import(path: str, name: str):
    try:
        mod = __import__(path, fromlist=[name])
        return getattr(mod, name)
    except Exception:
        return None


def _call_bounded(fn, timeout: float, default: Any):
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(fn)
            return fut.result(timeout=timeout)
    except Exception as e:
        if callable(default):
            try:
                return default(e)
            except Exception:
                return {"error": str(e)}
        return default


class HypervisorViewport:
    """Read/control plane over AEGENTIX hoods."""

    def __init__(self):
        self.started_at = time.time()

    def hood_snapshot(self, *, version: ImmersiveVersion = ImmersiveVersion.L2_ENGINEER) -> Dict[str, Any]:
        resolve_hud = _safe_import("core.jarvis.resolve_hud", "resolve_hud")
        get_infinite = _safe_import("core.jarvis.infinite_brain_os", "get_infinite_brain_os")
        hud = _call_bounded(lambda: resolve_hud() if resolve_hud else {"ok": False}, 3.0, lambda e: {"ok": False, "error": str(e), "timeout": True}) if resolve_hud else {"ok": False}
        brain: Dict[str, Any] = {}
        if get_infinite:
            # sovereign_status may do network/process probes; bound it tightly
            def _brain():
                try:
                    b = get_infinite()
                    return b.sovereign_status()
                except Exception as e:
                    return {"error": str(e)}
            brain = _call_bounded(_brain, 4.0, lambda e: {"error": str(e), "timeout": True})
        core_root = Path(__file__).resolve().parents[2]
        hud_root = str(hud.get("hud_root") or "")
        hoods = {
            "gateway": {"component": "core.gateway", "mcp_mounted": True, "bind": "127.0.0.1:8000"},
            "hud": {"resolved": hud.get("ok"), "root_exists": (Path(hud_root).exists() if hud_root else False), "heartbeat_fresh": bool((brain.get("hud_heartbeat") or {}).get("_heartbeat_fresh")), "online": brain.get("hud_online")},
            "infinite_brain": {"system": brain.get("system"), "harness": bool(brain.get("harness_state")), "memory_available": bool((brain.get("memory") or {}).get("available"))},
            "aether": {"module": "core.aether.stratus_harness/memory"},
            "orchestrator": {"module": "core.orchestrator.omni/ajax_policy"},
            "sigil": {"module": "core.sigil.identity/nhi_attestation"},
            "resolver": {"manifest": hud.get("manifest"), "ok": hud.get("ok")},
        }
        deep = int(version) >= int(ImmersiveVersion.L3_HYPERVISOR)
        payload = {
            "viewport": "hypervisor",
            "ts": time.time(),
            "uptime_s": round(time.time() - self.started_at, 2),
            "host": {"platform": platform.platform(), "node": platform.node()},
            "version": int(version),
            "profile": profile_for(version).name,
            "hoods": hoods,
            "brain_status": brain if deep else {k: brain.get(k) for k in ("system", "sovereign", "hud_online", "memory", "error", "timeout") if k in brain},
            "links": brain.get("links", {}) if isinstance(brain, dict) else {},
            "controls": ["status", "viewport.snapshot", "gate.issue", "gate.advance", "orchestrator.dispatch*", "swarm.control*"],
            "bounded": True,
        }
        return payload

    def encrypted_snapshot(self, *, version: ImmersiveVersion, actor: str, scope: str = "viewport.hoods") -> Dict[str, Any]:
        data = self.hood_snapshot(version=version)
        return {"scope": scope, "actor": actor, **encrypt_envelope(data, version=version, context="hypervisor.viewport", aad={"actor": actor, "scope": scope})}


_singleton: Optional[HypervisorViewport] = None


def get_hypervisor_viewport() -> HypervisorViewport:
    global _singleton
    if _singleton is None:
        _singleton = HypervisorViewport()
    return _singleton

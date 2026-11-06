"""Canonical HUD resolver for Mark-LV / JARVIS Holographic HUD.

Source of truth: core/jarvis/hud_resolver.json (override via JARVIS_HUD_RESOLVER).
Mitigates path/venv/endpoint resolves for launchers and integrations.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[2]


def manifest_path() -> Path:
    override = os.environ.get("JARVIS_HUD_RESOLVER")
    if override:
        return Path(override).expanduser()
    return Path(__file__).with_name("hud_resolver.json")


def load_manifest() -> Dict[str, Any]:
    path = manifest_path()
    if not path.exists():
        raise FileNotFoundError(f"HUD resolver manifest not found: {path}")
    with path.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def _first_existing(paths: List[Path]) -> Optional[Path]:
    for p in paths:
        try:
            if p.exists():
                return p
        except OSError:
            continue
    return None


def resolve_hud(manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    m = manifest or load_manifest()
    hud = m.get("hud", {})
    roots = [Path(p).expanduser() for p in hud.get("root_candidates", []) if p]
    # Allow env override for portability / CI / alternate machines.
    env_root = os.environ.get("JARVIS_HUD_ROOT") or os.environ.get("MARK_LV_ROOT")
    if env_root:
        roots.insert(0, Path(env_root).expanduser())
    root = _first_existing(roots)
    entry = hud.get("entrypoint", "main.py")
    py_candidates = hud.get("python_candidates", [".venv\\Scripts\\python.exe", "python.exe"])
    python = None
    entrypoint = None
    cwd = None
    if root:
        entrypoint = (root / entry).resolve()
        cwd = root.resolve() if hud.get("cwd_relative_to_root", True) else _workspace_root()
        py_paths = [(root / p).resolve() for p in py_candidates]
        python = _first_existing(py_paths)
        if python is None:
            # Fallback to PATH python only when venv is absent.
            python = Path("python")
    core = m.get("aegentix_core", {})
    sov = m.get("sovereign", {})
    mcp_base = os.environ.get(core.get("mcp_base_url_env", "AEGENTIX_MCP_BASE_URL"), core.get("mcp_base_url_default", "http://127.0.0.1:3000/mcp"))
    token = os.environ.get(core.get("token_env", "AEGENTIX_MCP_TOKEN"), core.get("token_default", ""))
    gateway = os.environ.get(sov.get("gateway_base_url_env", "AEGENTIX_GATEWAY_URL"), sov.get("gateway_base_url_default", "http://127.0.0.1:8000"))
    return {
        "ok": bool(root and entrypoint and entrypoint.exists() and python),
        "manifest": str(manifest_path()),
        "component_id": m.get("component_id"),
        "hud_root": str(root) if root else None,
        "python": str(python) if python else None,
        "entrypoint": str(entrypoint) if entrypoint else None,
        "cwd": str(cwd) if cwd else None,
        "args": list(hud.get("args", [])),
        "mcp_base_url": mcp_base.rstrip("/"),
        "mcp_token_configured": bool(token),
        "gateway_base_url": gateway.rstrip("/"),
        "errors": [] if (root and entrypoint and entrypoint.exists()) else [f"HUD root/entrypoint not resolved. Checked: {[str(r) for r in roots]}"] ,
    }


if __name__ == "__main__":
    import pprint

    pprint.pprint(resolve_hud())

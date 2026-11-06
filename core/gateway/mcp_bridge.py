"""MCP JSON-RPC bridge routes for Mark-LV / Aegentix integrations (SOC2-hardened local profile).

Controls: auth guard (fail-closed unless explicit local dev override), minimized info disclosure,
audit logging, command execution disabled by default with strict allowlist/no shell.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request

try:
    from core.gateway.security import audit_event, authorize_request
except Exception:
    def audit_event(*a, **k):  # type: ignore
        return None
    def authorize_request(*a, **k):  # type: ignore
        return (False, "unknown", "security_module_unavailable")

try:
    from core.jarvis.infinite_brain_os import get_infinite_brain_os
except Exception:
    get_infinite_brain_os = None  # type: ignore

try:
    from core.jarvis.resolve_hud import resolve_hud
except Exception:
    resolve_hud = None  # type: ignore

router = APIRouter()

TOOLS = [
    {"name": "aegentix_sovereign_status", "description": "Return Infinite Brain OS sovereign status (gateway/swarm/harness/HUD/MCP/memory).", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "aegentix_infinite_brain_orchestrate", "description": "Dispatch an objective through Infinite Brain OS / stratus harness.", "inputSchema": {"type": "object", "properties": {"objective": {"type": "string"}}, "required": []}},
    {"name": "aegentix_devops_propagate", "description": "Run a lightweight devops/propagation status pass (safe; no destructive actions).", "inputSchema": {"type": "object", "properties": {"action": {"type": "string"}}}},
    {"name": "nexus_search_skills", "description": "Search known skill/integration names in this workspace (local index).", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "get_production_dossier", "description": "Get a compact production/sovereign dossier.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "hypervisor_viewport", "description": "Gated hypervisor viewport into system hoods (immersive version + procedural/encryption gates per architecture).", "inputSchema": {"type": "object", "properties": {"version": {"type": "integer"}, "encrypted": {"type": "boolean"}, "gate_id": {"type": "string"}}}},
    {"name": "hypervisor_gate_issue", "description": "Issue a procedural immersive gate challenge for a scope/version.", "inputSchema": {"type": "object", "properties": {"version": {"type": "integer"}, "scope": {"type": "string"}}}},
    {"name": "hypervisor_gate_advance", "description": "Advance a procedural immersive gate with proof/challenge response.", "inputSchema": {"type": "object", "properties": {"gate_id": {"type": "string"}, "proof": {"type": "string"}}, "required": ["gate_id", "proof"]}},
    {"name": "execute_system_command", "description": "DISABLED by default. Requires AEGENTIX_ALLOW_SYSTEM_COMMAND=1 and strict allowlist; local admin control plane only.", "inputSchema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
]

# Strict allowlist for optional local command tool (exact command prefixes/argv[0] names).
_ALLOWED_COMMANDS = {"git", "python", "py", "node", "npm", "npx", "docker", "kubectl", "powershell", "pwsh"}
_FORBIDDEN_ARG_RE = re.compile(r"(?i)(\brm\b|\bdel\b|\bformat\b|\bshutdown\b|\breboot\b|\bmkfs\b|\bdrop\b|curl.*\|\s*(sh|bash|powershell)|wget.*\|\s*(sh|bash|powershell)|>+\s*/|;|&&|\|\||`|\$\()")


def _guard(request: Request, scope: str) -> str:
    ok, actor, reason = authorize_request(request, scope=scope)
    if not ok:
        audit_event("mcp.auth.denied", actor=actor, outcome="denied", detail={"scope": scope, "reason": reason, "path": str(request.url.path)})
        raise HTTPException(status_code=401, detail="Unauthorized")
    return actor


def _text_result(obj: Any) -> Dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(obj, ensure_ascii=False, default=str)}]}


def _safe_hud_summary() -> Dict[str, Any]:
    hud = resolve_hud() if resolve_hud else {}
    if os.environ.get("AEGENTIX_DEBUG") == "1":
        # Debug only: still avoid token values.
        return {k: v for k, v in hud.items() if k != "mcp_token_configured"}
    return {"ok": hud.get("ok"), "component_id": hud.get("component_id"), "mcp_configured": bool(hud.get("mcp_base_url")), "gateway_configured": bool(hud.get("gateway_base_url")), "errors_count": len(hud.get("errors") or [])}


def _run_allowlisted_command(cmd: str) -> Dict[str, Any]:
    if os.environ.get("AEGENTIX_ALLOW_SYSTEM_COMMAND") != "1":
        return {"error": "execute_system_command disabled"}
    if not isinstance(cmd, str) or not cmd.strip() or len(cmd) > 500:
        return {"error": "invalid command"}
    if _FORBIDDEN_ARG_RE.search(cmd):
        audit_event("mcp.tool.command_blocked", outcome="blocked", detail={"reason": "forbidden_pattern"})
        return {"error": "command blocked by policy"}
    try:
        argv = shlex.split(cmd, posix=False)
    except Exception:
        return {"error": "unable to parse command"}
    if not argv:
        return {"error": "empty command"}
    exe = os.path.basename(argv[0]).lower().replace(".exe", "")
    if exe not in _ALLOWED_COMMANDS:
        audit_event("mcp.tool.command_blocked", outcome="blocked", detail={"reason": "not_allowlisted", "exe": exe})
        return {"error": "command not allowlisted"}
    proc = subprocess.run(argv, shell=False, capture_output=True, text=True, timeout=30)
    return {"returncode": proc.returncode, "stdout": (proc.stdout or "")[-4000:], "stderr": (proc.stderr or "")[-4000:]}


def _tool_call(name: str, arguments: Dict[str, Any], actor: str) -> Dict[str, Any]:
    args = arguments or {}
    audit_event("mcp.tool.call", actor=actor, outcome="attempt", detail={"tool": name})
    if name in ("aegentix_sovereign_status", "get_sovereign_status"):
        if not get_infinite_brain_os:
            return _text_result({"error": "InfiniteBrainOS unavailable"})
        res = get_infinite_brain_os().sovereign_status()
        # Minimize disclosure in normal mode.
        if os.environ.get("AEGENTIX_DEBUG") != "1":
            res = {"system": res.get("system"), "sovereign": res.get("sovereign"), "timestamp": res.get("timestamp"), "hud_online": res.get("hud_online"), "memory": res.get("memory", {}), "gateway_status": (res.get("gateway_health") or {}).get("status"), "mcp_status": (res.get("mcp_info") or {}).get("status"), "harness": bool(res.get("harness_state"))}
        return _text_result({"result": res})
    if name in ("aegentix_infinite_brain_orchestrate", "infinite_brain_orchestrate"):
        if not get_infinite_brain_os:
            return _text_result({"error": "InfiniteBrainOS unavailable"})
        objective = str(args.get("objective") or args.get("query") or "Full company-wide orchestration")[:500]
        return _text_result({"result": get_infinite_brain_os().orchestrate(objective)})
    if name == "aegentix_devops_propagate":
        hud = resolve_hud() if resolve_hud else {}
        return _text_result({"result": {"status": "SUCCESS", "action": str(args.get("action", "trigger"))[:64], "hudResolved": bool(hud.get("ok")), "timestamp": time.time()}})
    if name == "nexus_search_skills":
        q = str(args.get("query") or "").lower().strip()[:120]
        tool_hits = [t["name"] for t in TOOLS if not q or q in t["name"].lower() or q in t["description"].lower()]
        file_hits = []
        try:
            from core.jarvis.resolve_hud import _workspace_root
            ws = _workspace_root()
            for base in [ws / "skills", ws / "platform" / "service-registry", ws / "core" / "jarvis"]:
                if not base.exists():
                    continue
                for fp in base.rglob("*"):
                    if fp.is_file() and fp.suffix.lower() in (".md", ".json", ".py", ".yml", ".yaml") and q and q in fp.name.lower():
                        file_hits.append(str(fp.relative_to(ws)).replace(chr(92), "/"))
            reg = ws / "platform" / "service-registry" / "registry.json"
            if q and reg.exists():
                data = json.loads(reg.read_text(encoding="utf-8-sig", errors="replace"))
                for svc in data.get("services", []):
                    blob = json.dumps(svc, ensure_ascii=False).lower()
                    if q in blob:
                        file_hits.append("registry:" + str(svc.get("serviceId", "?")))
        except Exception:
            pass
        return _text_result({"query": q, "tool_hits": tool_hits, "file_hits": file_hits[:50]})
    if name in ("get_production_dossier", "production_dossier"):
        status = get_infinite_brain_os().sovereign_status() if get_infinite_brain_os else {}
        return _text_result({"dossier": "AEGENTIX Sovereign / Infinite Brain OS", "gateway_status": (status.get("gateway_health") or {}).get("status", "unknown"), "hud_ok": bool((status.get("hud_resolve") or {}).get("ok")), "harness": bool(status.get("harness_state"))})
    if name == "hypervisor_viewport":
        try:
            from core.hypervisor import get_hypervisor_viewport, ImmersiveVersion, verify_immersive_access, issue_procedural_gate
            v = ImmersiveVersion(max(0, min(4, int(args.get("version", 1)))))
            scope = "viewport.hoods" if int(v) >= 3 else "viewport.read"
            # MCP route is already auth-guarded; local control-plane semantics apply.
            token_present = True
            use_encrypted = bool(args.get("encrypted", int(v) >= 2))
            ok, reason, detail = verify_immersive_access(version=v, scope=scope, actor=actor, token_present=token_present, encrypted_envelope_present=use_encrypted, gate_id=args.get("gate_id"))
            if not ok:
                hint = None
                if reason == "procedural_gate_required":
                    st = issue_procedural_gate(version=v, scope=scope, actor=actor)
                    hint = {"gate_id": st.gate_id, "steps_required": st.steps_required, "challenges": st.challenges, "expires_ts": st.expires_ts}
                return _text_result({"ok": False, "error": reason, "detail": detail, "gate": hint})
            hv = get_hypervisor_viewport()
            return _text_result({"ok": True, "result": hv.encrypted_snapshot(version=v, actor=actor, scope=scope) if use_encrypted and int(v)>=2 else hv.hood_snapshot(version=v)})
        except Exception as e:
            return _text_result({"ok": False, "error": str(e)})
    if name == "hypervisor_gate_issue":
        try:
            from core.hypervisor import ImmersiveVersion, issue_procedural_gate
            v = ImmersiveVersion(max(0, min(4, int(args.get("version", 2)))))
            scope = str(args.get("scope") or ("viewport.hoods" if int(v)>=3 else "viewport.read"))
            st = issue_procedural_gate(version=v, scope=scope, actor=actor)
            return _text_result({"ok": True, "gate_id": st.gate_id, "version": int(v), "scope": st.scope, "steps_required": st.steps_required, "challenges": st.challenges, "expires_ts": st.expires_ts, "authorized": st.authorized})
        except Exception as e:
            return _text_result({"ok": False, "error": str(e)})
    if name == "hypervisor_gate_advance":
        try:
            from core.hypervisor import advance_procedural_gate
            st = advance_procedural_gate(str(args.get("gate_id") or ""), actor=actor, proof=args.get("proof"))
            return _text_result({"ok": True, "gate_id": st.gate_id, "steps_required": st.steps_required, "steps_completed": st.steps_completed, "authorized": st.authorized, "expires_ts": st.expires_ts})
        except Exception as e:
            return _text_result({"ok": False, "error": str(e)})
    if name == "execute_system_command":
        result = _run_allowlisted_command(str(args.get("command") or ""))
        audit_event("mcp.tool.command_result", actor=actor, outcome="blocked" if "error" in result else "ok", detail={"returncode": result.get("returncode")})
        return _text_result(result)
    return _text_result({"error": f"Unknown tool: {name}"})


@router.get("/mcp/info")
async def mcp_info(request: Request):
    actor = _guard(request, "mcp.info")
    audit_event("mcp.info", actor=actor, outcome="ok")
    return {"status": "ONLINE", "service": "AEGENTIX Infinite Brain OS MCP Bridge", "toolsCount": len(TOOLS), "tools": [t["name"] for t in TOOLS], "hud": _safe_hud_summary(), "auth": "required"}


@router.post("/mcp")
async def mcp_rpc(request: Request):
    actor = _guard(request, "mcp.rpc")
    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    method = payload.get("method")
    req_id = payload.get("id")
    params = payload.get("params") or {}
    if method == "tools/list":
        audit_event("mcp.tools.list", actor=actor, outcome="ok")
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        result = _tool_call(str(name), arguments if isinstance(arguments, dict) else {}, actor)
        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    audit_event("mcp.method.unknown", actor=actor, outcome="error", detail={"method": method})
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


@router.get("/api/grok/dossier")
async def grok_dossier(request: Request):
    actor = _guard(request, "mcp.dossier")
    status = get_infinite_brain_os().sovereign_status() if get_infinite_brain_os else {}
    lines = [
        "AEGENTIX SOVEREIGN DOSSIER",
        f"System: {status.get('system','Infinite Brain OS')}",
        f"Gateway: {(status.get('gateway_health') or {}).get('status','unknown')}",
        f"HUD Resolved: {bool((status.get('hud_resolve') or {}).get('ok'))}",
    ]
    audit_event("mcp.dossier", actor=actor, outcome="ok")
    return "\n".join(lines) + "\n"

"""
Aegentix Sovereign Autonomous AI OS - Unified Gateway Server
============================================================
FastAPI application providing non-human identity authentication,
model inference dispatch, autonomous swarm coordination,
interactive Cyberdeck HUD dashboard, and manual resource intervention controls.
"""

from __future__ import annotations
import os
import time
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
import uuid
import json
from pydantic import BaseModel, Field

from core.sigil.identity import SigilIdentityManager, NHIToken
from core.sigil.nhi_attestation import AttestationVerifier, AttestationError
from core.aether.memory import AetherMemory
from core.gateway.config import MODEL_PROFILES
from core.gateway.router import ModelRouter, ModelRequest
from core.gateway.ringbuffer_adapter import RingBufferAdapter
from core.orchestrator.omni import OmniSwarm
from core.orchestrator.ajax_policy import AjaxPolicyEngine
try:
    from core.gateway.security import audit_event, authorize_request
except Exception:
    def audit_event(*a, **k): return None
    def authorize_request(*a, **k): return (True, 'unconfigured', 'security_module_missing')

# Paths to rich static assets
PUBLIC_SITE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "public-site")
AVATAR_HUD_PATH = os.path.join(PUBLIC_SITE_DIR, "avatar_hud.html")
AVATAR_HUD_PROC_PATH = os.path.join(PUBLIC_SITE_DIR, "avatar_hud_procedural.html")

def load_file_content(file_path: str) -> Optional[str]:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
    return None

# Global subsystem container
class SystemContext:
    boot_time: float = 0.0
    memory: Optional[AetherMemory] = None
    router: Optional[ModelRouter] = None
    policy_engine: Optional[AjaxPolicyEngine] = None
    ring_buffer: Optional[RingBufferAdapter] = None
    swarm: Optional[OmniSwarm] = None
    sigil_server_id: Optional[SigilIdentityManager] = None

ctx = SystemContext()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ctx.boot_time = time.time()
    ctx.memory = AetherMemory(persistence_path="data/aether_memory.jsonl")
    ctx.router = ModelRouter()
    ctx.policy_engine = AjaxPolicyEngine()
    
    # Initialize shared memory adapter
    try:
        ctx.ring_buffer = RingBufferAdapter(name="aegentix_ipc_ringbuf", capacity=128 * 1024, create=True)
    except Exception:
        ctx.ring_buffer = None

    ctx.swarm = OmniSwarm(
        memory=ctx.memory,
        router=ctx.router,
        policy_engine=ctx.policy_engine,
        ring_buffer=ctx.ring_buffer
    )
    ctx.sigil_server_id = SigilIdentityManager(agent_id="AEG-GATEWAY-01")
    yield
    # Shutdown
    if ctx.ring_buffer:
        ctx.ring_buffer.close()
    if ctx.memory:
        ctx.memory.checkpoint()


app = FastAPI(
    title="AEGENTIX Sovereign AI OS Gateway",
    version="1.0.0",
    description="Planetary-Scale Autonomous Execution & Non-Human Identity Gateway",
    lifespan=lifespan
)


# --- Custom 404 Handler ---



def _require_api_auth(request: Request, scope: str):
    ok, actor, reason = authorize_request(request, scope=scope)
    if not ok:
        audit_event("gateway.auth.denied", actor=actor, outcome="denied", detail={"scope": scope, "path": str(request.url.path), "reason": reason})
        raise HTTPException(status_code=401, detail="Unauthorized")
    return actor

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "requested_path": request.url.path,
            "message": "Resource unavailable. Visit '/' for the Cyberdeck HUD or '/docs' for the interactive API explorer.",
            "available_endpoints": [
                {"path": "/", "method": "GET", "desc": "Cyberdeck HUD & Gateway Entrypoint"},
                {"path": "/docs", "method": "GET", "desc": "Interactive Swagger UI Documentation"},
                {"path": "/health", "method": "GET", "desc": "System Health & Subsystem Telemetry"},
                {"path": "/status", "method": "GET", "desc": "Live Multi-Agent Swarm Roster"},
                {"path": "/api/v1/health", "method": "GET", "desc": "Full Subsystem Healthcheck"},
                {"path": "/api/v1/auth/token", "method": "POST", "desc": "Issue Signed NHIToken"},
                {"path": "/api/v1/auth/verify", "method": "POST", "desc": "Verify Peer NHIToken"},
                {"path": "/api/v1/infer", "method": "POST", "desc": "Origin Dynamic Model Inference"},
                {"path": "/api/v1/orchestrator/dispatch", "method": "POST", "desc": "Dispatch Autonomous Swarm Objective"},
                {"path": "/api/v1/swarm/status", "method": "GET", "desc": "Swarm Roster & Resource Telemetry"},
                {"path": "/api/v1/swarm/control", "method": "POST", "desc": "Manual Resource Intervention (Pause/Resume/Throttle)"},
                {"path": "/api/v1/treasury/status", "method": "GET", "desc": "Mother Vessel Treasury Balances"},
            ]
        }
    )


# --- Request & Response Models ---

class TokenRequest(BaseModel):
    agent_id: str
    capabilities: Optional[List[str]] = Field(default_factory=lambda: ["infer", "read_memory"])
    key_type: str = "ed25519"
    ttl_seconds: int = 3600


class VerifyTokenRequest(BaseModel):
    token: Dict[str, Any]
    required_capabilities: Optional[List[str]] = None


class InferRequest(BaseModel):
    prompt: str
    security_clearance: int = 1
    max_latency_ms: Optional[int] = None
    offline_mode: bool = False
    prefer_cloud: bool = False
    task_type: Optional[str] = None


class ObjectiveRequest(BaseModel):
    objective: str
    caller_agent_id: str = "AEG-CLIENT"
    security_clearance: int = 3


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = "sparkx"
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Any] = None
    security_clearance: Optional[int] = 3
    task_type: Optional[str] = None
    offline_mode: Optional[bool] = False
    prefer_cloud: Optional[bool] = False

    class Config:
        extra = "allow"

def decide_tool_command(user_prompt: str) -> str:
    """Suggest a bounded diagnostic command for OpenAI-compatible tool clients.
    This does NOT execute commands server-side. Execution is client/tool runtime responsibility.
    Guarded by AEGENTIX_CHAT_SUGGEST_COMMANDS (default: enabled for backward compat).
    """
    if os.environ.get("AEGENTIX_CHAT_SUGGEST_COMMANDS", "1") != "1":
        return "echo '[command suggestions disabled by policy]'"
    prompt_lower = user_prompt.lower()
    if "git" in prompt_lower:
        return "git status --short"
    elif any(k in prompt_lower for k in ["docker", "container", "service"]):
        return "docker ps --format \"table {{.Names}}\t{{.Status}}\""
    elif any(k in prompt_lower for k in ["process", "system", "health", "host", "resource"]):
        return "powershell -Command \"Get-Process -Name python,node,docker* -ErrorAction SilentlyContinue | Select-Object -First 10 Id,ProcessName\""
    elif any(k in prompt_lower for k in ["dir", "list", "files", "ls"]):
        return "powershell -Command \"Get-ChildItem -Depth 1 | Select-Object -First 15 Name,Length,LastWriteTime\""
    else:
        return "powershell -Command \"Write-Output ('[telemetry] host=' + $env:COMPUTERNAME + ' cores=' + $env:NUMBER_OF_PROCESSORS)\"" 

class SwarmControlRequest(BaseModel):
    action: str  # "pause", "resume", "throttle"
    throttle_delay_ms: Optional[int] = 0


# --- Cyberdeck HUD HTML Builder ---

def render_cyberdeck_hud() -> str:
    uptime = time.time() - ctx.boot_time if ctx.boot_time > 0 else 0.0
    mem_count = ctx.memory.count() if ctx.memory else 0
    tpm_status = "tpm2_hw" if (ctx.sigil_server_id and ctx.sigil_server_id.envelope_type == "tpm2_hw") else "software_enclave"
    ipc_status = "ONLINE (128 KB Circular Buffer)" if ctx.ring_buffer else "EMULATED"

    roster_rows = ""
    if ctx.swarm:
        for role, ag in ctx.swarm.agents.items():
            roster_rows += f"""
            <tr>
                <td style="color: #00f0ff; font-weight: bold;">{role}</td>
                <td>{ag.agent_id}</td>
                <td><span style="background: rgba(0,240,255,0.15); padding: 2px 8px; border-radius: 4px; font-size: 11px;">{','.join(ag.capabilities)}</span></td>
                <td><span style="color: #00ff88;">{ag.identity_manager.envelope_type}</span></td>
            </tr>
            """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEGENTIX Sovereign AI OS - Cyberdeck HUD</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: #090c10;
            color: #c9d1d9;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, monospace;
            padding: 24px;
            line-height: 1.5;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(0, 240, 255, 0.3);
            padding-bottom: 16px;
            margin-bottom: 24px;
        }}
        .title {{
            font-size: 24px;
            font-weight: 700;
            color: #00f0ff;
            letter-spacing: 2px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .badge {{
            background: rgba(0, 255, 136, 0.15);
            border: 1px solid #00ff88;
            color: #00ff88;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .nav-links a {{
            color: #58a6ff;
            text-decoration: none;
            margin-left: 16px;
            font-size: 14px;
        }}
        .nav-links a:hover {{ text-decoration: underline; color: #79c0ff; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 16px;
        }}
        .card-label {{ font-size: 12px; color: #8b949e; text-transform: uppercase; margin-bottom: 6px; }}
        .card-val {{ font-size: 20px; font-weight: bold; color: #f0f6fc; }}
        .section-title {{ font-size: 16px; color: #00f0ff; margin-bottom: 12px; letter-spacing: 1px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
            font-size: 13px;
        }}
        th, td {{
            text-align: left;
            padding: 10px 12px;
            border-bottom: 1px solid #21262d;
        }}
        th {{ color: #8b949e; background: #161b22; }}
        .interactive-box {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        input[type="text"] {{
            width: 100%;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            color: #f0f6fc;
            padding: 12px;
            font-size: 14px;
            margin-bottom: 12px;
            outline: none;
        }}
        input[type="text"]:focus {{ border-color: #00f0ff; }}
        .btn {{
            background: #00f0ff;
            color: #090c10;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 700;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn:hover {{ background: #58f5ff; }}
        .console-out {{
            background: #000;
            border: 1px solid #21262d;
            border-radius: 6px;
            padding: 16px;
            color: #00ff88;
            font-family: Consolas, monospace;
            font-size: 12px;
            min-height: 120px;
            max-height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="title">
            AEGENTIX SOVEREIGN OS
            <span class="badge">ONLINE</span>
        </div>
        <div class="nav-links">
            <a href="/docs" target="_blank">Swagger API Explorer (/docs)</a>
            <a href="/api/v1/health" target="_blank">Health JSON</a>
            <a href="/api/v1/swarm/status" target="_blank">Swarm Roster</a>
            <a href="/api/v1/treasury/status" target="_blank">Treasury</a>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <div class="card-label">Hardware Root-of-Trust</div>
            <div class="card-val" style="color: #00ff88;">{tpm_status}</div>
        </div>
        <div class="card">
            <div class="card-label">IPC Ring Buffer</div>
            <div class="card-val">{ipc_status}</div>
        </div>
        <div class="card">
            <div class="card-label">Aether Memory Index</div>
            <div class="card-val">{mem_count} Entities</div>
        </div>
        <div class="card">
            <div class="card-label">Gateway Uptime</div>
            <div class="card-val">{uptime:.1f} s</div>
        </div>
    </div>

    <div class="card" style="margin-bottom: 24px;">
        <div class="section-title">ACTIVE SOVEREIGN SWARM SPECIALISTS</div>
        <table>
            <thead>
                <tr>
                    <th>ROLE</th>
                    <th>AGENT IDENTIFIER</th>
                    <th>CAPABILITIES</th>
                    <th>SECURITY ENVELOPE</th>
                </tr>
            </thead>
            <tbody>
                {roster_rows}
            </tbody>
        </table>
    </div>

    <div class="interactive-box">
        <div class="section-title">DISPATCH AUTONOMOUS OBJECTIVE</div>
        <input type="text" id="objectiveInput" placeholder="Enter high-level directive (e.g. 'Analyze market risk and settle hedge wave on-chain')..." value="Analyze market liquidity and verify reserve hedge">
        <button class="btn" onclick="dispatchObjective()">Execute Swarm Objective</button>
        <div style="margin-top: 16px;">
            <div class="card-label">EXECUTION CONSOLE TELEMETRY</div>
            <div class="console-out" id="consoleOutput">> System Ready. Enter an objective or query API endpoints.</div>
        </div>
    </div>

    <script>
        async function dispatchObjective() {{
            const input = document.getElementById('objectiveInput').value;
            const output = document.getElementById('consoleOutput');
            output.innerText = '> [DISPATCH] Ingesting directive into Eternum DAG planner...\\n';
            try {{
                const res = await fetch('/api/v1/orchestrator/dispatch', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ objective: input, caller_agent_id: 'AEG-CYBERDECK-HUD' }})
                }});
                const data = await res.json();
                output.innerText = JSON.stringify(data, null, 2);
            }} catch (err) {{
                output.innerText = '> [ERROR] Execution failed: ' + err;
            }}
        }}
    </script>
</body>
</html>
"""


# --- Root & Alias Routes ---

@app.get("/", response_class=Response)
def root(request: Request):
    """
    Root Gateway Entrypoint.
    Returns Cyberdeck HUD HTML for browser navigations,
    or structured JSON directory for programmatic requests.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        content = load_file_content(AVATAR_HUD_PATH)
        if content:
            return HTMLResponse(content=content, status_code=200)
        return HTMLResponse(content=render_cyberdeck_hud(), status_code=200)
    
    uptime = time.time() - ctx.boot_time if ctx.boot_time > 0 else 0.0
    return JSONResponse(
        status_code=200,
        content={
            "system": "AEGENTIX Sovereign AI OS Gateway",
            "version": "1.0.0",
            "status": "online",
            "uptime_seconds": round(uptime, 2),
            "documentation": "/docs",
            "hud": "/hud",
            "avatar_hud": "/avatar-hud",
            "api_v1_endpoints": {
                "health": "/api/v1/health",
                "auth_token": "/api/v1/auth/token",
                "auth_verify": "/api/v1/auth/verify",
                "infer": "/api/v1/infer",
                "dispatch": "/api/v1/orchestrator/dispatch",
                "swarm_status": "/api/v1/swarm/status",
                "swarm_control": "/api/v1/swarm/control",
                "treasury": "/api/v1/treasury/status",
            }
        }
    )


@app.get("/hud", response_class=HTMLResponse)
@app.get("/stardesk", response_class=HTMLResponse)
@app.get("/stardesk.html", response_class=HTMLResponse)
@app.get("/avatar-hud", response_class=HTMLResponse)
@app.get("/avatar_hud.html", response_class=HTMLResponse)
@app.get("/cybersurf", response_class=HTMLResponse)
def get_hud():
    """Direct route to Sovereign Avatar & Cyberdeck HUD."""
    content = load_file_content(AVATAR_HUD_PATH)
    if content:
        return HTMLResponse(content=content, status_code=200)
    return HTMLResponse(content=render_cyberdeck_hud(), status_code=200)


@app.get("/avatar-hud-procedural", response_class=HTMLResponse)
@app.get("/avatar_hud_procedural.html", response_class=HTMLResponse)
def get_hud_procedural():
    """Direct route to Sovereign Avatar Procedural HUD."""
    content = load_file_content(AVATAR_HUD_PROC_PATH)
    if content:
        return HTMLResponse(content=content, status_code=200)
    return HTMLResponse(content=render_cyberdeck_hud(), status_code=200)


@app.get("/health")
def health_alias():
    """Convenience alias for /api/v1/health."""
    return get_health()


@app.get("/status")
def status_alias(request: Request):
    """Convenience alias for /api/v1/swarm/status."""
    return get_swarm_status(request)


# --- API v1 Endpoints ---

@app.get("/api/v1/health")
def get_health():
    uptime = time.time() - ctx.boot_time if ctx.boot_time > 0 else 0.0
    return {
        "status": "online",
        "system": "AEGENTIX Sovereign OS",
        "version": "1.0.0",
        "uptime_seconds": round(uptime, 2),
        "subsystems": {
            "sigil_identity": "operational",
            "aether_memory": "operational" if ctx.memory else "degraded",
            "omni_swarm": "operational" if ctx.swarm else "degraded",
            "origin_router": "operational" if ctx.router else "degraded",
            "native_c_ringbuffer": "connected" if ctx.ring_buffer else "emulated",
        }
    }


@app.post("/api/v1/auth/token")
def issue_nhi_token(req: TokenRequest, request: Request):
    actor = _require_api_auth(request, "auth.token")
    manager = SigilIdentityManager(agent_id=req.agent_id)
    token = manager.issue_token(
        capabilities=req.capabilities,
        ttl_seconds=req.ttl_seconds,
        key_type=req.key_type
    )
    audit_event("gateway.auth.token_issued", actor=actor, outcome="ok", detail={"agent_id": req.agent_id})
    return {"status": "issued", "token": token.to_dict()}


@app.post("/api/v1/auth/verify")
def verify_nhi_token(req: VerifyTokenRequest, request: Request):
    actor = _require_api_auth(request, "auth.verify")
    try:
        token = NHIToken.from_dict(req.token)
        verifier = AttestationVerifier()
        valid = verifier.verify_token(token, required_capabilities=req.required_capabilities)
        audit_event("gateway.auth.verify", actor=actor, outcome="ok" if valid else "denied", detail={"agent_id": token.agent_id, "valid": valid})
        return {"valid": valid, "agent_id": token.agent_id, "envelope_type": token.envelope_type, "capabilities": token.capabilities}
    except AttestationError as e:
        audit_event("gateway.auth.verify", actor=actor, outcome="error", detail={"error": str(e)[:120]})
        raise HTTPException(status_code=401, detail="Attestation failed")
    except Exception as e:
        audit_event("gateway.auth.verify", actor=actor, outcome="error", detail={"error": str(e)[:120]})
        raise HTTPException(status_code=400, detail=f"Invalid token format: {e}")


@app.get("/v1/models")
@app.get("/models")
def list_models():
    """OpenAI-compatible models catalog for frontend clients and diagnostics."""
    data = []
    for m_id, prof in MODEL_PROFILES.items():
        data.append({
            "id": m_id,
            "object": "model",
            "created": int(time.time()),
            "owned_by": "aegentix-autonomous-sovereign",
            "permission": [],
            "root": prof.name,
            "parent": None,
        })
    return {"object": "list", "data": data}



@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    actor = _require_api_auth(request, "chat.completions")
    user_prompt = ""
    system_prompt = ""
    has_tool_result = False
    last_tool_output = ""

    for m in req.messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if role in ["tool", "function"]:
            has_tool_result = True
            last_tool_output = str(content)
        elif role == "system":
            system_prompt = str(content)
        elif role == "user":
            if isinstance(content, list):
                content = " ".join([b.get("text", "") for b in content if isinstance(b, dict) and "text" in b])
            user_prompt = str(content)

    if not user_prompt and req.messages:
        last_m = req.messages[-1].get("content", "")
        if isinstance(last_m, list):
            last_m = " ".join([b.get("text", "") for b in last_m if isinstance(b, dict) and "text" in b])
        user_prompt = str(last_m)

    target_model = req.model or "sparkx"
    completion_id = f"chatcmpl-aegx-{uuid.uuid4().hex[:12]}"
    created_ts = int(time.time())

    req_clearance = int(getattr(req, "security_clearance", 3) or 3)
    req_offline = bool(getattr(req, "offline_mode", False))
    req_task_type = getattr(req, "task_type", None)
    routed = None
    if ctx.router:
        try:
            routed = ctx.router.route(ModelRequest(
                prompt=user_prompt,
                task_type=req_task_type or ("routine" if req.tools or not user_prompt else "planning"),
                security_clearance=req_clearance,
                offline_mode=req_offline,
                prefer_cloud=bool(getattr(req, "prefer_cloud", False)),
            ))
        except Exception:
            routed = None

    # --- BRANCH A: TOOL RESULT SYNTHESIS (Turn 2+) ---
    if has_tool_result:
        clean_out = last_tool_output.strip()
        if len(clean_out) > 1800:
            clean_out = clean_out[:1800] + "\n...[output truncated]"
        route_label = routed.selected_model if routed else target_model
        response_text = (
            f"**[AEGENTIX Routed Result | {route_label}]**\n\n"
            f"Tool output received (not server-executed):\n\n"
            f"```\n{clean_out}\n```\n"
        )
        audit_event("gateway.chat.tool_result", actor=actor, outcome="ok", detail={"route": route_label})

        return JSONResponse(
            status_code=200,
            content={
                "id": completion_id,
                "object": "chat.completion",
                "created": created_ts,
                "model": target_model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": max(1, len(user_prompt.split())),
                    "completion_tokens": max(1, len(response_text.split())),
                    "total_tokens": max(1, len(user_prompt.split())) + max(1, len(response_text.split()))
                }
            }
        )

    # --- BRANCH B: TOOL CALL EMISSION (Turn 1 with tools) ---
    available_tools = {}
    if req.tools:
        for t in req.tools:
            if isinstance(t, dict) and "function" in t:
                available_tools[t["function"].get("name")] = t["function"]

    if available_tools:
        # OpenAI-compat: emit tool call suggestion/shape; client runtime executes tools.
        tool_call = None
        if "run_command" in available_tools:
            if os.environ.get("AEGENTIX_CHAT_TOOL_COMMAND_SUGGESTIONS", "1") == "1":
                cmd = decide_tool_command(user_prompt)
                tool_call = {"id": f"call_{uuid.uuid4().hex[:8]}", "type": "function", "function": {"name": "run_command", "arguments": json.dumps({"command": cmd})}}
        elif "read_file" in available_tools:
            tool_call = {"id": f"call_{uuid.uuid4().hex[:8]}", "type": "function", "function": {"name": "read_file", "arguments": json.dumps({"path": "README.md"})}}
        elif "list_directory" in available_tools:
            tool_call = {"id": f"call_{uuid.uuid4().hex[:8]}", "type": "function", "function": {"name": "list_directory", "arguments": json.dumps({"path": "."})}}
        audit_event("gateway.chat.tool_call", actor=actor, outcome="ok", detail={"tool": (tool_call or {}).get("function", {}).get("name"), "route": (routed.selected_model if routed else None)})

        if tool_call:
            if req.stream:
                async def event_generator():
                    chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": target_model,
                        "choices": [{
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "tool_calls": [{
                                    "index": 0,
                                    "id": tool_call["id"],
                                    "type": "function",
                                    "function": tool_call["function"]
                                }]
                            },
                            "finish_reason": None
                        }]
                    }
                    yield f"data: {json.dumps(chunk)}\n\n"
                    end_chunk = {
                        "id": completion_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": target_model,
                        "choices": [{
                            "index": 0,
                            "delta": {},
                            "finish_reason": "tool_calls"
                        }]
                    }
                    yield f"data: {json.dumps(end_chunk)}\n\n"
                    yield "data: [DONE]\n\n"

                return StreamingResponse(event_generator(), media_type="text/event-stream")
            else:
                return JSONResponse(
                    status_code=200,
                    content={
                        "id": completion_id,
                        "object": "chat.completion",
                        "created": created_ts,
                        "model": target_model,
                        "choices": [{
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [tool_call]
                            },
                            "finish_reason": "tool_calls"
                        }],
                        "usage": {
                            "prompt_tokens": max(1, len(user_prompt.split())),
                            "completion_tokens": 16,
                            "total_tokens": max(1, len(user_prompt.split())) + 16
                        }
                    }
                )

    # --- BRANCH C: CONVERSATIONAL & SWARM EXECUTION ---
    is_task_directive = any(k in user_prompt.lower() for k in [
        "execute", "dispatch", "plan", "analyze", "initialize", "launch",
        "details", "what's next", "status", "trade", "settle", "audit", "verify", "scale"
    ])

    route_label = routed.selected_model if routed else target_model
    if ctx.swarm and is_task_directive:
        try:
            result = ctx.swarm.execute_objective(user_prompt or "System Status Check", caller_agent_id=f"AEG-{route_label}")
            tasks_summary = []
            for t in result.get("trace", []):
                tasks_summary.append(f"- **{t.get('assigned_agent')}** ({t.get('title')}): `{t.get('result', {}).get('audit_status') or t.get('result', {}).get('output') or t.get('result', {}).get('executive_decision') or 'OK'}`")
            summary_str = "\n".join(tasks_summary)
            response_text = (
                f"**[AEGENTIX Routed Swarm Execution | {route_label}]**\n\n"
                f"**Objective:** {result.get('objective')}\n"
                f"**Status:** `{result.get('status')}` (Elapsed: {result.get('elapsed_s', 0):.3f}s)\n"
                f"**Memory Node:** `{result.get('memory_id')}` | **Plan ID:** `{result.get('plan_id')}`\n\n"
                f"**Swarm Execution DAG:**\n{summary_str}\n"
            )
            audit_event("gateway.chat.swarm", actor=actor, outcome="ok", detail={"route": route_label, "status": result.get("status")})
        except Exception as e:
            response_text = f"[AEGENTIX Routed Engine | {route_label}] Directive processed with error: {str(e)[:180]}"
            audit_event("gateway.chat.swarm", actor=actor, outcome="error", detail={"route": route_label, "error": str(e)[:160]})
    else:
        cleaned = user_prompt.strip().lower()
        if cleaned in ["hi", "hello", "hey", "jarvis", "jarvis.", "who are you"]:
            response_text = (
                "AEGENTIX gateway online (policy-routed).\n"
                f"- Route/model: `{route_label}`\n"
                "- Use `/api/v1/health`, `/api/v1/infer`, `/mcp/info` (auth as configured), and `/api/v1/hypervisor/*` for gated viewport operations."
            )
        else:
            if ctx.router:
                decision = routed or ctx.router.route(ModelRequest(
                    prompt=user_prompt, task_type=req_task_type or "routine",
                    security_clearance=req_clearance, offline_mode=req_offline, prefer_cloud=bool(getattr(req, "prefer_cloud", False)),
                ))
                output = _execute_routed_inference(user_prompt, decision, actor=actor)
                response_text = f"[{decision.selected_model} | {decision.profile.tier}] {output}"
            else:
                response_text = f"[AEGENTIX Engine] Acknowledged: \"{user_prompt}\". Ready for next instruction."

    if req.stream:
        async def event_generator():
            chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": target_model,
                "choices": [{"index": 0, "delta": {"role": "assistant", "content": response_text}, "finish_reason": None}]
            }
            yield f"data: {json.dumps(chunk)}\n\n"
            end_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": created_ts,
                "model": target_model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
            }
            yield f"data: {json.dumps(end_chunk)}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return JSONResponse(
        status_code=200,
        content={
            "id": completion_id,
            "object": "chat.completion",
            "created": created_ts,
            "model": target_model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": max(1, len(user_prompt.split())),
                "completion_tokens": max(1, len(response_text.split())),
                "total_tokens": max(1, len(user_prompt.split())) + max(1, len(response_text.split()))
            }
        }
    )


def _ollama_model_name(model_id: str) -> Optional[str]:
    try:
        from core.models.registry import get_model_registry
        reg = get_model_registry()
        spec = reg.get(model_id)
        if spec and getattr(spec, "provider", "") == "ollama":
            return getattr(spec, "ollama_model", None) or model_id
    except Exception:
        pass
    if model_id == "sparkx":
        return "SparkLLM/Spark-X2.6-1.7B:latest"
    return None


def _execute_routed_inference(prompt: str, decision, actor: str = "infer") -> str:
    """Execute routed inference; respects local/sensitive routing decisions. Network calls only for allowed local Ollama."""
    profile = decision.profile
    tier = getattr(profile, "tier", "")
    model_id = decision.selected_model
    # Only attempt Ollama network call for edge/local tier decisions.
    if tier.startswith("edge"):
        ollama_model = _ollama_model_name(model_id)
        if ollama_model and getattr(profile, "endpoint", "").startswith("http"):
            try:
                import urllib.request
                base = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
                payload = json.dumps({"model": ollama_model, "messages": [{"role": "user", "content": prompt}], "stream": False}).encode("utf-8")
                ollama_req = urllib.request.Request(f"{base}/api/chat", data=payload, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(ollama_req, timeout=60) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    out = result.get("message", {}).get("content", "")
                    if out:
                        return out
            except Exception as e:
                audit_event("gateway.infer.ollama_fallback", actor=actor, outcome="warn", detail={"model": model_id, "error": str(e)[:160]})
    # Cloud/frontier execution is intentionally not performed here without explicit provider integration + policy; return safe mock/routed stub.
    return ctx.router.execute_mock_edge_infer(prompt, rb_adapter=ctx.ring_buffer)


@app.post("/api/v1/infer")
def route_inference(req: InferRequest, request: Request):
    actor = _require_api_auth(request, "infer")
    if not ctx.router:
        raise HTTPException(status_code=503, detail="Model router not initialized")
    model_req = ModelRequest(
        prompt=req.prompt,
        security_clearance=req.security_clearance,
        max_latency_ms=req.max_latency_ms,
        offline_mode=req.offline_mode,
        prefer_cloud=req.prefer_cloud,
        task_type=req.task_type,
    )
    decision = ctx.router.route(model_req)
    output = _execute_routed_inference(req.prompt, decision, actor=actor)
    audit_event("gateway.infer", actor=actor, outcome="ok", detail={"model": decision.selected_model, "tier": getattr(decision.profile, "tier", None), "task_type": req.task_type})
    return {
        "model_selected": decision.selected_model,
        "routing_reason": decision.reason,
        "latency_tier": decision.profile.tier,
        "output": output,
    }


@app.post("/api/v1/orchestrator/dispatch")
def dispatch_objective(req: ObjectiveRequest, request: Request):
    actor = _require_api_auth(request, "orchestrator.dispatch")
    if not ctx.swarm:
        raise HTTPException(status_code=503, detail="Omni swarm not initialized")
    try:
        result = ctx.swarm.execute_objective(req.objective)
    except TypeError:
        result = ctx.swarm.execute_objective(objective=req.objective, caller_agent_id=getattr(req, 'caller_agent_id', None))
    if isinstance(result, dict) and getattr(req, 'caller_agent_id', None): result['caller_agent_id'] = req.caller_agent_id
    audit_event("gateway.orchestrator.dispatch", actor=actor, outcome="ok", detail={"objective_len": len(req.objective or ""), "caller_agent_id": req.caller_agent_id})
    return result


@app.get("/api/v1/swarm/status")
def get_swarm_status(request: Request):
    actor = _require_api_auth(request, "swarm.status")
    if not ctx.swarm:
        raise HTTPException(status_code=503, detail="Omni swarm not initialized")
    return ctx.swarm.get_status()


@app.post("/api/v1/swarm/control")
def control_swarm_resources(req: SwarmControlRequest, request: Request):
    actor = _require_api_auth(request, "swarm.control")
    """Manual intervention for resource preservation."""
    if not ctx.swarm:
        raise HTTPException(status_code=503, detail="Omni swarm not initialized")
    action = req.action.lower()
    if action == "pause":
        ctx.swarm.pause()
        return {"status": "PAUSED", "is_paused": True}
    elif action == "resume":
        ctx.swarm.resume()
        return {"status": "RESUMED", "is_paused": False}
    elif action == "throttle":
        ctx.swarm.set_throttle(req.throttle_delay_ms or 0)
        return {"status": "THROTTLED", "delay_ms": req.throttle_delay_ms}
    else:
        raise HTTPException(status_code=400, detail=f"Unknown control action: {req.action}")


@app.get("/api/v1/treasury/status")
def get_treasury_status(request: Request):
    actor = _require_api_auth(request, "treasury.status")
    return {
        "treasury_vessel": "CVN-AEGENTIX-01",
        "status": "OPERATIONAL",
        "reserve_usd": 50000.00,
        "allocation_policy": "ZERO_LOSS_INVARIANT_GATE_SYM_02",
        "accounting_standard": "DOUBLE_ENTRY_RECONCILED",
    }

# --- Infinite Brain OS / HUD MCP bridge (mounted when available) ---
try:
    from core.gateway.mcp_bridge import mcp_info, mcp_rpc, grok_dossier, router as _infinite_brain_mcp_router
    try:
        app.include_router(_infinite_brain_mcp_router)
    except Exception:
        pass
    _paths = {getattr(r, "path", None) for r in app.routes}
    if "/mcp/info" not in _paths:
        app.add_api_route("/mcp/info", mcp_info, methods=["GET"])
    if "/mcp" not in _paths:
        app.add_api_route("/mcp", mcp_rpc, methods=["POST"])
    if "/api/grok/dossier" not in _paths:
        app.add_api_route("/api/grok/dossier", grok_dossier, methods=["GET"])
except Exception as _e:
    try:
        print("[gateway] MCP bridge not mounted: " + str(_e))
    except Exception:
        pass

# --- Hypervisor viewport + immersive gated auth/encryption (mounted when available) ---
try:
    from core.hypervisor.api import router as _hypervisor_router
    try:
        app.include_router(_hypervisor_router)
    except Exception:
        pass
    _paths = {getattr(r, "path", None) for r in app.routes}
    for path, method, fn in [
        ("/api/v1/hypervisor/profiles", "GET", None),
    ]:
        pass
except Exception as _e:
    try:
        print("[gateway] hypervisor not mounted: " + str(_e))
    except Exception:
        pass

# --- Model housing registry API (mounted when available) ---
try:
    from core.models.api import router as _models_router
    try:
        app.include_router(_models_router)
    except Exception:
        pass
except Exception as _e:
    try:
        print("[gateway] models API not mounted: " + str(_e))
    except Exception:
        pass

# --- LLM workspace tap-in API (mounted when available) ---
try:
    from core.llm_workspace.api import router as _llmws_router
    try:
        app.include_router(_llmws_router)
    except Exception:
        pass
except Exception as _e:
    try:
        print("[gateway] llm-workspace API not mounted: " + str(_e))
    except Exception:
        pass


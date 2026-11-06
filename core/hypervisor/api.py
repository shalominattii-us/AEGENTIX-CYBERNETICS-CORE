"""Gateway routes for Hypervisor viewport and procedural immersive gates."""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

try:
    from core.gateway.security import audit_event, authorize_request
except Exception:
    def audit_event(*a, **k): return None
    def authorize_request(*a, **k): return (False, "unknown", "security_unavailable")

from core.hypervisor import (
    ImmersiveVersion, profile_for, get_hypervisor_viewport,
    issue_procedural_gate, advance_procedural_gate, get_gate, verify_immersive_access,
    decrypt_envelope,
)
try:
    from core.hypervisor.gates import list_active_gates, revoke_gate
except Exception:
    list_active_gates = revoke_gate = None  # type: ignore

router = APIRouter(prefix="/api/v1/hypervisor", tags=["hypervisor"])


def _auth(request: Request, scope: str, min_version: int = 1):
    # Allow L0 status-like probes only via explicit scope rules; default requires auth.
    ok, actor, reason = authorize_request(request, scope=scope)
    if not ok:
        audit_event("hypervisor.auth.denied", actor=actor, outcome="denied", detail={"scope": scope, "reason": reason})
        raise HTTPException(status_code=401, detail="Unauthorized")
    return actor


class GateIssueRequest(BaseModel):
    version: int = Field(default=2, ge=0, le=4)
    scope: str = Field(default="viewport.hoods")


class GateAdvanceRequest(BaseModel):
    gate_id: str
    proof: Optional[str] = None  # procedural proof/challenge response; production binds to hardware/WebAuthn/signed claims


class EnvelopeRequest(BaseModel):
    version: int = Field(default=2, ge=0, le=4)
    scope: str = Field(default="viewport.hoods")
    gate_id: Optional[str] = None
    encrypted: bool = True


@router.get("/profiles")
async def list_profiles(request: Request):
    actor = _auth(request, "viewport.read", 1)
    audit_event("hypervisor.profiles", actor=actor, outcome="ok")
    return {"profiles": {int(v): {"name": p.name, "scopes": sorted(p.scopes), "requires_token": p.requires_token, "requires_encrypted_envelope": p.requires_encrypted_envelope, "requires_procedural_steps": p.requires_procedural_steps, "description": p.description} for v, p in __import__('core.hypervisor.immersive', fromlist=['PROFILES']).PROFILES.items()}}


@router.get("/viewport")
async def viewport_snapshot(request: Request, version: int = 1, encrypted: Optional[bool] = None, gate_id: Optional[str] = None):
    v = ImmersiveVersion(max(0, min(4, int(version))))
    scope = "viewport.hoods" if int(v) >= 3 else "viewport.read"
    # Determine token presence from request; local-noauth ROG mode is handled by verify_immersive_access/profile.
    from core.gateway.security import extract_bearer
    token_present = bool(extract_bearer(request))
    actor = _auth(request, scope, min_version=max(0, min(int(v), 4)))
    profile = profile_for(v)
    use_encrypted = profile.requires_encrypted_envelope if encrypted is None else bool(encrypted)
    if profile.requires_encrypted_envelope and encrypted is False and int(v) >= 2:
        use_encrypted = True  # enforce for engineer+ hoods
    ok, reason, detail = verify_immersive_access(version=v, scope=scope, actor=actor, token_present=token_present or profile.allow_local_noauth, encrypted_envelope_present=use_encrypted, gate_id=gate_id)
    if not ok:
        audit_event("hypervisor.viewport.denied", actor=actor, outcome="denied", detail={"reason": reason, **detail})
        hint = None
        if reason == "procedural_gate_required":
            try:
                st = issue_procedural_gate(version=v, scope=scope, actor=actor)
                hint = {"gate_id": st.gate_id, "steps_required": st.steps_required, "challenges": st.challenges, "expires_ts": st.expires_ts}
            except Exception:
                pass
        raise HTTPException(status_code=403, detail={"error": reason, "detail": detail, "gate": hint})
    hv = get_hypervisor_viewport()
    audit_event("hypervisor.viewport", actor=actor, outcome="ok", detail={"version": int(v), "scope": scope, "encrypted": use_encrypted})
    if use_encrypted and int(v) >= 2:
        return hv.encrypted_snapshot(version=v, actor=actor, scope=scope)
    return hv.hood_snapshot(version=v)


@router.post("/gate/issue")
async def gate_issue(req: GateIssueRequest, request: Request):
    actor = _auth(request, "viewport.read", 1)
    v = ImmersiveVersion(max(0, min(4, req.version)))
    st = issue_procedural_gate(version=v, scope=req.scope, actor=actor)
    audit_event("hypervisor.gate.issue", actor=actor, outcome="ok", detail={"gate_id": st.gate_id, "version": int(v), "scope": req.scope})
    return {"gate_id": st.gate_id, "version": int(v), "scope": st.scope, "steps_required": st.steps_required, "steps_completed": st.steps_completed, "challenges": st.challenges, "expires_ts": st.expires_ts, "authorized": st.authorized}


@router.post("/gate/advance")
async def gate_advance(req: GateAdvanceRequest, request: Request):
    actor = _auth(request, "viewport.read", 1)
    try:
        st = advance_procedural_gate(req.gate_id, actor=actor, proof=req.proof)
    except Exception as e:
        audit_event("hypervisor.gate.advance", actor=actor, outcome="error", detail={"gate_id": req.gate_id, "error": str(e)})
        raise HTTPException(status_code=400, detail=str(e))
    audit_event("hypervisor.gate.advance", actor=actor, outcome="ok", detail={"gate_id": st.gate_id, "steps_completed": st.steps_completed, "authorized": st.authorized})
    return {"gate_id": st.gate_id, "steps_required": st.steps_required, "steps_completed": st.steps_completed, "authorized": st.authorized, "expires_ts": st.expires_ts}


@router.post("/gate/status")
async def gate_status(request: Request, gate_id: str):
    actor = _auth(request, "viewport.read", 1)
    st = get_gate(gate_id)
    if not st:
        raise HTTPException(status_code=404, detail="gate not found")
    return {"gate_id": st.gate_id, "version": int(st.version), "scope": st.scope, "steps_required": st.steps_required, "steps_completed": st.steps_completed, "authorized": st.authorized, "expires_ts": st.expires_ts}


@router.get("/gates")
async def gates_list(request: Request):
    actor = _auth(request, "viewport.read", 1)
    items = list_active_gates(actor=None) if list_active_gates else []
    audit_event("hypervisor.gates.list", actor=actor, outcome="ok", detail={"count": len(items)})
    return {"gates": items, "count": len(items)}


@router.post("/gate/revoke")
async def gate_revoke(request: Request, gate_id: str, reason: str = ""):
    actor = _auth(request, "swarm.control", 3)
    if not revoke_gate:
        raise HTTPException(status_code=501, detail="revoke unavailable")
    revoke_gate(gate_id, actor=actor, reason=reason)
    audit_event("hypervisor.gate.revoke", actor=actor, outcome="ok", detail={"gate_id": gate_id, "reason": reason[:120]})
    return {"ok": True, "gate_id": gate_id, "revoked": True}

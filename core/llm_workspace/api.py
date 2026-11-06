"""Gateway routes for gated LLM workspace tap-in."""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

try:
    from core.gateway.security import audit_event, authorize_request
except Exception:
    def audit_event(*a, **k): return None
    def authorize_request(*a, **k): return (False, "unknown", "security_unavailable")

from .resolver import resolve_llm_workspace
from .jobs import workspace_status, list_checkpoints, create_job, get_job

router = APIRouter(prefix="/api/v1/llm-workspace", tags=["llm-workspace"])


def _auth(request: Request, scope: str):
    ok, actor, reason = authorize_request(request, scope=scope)
    if not ok:
        audit_event("llm_workspace.auth.denied", actor=actor, outcome="denied", detail={"scope": scope, "reason": reason})
        raise HTTPException(status_code=401, detail="Unauthorized")
    return actor


class PlanRequest(BaseModel):
    kind: str = Field(default="train_plan")
    detail: Dict[str, Any] = Field(default_factory=dict)


@router.get("/status")
async def status(request: Request):
    actor = _auth(request, "models.read")
    return workspace_status(actor=actor)


@router.get("/checkpoints")
async def checkpoints(request: Request, limit: int = 50):
    actor = _auth(request, "models.read")
    try:
        items = list_checkpoints(actor=actor, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"checkpoints": items, "count": len(items)}


@router.post("/jobs/plan")
async def plan_job(req: PlanRequest, request: Request):
    actor = _auth(request, "orchestrator.dispatch")
    try:
        job = create_job(req.kind, actor=actor, detail=req.detail)
    except Exception as e:
        audit_event("llm_workspace.job.plan_failed", actor=actor, outcome="error", detail={"error": str(e)[:160]})
        raise HTTPException(status_code=400, detail=str(e))
    return job


@router.get("/jobs/{job_id}")
async def read_job(job_id: str, request: Request):
    actor = _auth(request, "models.read")
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job

"""Gated LLM workspace tap-in control plane (local, audited).

This module provides *scoped* metadata/planning interfaces for the LLM Development Workspace.
It does not execute arbitrary shell by default. Training/run execution requires explicit
AEGENTIX_LLM_WORKSPACE_ALLOW_EXEC=1 and is constrained to the resolved workspace root.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .resolver import resolve_llm_workspace

try:
    from core.gateway.security import audit_event
except Exception:
    def audit_event(*a, **k): return None


@dataclass
class WorkspaceJob:
    job_id: str
    kind: str
    status: str
    actor: str
    created_ts: float
    detail: Dict[str, Any]


_JOBS: Dict[str, WorkspaceJob] = {}


def _workspace_root() -> Path:
    r = resolve_llm_workspace()
    root = r.get("workspace_root")
    if not root:
        raise ValueError("llm workspace root not resolved")
    return Path(root).resolve()


def _safe_under_root(path: str) -> Path:
    root = _workspace_root()
    p = (root / path).resolve() if not os.path.isabs(path) else Path(path).resolve()
    try:
        p.relative_to(root)
    except Exception:
        raise ValueError("path escapes workspace root")
    return p


def workspace_status(actor: str = "unknown") -> Dict[str, Any]:
    r = resolve_llm_workspace()
    audit_event("llm_workspace.status", actor=actor, outcome="ok" if r.get("ok") else "warn", detail={"ok": r.get("ok")})
    return r


def list_checkpoints(actor: str = "unknown", limit: int = 50) -> List[Dict[str, Any]]:
    root = _workspace_root()
    ckpt = root / "checkpoints"
    items = []
    if ckpt.exists():
        for p in sorted(ckpt.rglob("*"), key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True):
            if p.is_file():
                try:
                    st = p.stat()
                    items.append({"path": str(p.relative_to(root)).replace("\\", "/"), "bytes": st.st_size, "mtime": st.st_mtime})
                except Exception:
                    pass
            if len(items) >= max(1, min(limit, 500)):
                break
    audit_event("llm_workspace.checkpoints.list", actor=actor, outcome="ok", detail={"count": len(items)})
    return items


def create_job(kind: str, actor: str, detail: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    allowed = {"train_plan", "eval_plan", "artifact_register_plan"}
    if kind not in allowed:
        raise ValueError(f"unsupported job kind: {kind}")
    job = WorkspaceJob(job_id="llmws_" + uuid.uuid4().hex[:12], kind=kind, status="planned", actor=actor, created_ts=time.time(), detail=dict(detail or {}))
    _JOBS[job.job_id] = job
    audit_event("llm_workspace.job.planned", actor=actor, outcome="ok", detail={"job_id": job.job_id, "kind": kind})
    return asdict(job)


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    j = _JOBS.get(job_id)
    return asdict(j) if j else None

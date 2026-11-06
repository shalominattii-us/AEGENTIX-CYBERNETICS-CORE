"""Persistent store for procedural gates, gate audit, and token/gate lifecycle.

Uses JSONL append-only + in-memory index (consistent with AetherMemory pattern).
Survives gateway restarts; supports revocation, TTL cleanup, replay protection.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

_STORE_PATH = Path(os.environ.get("AEGENTIX_GATE_STORE", "data/hypervisor_gates.jsonl"))
_LOCK = threading.Lock()
_LOADED = False
_GATES: Dict[str, Dict[str, Any]] = {}
_USED_PROOFS: Dict[str, float] = {}
_REVOKED: set = set()


def _ensure_loaded() -> None:
    global _LOADED
    if _LOADED:
        return
    with _LOCK:
        if _LOADED:
            return
        if _STORE_PATH.exists():
            try:
                for line in _STORE_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue
                    ev = rec.get("event")
                    gid = rec.get("gate_id")
                    if ev == "issue" and gid:
                        _GATES[gid] = rec.get("state") or {}
                    elif ev == "advance" and gid and gid in _GATES:
                        _GATES[gid] = rec.get("state") or _GATES[gid]
                    elif ev == "revoke" and gid:
                        _REVOKED.add(gid)
                        if gid in _GATES:
                            _GATES[gid]["revoked"] = True
                            _GATES[gid]["authorized"] = False
                    elif ev == "proof_used":
                        ph = rec.get("proof_hash")
                        if ph:
                            _USED_PROOFS[ph] = rec.get("ts", time.time())
            except Exception:
                pass
        _LOADED = True


def _append(rec: Dict[str, Any]) -> None:
    try:
        _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(rec, ensure_ascii=False, default=str)
        with _LOCK:
            with _STORE_PATH.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
    except Exception:
        pass


def persist_issue(state: Dict[str, Any]) -> None:
    _ensure_loaded()
    gid = state.get("gate_id")
    if gid:
        _GATES[gid] = dict(state)
    _append({"event": "issue", "ts": time.time(), "gate_id": gid, "state": state})


def persist_advance(state: Dict[str, Any]) -> None:
    _ensure_loaded()
    gid = state.get("gate_id")
    if gid:
        _GATES[gid] = dict(state)
    _append({"event": "advance", "ts": time.time(), "gate_id": gid, "state": state})


def persist_revoke(gate_id: str, actor: str, reason: str = "") -> bool:
    _ensure_loaded()
    _REVOKED.add(gate_id)
    if gate_id in _GATES:
        _GATES[gate_id]["revoked"] = True
        _GATES[gate_id]["authorized"] = False
    _append({"event": "revoke", "ts": time.time(), "gate_id": gate_id, "actor": actor, "reason": reason})
    return True


def get_persisted(gate_id: str) -> Optional[Dict[str, Any]]:
    _ensure_loaded()
    st = _GATES.get(gate_id)
    if not st:
        return None
    if gate_id in _REVOKED or st.get("revoked"):
        st = dict(st); st["revoked"] = True; st["authorized"] = False
    return st


def mark_proof_used(proof_hash: str) -> bool:
    """Returns True if proof was new (ok), False if replay detected."""
    _ensure_loaded()
    now = time.time()
    cutoff = now - 600
    for k in [k for k, v in _USED_PROOFS.items() if v < cutoff]:
        _USED_PROOFS.pop(k, None)
    if proof_hash in _USED_PROOFS:
        return False
    _USED_PROOFS[proof_hash] = now
    _append({"event": "proof_used", "ts": now, "proof_hash": proof_hash})
    return True


def list_gates(actor: Optional[str] = None, include_expired: bool = False) -> List[Dict[str, Any]]:
    _ensure_loaded()
    now = time.time()
    out = []
    for gid, st in _GATES.items():
        if actor and st.get("actor") != actor:
            continue
        if not include_expired and float(st.get("expires_ts", 0) or 0) < now:
            continue
        s = dict(st)
        s["revoked"] = gid in _REVOKED or s.get("revoked", False)
        out.append(s)
    out.sort(key=lambda x: x.get("created_ts", 0), reverse=True)
    return out


def cleanup_expired() -> int:
    _ensure_loaded()
    now = time.time()
    expired = [gid for gid, st in _GATES.items() if float(st.get("expires_ts", 0) or 0) < now - 3600]
    for gid in expired:
        _GATES.pop(gid, None)
    return len(expired)

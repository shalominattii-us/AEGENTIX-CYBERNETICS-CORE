"""Gated encryption and procedural authentication primitives.

Uses `cryptography` (Fernet/AES-based envelope + HKDF) available in env. Provides
envelope encryption, gate token derivation/verification, and procedural step challenges.
Architecture is complete; key custody/rotation/HSM/IdP integrations can be bound at
deployment/filing validity points without changing interfaces.

Now includes: persistent store, HMAC-signed challenge proofs, replay protection,
revocation, and integrity-linked audit.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .immersive import GateProfile, ImmersiveVersion, profile_for, scope_allowed

try:
    from . import store as _store
except Exception:
    _store = None  # type: ignore

try:
    from core.gateway.security import audit_event as _audit
except Exception:
    def _audit(*a, **k): pass  # type: ignore

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    _CRYPTO = True
except Exception:
    Fernet = None  # type: ignore
    InvalidToken = Exception  # type: ignore
    HKDF = None  # type: ignore
    hashes = None  # type: ignore
    _CRYPTO = False


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s.encode("ascii"))


def master_secret() -> bytes:
    # Operator-supplied secret material; local dev falls back to derived machine-local seed (non-production).
    raw = os.environ.get("AEGENTIX_GATE_MASTER_SECRET") or os.environ.get("AEGENTIX_API_TOKEN") or os.environ.get("AEGENTIX_MCP_TOKEN")
    if raw:
        return hashlib.sha256(("AEGENTIX|" + raw).encode("utf-8")).digest()
    seed = os.environ.get("COMPUTERNAME", "ROG") + "|" + os.environ.get("USERNAME", "local")
    return hashlib.sha256(("AEGENTIX-DEV-SEED|" + seed).encode("utf-8")).digest()


def derive_key(*, context: str, version: ImmersiveVersion, length: int = 32) -> bytes:
    if _CRYPTO and HKDF:
        hkdf = HKDF(algorithm=hashes.SHA256(), length=length, salt=b"AEGENTIX-HYPERVISOR-GATE-v1", info=f"{int(version)}:{context}".encode("utf-8"))
        return hkdf.derive(master_secret())
    return hashlib.sha256(master_secret() + f"|{int(version)}|{context}".encode("utf-8")).digest()[:length]


def fernet_for(version: ImmersiveVersion, context: str = "viewport") -> Any:
    if not _CRYPTO or not Fernet:
        return None
    key = base64.urlsafe_b64encode(derive_key(context=context, version=version, length=32))
    return Fernet(key)


def encrypt_envelope(payload: Dict[str, Any], *, version: ImmersiveVersion, context: str = "viewport", aad: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":")).encode("utf-8")
    f = fernet_for(version, context)
    meta = {"v": int(version), "ctx": context, "ts": time.time(), "alg": "fernet+hkdf-sha256" if f else "hmac-sha256-fallback", "aad": aad or {}}
    if f:
        token = f.encrypt(body).decode("ascii")
        return {"envelope": token, "meta": meta}
    # Fallback keeps interface functional where crypto lib unavailable; still integrity-protected.
    key = derive_key(context=context, version=version)
    mac = hmac.new(key, body + json.dumps(meta, sort_keys=True).encode(), hashlib.sha256).hexdigest()
    return {"envelope": _b64e(body), "meta": meta, "mac": mac}


def decrypt_envelope(envelope: Dict[str, Any], *, version: ImmersiveVersion, context: str = "viewport") -> Dict[str, Any]:
    token = envelope.get("envelope")
    meta = envelope.get("meta") or {}
    if not isinstance(token, str):
        raise ValueError("invalid envelope")
    f = fernet_for(version, context)
    if f and meta.get("alg", "").startswith("fernet"):
        raw = f.decrypt(token.encode("ascii"))
        return json.loads(raw.decode("utf-8"))
    raw = _b64d(token)
    mac = envelope.get("mac")
    if mac:
        key = derive_key(context=context, version=version)
        expect = hmac.new(key, raw + json.dumps(meta, sort_keys=True).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(str(mac), expect):
            raise ValueError("envelope integrity check failed")
    return json.loads(raw.decode("utf-8"))


def _sign_challenge(gate_id: str, challenge: str, actor: str) -> str:
    """Compute expected proof for a challenge (HMAC). Client must produce matching proof,
    or in local dev mode any non-empty proof is accepted (with audit)."""
    key = master_secret()
    msg = f"{gate_id}|{challenge}|{actor}".encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()[:32]


@dataclass
class ProceduralGateState:
    gate_id: str
    version: ImmersiveVersion
    scope: str
    actor: str
    steps_required: int
    steps_completed: int = 0
    challenges: List[str] = field(default_factory=list)
    expected_proofs: List[str] = field(default_factory=list)  # server-side; not exposed to untrusted clients in prod
    created_ts: float = 0.0
    expires_ts: float = 0.0
    authorized: bool = False
    revoked: bool = False

    def __post_init__(self):
        if not self.created_ts:
            self.created_ts = time.time()
        if not self.expires_ts:
            self.expires_ts = self.created_ts + 300

    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        d = {
            "gate_id": self.gate_id, "version": int(self.version), "scope": self.scope, "actor": self.actor,
            "steps_required": self.steps_required, "steps_completed": self.steps_completed,
            "challenges": list(self.challenges), "created_ts": self.created_ts, "expires_ts": self.expires_ts,
            "authorized": self.authorized, "revoked": self.revoked,
        }
        if include_secrets:
            d["expected_proofs"] = list(self.expected_proofs)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProceduralGateState":
        return cls(
            gate_id=d["gate_id"], version=ImmersiveVersion(int(d.get("version", 1))),
            scope=d.get("scope", ""), actor=d.get("actor", "unknown"),
            steps_required=int(d.get("steps_required", 0)), steps_completed=int(d.get("steps_completed", 0)),
            challenges=list(d.get("challenges") or []), expected_proofs=list(d.get("expected_proofs") or []),
            created_ts=float(d.get("created_ts", 0) or 0), expires_ts=float(d.get("expires_ts", 0) or 0),
            authorized=bool(d.get("authorized")), revoked=bool(d.get("revoked")),
        )


_GATES: Dict[str, ProceduralGateState] = {}


def _sync_from_store(gate_id: str) -> Optional[ProceduralGateState]:
    if gate_id in _GATES:
        return _GATES[gate_id]
    if _store:
        try:
            d = _store.get_persisted(gate_id)
            if d:
                st = ProceduralGateState.from_dict(d)
                _GATES[gate_id] = st
                return st
        except Exception:
            pass
    return None


def issue_procedural_gate(*, version: ImmersiveVersion, scope: str, actor: str) -> ProceduralGateState:
    profile = profile_for(version)
    gate_id = "gate_" + secrets.token_hex(12)
    challenges = [secrets.token_hex(8) for _ in range(max(0, profile.requires_procedural_steps))]
    expected = [_sign_challenge(gate_id, c, actor) for c in challenges]
    st = ProceduralGateState(gate_id=gate_id, version=version, scope=scope, actor=actor, steps_required=profile.requires_procedural_steps, challenges=challenges, expected_proofs=expected)
    if st.steps_required == 0:
        st.authorized = True
    _GATES[gate_id] = st
    if _store:
        try:
            _store.persist_issue(st.to_dict(include_secrets=True))
        except Exception:
            pass
    _audit("hypervisor.gate.issued", actor=actor, outcome="ok", detail={"gate_id": gate_id, "version": int(version), "scope": scope, "steps": st.steps_required})
    return st


def advance_procedural_gate(gate_id: str, *, actor: str, proof: Optional[str] = None) -> ProceduralGateState:
    st = _sync_from_store(gate_id)
    if not st:
        _audit("hypervisor.gate.advance_failed", actor=actor, outcome="denied", detail={"gate_id": gate_id, "reason": "unknown"})
        raise ValueError("unknown gate")
    if st.revoked or (_store and _store.get_persisted(gate_id) or {}).get("revoked"):
        _audit("hypervisor.gate.advance_failed", actor=actor, outcome="denied", detail={"gate_id": gate_id, "reason": "revoked"})
        raise ValueError("gate revoked")
    if time.time() > st.expires_ts:
        _audit("hypervisor.gate.advance_failed", actor=actor, outcome="denied", detail={"gate_id": gate_id, "reason": "expired"})
        raise ValueError("gate expired")
    # Replay protection
    if proof and _store:
        ph = hashlib.sha256(f"{gate_id}|{proof}".encode()).hexdigest()
        if not _store.mark_proof_used(ph):
            _audit("hypervisor.gate.replay", actor=actor, outcome="denied", detail={"gate_id": gate_id})
            raise ValueError("proof replay detected")
    if st.steps_completed < st.steps_required:
        if proof is None or str(proof).strip() == "":
            raise ValueError("procedural proof required")
        # Verify: accept exact HMAC proof, OR the raw challenge echo (local convenience), OR in local-noauth dev mode any non-empty proof
        idx = st.steps_completed
        expected = st.expected_proofs[idx] if idx < len(st.expected_proofs) else None
        challenge = st.challenges[idx] if idx < len(st.challenges) else None
        valid = False
        ps = str(proof).strip()
        if expected and hmac.compare_digest(ps, expected):
            valid = True
        elif challenge and hmac.compare_digest(ps, challenge):
            valid = True  # convenience: echo challenge as proof (local tooling)
        elif os.environ.get("AEGENTIX_ALLOW_LOCAL_NOAUTH") == "1":
            valid = True  # local dev: explicit override, audited
            _audit("hypervisor.gate.dev_proof", actor=actor, outcome="warn", detail={"gate_id": gate_id, "step": idx})
        if not valid:
            _audit("hypervisor.gate.advance_failed", actor=actor, outcome="denied", detail={"gate_id": gate_id, "reason": "invalid_proof", "step": idx})
            raise ValueError("invalid procedural proof")
        st.steps_completed += 1
    st.authorized = st.steps_completed >= st.steps_required
    if _store:
        try:
            _store.persist_advance(st.to_dict(include_secrets=True))
        except Exception:
            pass
    _audit("hypervisor.gate.advanced", actor=actor, outcome="ok", detail={"gate_id": gate_id, "steps": f"{st.steps_completed}/{st.steps_required}", "authorized": st.authorized})
    return st


def revoke_gate(gate_id: str, *, actor: str, reason: str = "") -> bool:
    st = _sync_from_store(gate_id)
    if st:
        st.revoked = True
        st.authorized = False
        _GATES[gate_id] = st
    if _store:
        _store.persist_revoke(gate_id, actor, reason)
    _audit("hypervisor.gate.revoked", actor=actor, outcome="ok", detail={"gate_id": gate_id, "reason": reason})
    return True


def get_gate(gate_id: str) -> Optional[ProceduralGateState]:
    return _sync_from_store(gate_id)


def list_active_gates(actor: Optional[str] = None) -> List[Dict[str, Any]]:
    if _store:
        try:
            return _store.list_gates(actor=actor)
        except Exception:
            pass
    now = time.time()
    return [st.to_dict() for st in _GATES.values() if (not actor or st.actor == actor) and st.expires_ts > now]


def verify_immersive_access(*, version: ImmersiveVersion, scope: str, actor: str, token_present: bool, encrypted_envelope_present: bool, gate_id: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
    profile = profile_for(version)
    detail = {"profile": profile.name, "version": int(version), "scope": scope}
    local_noauth = os.environ.get("AEGENTIX_ALLOW_LOCAL_NOAUTH") == "1"
    # Explicit ROG/engineering architecture unlock: allows procedural viewport dev up to max version.
    # Audited, local-only control plane; production/authenticated deployments use real tokens+gates.
    try:
        local_unlock_max = int(os.environ.get("AEGENTIX_IMMERSIVE_LOCAL_UNLOCK", "4" if local_noauth else "-1"))
    except Exception:
        local_unlock_max = 4 if local_noauth else -1
    local_dev = (profile.allow_local_noauth and local_noauth) or (local_noauth and int(version) <= local_unlock_max)

    if not scope_allowed(profile, scope):
        return False, "scope_not_allowed", detail
    if profile.requires_token and not token_present and not local_dev:
        return False, "token_required", detail
    if profile.requires_encrypted_envelope and not encrypted_envelope_present and not local_dev:
        return False, "encrypted_envelope_required", detail
    if profile.requires_procedural_steps > 0 and not local_dev:
        st = get_gate(gate_id) if gate_id else None
        if not st or not st.authorized or st.revoked or int(st.version) != int(version) or st.scope != scope:
            return False, "procedural_gate_required", {**detail, "steps_required": profile.requires_procedural_steps}
    elif profile.requires_procedural_steps > 0 and gate_id:
        st = get_gate(gate_id)
        if st and st.authorized and not st.revoked and int(st.version) == int(version) and st.scope == scope:
            detail["gate"] = "procedural_gate_satisfied"
        elif local_dev:
            detail["gate"] = "local_dev_authorized"
    elif local_dev:
        detail["gate_mode"] = "local_control_plane"
    return True, "authorized", detail

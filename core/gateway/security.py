"""SOC2-aligned security controls for gateway/MCP (local ROG profile)."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

AUDIT_LOG_PATH = Path(os.environ.get("AEGENTIX_AUDIT_LOG", "data/security_audit.jsonl"))
_AUDIT_LOCK = threading.Lock()


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            lk = str(k).lower()
            if any(s in lk for s in ("token", "secret", "password", "authorization", "api_key", "credential")):
                out[k] = "<redacted>"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


def audit_event(event: str, *, actor: str = "unknown", outcome: str = "info", detail: Optional[Dict[str, Any]] = None) -> None:
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "ts": time.time(),
            "event": event,
            "actor": actor,
            "outcome": outcome,
            "detail": _redact(detail or {}),
        }
        line = json.dumps(rec, ensure_ascii=False, default=str)
        with _AUDIT_LOCK:
            with AUDIT_LOG_PATH.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
    except Exception:
        pass


def _expected_token() -> Optional[str]:
    # Primary control token for local/admin API access. In production, replace with mTLS/IdP/JWT validation.
    for k in ("AEGENTIX_API_TOKEN", "AEGENTIX_MCP_TOKEN"):
        v = os.environ.get(k)
        if v:
            return v
    return None


def extract_bearer(request) -> Optional[str]:
    auth = (getattr(request, "headers", {}) or {}).get("authorization") or (getattr(request, "headers", {}) or {}).get("Authorization")
    if not auth:
        return None
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


def authorize_request(request, *, scope: str = "api", allow_localhost_without_token: bool = False) -> Tuple[bool, str, str]:
    """Return (ok, actor, reason). Fail-closed unless explicitly allowed."""
    token = extract_bearer(request)
    expected = _expected_token()
    client_host = None
    try:
        client_host = getattr(getattr(request, "client", None), "host", None)
    except Exception:
        client_host = None
    is_local = client_host in ("127.0.0.1", "::1", "localhost", "testclient", None)

    # Explicit local ROG/dev override: loopback-only, operator-controlled, audited.
    # Takes precedence to keep HUD/local control plane functional on machines with stale token env vars.
    if is_local and os.environ.get("AEGENTIX_ALLOW_LOCAL_NOAUTH") == "1":
        if token and expected and hmac.compare_digest(token, expected):
            actor = "token:" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]
            return True, actor, "authorized_token_local"
        return True, f"local:{client_host or 'unknown'}", "local_noauth_dev_override"

    if expected:
        if token and hmac.compare_digest(token, expected):
            actor = "token:" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]
            return True, actor, "authorized"
        return False, f"client:{client_host or 'unknown'}", "missing_or_invalid_token"

    # SOC2 local control-plane mode: fail closed by default unless explicit local override above.
    if allow_localhost_without_token and is_local:
        return True, f"local:{client_host or 'unknown'}", "local_noauth_param"
    return False, f"client:{client_host or 'unknown'}", "auth_not_configured"

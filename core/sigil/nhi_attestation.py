class AttestationError(Exception):
    pass


class AttestationVerifier:
    """Fail-closed verifier. Real cryptographic attestation must be configured in production."""
    def __init__(self, expected_token: str | None = None, *args, **kwargs):
        import os
        self.expected_token = expected_token or os.environ.get("AEGENTIX_API_TOKEN") or os.environ.get("AEGENTIX_MCP_TOKEN")

    def verify_token(self, token, required_capabilities=None):
        import hmac, time
        if token is None:
            return False
        # Accept only when a token string/field matches configured expected token (local control plane).
        # This replaces the previous permissive shim; production should use signed NHI claims.
        if not self.expected_token:
            return False
        candidate = None
        if hasattr(token, "raw") and isinstance(getattr(token, "raw"), dict):
            candidate = token.raw.get("token") or token.raw.get("access_token")
        if not candidate and hasattr(token, "to_dict"):
            try:
                d = token.to_dict()
                candidate = d.get("token") or d.get("access_token")
            except Exception:
                candidate = None
        if not candidate and isinstance(token, dict):
            candidate = token.get("token") or token.get("access_token")
        if not isinstance(candidate, str) or not candidate:
            return False
        if not hmac.compare_digest(candidate, self.expected_token):
            return False
        if required_capabilities:
            caps = set(getattr(token, "capabilities", []) or (token.get("capabilities") if isinstance(token, dict) else []) or [])
            if not set(required_capabilities).issubset(caps):
                return False
        exp = getattr(token, "ttl_seconds", None)
        if exp is None and isinstance(token, dict):
            exp = token.get("expires_at") or token.get("ttl_seconds")
        # If expires_at epoch provided, enforce it.
        if isinstance(exp, (int, float)) and exp > 10_000_000_000 / 1000 and exp < 10_000_000_000:  # epoch-like
            if time.time() > float(exp):
                return False
        return True

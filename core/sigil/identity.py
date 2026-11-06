import hashlib
import hmac
import os
import secrets
import time


class SigilIdentityManager:
    def __init__(self, agent_id: str = "AEG-UNKNOWN"):
        self.agent_id = agent_id

    def issue_token(self, capabilities=None, ttl_seconds=3600, key_type="hmac"):
        caps = capabilities or []
        # Never mint privileged tokens unless an API control token is configured.
        secret = os.environ.get("AEGENTIX_API_TOKEN") or os.environ.get("AEGENTIX_MCP_TOKEN")
        token_value = None
        if secret:
            nonce = secrets.token_hex(16)
            payload = f"{self.agent_id}|{int(time.time())}|{int(ttl_seconds)}|{','.join(caps)}|{nonce}"
            sig = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
            token_value = f"sigil.{nonce}.{sig}"
        return NHIToken(agent_id=self.agent_id, capabilities=caps, ttl_seconds=ttl_seconds, key_type=key_type, raw={"token": token_value} if token_value else {})


class NHIToken:
    def __init__(self, agent_id="AEG-UNKNOWN", capabilities=None, ttl_seconds=3600, key_type="hmac", raw=None):
        self.agent_id = agent_id
        self.capabilities = capabilities or []
        self.ttl_seconds = ttl_seconds
        self.envelope_type = key_type
        self.raw = raw or {}

    def to_dict(self):
        d = {"agent_id": self.agent_id, "capabilities": self.capabilities, "ttl_seconds": self.ttl_seconds, "envelope_type": self.envelope_type}
        # Do not expose raw token value in general listings; callers needing issuance get it from issue path.
        if self.raw and isinstance(self.raw, dict) and "token" in self.raw:
            d["token_issued"] = bool(self.raw.get("token"))
        return d

    @classmethod
    def from_dict(cls, d):
        return cls(agent_id=d.get("agent_id"), capabilities=d.get("capabilities"), ttl_seconds=d.get("ttl_seconds", 3600), key_type=d.get("envelope_type"), raw=d if isinstance(d, dict) else {})

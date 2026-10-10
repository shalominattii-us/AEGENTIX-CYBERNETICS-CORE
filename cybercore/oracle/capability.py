"""
Capability Token System for Signing Oracle Authorization.

Short-lived, agent-scoped tokens with path/chain restrictions.
"""

import time
import hmac
import hashlib
import secrets
import json
import base64
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum

from cybercore.entropy.jurisdiction import validate_jurisdiction


class CapabilityType(Enum):
    SIGN = "sign"
    PUBLIC_KEY = "public_key"
    ADDRESS = "address"
    ADMIN = "admin"


@dataclass
class CapabilityToken:
    """Capability token for agent authorization."""
    token: str              # Base64 encoded token
    agent_id: str
    allowed_paths: List[str]  # Glob patterns
    allowed_chains: List[str]
    capabilities: List[CapabilityType]
    expires_at: int         # Unix timestamp
    issued_at: int
    nonce: str
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at
    
    def allows_path(self, path: str) -> bool:
        """Check if token allows the given path (glob matching)."""
        import fnmatch
        for pattern in self.allowed_paths:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False
    
    def allows_chain(self, chain: str) -> bool:
        """Check if token allows the given chain."""
        return chain in self.allowed_chains or "*" in self.allowed_chains
    
    def has_capability(self, cap: CapabilityType) -> bool:
        return cap in self.capabilities


class CapabilityManager:
    """Manages capability token issuance and validation."""
    
    def __init__(self, signing_key: bytes = None, default_ttl: int = 3600):
        if signing_key is None:
            import os
            env_key = os.environ.get("CYBERCORE_CAPABILITY_KEY")
            if env_key:
                signing_key = bytes.fromhex(env_key) if len(env_key) == 64 else env_key.encode()
            else:
                signing_key = b"AEGENTIX_CYBERCORE_CAPABILITY_KEY_2026_SOVEREIGN"[:32]
        self.signing_key = signing_key
        self.default_ttl = default_ttl
        self._issued_tokens: Dict[str, CapabilityToken] = {}  # nonce -> token
        self._revoked: Set[str] = set()
    
    def issue_token(
        self,
        agent_id: str,
        allowed_paths: List[str],
        allowed_chains: List[str] = None,
        capabilities: List[CapabilityType] = None,
        ttl: int = None,
        metadata: Dict = None
    ) -> CapabilityToken:
        """Issue a new capability token."""
        now = int(time.time())
        ttl = ttl or self.default_ttl
        nonce = secrets.token_hex(16)
        
        token = CapabilityToken(
            token="",  # Will be set after signing
            agent_id=agent_id,
            allowed_paths=allowed_paths or ["*"],
            allowed_chains=allowed_chains or ["*"],
            capabilities=capabilities or [CapabilityType.SIGN, CapabilityType.PUBLIC_KEY, CapabilityType.ADDRESS],
            expires_at=now + ttl,
            issued_at=now,
            nonce=nonce,
            metadata=metadata or {},
        )
        
        # Sign the token
        token.token = self._sign_token(token)
        
        # Store for revocation checking
        self._issued_tokens[nonce] = token
        
        return token
    
    def _sign_token(self, token: CapabilityToken) -> str:
        """Sign token with HMAC."""
        # Create payload (exclude the token field itself)
        payload = {
            "agent_id": token.agent_id,
            "allowed_paths": token.allowed_paths,
            "allowed_chains": token.allowed_chains,
            "capabilities": [c.value for c in token.capabilities],
            "expires_at": token.expires_at,
            "issued_at": token.issued_at,
            "nonce": token.nonce,
            "metadata": token.metadata,
        }
        payload_bytes = json.dumps(payload, separators=(',', ':')).encode()
        
        sig = hmac.new(self.signing_key, payload_bytes, hashlib.sha256).digest()
        
        # Combine payload + signature
        combined = payload_bytes + b'.' + sig
        return base64.urlsafe_b64encode(combined).decode()
    
    def verify_token(self, token_str: str) -> Optional[CapabilityToken]:
        """Verify and parse a capability token."""
        try:
            combined = base64.urlsafe_b64decode(token_str.encode())
            payload_bytes, sig = combined.rsplit(b'.', 1)
            
            # Verify signature
            expected_sig = hmac.new(self.signing_key, payload_bytes, hashlib.sha256).digest()
            if not hmac.compare_digest(sig, expected_sig):
                return None
            
            payload = json.loads(payload_bytes.decode())
            
            token = CapabilityToken(
                token=token_str,
                agent_id=payload["agent_id"],
                allowed_paths=payload["allowed_paths"],
                allowed_chains=payload["allowed_chains"],
                capabilities=[CapabilityType(c) for c in payload["capabilities"]],
                expires_at=payload["expires_at"],
                issued_at=payload["issued_at"],
                nonce=payload["nonce"],
                metadata=payload.get("metadata", {}),
            )
            
            # Check revocation
            if token.nonce in self._revoked:
                return None
            
            return token
            
        except Exception:
            return None
    
    def revoke_token(self, nonce: str) -> bool:
        """Revoke a token by nonce."""
        if nonce in self._issued_tokens:
            self._revoked.add(nonce)
            del self._issued_tokens[nonce]
            return True
        return False
    
    def revoke_agent_tokens(self, agent_id: str) -> int:
        """Revoke all tokens for an agent."""
        revoked = 0
        for nonce, token in list(self._issued_tokens.items()):
            if token.agent_id == agent_id:
                self._revoked.add(nonce)
                del self._issued_tokens[nonce]
                revoked += 1
        return revoked
    
    def cleanup_expired(self) -> int:
        """Remove expired tokens from storage."""
        now = time.time()
        removed = 0
        for nonce, token in list(self._issued_tokens.items()):
            if token.is_expired():
                del self._issued_tokens[nonce]
                removed += 1
        return removed


# Global capability manager
_global_capability_manager: Optional[CapabilityManager] = None


def get_capability_manager() -> CapabilityManager:
    global _global_capability_manager
    if _global_capability_manager is None:
        _global_capability_manager = CapabilityManager()
    return _global_capability_manager


def initialize_capability_manager(signing_key: bytes = None, default_ttl: int = 3600) -> CapabilityManager:
    global _global_capability_manager
    _global_capability_manager = CapabilityManager(signing_key, default_ttl)
    return _global_capability_manager
import secrets
import time
from typing import Dict, Tuple, Any

class SovereignIdentitySubstrate:
    def __init__(self) -> None:
        self._active_challenges: Dict[str, Tuple[float, str]] = {}

    def issue_challenge(self, wallet: str, ttl: int = 60) -> str:
        nonce = secrets.token_hex(32)
        expiry = time.time() + ttl
        self._active_challenges[nonce] = (expiry, wallet)
        return nonce

    def verify_assertion(self, wallet: str, nonce: str, signature_hex: str, message_bytes: bytes) -> bool:
        if nonce not in self._active_challenges:
            return False
        expiry, bound_wallet = self._active_challenges.pop(nonce)
        if time.time() > expiry or bound_wallet != wallet:
            return False
        return bool(signature_hex)

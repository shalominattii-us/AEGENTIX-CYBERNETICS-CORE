"""
Argon2id Passphrase Entropy Provider for user-provided entropy fallback.
"""

import os
import logging
from typing import Optional

from .provider import EntropyProvider
from .jurisdiction import validate_jurisdiction, JurisdictionalError

logger = logging.getLogger(__name__)


class Argon2Provider(EntropyProvider):
    """Argon2id KDF from user passphrase for portable entropy."""
    
    def __init__(self, passphrase: str = None, salt: bytes = None,
                 time_cost: int = 3, memory_cost: int = 65536, parallelism: int = 4,
                 hash_len: int = 64,
                 country_code: str = "US", region: str = "", entity_name: str = ""):
        if not validate_jurisdiction(country_code, region, entity_name):
            raise JurisdictionalError(f"Argon2 provider excluded: {country_code}/{region}")
        
        super().__init__("Argon2id", country_code, region, entity_name)
        
        self.passphrase = passphrase
        self.salt = salt or os.urandom(32)
        self.time_cost = time_cost
        self.memory_cost = memory_cost
        self.parallelism = parallelism
        self.hash_len = hash_len
        self._derived_key = None
        
        if passphrase:
            self._derive()
    
    def set_passphrase(self, passphrase: str):
        """Set passphrase and derive key."""
        self.passphrase = passphrase
        self._derive()
    
    def _derive(self):
        """Derive key using Argon2id."""
        try:
            from argon2 import PasswordHasher
            import hashlib
            
            # Use argon2 library if available
            ph = PasswordHasher(
                time_cost=self.time_cost,
                memory_cost=self.memory_cost,
                parallelism=self.parallelism,
                hash_len=self.hash_len,
                salt_len=len(self.salt)
            )
            
            # We need to use raw argon2 for deterministic derivation
            # PasswordHasher is for password verification, not key derivation
            try:
                import argon2.low_level as argon2_ll
                self._derived_key = argon2_ll.hash_secret_raw(
                    secret=self.passphrase.encode(),
                    salt=self.salt,
                    time_cost=self.time_cost,
                    memory_cost=self.memory_cost,
                    parallelism=self.parallelism,
                    hash_len=self.hash_len,
                    type=argon2_ll.Type.ID
                )
            except ImportError:
                # Fallback: use PBKDF2 with high iterations
                import hashlib
                self._derived_key = hashlib.pbkdf2_hmac(
                    'sha256',
                    self.passphrase.encode(),
                    self.salt,
                    1000000,  # 1M iterations
                    dklen=self.hash_len
                )
            
            logger.info("Argon2id key derived successfully")
        except Exception as e:
            logger.error(f"Argon2 derivation failed: {e}")
            raise
    
    @property
    def provider_type(self) -> str:
        return "Argon2id"
    
    def health_check(self) -> bool:
        return self._derived_key is not None
    
    def get_entropy(self, length: int = 64) -> bytes:
        if self._derived_key is None:
            raise RuntimeError("No passphrase set - call set_passphrase() first")
        
        if length <= len(self._derived_key):
            return self._derived_key[:length]
        
        # Extend using HKDF if needed
        import hmac
        from hashlib import sha256
        
        okm = bytearray()
        counter = 1
        while len(okm) < length:
            info = f"argon2-extend-{counter}".encode()
            h = hmac.new(self._derived_key, info + b'\x00', sha256)
            okm.extend(h.digest())
            counter += 1
        
        return bytes(okm[:length])


def create_argon2_provider(passphrase: str = None,
                          country_code: str = "US", region: str = "", entity_name: str = "") -> Optional[EntropyProvider]:
    """Factory for Argon2 provider."""
    try:
        return Argon2Provider(
            passphrase=passphrase,
            country_code=country_code,
            region=region,
            entity_name=entity_name
        )
    except Exception as e:
        logger.warning(f"Argon2 provider creation failed: {e}")
        return None


# Convenience function for interactive use
def prompt_passphrase() -> str:
    """Securely prompt for passphrase."""
    import getpass
    return getpass.getpass("Enter CyberCore master passphrase: ")
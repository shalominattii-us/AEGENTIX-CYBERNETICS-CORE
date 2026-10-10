"""
Secure memory utilities for zero-storage key handling.
Keys are zeroized immediately after use.
"""

import ctypes
import os
import secrets
import logging
import hashlib
from typing import Optional, Tuple
from contextlib import contextmanager

try:
    import eth_keys
except ImportError:
    eth_keys = None

from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives import hashes, serialization

logger = logging.getLogger(__name__)


class SecureBytes:
    """
    Wrapper for bytes that ensures zeroization on deletion.
    Uses mutable bytearray internally for secure clearing.
    """
    
    def __init__(self, data: bytes = b''):
        self._data = bytearray(data)
        self._cleared = False
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __bytes__(self) -> bytes:
        if self._cleared:
            raise ValueError("SecureBytes already cleared")
        return bytes(self._data)
    
    def __getitem__(self, key):
        if self._cleared:
            raise ValueError("SecureBytes already cleared")
        return self._data[key]
    
    def clear(self):
        """Securely zero the memory."""
        if not self._cleared:
            # Overwrite with random then zero
            for i in range(len(self._data)):
                self._data[i] = secrets.randbits(8)
            for i in range(len(self._data)):
                self._data[i] = 0
            self._cleared = True
    
    def __del__(self):
        self.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()
        return False
    
    @property
    def is_cleared(self) -> bool:
        return self._cleared


@contextmanager
def secure_memory(length: int) -> SecureBytes:
    """Context manager for temporary secure memory allocation."""
    sb = SecureBytes(os.urandom(length))
    try:
        yield sb
    finally:
        sb.clear()


def zeroize(data: bytearray) -> None:
    """Zeroize a bytearray in place."""
    for i in range(len(data)):
        data[i] = 0


def constant_time_compare(a: bytes, b: bytes) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    return result == 0


class SecureKey:
    """
    Secure container for private keys with automatic zeroization.
    """
    
    def __init__(self, key: bytes, curve: str = "secp256k1"):
        self._key = SecureBytes(key)
        self.curve = curve
        self._public_key = None
        self._address = None
    
    @property
    def key(self) -> bytes:
        return bytes(self._key)
    
    @property
    def is_cleared(self) -> bool:
        return self._key.is_cleared
    
    @property
    def public_key(self) -> bytes:
        if self._public_key is None:
            self._public_key = self._derive_public()
        return self._public_key
    
    def _derive_public(self) -> bytes:
        if self.curve == "secp256k1":
            if eth_keys is not None:
                return eth_keys.keys.PrivateKey(self.key).public_key.to_compressed_bytes()
            priv_key = ec.derive_private_key(int.from_bytes(self.key, 'big'), ec.SECP256K1())
            return priv_key.public_key().public_bytes(
                serialization.Encoding.X962,
                serialization.PublicFormat.CompressedPoint
            )
        elif self.curve == "ed25519":
            k = ed25519.Ed25519PrivateKey.from_private_bytes(self.key)
            return k.public_key().public_bytes_raw()
        raise ValueError(f"Unknown curve: {self.curve}")
    
    def sign(self, message: bytes) -> bytes:
        """Sign message with private key."""
        if self.curve == "secp256k1":
            priv_key = ec.derive_private_key(int.from_bytes(self.key, 'big'), ec.SECP256K1())
            return priv_key.sign(message, ec.ECDSA(hashes.SHA256()))
        elif self.curve == "ed25519":
            k = ed25519.Ed25519PrivateKey.from_private_bytes(self.key)
            return k.sign(message)
        raise ValueError(f"Unknown curve: {self.curve}")
    
    def derive_address(self, chain: str) -> str:
        """Derive address for chain."""
        if self._address is None:
            self._address = {}
        
        if chain not in self._address:
            if self.curve == "secp256k1":
                from cybercore.derivation.bip32 import derive_address
                self._address[chain] = derive_address(self.key, chain)
            elif self.curve == "ed25519":
                from cybercore.derivation.slip0010 import derive_address_ed25519
                self._address[chain] = derive_address_ed25519(self.key, chain)
        
        return self._address[chain]
    
    def clear(self):
        """Clear the private key."""
        self._key.clear()
        self._public_key = None
        self._address = None
    
    def __del__(self):
        self.clear()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clear()
        return False


def derive_and_sign(
    seed: bytes,
    path: str,
    message: bytes,
    chain: str
) -> Tuple[bytes, str]:
    """
    Derive key from seed+path, sign message, return signature and address.
    Key is zeroized immediately after signing.
    """
    from cybercore.derivation import parse_path, CurveType, ChainRegistry
    
    registry = ChainRegistry()
    config = registry.get(chain)
    if not config:
        raise ValueError(f"Unknown chain: {chain}")
    
    parsed_path = parse_path(path, config.curve)
    
    if config.curve == CurveType.SECP256K1:
        from cybercore.derivation.bip32 import derive_path
        private_key, _ = derive_path(seed, str(parsed_path))
        with SecureKey(private_key, "secp256k1") as sk:
            signature = sk.sign(message)
            address = sk.derive_address(chain)
        return signature, address
    
    elif config.curve == CurveType.ED25519:
        from cybercore.derivation.slip0010 import derive_path_ed25519
        private_key, _ = derive_path_ed25519(seed, str(parsed_path))
        with SecureKey(private_key, "ed25519") as sk:
            signature = sk.sign(message)
            address = sk.derive_address(chain)
        return signature, address
    
    raise ValueError(f"Unsupported curve: {config.curve}")
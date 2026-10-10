"""
SLIP-0010 Ed25519 Derivation for XRPL, Solana, and other Ed25519 chains.
"""

import hashlib
import hmac
import struct
from typing import Tuple, Optional
from dataclasses import dataclass

from cryptography.hazmat.primitives.asymmetric import ed25519

# SLIP-0010 constants
SLIP10_HARDENED = 0x80000000
SLIP10_CURVE_ED25519 = b"ed25519 seed"
MASTER_KEY_HMAC_KEY = b"ed25519 seed"


def _get_ed25519_pub(priv_seed: bytes) -> bytes:
    """Get 32-byte Ed25519 public key from 32-byte seed."""
    k = ed25519.Ed25519PrivateKey.from_private_bytes(priv_seed)
    return k.public_key().public_bytes_raw()


def _sign_ed25519(priv_seed: bytes, message: bytes) -> bytes:
    """Sign message using Ed25519 private key seed."""
    k = ed25519.Ed25519PrivateKey.from_private_bytes(priv_seed)
    return k.sign(message)


@dataclass
class Ed25519ExtendedKey:
    """SLIP-0010 Extended Key for Ed25519."""
    private_key: bytes  # 32 bytes (seed)
    chain_code: bytes   # 32 bytes
    depth: int = 0
    parent_fingerprint: bytes = b'\x00\x00\x00\x00'
    child_number: int = 0
    
    def public_key(self) -> bytes:
        """Get 32-byte Ed25519 public key."""
        return _get_ed25519_pub(self.private_key)
    
    def fingerprint(self) -> bytes:
        """First 4 bytes of SHA256 of public key."""
        pk = self.public_key()
        return hashlib.sha256(pk).digest()[:4]
    
    def to_bytes(self) -> bytes:
        """Serialize (non-standard, for internal use)."""
        return (
            bytes([self.depth]) +
            self.parent_fingerprint +
            struct.pack(">I", self.child_number) +
            self.chain_code +
            self.private_key
        )


def hmac_sha512(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha512).digest()


def derive_master_key_ed25519(seed: bytes) -> Tuple[bytes, bytes]:
    """SLIP-0010 master key derivation for Ed25519."""
    h = hmac_sha512(MASTER_KEY_HMAC_KEY, seed)
    master_private = h[:32]
    master_chain_code = h[32:]
    return master_private, master_chain_code


def derive_child_key_ed25519(parent_key: bytes, parent_chain_code: bytes,
                             child_index: int) -> Tuple[bytes, bytes]:
    """SLIP-0010 child key derivation for Ed25519."""
    if child_index & SLIP10_HARDENED:
        # Hardened: use private key
        data = b'\x00' + parent_key + struct.pack(">I", child_index)
    else:
        # Normal: use public key
        pk = _get_ed25519_pub(parent_key)
        data = pk + struct.pack(">I", child_index)
    
    h = hmac_sha512(parent_chain_code, data)
    child_private = bytes((a + b) % 256 for a, b in zip(parent_key, h[:32]))
    child_chain_code = h[32:]
    
    return child_private, child_chain_code


def derive_path_ed25519(seed: bytes, path: str) -> Tuple[bytes, bytes]:
    """
    Derive Ed25519 key from SLIP-0010 path (e.g., "m/44'/144'/0'/0/0").
    Returns (private_key_seed, chain_code).
    """
    if not path.startswith("m/"):
        raise ValueError("Path must start with 'm/'")
    
    private_key, chain_code = derive_master_key_ed25519(seed)
    
    components = path[2:].split('/')
    for comp in components:
        if not comp:
            continue
        hardened = comp.endswith("'") or comp.endswith("h")
        index = int(comp.rstrip("'h"))
        if hardened:
            index |= SLIP10_HARDENED
        private_key, chain_code = derive_child_key_ed25519(private_key, chain_code, index)
    
    return private_key, chain_code


def derive_address_ed25519(private_key: bytes, chain: str = "xrp") -> str:
    """Derive address from Ed25519 private key for specific chain."""
    pk = _get_ed25519_pub(private_key)
    
    chain_lower = chain.lower()
    if chain_lower in ("xrp", "xrpl"):
        import base58
        h = hashlib.new('ripemd160', hashlib.sha256(pk).digest()).digest()
        return base58.b58encode_check(b'\x00' + h, alphabet=base58.RIPPLE_ALPHABET).decode()
    
    elif chain_lower in ("solana", "sol"):
        import base58
        return base58.b58encode(pk).decode()
    
    # Fallback default
    import base58
    return base58.b58encode(pk).decode()


class SLIP10Deriver:
    """SLIP-0010 Ed25519 key derivation engine."""
    
    def __init__(self, seed: bytes):
        self.seed = seed
        self._master_private, self._master_chain_code = derive_master_key_ed25519(seed)
    
    def derive(self, path: str) -> Tuple[bytes, bytes]:
        """Derive private key seed and chain code from path."""
        return derive_path_ed25519(self.seed, path)
    
    def derive_private_key(self, path: str) -> bytes:
        """Derive private key seed only."""
        pk, _ = self.derive(path)
        return pk
    
    def derive_public_key(self, path: str) -> bytes:
        """Derive public key from path."""
        pk, _ = self.derive(path)
        return _get_ed25519_pub(pk)
    
    def derive_address(self, path: str, chain: str = "xrp") -> str:
        """Derive address from path."""
        pk, _ = self.derive(path)
        return derive_address_ed25519(pk, chain)
    
    def derive_extended_key(self, path: str) -> Ed25519ExtendedKey:
        """Derive extended key from path."""
        if not path.startswith("m/"):
            raise ValueError("Path must start with 'm/'")
        
        priv, chain_code = self.derive(path)
        return Ed25519ExtendedKey(
            private_key=priv,
            chain_code=chain_code,
            depth=len(path[2:].split('/'))
        )


SLIP44_COIN_TYPES = {
    "xrp": 144,
    "xrpl": 144,
    "solana": 501,
    "sui": 784,
    "aptos": 637,
}


def slip10_path(coin_type: int = 144, account: int = 0, change: int = 0, index: int = 0) -> str:
    """Generate SLIP-0010 derivation path string."""
    return f"m/44'/{coin_type}'/{account}'/{change}/{index}"
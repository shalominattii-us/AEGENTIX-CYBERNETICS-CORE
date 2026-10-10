"""
BIP32/BIP44 Derivation for secp256k1 curves (EVM, Bitcoin, Cosmos, etc.).
"""

import hashlib
import hmac
import struct
from typing import Tuple, Optional
from dataclasses import dataclass

try:
    import eth_keys
except ImportError:
    eth_keys = None

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# BIP32 constants
BIP32_HARDENED = 0x80000000
MASTER_KEY_HMAC_KEY = b"Bitcoin seed"
SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def priv_to_compressed_pub(priv_bytes: bytes) -> bytes:
    """Derive 33-byte compressed public key from 32-byte private key."""
    if eth_keys is not None:
        return eth_keys.keys.PrivateKey(priv_bytes).public_key.to_compressed_bytes()
    priv_key = ec.derive_private_key(int.from_bytes(priv_bytes, 'big'), ec.SECP256K1())
    return priv_key.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.CompressedPoint
    )


def priv_to_uncompressed_pub(priv_bytes: bytes) -> bytes:
    """Derive 65-byte uncompressed public key from 32-byte private key."""
    if eth_keys is not None:
        return b'\x04' + eth_keys.keys.PrivateKey(priv_bytes).public_key.to_bytes()
    priv_key = ec.derive_private_key(int.from_bytes(priv_bytes, 'big'), ec.SECP256K1())
    return priv_key.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint
    )


@dataclass
class ExtendedKey:
    """BIP32 Extended Key (xprv/xpub)."""
    version: bytes  # 4 bytes: 0x0488ADE4 (xprv) or 0x0488B21E (xpub)
    depth: int      # 1 byte
    parent_fingerprint: bytes  # 4 bytes
    child_number: int  # 4 bytes (big endian)
    chain_code: bytes  # 32 bytes
    key_data: bytes   # 33 bytes (0x00 + privkey for xprv, or compressed pubkey for xpub)
    
    def is_private(self) -> bool:
        return self.key_data[0] == 0x00
    
    def private_key(self) -> bytes:
        if not self.is_private():
            raise ValueError("Not a private extended key")
        return self.key_data[1:]
    
    def public_key(self) -> bytes:
        if self.is_private():
            return priv_to_compressed_pub(self.private_key())
        return self.key_data
    
    def fingerprint(self) -> bytes:
        """First 4 bytes of HASH160 of compressed public key."""
        pub = self.public_key()
        h160 = hashlib.new('ripemd160', hashlib.sha256(pub).digest()).digest()
        return h160[:4]
    
    def serialize(self) -> bytes:
        """Serialize to 78-byte extended key format."""
        return (
            self.version +
            bytes([self.depth]) +
            self.parent_fingerprint +
            struct.pack(">I", self.child_number) +
            self.chain_code +
            self.key_data
        )
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'ExtendedKey':
        if len(data) != 78:
            raise ValueError("Extended key must be 78 bytes")
        return cls(
            version=data[0:4],
            depth=data[4],
            parent_fingerprint=data[5:9],
            child_number=struct.unpack(">I", data[9:13])[0],
            chain_code=data[13:45],
            key_data=data[45:78]
        )
    
    def to_base58(self) -> str:
        """Encode as Base58Check (xprv/xpub format)."""
        import base58
        return base58.b58encode_check(self.serialize()).decode()


def hmac_sha512(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha512).digest()


def derive_master_key(seed: bytes) -> Tuple[bytes, bytes]:
    """BIP32 master key derivation from seed."""
    h = hmac_sha512(MASTER_KEY_HMAC_KEY, seed)
    master_private = h[:32]
    master_chain_code = h[32:]
    return master_private, master_chain_code


def derive_child_key(parent_key: bytes, parent_chain_code: bytes, 
                     child_index: int) -> Tuple[bytes, bytes]:
    """BIP32 child key derivation (CKDpriv)."""
    if child_index & BIP32_HARDENED:
        # Hardened derivation: use private key
        data = b'\x00' + parent_key + struct.pack(">I", child_index)
    else:
        # Normal derivation: use public key
        pub = priv_to_compressed_pub(parent_key)
        data = pub + struct.pack(">I", child_index)
    
    h = hmac_sha512(parent_chain_code, data)
    child_private = (int.from_bytes(parent_key, 'big') + int.from_bytes(h[:32], 'big')) % SECP256K1_ORDER
    child_chain_code = h[32:]
    
    return child_private.to_bytes(32, 'big'), child_chain_code


def derive_path(seed: bytes, path: str) -> Tuple[bytes, bytes]:
    """
    Derive key from BIP32 path (e.g., "m/44'/60'/0'/0/0").
    Returns (private_key, chain_code).
    """
    if not path.startswith("m/"):
        raise ValueError("Path must start with 'm/'")
    
    # Master key
    private_key, chain_code = derive_master_key(seed)
    
    # Parse path components
    components = path[2:].split('/')
    for comp in components:
        if not comp:
            continue
        hardened = comp.endswith("'") or comp.endswith("h")
        index = int(comp.rstrip("'h"))
        if hardened:
            index |= BIP32_HARDENED
        private_key, chain_code = derive_child_key(private_key, chain_code, index)
    
    return private_key, chain_code


def derive_address(private_key: bytes, chain: str = "ethereum") -> str:
    """Derive address from private key for specific chain."""
    pub_uncompressed = priv_to_uncompressed_pub(private_key)
    
    chain_lower = chain.lower()
    if chain_lower in ("ethereum", "evm", "base", "arbitrum", "optimism", "polygon", "bsc"):
        if eth_keys is not None:
            return eth_keys.keys.PrivateKey(private_key).public_key.to_checksum_address()
        from eth_hash.auto import keccak
        addr = keccak(pub_uncompressed[1:])[-20:]
        return "0x" + addr.hex()
    elif chain_lower in ("bitcoin", "btc"):
        import base58
        pub_compressed = priv_to_compressed_pub(private_key)
        h160 = hashlib.new('ripemd160', hashlib.sha256(pub_compressed).digest()).digest()
        return base58.b58encode_check(b'\x00' + h160).decode()
    elif chain_lower in ("cosmos", "atom"):
        import bech32
        pub_compressed = priv_to_compressed_pub(private_key)
        h160 = hashlib.new('ripemd160', hashlib.sha256(pub_compressed).digest()).digest()
        data = bech32.convertbits(h160, 8, 5)
        return bech32.bech32_encode("cosmos", data)
    
    # Default EVM fallback
    if eth_keys is not None:
        return eth_keys.keys.PrivateKey(private_key).public_key.to_checksum_address()
    from eth_hash.auto import keccak
    return "0x" + keccak(pub_uncompressed[1:])[-20:].hex()


class BIP32Deriver:
    """BIP32/BIP44 key derivation engine."""
    
    def __init__(self, seed: bytes):
        self.seed = seed
        self._master_private, self._master_chain_code = derive_master_key(seed)
    
    def derive(self, path: str) -> Tuple[bytes, bytes]:
        """Derive private key and chain code from path."""
        return derive_path(self.seed, path)
    
    def derive_private_key(self, path: str) -> bytes:
        """Derive private key only."""
        pk, _ = self.derive(path)
        return pk
    
    def derive_public_key(self, path: str) -> bytes:
        """Derive compressed public key from path."""
        pk, _ = self.derive(path)
        return priv_to_compressed_pub(pk)
    
    def derive_address(self, path: str, chain: str = "ethereum") -> str:
        """Derive address from path."""
        pk, _ = self.derive(path)
        return derive_address(pk, chain)
    
    def derive_extended_key(self, path: str, public: bool = False) -> ExtendedKey:
        """Derive extended key (xprv/xpub) from path."""
        if not path.startswith("m/"):
            raise ValueError("Path must start with 'm/'")
        
        priv, chain_code = self.derive(path)
        version = b'\x04\x88\xad\xe4' if not public else b'\x04\x88\xb2\x1e'
        key_data = b'\x00' + priv if not public else priv_to_compressed_pub(priv)
        
        return ExtendedKey(
            version=version,
            depth=len(path[2:].split('/')),
            parent_fingerprint=b'\x00\x00\x00\x00',
            child_number=0,
            chain_code=chain_code,
            key_data=key_data
        )


COIN_TYPES = {
    "ethereum": 60,
    "bitcoin": 0,
    "cosmos": 118,
    "dogecoin": 3,
    "polygon": 966,
    "arbitrum": 42161,
    "optimism": 614,
    "base": 8453,
}


def bip44_path(coin_type: int = 60, account: int = 0, change: int = 0, index: int = 0) -> str:
    """Generate BIP44 derivation path string."""
    return f"m/44'/{coin_type}'/{account}'/{change}/{index}"


def bip84_path(coin_type: int = 0, account: int = 0, change: int = 0, index: int = 0) -> str:
    """Generate BIP84 derivation path string."""
    return f"m/84'/{coin_type}'/{account}'/{change}/{index}"
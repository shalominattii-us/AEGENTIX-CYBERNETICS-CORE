"""
BIP32/SLIP-0010 Path parsing and validation.
"""

import re
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class CurveType(Enum):
    SECP256K1 = "secp256k1"
    ED25519 = "ed25519"


@dataclass
class DerivationPath:
    """Parsed derivation path with components."""
    components: List[int]
    curve: CurveType
    is_absolute: bool = True  # starts with m/
    
    @property
    def depth(self) -> int:
        return len(self.components)
    
    def __str__(self) -> str:
        parts = []
        for c in self.components:
            if c & 0x80000000:
                parts.append(f"{(c & 0x7FFFFFFF)}'")
            else:
                parts.append(str(c))
        prefix = "m/" if self.is_absolute else ""
        return prefix + "/".join(parts)
    
    def to_list(self) -> List[int]:
        return self.components.copy()


# Regex for path components
PATH_REGEX = re.compile(r"^m(?:/(\d+)('|h)?)*$")
COMPONENT_REGEX = re.compile(r"^(\d+)('|h)?$")


def parse_path(path: str, curve: CurveType = CurveType.SECP256K1) -> DerivationPath:
    """
    Parse BIP32/SLIP-0010 derivation path.
    Examples:
        "m/44'/60'/0'/0/0" -> [44|H, 60|H, 0|H, 0, 0]
        "m/44'/144'/0'/0/0" -> [44|H, 144|H, 0|H, 0, 0] (Ed25519)
    """
    if not path.startswith("m/"):
        raise ValueError(f"Path must start with 'm/': {path}")
    
    components = []
    parts = path[2:].split('/')
    
    for part in parts:
        if not part:
            continue
        match = COMPONENT_REGEX.match(part)
        if not match:
            raise ValueError(f"Invalid path component: {part}")
        
        index = int(match.group(1))
        hardened = match.group(2) in ("'", "h")
        
        if index < 0 or index > 0x7FFFFFFF:
            raise ValueError(f"Index out of range (0-0x7FFFFFFF): {index}")
        
        if hardened:
            index |= 0x80000000
        
        components.append(index)
    
    return DerivationPath(components=components, curve=curve)


def path_to_indices(path: DerivationPath) -> List[int]:
    """Extract raw indices from path."""
    return path.components.copy()


def validate_path_structure(path: DerivationPath, expected_depth: int = None,
                           expected_purpose: int = None,
                           expected_coin_type: int = None) -> bool:
    """Validate path follows expected structure."""
    if expected_depth is not None and path.depth != expected_depth:
        return False
    
    if expected_purpose is not None:
        if path.depth < 1:
            return False
        if (path.components[0] & 0x7FFFFFFF) != expected_purpose:
            return False
    
    if expected_coin_type is not None:
        if path.depth < 2:
            return False
        if (path.components[1] & 0x7FFFFFFF) != expected_coin_type:
            return False
    
    return True


def bip44_path_parts(path: DerivationPath) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[int], Optional[int]]:
    """
    Extract BIP44 path parts: (purpose, coin_type, account, change, index)
    Returns None for missing parts.
    """
    parts = [None, None, None, None, None]
    for i, comp in enumerate(path.components):
        if i < 5:
            parts[i] = comp & 0x7FFFFFFF
    return tuple(parts)


def slip10_path_parts(path: DerivationPath) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[int], Optional[int]]:
    """Extract SLIP-0010 path parts (same structure as BIP44)."""
    return bip44_path_parts(path)


def join_path(*parts: int) -> str:
    """Join path components into string."""
    str_parts = []
    for p in parts:
        if p & 0x80000000:
            str_parts.append(f"{(p & 0x7FFFFFFF)}'")
        else:
            str_parts.append(str(p))
    return "m/" + "/".join(str_parts)


def hardened(index: int) -> int:
    """Mark index as hardened."""
    return index | 0x80000000


def normal(index: int) -> int:
    """Mark index as normal (non-hardened)."""
    return index & 0x7FFFFFFF


# Common path templates
class PathTemplates:
    """Standard derivation path templates."""
    
    # BIP44: m/44'/coin_type'/account'/change/index
    @staticmethod
    def bip44(coin_type: int, account: int = 0, change: int = 0, index: int = 0) -> str:
        return join_path(
            hardened(44),
            hardened(coin_type),
            hardened(account),
            normal(change),
            normal(index)
        )
    
    # BIP84 (Native SegWit): m/84'/coin_type'/account'/change/index
    @staticmethod
    def bip84(coin_type: int, account: int = 0, change: int = 0, index: int = 0) -> str:
        return join_path(
            hardened(84),
            hardened(coin_type),
            hardened(account),
            normal(change),
            normal(index)
        )
    
    # SLIP-0010 (Ed25519): m/44'/coin_type'/account'/change/index
    @staticmethod
    def slip10(coin_type: int, account: int = 0, change: int = 0, index: int = 0) -> str:
        return join_path(
            hardened(44),
            hardened(coin_type),
            hardened(account),
            normal(change),
            normal(index)
        )
    
    # CyberCore agent wallet: m/44'/coin_type'/0'/shard/agent/nonce
    @staticmethod
    def agent_wallet(coin_type: int, shard: int, agent_id: int, nonce: int = 0) -> str:
        return join_path(
            hardened(44),
            hardened(coin_type),
            hardened(0),
            normal(shard),
            normal(agent_id),
            normal(nonce)
        )
    
    # CyberCore shard wallet: m/44'/coin_type'/0'/shard
    @staticmethod
    def shard_wallet(coin_type: int, shard: int) -> str:
        return join_path(
            hardened(44),
            hardened(coin_type),
            hardened(0),
            normal(shard)
        )


# Validation helpers
def is_hardened(index: int) -> bool:
    return (index & 0x80000000) != 0


def unharden(index: int) -> int:
    return index & 0x7FFFFFFF


def path_from_string(path_str: str, curve: CurveType = CurveType.SECP256K1) -> DerivationPath:
    """Alias for parse_path."""
    return parse_path(path_str, curve)
"""
CyberCore Derivation Module - SLIP-0010, BIP32, Path parsing, Chain Registry.

Exports:
- BIP32Deriver, SLIP10Deriver
- derive_path, derive_path_ed25519
- parse_path, DerivationPath, PathTemplates
- ChainConfig, ChainFamily, ChainRegistry, get_chain_registry
"""

from .bip32 import (
    BIP32Deriver,
    ExtendedKey,
    derive_master_key,
    derive_child_key,
    derive_path,
    derive_address,
    bip44_path,
    bip84_path,
    COIN_TYPES,
)

from .slip0010 import (
    SLIP10Deriver,
    Ed25519ExtendedKey,
    derive_master_key_ed25519,
    derive_child_key_ed25519,
    derive_path_ed25519,
    derive_address_ed25519,
    slip10_path,
    SLIP44_COIN_TYPES,
)

from .path import (
    DerivationPath,
    CurveType,
    parse_path,
    path_to_indices,
    validate_path_structure,
    bip44_path_parts,
    slip10_path_parts,
    join_path,
    hardened,
    normal,
    is_hardened,
    unharden,
    PathTemplates,
)

from .chain_registry import (
    ChainConfig,
    ChainFamily,
    ChainRegistry,
    get_chain_registry,
    register_custom_chain,
    CHAIN_REGISTRY,
    TREASURY_CHAINS,
)

__all__ = [
    # BIP32
    "BIP32Deriver",
    "ExtendedKey",
    "derive_master_key",
    "derive_child_key",
    "derive_path",
    "derive_address",
    "bip44_path",
    "bip84_path",
    "COIN_TYPES",
    # SLIP-0010
    "SLIP10Deriver",
    "Ed25519ExtendedKey",
    "derive_master_key_ed25519",
    "derive_child_key_ed25519",
    "derive_path_ed25519",
    "derive_address_ed25519",
    "slip10_path",
    "SLIP44_COIN_TYPES",
    # Path
    "DerivationPath",
    "CurveType",
    "parse_path",
    "path_to_indices",
    "validate_path_structure",
    "bip44_path_parts",
    "slip10_path_parts",
    "join_path",
    "hardened",
    "normal",
    "is_hardened",
    "unharden",
    "PathTemplates",
    # Chain Registry
    "ChainConfig",
    "ChainFamily",
    "ChainRegistry",
    "get_chain_registry",
    "register_custom_chain",
    "CHAIN_REGISTRY",
    "TREASURY_CHAINS",
]
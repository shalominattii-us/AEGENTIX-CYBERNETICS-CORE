"""
CyberCore Stateless Vault Interface.

Zero-storage key management:
- Keys derived on-demand from master entropy
- Private keys never persisted
- Automatic zeroization after use
- Supports all chain types via derivation engine
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from contextlib import contextmanager

from .secure_memory import SecureKey, derive_and_sign, secure_memory
from cybercore.entropy import EntropyRegistry, get_global_registry
from cybercore.derivation import (
    ChainRegistry, ChainConfig, CurveType, 
    parse_path, PathTemplates,
    get_chain_registry,
)

logger = logging.getLogger(__name__)


@dataclass
class VaultConfig:
    """Configuration for vault instance."""
    entropy_sources: List[str] = None  # Provider names to use
    min_entropy_providers: int = 2
    default_chain: str = "ethereum"
    cache_public_keys: bool = True
    audit_enabled: bool = True


@dataclass
class KeyInfo:
    """Information about a derived key (public only)."""
    path: str
    chain: str
    public_key: bytes
    address: str
    curve: str
    depth: int
    purpose: str = ""


class StatelessVault:
    """
    Stateless vault - keys derived on-demand, never stored.
    
    Architecture:
    Master Entropy -> Entropy Registry (quorum) -> Derivation Engine -> SecureKey -> Sign -> Zeroize
    """
    
    def __init__(self, config: VaultConfig = None):
        self.config = config or VaultConfig()
        self.entropy_registry = get_global_registry()
        self.chain_registry = get_chain_registry()
        self._public_key_cache: Dict[str, KeyInfo] = {}
        self._master_seed: Optional[bytes] = None
        self._initialized = False
    
    def initialize(self, master_seed: bytes = None) -> None:
        """Initialize vault with master seed (or generate from entropy)."""
        if master_seed:
            self._master_seed = master_seed
        else:
            # Generate from entropy quorum
            self._master_seed = self.entropy_registry.get_entropy_quorum(64)
        
        self._initialized = True
        logger.info("StatelessVault initialized")
    
    def initialize_from_entropy_provider(self, provider_name: str) -> None:
        """Initialize using a specific entropy provider."""
        self._master_seed = self.entropy_registry.get_single_entropy(provider_name, 64)
        self._initialized = True
        logger.info(f"StatelessVault initialized from {provider_name}")
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized and self._master_seed is not None
    
    def _ensure_initialized(self):
        if not self.is_initialized:
            raise RuntimeError("Vault not initialized. Call initialize() first.")
    
    def _get_chain_config(self, chain: str) -> ChainConfig:
        config = self.chain_registry.get(chain)
        if not config:
            raise ValueError(f"Unknown chain: {chain}")
        return config
    
    def _resolve_path(self, path: str, chain: str) -> str:
        """Resolve path template if needed."""
        if path.startswith("template:"):
            template_name = path[9:]
            config = self._get_chain_config(chain)
            
            if template_name == "shard_wallet":
                # Extract shard from path like "template:shard_wallet:001"
                parts = path.split(":")
                if len(parts) >= 3:
                    shard = int(parts[2])
                    return self.chain_registry.get_shard_wallet_path(chain, shard)
            
            elif template_name == "agent_wallet":
                # template:agent_wallet:shard:agent_id:nonce
                parts = path.split(":")
                if len(parts) >= 5:
                    shard = int(parts[2])
                    agent_id = int(parts[3])
                    nonce = int(parts[4]) if len(parts) > 5 else 0
                    return self.chain_registry.get_agent_wallet_path(chain, shard, agent_id, nonce)
        
        return path
    
    def derive_public_key(self, path: str, chain: str = None) -> bytes:
        """Derive public key only (no private key material)."""
        self._ensure_initialized()
        chain = chain or self.config.default_chain
        path = self._resolve_path(path, chain)
        
        cache_key = f"{chain}:{path}"
        if self.config.cache_public_keys and cache_key in self._public_key_cache:
            return self._public_key_cache[cache_key].public_key
        
        config = self._get_chain_config(chain)
        parsed_path = parse_path(path, config.curve)
        
        if config.curve == CurveType.SECP256K1:
            from cybercore.derivation.bip32 import derive_path
            _, _ = derive_path(self._master_seed, str(parsed_path))
            # For public key only, we'd need the full derivation
            # This is a simplified version
            from cybercore.derivation.bip32 import BIP32Deriver
            deriver = BIP32Deriver(self._master_seed)
            pubkey = deriver.derive_public_key(str(parsed_path))
        else:
            from cybercore.derivation.slip0010 import derive_path_ed25519, SLIP10Deriver
            deriver = SLIP10Deriver(self._master_seed)
            pubkey = deriver.derive_public_key(str(parsed_path))
        
        address = self.derive_address(path, chain)
        
        info = KeyInfo(
            path=path,
            chain=chain,
            public_key=pubkey,
            address=address,
            curve=config.curve.value,
            depth=parsed_path.depth,
        )
        
        if self.config.cache_public_keys:
            self._public_key_cache[cache_key] = info
        
        return pubkey
    
    def derive_address(self, path: str, chain: str = None) -> str:
        """Derive address from path."""
        self._ensure_initialized()
        chain = chain or self.config.default_chain
        path = self._resolve_path(path, chain)
        
        config = self._get_chain_config(chain)
        parsed_path = parse_path(path, config.curve)
        
        if config.curve == CurveType.SECP256K1:
            from cybercore.derivation.bip32 import derive_path, derive_address
            private_key, _ = derive_path(self._master_seed, str(parsed_path))
            return derive_address(private_key, chain)
        else:
            from cybercore.derivation.slip0010 import derive_path_ed25519, derive_address_ed25519
            private_key, _ = derive_path_ed25519(self._master_seed, str(parsed_path))
            return derive_address_ed25519(private_key, chain)
    
    def sign(self, path: str, message: bytes, chain: str = None) -> bytes:
        """
        Sign message with key at path.
        Private key is derived, used, and zeroized in one operation.
        """
        self._ensure_initialized()
        chain = chain or self.config.default_chain
        path = self._resolve_path(path, chain)
        
        config = self._get_chain_config(chain)
        parsed_path = parse_path(path, config.curve)
        
        # Derive and sign in secure context
        if config.curve == CurveType.SECP256K1:
            from cybercore.derivation.bip32 import derive_path
            private_key, _ = derive_path(self._master_seed, str(parsed_path))
            with SecureKey(private_key, "secp256k1") as sk:
                return sk.sign(message)
        else:
            from cybercore.derivation.slip0010 import derive_path_ed25519
            private_key, _ = derive_path_ed25519(self._master_seed, str(parsed_path))
            with SecureKey(private_key, "ed25519") as sk:
                return sk.sign(message)
    
    def sign_and_get_address(self, path: str, message: bytes, chain: str = None) -> Tuple[bytes, str]:
        """Sign message and return signature + address."""
        self._ensure_initialized()
        chain = chain or self.config.default_chain
        path = self._resolve_path(path, chain)
        
        return derive_and_sign(self._master_seed, path, message, chain)
    
    def get_key_info(self, path: str, chain: str = None) -> KeyInfo:
        """Get public key info for path."""
        self._ensure_initialized()
        chain = chain or self.config.default_chain
        path = self._resolve_path(path, chain)
        
        pubkey = self.derive_public_key(path, chain)
        address = self.derive_address(path, chain)
        config = self._get_chain_config(chain)
        parsed_path = parse_path(path, config.curve)
        
        return KeyInfo(
            path=path,
            chain=chain,
            public_key=pubkey,
            address=address,
            curve=config.curve.value,
            depth=parsed_path.depth,
        )
    
    def list_derived_keys(self) -> List[KeyInfo]:
        """List all cached public keys."""
        return list(self._public_key_cache.values())
    
    def clear_cache(self):
        """Clear public key cache."""
        self._public_key_cache.clear()
    
    @contextmanager
    def ephemeral_key(self, path: str, chain: str = None):
        """
        Context manager for ephemeral key usage.
        Yields SecureKey that auto-zeroizes on exit.
        """
        self._ensure_initialized()
        chain = chain or self.config.default_chain
        path = self._resolve_path(path, chain)
        
        config = self._get_chain_config(chain)
        parsed_path = parse_path(path, config.curve)
        
        if config.curve == CurveType.SECP256K1:
            from cybercore.derivation.bip32 import derive_path
            private_key, _ = derive_path(self._master_seed, str(parsed_path))
            key = SecureKey(private_key, "secp256k1")
        else:
            from cybercore.derivation.slip0010 import derive_path_ed25519
            private_key, _ = derive_path_ed25519(self._master_seed, str(parsed_path))
            key = SecureKey(private_key, "ed25519")
        
        try:
            yield key
        finally:
            key.clear()
    
    def derive_shard_wallet(self, chain: str, shard: int) -> KeyInfo:
        """Derive shard wallet for chain."""
        path = self.chain_registry.get_shard_wallet_path(chain, shard)
        return self.get_key_info(path, chain)
    
    def derive_agent_wallet(self, chain: str, shard: int, agent_id: int, nonce: int = 0) -> KeyInfo:
        """Derive agent wallet for chain."""
        path = self.chain_registry.get_agent_wallet_path(chain, shard, agent_id, nonce)
        return self.get_key_info(path, chain)
    
    def sign_as_agent(self, chain: str, shard: int, agent_id: int, 
                      message: bytes, nonce: int = 0) -> Tuple[bytes, str]:
        """Sign message as specific agent."""
        path = self.chain_registry.get_agent_wallet_path(chain, shard, agent_id, nonce)
        return self.sign_and_get_address(path, message, chain)
    
    def get_treasury_wallet(self, treasury_name: str) -> Optional[KeyInfo]:
        """Get treasury wallet info."""
        treasury = TREASURY_CHAINS.get(treasury_name)
        if not treasury:
            return None
        
        chain = treasury["chain"]
        # For treasury wallets, we use standard BIP44 derivation path
        coin_cfg = self.chain_registry.get(chain)
        coin_type = coin_cfg.coin_type if coin_cfg else 60
        path = f"m/44'/{coin_type}'/0'/0/0"
        return self.get_key_info(path, chain)
    
    def close(self):
        """Clean up vault resources."""
        self._master_seed = None
        self._public_key_cache.clear()
        self._initialized = False
        logger.info("StatelessVault closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


# Convenience functions for common operations
def create_vault(config: VaultConfig = None) -> StatelessVault:
    """Create and initialize a vault with entropy quorum."""
    vault = StatelessVault(config)
    vault.initialize()
    return vault


def create_vault_from_seed(seed: bytes, config: VaultConfig = None) -> StatelessVault:
    """Create and initialize a vault with specific seed."""
    vault = StatelessVault(config)
    vault.initialize(seed)
    return vault


# Export TREASURY_CHAINS from derivation module
from cybercore.derivation.chain_registry import TREASURY_CHAINS
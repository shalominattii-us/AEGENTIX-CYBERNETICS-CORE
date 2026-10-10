"""
Wallet Registry - Public address registry for all derived wallets.
Replaces the old cybercore_auto_keypairs.json (which had private keys).
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict, field

from cybercore.vault import StatelessVault, create_vault
from cybercore.derivation import get_chain_registry, ChainRegistry

logger = logging.getLogger(__name__)


@dataclass
class WalletEntry:
    """Single wallet entry in registry."""
    wallet_id: str
    chain: str
    shard: int
    wallet_type: str  # "shard", "agent", "treasury", "reward"
    path: str
    address: str
    public_key: str
    curve: str
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)


class WalletRegistry:
    """
    Public wallet registry - only stores public information.
    No private keys, no seeds, no sensitive material.
    """
    
    def __init__(self, vault: StatelessVault = None):
        self.vault = vault or create_vault()
        self.registry = get_chain_registry()
        self._wallets: Dict[str, WalletEntry] = {}
        self._by_chain: Dict[str, List[str]] = {}
        self._by_shard: Dict[int, List[str]] = {}
    
    def register_shard_wallet(self, chain: str, shard: int, 
                             metadata: Dict = None) -> WalletEntry:
        """Register a shard wallet."""
        path = self.registry.get_shard_wallet_path(chain, shard)
        info = self.vault.get_key_info(path, chain)
        
        wallet_id = f"{chain}-shard-{shard:03d}"
        entry = WalletEntry(
            wallet_id=wallet_id,
            chain=chain,
            shard=shard,
            wallet_type="shard",
            path=path,
            address=info.address,
            public_key=info.public_key.hex(),
            curve=info.curve,
            metadata=metadata or {},
        )
        
        self._wallets[wallet_id] = entry
        self._index_entry(entry)
        
        return entry
    
    def register_agent_wallet(self, chain: str, shard: int, agent_id: int,
                             metadata: Dict = None) -> WalletEntry:
        """Register an agent wallet."""
        path = self.registry.get_agent_wallet_path(chain, shard, agent_id)
        info = self.vault.get_key_info(path, chain)
        
        wallet_id = f"{chain}-shard-{shard:03d}-agent-{agent_id:04d}"
        entry = WalletEntry(
            wallet_id=wallet_id,
            chain=chain,
            shard=shard,
            wallet_type="agent",
            path=path,
            address=info.address,
            public_key=info.public_key.hex(),
            curve=info.curve,
            metadata=metadata or {"agent_id": agent_id},
        )
        
        self._wallets[wallet_id] = entry
        self._index_entry(entry)
        
        return entry
    
    def register_treasury_wallet(self, chain: str, name: str,
                                metadata: Dict = None) -> WalletEntry:
        """Register a treasury wallet."""
        path = f"m/44'/{self.registry.get(chain).coin_type | 0x80000000}'/0'/0/0"
        info = self.vault.get_key_info(path, chain)
        
        wallet_id = f"{chain}-treasury-{name}"
        entry = WalletEntry(
            wallet_id=wallet_id,
            chain=chain,
            shard=0,
            wallet_type="treasury",
            path=path,
            address=info.address,
            public_key=info.public_key.hex(),
            curve=info.curve,
            metadata=metadata or {"treasury_name": name},
        )
        
        self._wallets[wallet_id] = entry
        self._index_entry(entry)
        
        return entry
    
    def register_reward_wallet(self, chain: str, purpose: str,
                              metadata: Dict = None) -> WalletEntry:
        """Register a reward distribution wallet."""
        path = f"m/44'/{self.registry.get(chain).coin_type | 0x80000000}'/1'/0/0"
        info = self.vault.get_key_info(path, chain)
        
        wallet_id = f"{chain}-reward-{purpose}"
        entry = WalletEntry(
            wallet_id=wallet_id,
            chain=chain,
            shard=0,
            wallet_type="reward",
            path=path,
            address=info.address,
            public_key=info.public_key.hex(),
            curve=info.curve,
            metadata=metadata or {"purpose": purpose},
        )
        
        self._wallets[wallet_id] = entry
        self._index_entry(entry)
        
        return entry
    
    def _index_entry(self, entry: WalletEntry):
        """Update indexes."""
        if entry.chain not in self._by_chain:
            self._by_chain[entry.chain] = []
        self._by_chain[entry.chain].append(entry.wallet_id)
        
        if entry.shard > 0:
            if entry.shard not in self._by_shard:
                self._by_shard[entry.shard] = []
            self._by_shard[entry.shard].append(entry.wallet_id)
    
    def get(self, wallet_id: str) -> Optional[WalletEntry]:
        return self._wallets.get(wallet_id)
    
    def get_by_chain(self, chain: str) -> List[WalletEntry]:
        ids = self._by_chain.get(chain, [])
        return [self._wallets[i] for i in ids]
    
    def get_by_shard(self, shard: int) -> List[WalletEntry]:
        ids = self._by_shard.get(shard, [])
        return [self._wallets[i] for i in ids]
    
    def get_by_type(self, wallet_type: str) -> List[WalletEntry]:
        return [w for w in self._wallets.values() if w.wallet_type == wallet_type]
    
    def all(self) -> List[WalletEntry]:
        return list(self._wallets.values())
    
    def save(self, filepath: str):
        """Save registry to JSON (public data only)."""
        data = {
            "version": "1.0",
            "wallets": [w.to_dict() for w in self._wallets.values()],
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved wallet registry to {filepath} ({len(self._wallets)} entries)")
    
    def load(self, filepath: str):
        """Load registry from JSON."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self._wallets.clear()
        self._by_chain.clear()
        self._by_shard.clear()
        
        for w_data in data.get("wallets", []):
            entry = WalletEntry(**w_data)
            self._wallets[entry.wallet_id] = entry
            self._index_entry(entry)
        
        logger.info(f"Loaded wallet registry from {filepath} ({len(self._wallets)} entries)")
    
    def build_full_registry(self, max_shards: int = 300, max_agents_per_shard: int = 10) -> int:
        """Build complete registry for all shards and agents."""
        count = 0
        
        # Register all shard wallets
        for shard in range(1, max_shards + 1):
            for chain_name, config in self.registry._chains.items():
                # Only register shards for appropriate chains
                if config.family == ChainFamily.EVM and shard <= 150:
                    self.register_shard_wallet(chain_name, shard)
                    count += 1
                elif config.family == ChainFamily.XRPL and shard == 151:
                    self.register_shard_wallet(chain_name, shard)
                    count += 1
                elif config.family == ChainFamily.SOLANA and 152 <= shard <= 201:
                    self.register_shard_wallet(chain_name, shard)
                    count += 1
                elif config.family == ChainFamily.COSMOS and 202 <= shard <= 251:
                    self.register_shard_wallet(chain_name, shard)
                    count += 1
                elif config.family == ChainFamily.BITCOIN_L2 and 252 <= shard <= 300:
                    self.register_shard_wallet(chain_name, shard)
                    count += 1
        
        # Register treasury wallets
        for treasury_name, treasury_info in self.registry._chains.items():
            if treasury_name in ["ethereum", "xrpl", "solana", "cosmos", "stacks"]:
                self.register_treasury_wallet(treasury_name, treasury_name)
                count += 1
        
        # Register agent wallets (subset)
        for shard in range(1, min(max_shards, 50) + 1):
            for chain_name in ["ethereum", "xrpl", "solana", "cosmos", "stacks"]:
                for agent_id in range(1, max_agents_per_shard + 1):
                    self.register_agent_wallet(chain_name, shard, agent_id)
                    count += 1
        
        logger.info(f"Built full registry with {count} wallet entries")
        return count
    
    def export_for_agents(self, output_path: str):
        """Export minimal registry for agent consumption."""
        minimal = {}
        for entry in self._wallets.values():
            if entry.wallet_type in ("shard", "treasury"):
                minimal[entry.wallet_id] = {
                    "address": entry.address,
                    "chain": entry.chain,
                    "public_key": entry.public_key,
                }
        
        with open(output_path, 'w') as f:
            json.dump(minimal, f, indent=2)
        
        logger.info(f"Exported minimal registry to {output_path}")


def create_wallet_registry(vault: StatelessVault = None) -> WalletRegistry:
    """Factory for WalletRegistry."""
    return WalletRegistry(vault)
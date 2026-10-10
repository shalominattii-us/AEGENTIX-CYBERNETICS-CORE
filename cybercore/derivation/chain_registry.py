"""
Chain Registry - Maps blockchain networks to derivation parameters.
Integrates with existing 300-node mesh and treasury wallets.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from .path import CurveType, PathTemplates


class ChainFamily(Enum):
    EVM = "EVM"
    XRPL = "XRPL"
    SOLANA = "SOLANA"
    COSMOS = "COSMOS"
    BITCOIN_L2 = "BITCOIN_L2"
    MOVE = "MOVE"
    UNKNOWN = "UNKNOWN"


@dataclass
class ChainConfig:
    """Configuration for a blockchain chain."""
    chain_id: int
    name: str
    family: ChainFamily
    curve: CurveType
    coin_type: int  # SLIP-0044 coin type
    bip44_purpose: int = 44
    address_prefix: str = ""
    native_token: str = ""
    stablecoin_contracts: Dict[str, str] = field(default_factory=dict)  # symbol -> contract
    rpc_endpoints: List[str] = field(default_factory=list)
    explorer_url: str = ""
    decimals: int = 18
    is_testnet: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


# Core chain configurations matching the 300-node mesh
CHAIN_REGISTRY: Dict[str, ChainConfig] = {
    # EVM Chains
    "ethereum": ChainConfig(
        chain_id=1,
        name="Ethereum Mainnet",
        family=ChainFamily.EVM,
        curve=CurveType.SECP256K1,
        coin_type=60,
        address_prefix="0x",
        native_token="ETH",
        stablecoin_contracts={
            "USDC": "0xA0b86a33E6441c8C06DD44B451D4A3b56e4e8D5B",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        },
        rpc_endpoints=["https://eth.aegentix.net/rpc"],
        explorer_url="https://etherscan.io",
    ),
    "arbitrum": ChainConfig(
        chain_id=42161,
        name="Arbitrum One",
        family=ChainFamily.EVM,
        curve=CurveType.SECP256K1,
        coin_type=42161,
        address_prefix="0x",
        native_token="ETH",
        stablecoin_contracts={
            "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        },
        rpc_endpoints=["https://arb.aegentix.net/rpc"],
        explorer_url="https://arbiscan.io",
    ),
    "base": ChainConfig(
        chain_id=8453,
        name="Base Mainnet",
        family=ChainFamily.EVM,
        curve=CurveType.SECP256K1,
        coin_type=8453,
        address_prefix="0x",
        native_token="ETH",
        stablecoin_contracts={
            "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        },
        rpc_endpoints=["https://base.aegentix.net/rpc"],
        explorer_url="https://basescan.org",
    ),
    "optimism": ChainConfig(
        chain_id=10,
        name="Optimism Mainnet",
        family=ChainFamily.EVM,
        curve=CurveType.SECP256K1,
        coin_type=10,
        address_prefix="0x",
        native_token="ETH",
        stablecoin_contracts={
            "USDC": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
        },
        rpc_endpoints=["https://opt.aegentix.net/rpc"],
        explorer_url="https://optimistic.etherscan.io",
    ),
    "polygon": ChainConfig(
        chain_id=137,
        name="Polygon PoS",
        family=ChainFamily.EVM,
        curve=CurveType.SECP256K1,
        coin_type=966,
        address_prefix="0x",
        native_token="MATIC",
        stablecoin_contracts={
            "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        },
        rpc_endpoints=["https://polygon.aegentix.net/rpc"],
        explorer_url="https://polygonscan.com",
    ),
    "avalanche": ChainConfig(
        chain_id=43114,
        name="Avalanche C-Chain",
        family=ChainFamily.EVM,
        curve=CurveType.SECP256K1,
        coin_type=43114,
        address_prefix="0x",
        native_token="AVAX",
        stablecoin_contracts={
            "USDC": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
        },
        rpc_endpoints=["https://avax.aegentix.net/rpc"],
        explorer_url="https://snowtrace.io",
    ),
    "bsc": ChainConfig(
        chain_id=56,
        name="BNB Smart Chain",
        family=ChainFamily.EVM,
        curve=CurveType.SECP256K1,
        coin_type=714,
        address_prefix="0x",
        native_token="BNB",
        stablecoin_contracts={
            "USDT": "0x55d398326f99059fF775485246999027B3197955",
            "USDC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
        },
        rpc_endpoints=["https://bsc.aegentix.net/rpc"],
        explorer_url="https://bscscan.com",
    ),
    "mantle": ChainConfig(
        chain_id=5000,
        name="Mantle Network",
        family=ChainFamily.EVM,
        curve=CurveType.SECP256K1,
        coin_type=5000,
        address_prefix="0x",
        native_token="MNT",
        rpc_endpoints=["https://mantle.aegentix.net/rpc"],
        explorer_url="https://explorer.mantle.xyz",
    ),
    "blast": ChainConfig(
        chain_id=81457,
        name="Blast Mainnet",
        family=ChainFamily.EVM,
        curve=CurveType.SECP256K1,
        coin_type=81457,
        address_prefix="0x",
        native_token="ETH",
        rpc_endpoints=["https://blast.aegentix.net/rpc"],
        explorer_url="https://blastscan.io",
    ),
    
    # XRPL
    "xrpl": ChainConfig(
        chain_id=144,
        name="XRP Ledger Mainnet",
        family=ChainFamily.XRPL,
        curve=CurveType.ED25519,
        coin_type=144,
        address_prefix="r",
        native_token="XRP",
        stablecoin_contracts={
            "USDC": "rUSDC...",  # XRPL uses trustlines, not contracts
        },
        rpc_endpoints=["https://xrplcluster.com", "wss://xrplcluster.com"],
        explorer_url="https://xrpscan.com",
        decimals=6,
    ),
    
    # Solana
    "solana": ChainConfig(
        chain_id=101,
        name="Solana Mainnet-Beta",
        family=ChainFamily.SOLANA,
        curve=CurveType.ED25519,
        coin_type=501,
        address_prefix="",
        native_token="SOL",
        stablecoin_contracts={
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        },
        rpc_endpoints=["https://solana.aegentix.net/rpc"],
        explorer_url="https://solscan.io",
        decimals=9,
    ),
    
    # MOVE chains
    "sui": ChainConfig(
        chain_id=201,
        name="Sui Mainnet",
        family=ChainFamily.MOVE,
        curve=CurveType.ED25519,
        coin_type=201,
        address_prefix="0x",
        native_token="SUI",
        rpc_endpoints=["https://sui.aegentix.net/rpc"],
        explorer_url="https://suiscan.xyz",
    ),
    "aptos": ChainConfig(
        chain_id=202,
        name="Aptos Mainnet",
        family=ChainFamily.MOVE,
        curve=CurveType.ED25519,
        coin_type=202,
        address_prefix="0x",
        native_token="APT",
        rpc_endpoints=["https://aptos.aegentix.net/rpc"],
        explorer_url="https://aptoscan.com",
    ),
    
    # Cosmos
    "cosmos": ChainConfig(
        chain_id=301,
        name="Cosmos Hub (Gaia)",
        family=ChainFamily.COSMOS,
        curve=CurveType.SECP256K1,
        coin_type=118,
        address_prefix="cosmos1",
        native_token="ATOM",
        rpc_endpoints=["https://cosmos.aegentix.net/rpc"],
        explorer_url="https://mintscan.io",
    ),
    "osmosis": ChainConfig(
        chain_id=302,
        name="Osmosis DEX Chain",
        family=ChainFamily.COSMOS,
        curve=CurveType.SECP256K1,
        coin_type=302,
        address_prefix="osmo1",
        native_token="OSMO",
        rpc_endpoints=["https://osmosis.aegentix.net/rpc"],
        explorer_url="https://mintscan.io/osmosis",
    ),
    "injective": ChainConfig(
        chain_id=303,
        name="Injective Protocol",
        family=ChainFamily.COSMOS,
        curve=CurveType.SECP256K1,
        coin_type=303,
        address_prefix="inj1",
        native_token="INJ",
        rpc_endpoints=["https://injective.aegentix.net/rpc"],
        explorer_url="https://mintscan.io/injective",
    ),
    
    # Bitcoin L2
    "stacks": ChainConfig(
        chain_id=401,
        name="Stacks Bitcoin L2",
        family=ChainFamily.BITCOIN_L2,
        curve=CurveType.SECP256K1,
        coin_type=401,
        address_prefix="SP",
        native_token="STX",
        rpc_endpoints=["https://stacks.aegentix.net/rpc"],
        explorer_url="https://explorer.stacks.co",
    ),
    "merlin": ChainConfig(
        chain_id=402,
        name="Merlin Chain",
        family=ChainFamily.BITCOIN_L2,
        curve=CurveType.SECP256K1,
        coin_type=402,
        address_prefix="0x",
        native_token="MERL",
        rpc_endpoints=["https://merlin.aegentix.net/rpc"],
        explorer_url="https://merlinscan.io",
    ),
    "babylon": ChainConfig(
        chain_id=403,
        name="Babylon Staking Mesh",
        family=ChainFamily.BITCOIN_L2,
        curve=CurveType.SECP256K1,
        coin_type=403,
        address_prefix="bc1",
        native_token="BTC",
        rpc_endpoints=["https://babylon.aegentix.net/rpc"],
        explorer_url="https://babylonscan.io",
    ),
}


# Treasury wallet chains (from minimal_node_treasury_wallets.json)
TREASURY_CHAINS = {
    "evm_treasury": {
        "chain": "ethereum",
        "address": "0x71C865d4fC35E2a188B67B7A98AcB921098A1904",
        "family": ChainFamily.EVM,
        "purpose": "Swap Aggregation, 5-15 BPS Fee Capture, Dilithium PQC Signing",
    },
    "xrpl_treasury": {
        "chain": "xrpl",
        "address": "rZamanXRPLMainnetVaultAddr9948271",
        "family": ChainFamily.XRPL,
        "purpose": "XRPL OfferCreate, Trustlines, CBDC Settlement",
    },
    "solana_treasury": {
        "chain": "solana",
        "address": "SolanaMinimalTreasuryVault111111111111111111",
        "family": ChainFamily.SOLANA,
        "purpose": "High-Throughput DEX Routing & Micro-Fee Capture",
    },
    "cosmos_treasury": {
        "chain": "cosmos",
        "address": "cosmos1aegentixminimaltreasuryvault99999",
        "family": ChainFamily.COSMOS,
        "purpose": "IBC Cross-Chain Intent Solves & Staking Vault Yield",
    },
    "bitcoin_l2_treasury": {
        "chain": "stacks",
        "address": "bc1qaegentixminimalnodebtc2026vault999",
        "family": ChainFamily.BITCOIN_L2,
        "purpose": "Bitcoin L2 Staking, BTC Yield Rebalancing & Tokenization",
    },
}


class ChainRegistry:
    """Registry for managing chain configurations."""
    
    def __init__(self):
        self._chains: Dict[str, ChainConfig] = dict(CHAIN_REGISTRY)
        self._by_chain_id: Dict[int, ChainConfig] = {}
        self._by_family: Dict[ChainFamily, List[ChainConfig]] = {}
        self._build_indexes()
    
    def _build_indexes(self):
        for chain in self._chains.values():
            self._by_chain_id[chain.chain_id] = chain
            if chain.family not in self._by_family:
                self._by_family[chain.family] = []
            self._by_family[chain.family].append(chain)
    
    def get(self, name: str) -> Optional[ChainConfig]:
        return self._chains.get(name.lower())
    
    def get_by_chain_id(self, chain_id: int) -> Optional[ChainConfig]:
        return self._by_chain_id.get(chain_id)
    
    def get_by_family(self, family: ChainFamily) -> List[ChainConfig]:
        return self._by_family.get(family, [])
    
    def all(self) -> List[ChainConfig]:
        return list(self._chains.values())
    
    def names(self) -> List[str]:
        return list(self._chains.keys())
    
    def get_stablecoin_contract(self, chain: str, symbol: str) -> Optional[str]:
        config = self.get(chain)
        if config:
            return config.stablecoin_contracts.get(symbol.upper())
        return None
    
    def get_native_token(self, chain: str) -> Optional[str]:
        config = self.get(chain)
        return config.native_token if config else None
    
    def get_derivation_path_template(self, chain: str) -> str:
        """Get standard derivation path template for chain."""
        config = self.get(chain)
        if not config:
            return PathTemplates.bip44(60)
        
        if config.curve == CurveType.ED25519:
            return PathTemplates.slip10(config.coin_type)
        else:
            return PathTemplates.bip44(config.coin_type)
    
    def get_agent_wallet_path(self, chain: str, shard: int, agent_id: int, nonce: int = 0) -> str:
        """Get agent wallet derivation path for chain."""
        config = self.get(chain)
        if not config:
            return PathTemplates.agent_wallet(60, shard, agent_id, nonce)
        return PathTemplates.agent_wallet(config.coin_type, shard, agent_id, nonce)
    
    def get_shard_wallet_path(self, chain: str, shard: int) -> str:
        """Get shard wallet derivation path for chain."""
        config = self.get(chain)
        if not config:
            return PathTemplates.shard_wallet(60, shard)
        return PathTemplates.shard_wallet(config.coin_type, shard)


# Global registry instance
_global_registry: Optional[ChainRegistry] = None


def get_chain_registry() -> ChainRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = ChainRegistry()
    return _global_registry


def register_custom_chain(config: ChainConfig):
    """Register a custom chain configuration."""
    registry = get_chain_registry()
    registry._chains[config.name.lower()] = config
    registry._build_indexes()
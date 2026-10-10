#!/usr/bin/env python3
"""
DeFi Yield Farming Optimizer - Auto-compound and strategy rotation
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from web3 import Web3
try:
    from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
except ImportError:
    try:
        from web3.middleware import geth_poa_middleware
    except ImportError:
        geth_poa_middleware = None

from ..core.base import (
    BaseEngine, ChainConfig, Opportunity, Position, PnLRecord,
    DEFAULT_CHAINS, TREASURY_ADDRESSES, BaseEngine
)


# Protocol ABIs
AAVE_POOL_ABI = [
    {"inputs": [{"internalType": "address", "name": "asset", "type": "address"}], "name": "getReserveData", "outputs": [{"internalType": "uint256", "name": "availableLiquidity", "type": "uint256"}, {"internalType": "uint256", "name": "totalStableDebt", "type": "uint256"}, {"internalType": "uint256", "name": "totalVariableDebt", "type": "uint256"}, {"internalType": "uint256", "name": "liquidityRate", "type": "uint256"}, {"internalType": "uint256", "name": "variableBorrowRate", "type": "uint256"}, {"internalType": "uint256", "name": "stableBorrowRate", "type": "uint256"}, {"internalType": "uint256", "name": "lastUpdateTimestamp", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "asset", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}, {"internalType": "address", "name": "onBehalfOf", "type": "address"}, {"internalType": "uint16", "name": "referralCode", "type": "uint16"}], "name": "supply", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "asset", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}, {"internalType": "address", "name": "to", "type": "address"}], "name": "withdraw", "outputs": [{"internalType": "uint256", "name": "amount", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"}
]

COMPOUND_COMPTROLLER_ABI = [
    {"inputs": [{"internalType": "address", "name": "cToken", "type": "address"}], "name": "getSupplyRate", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "address", "name": "cToken", "type": "address"}], "name": "getBorrowRate", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

CTOKEN_ABI = [
    {"inputs": [], "name": "supplyRatePerBlock", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "borrowRatePerBlock", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "exchangeRateCurrent", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "mintAmount", "type": "uint256"}], "name": "mint", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "redeemTokens", "type": "uint256"}], "name": "redeem", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"}
]

ERC4626_ABI = [
    {"inputs": [], "name": "totalAssets", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "assets", "type": "uint256"}], "name": "convertToShares", "outputs": [{"internalType": "uint256", "name": "shares", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "shares", "type": "uint256"}], "name": "convertToAssets", "outputs": [{"internalType": "uint256", "name": "assets", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "assets", "type": "uint256"}, {"internalType": "address", "name": "receiver", "type": "address"}], "name": "deposit", "outputs": [{"internalType": "uint256", "name": "shares", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "shares", "type": "uint256"}, {"internalType": "address", "name": "receiver", "type": "address"}, {"internalType": "address", "name": "owner", "type": "address"}], "name": "withdraw", "outputs": [{"internalType": "uint256", "name": "assets", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"}
]


@dataclass
class ProtocolConfig:
    """Protocol configuration"""
    name: str
    chain_id: int
    pool_address: str
    ctoken_addresses: Dict[str, str]  # token -> ctoken/vault
    vault_addresses: Dict[str, str]  # token -> ERC4626 vault
    is_aave: bool = False
    is_compound: bool = False
    is_erc4626: bool = False


class YieldFarmingEngine(BaseEngine):
    """DeFi Yield Farming Optimizer - Auto-compound and strategy rotation"""
    
    def __init__(self, name: str, chain_configs: Dict, treasury_addresses: Dict, capital_manager):
        super().__init__("yield_farming", {}, {}, None)
        self.name = "yield_farming"
        self.chain_configs = {}
        self.treasury_addresses = {}
        self.capital_manager = None
        self.web3_clients: Dict[int, Web3] = {}
        self.protocols: Dict[str, ProtocolConfig] = {}
        self.last_aprs: Dict[str, Dict[str, float]] = {}  # protocol -> token -> apr
        
    def initialize(self, chain_configs, treasury_addresses, capital_manager, rpc_manager):
        self.chain_configs = chain_configs
        self.treasury_addresses = treasury_addresses
        self.capital_manager = capital_manager
        
        # Initialize Web3 clients
        for chain_name, config in chain_configs.items():
            if config.rpc_urls:
                w3 = Web3(Web3.HTTPProvider(config.rpc_urls[0]))
                if config.chain_id in [137, 42161, 8453]:
                    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                self.web3_clients[config.chain_id] = w3
        
        # Configure protocols
        self.protocols = {
            "aave_v3_ethereum": ProtocolConfig(
                name="aave_v3",
                chain_id=1,
                pool_address="0x87870B93F396E354563C7A16F91F7d2A0B3A7A1",
                ctoken_addresses={},
                vault_addresses={
                    "USDC": "0x...",
                    "USDT": "0x...",
                    "DAI": "0x...",
                    "WETH": "0x..."
                },
                is_aave=True
            ),
            "aave_v3_base": ProtocolConfig(
                name="aave_v3",
                chain_id=8453,
                pool_address="0x...",
                vault_addresses={
                    "USDC": "0x...",
                    "WETH": "0x..."
                },
                is_aave=True
            ),
            "compound_v3_ethereum": ProtocolConfig(
                name="compound_v3",
                chain_id=1,
                pool_address="0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B",
                ctoken_addresses={
                    "USDC": "0x...",
                    "USDT": "0x...",
                    "WETH": "0x..."
                },
                is_compound=True
            ),
            "aerodrome_base": ProtocolConfig(
                name="aerodrome",
                chain_id=8453,
                pool_address="0x420DD381b31aEf6683db6B902084cB04ECe8890D",
                vault_addresses={
                    "USDC": "0x...",
                    "WETH": "0x..."
                },
                is_erc4626=True
            ),
            "morpho_blue_ethereum": ProtocolConfig(
                name="morpho_blue",
                chain_id=1,
                pool_address="0x...",
                vault_addresses={
                    "USDC": "0x...",
                    "WETH": "0x..."
                },
                is_erc4626=True
            ),
            "convex_ethereum": ProtocolConfig(
                name="convex",
                chain_id=1,
                pool_address="0xF403C135812408BFbE8713b5A23a04b3D48AAE31",
                vault_addresses={},
                is_erc4626=False
            )
        }
    
    async def scan_opportunities(self) -> List:
        """Scan for best yield opportunities across protocols"""
        opportunities = []
        
        for protocol_name, protocol in self.protocols.items():
            if protocol.chain_id not in self.web3_clients:
                continue
            
            w3 = self.web3_clients.get(protocol.chain_id)
            if not w3 or not w3.is_connected():
                continue
            
            try:
                if protocol.is_aave:
                    opportunities.extend(await self._scan_aave(protocol))
                elif protocol.is_compound:
                    opportunities.extend(await self._scan_compound(protocol))
                elif protocol.is_erc4626:
                    opportunities.extend(await self._scan_erc4626(protocol))
                    
            except Exception as e:
                print(f"Error scanning {protocol_name}: {e}")
        
        # Sort by APY descending
        opportunities.sort(key=lambda x: x.expected_profit_usd, reverse=True)
        
        # Return top opportunities
        return opportunities[:10]
    
    async def _scan_aave(self, protocol: ProtocolConfig) -> List:
        """Scan Aave V3 for best yields"""
        opportunities = []
        
        if protocol.chain_id not in self.web3_clients:
            return []
        
        w3 = self.web3_clients[protocol.chain_id]
        
        for token, vault in protocol.vault_addresses.items():
            try:
                pool = w3.eth.contract(
                    address=protocol.pool_address,
                    abi=[{"inputs": [{"internalType": "address", "name": "asset", "type": "address"}], "name": "getReserveData", "outputs": [{"internalType": "uint256", "name": "availableLiquidity", "type": "uint256"}, {"internalType": "uint256", "name": "totalStableDebt", "type": "uint256"}, {"internalType": "uint256", "name": "totalVariableDebt", "type": "uint256"}, {"internalType": "uint256", "name": "liquidityRate", "type": "uint256"}, {"internalType": "uint256", "name": "variableBorrowRate", "type": "uint256"}, {"internalType": "uint256", "name": "stableBorrowRate", "type": "uint256"}, {"internalType": "uint256", "name": "lastUpdateTimestamp", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
                )
                
                # Get token address from chain config
                token_addr = self.chain_configs["ethereum"].stablecoins.get(token)
                if not token_addr:
                    continue
                
                data = await self.web3_clients[protocol.chain_id].eth.call({
                    "to": protocol.pool_address,
                    "data": w3.eth.contract(abi=[{"inputs": [{"internalType": "address", "name": "asset", "type": "address"}], "name": "getReserveData", "outputs": [{"internalType": "uint256", "name": "liquidityRate", "type": "uint256"}], "stateMutability": "view", "type": "function"}]).encode_abi("getReserveData", [token_addr])
                })
                
                # Parse liquidity rate (RAY = rate * 1e27)
                liquidity_rate = int(data.hex(), 16)
                apr = (liquidity_rate / 1e27) * 100 * 31536000  # Convert to APR %
                
                self.last_aprs.setdefault("aave", {})[token] = apr
                
                # Create opportunity if APY is attractive
                if apr > 3.0:  # > 3% APY
                    from ..core.base import Opportunity
                    opp = Opportunity(
                        id=f"aave_{token}_{protocol.chain_id}_{int(time.time())}",
                        type="yield_farming",
                        chain=protocol.chain_id,
                        dex_a="aave_v3",
                        dex_b="deposit",
                        token_in="USDC",
                        token_out=token,
                        amount_in=Decimal("10000"),
                        expected_profit_usd=Decimal("10000") * Decimal(str(apr)) / Decimal("100"),
                        gas_estimate_usd=Decimal("5"),
                        net_profit_usd=Decimal("10000") * Decimal(str(apr)) / Decimal("100") - Decimal("5"),
                        confidence=0.9,
                        timestamp=datetime.now(),
                        execution_data={
                            "protocol": "aave_v3",
                            "token": token,
                            "apr": apr,
                            "action": "deposit"
                        }
                    )
                    opportunities.append(opp)
                    
            except Exception as e:
                continue
        
        return opportunities
    
    async def _scan_compound(self, protocol: ProtocolConfig) -> List:
        """Scan Compound V3 for yields"""
        opportunities = []
        
        if protocol.chain_id not in self.web3_clients:
            return []
        
        w3 = self.web3_clients[protocol.chain_id]
        
        for token, ctoken in protocol.ctoken_addresses.items():
            try:
                ctoken_contract = w3.eth.contract(
                    address=ctoken,
                    abi=[{"inputs": [], "name": "supplyRatePerBlock", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]
                )
                
                supply_rate_per_block = ctoken_contract.functions.supplyRatePerBlock().call()
                apr = (supply_rate_per_block / 1e18) * 2102400 * 100  # blocks per year * 100
                
                self.last_aprs.setdefault("compound", {})[token] = apr
                
                if apr > 3.0:
                    from ..core.base import Opportunity
                    opp = Opportunity(
                        id=f"compound_{token}_{protocol.chain_id}_{int(time.time())}",
                        type="yield_farming",
                        chain=protocol.chain_id,
                        dex_a="compound_v3",
                        dex_b="supply",
                        token_in="USDC",
                        token_out=token,
                        amount_in=Decimal("10000"),
                        expected_profit_usd=Decimal("10000") * Decimal(str(apr)) / Decimal("100"),
                        gas_estimate_usd=Decimal("5"),
                        net_profit_usd=Decimal("10000") * Decimal(str(apr)) / Decimal("100") - Decimal("5"),
                        confidence=0.9,
                        timestamp=datetime.now(),
                        execution_data={
                            "protocol": "compound_v3",
                            "token": token,
                            "apr": apr,
                            "action": "supply"
                        }
                    )
                    opportunities.append(opp)
                    
            except Exception as e:
                continue
        
        return opportunities
    
    async def _scan_erc4626(self, protocol: ProtocolConfig) -> List:
        """Scan ERC4626 vaults (Yearn, Morpho, Aerodrome, etc.)"""
        opportunities = []
        
        if protocol.chain_id not in self.web3_clients:
            return []
        
        w3 = self.web3_clients[protocol.chain_id]
        
        for token, vault in protocol.vault_addresses.items():
            try:
                vault_contract = w3.eth.contract(
                    address=vault,
                    abi=[
                        {"inputs": [], "name": "totalAssets", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
                        {"inputs": [], "name": "convertToShares", "outputs": [{"internalType": "uint256", "name": "shares", "type": "uint256"}], "stateMutability": "view", "type": "function"},
                        {"inputs": [{"internalType": "uint256", "name": "assets", "type": "uint256"}], "name": "convertToShares", "outputs": [{"internalType": "uint256", "name": "shares", "type": "uint256"}], "stateMutability": "view", "type": "function"}
                    ]
                )
                
                # Get APY from vault (simplified - would need historical data)
                total_assets = vault_contract.functions.totalAssets().call()
                
                # Simplified APY calculation - would need historical data
                apr = 10.0  # Placeholder
                
                self.last_aprs.setdefault(protocol.name, {})[token] = apr
                
                if apr > 5.0:
                    from ..core.base import Opportunity
                    opp = Opportunity(
                        id=f"{protocol.name}_{token}_{protocol.chain_id}_{int(time.time())}",
                        type="yield_farming",
                        chain=protocol.chain_id,
                        dex_a=protocol.name,
                        dex_b="deposit",
                        token_in="USDC",
                        token_out=token,
                        amount_in=Decimal("10000"),
                        expected_profit_usd=Decimal("10000") * Decimal(str(apr)) / Decimal("100"),
                        gas_estimate_usd=Decimal("5"),
                        net_profit_usd=Decimal("10000") * Decimal(str(apr)) / Decimal("100") - Decimal("5"),
                        confidence=0.8,
                        timestamp=datetime.now(),
                        execution_data={
                            "protocol": protocol.name,
                            "token": token,
                            "apr": apr,
                            "action": "deposit",
                            "vault": vault
                        }
                    )
                    opportunities.append(opp)
                    
            except Exception as e:
                continue
        
        return opportunities
    
    async def execute(self, opportunity) -> bool:
        """Execute yield farming deposit - placeholder"""
        print(f"Executing yield farm: {opportunity.id}")
        return False


def register_yield_engine(manager):
    """Register yield farming engine with manager"""
    engine = YieldFarmingEngine("yield_farming", {}, {}, None)
    manager.register_engine(engine)
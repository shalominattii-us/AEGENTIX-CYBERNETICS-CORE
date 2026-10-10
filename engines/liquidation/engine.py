#!/usr/bin/env python3
"""
Liquidation Bot - Liquidate undercollateralized positions for profit
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
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


# Liquidation ABIs
AAVE_POOL_LIQUIDATION_ABI = [
    {"inputs": [{"internalType": "address", "name": "collateralAsset", "type": "address"}, {"internalType": "address", "name": "debtAsset", "type": "address"}, {"internalType": "address", "name": "user", "type": "address"}, {"internalType": "uint256", "name": "debtToCover", "type": "uint256"}, {"internalType": "bool", "name": "receiveAToken", "type": "bool"}], "name": "liquidationCall", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]

COMPOUND_COMPTROLLER_LIQUIDATE_ABI = [
    {"inputs": [{"internalType": "address", "name": "borrower", "type": "address"}, {"internalType": "uint256", "name": "repayAmount", "type": "uint256"}, {"internalType": "address", "name": "cTokenCollateral", "type": "address"}], "name": "liquidateBorrow", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"}
]

MORPHO_BLUE_LIQUIDATE_ABI = [
    {"inputs": [{"internalType": "address", "name": "market", "type": "address"}, {"internalType": "address", "name": "borrower", "type": "address"}, {"internalType": "uint256", "name": "assets", "type": "uint256"}, {"internalType": "bytes", "name": "data", "type": "bytes"}], "name": "liquidate", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]


@dataclass
class LiquidatablePosition:
    """Liquidatable position data"""
    protocol: str
    chain_id: int
    borrower: str
    collateral_token: str
    debt_token: str
    collateral_amount: Decimal
    debt_amount: Decimal
    health_factor: float
    max_liquidatable: Decimal
    liquidation_bonus_bps: int
    estimated_profit_usd: Decimal
    gas_estimate_usd: Decimal
    net_profit_usd: Decimal


class LiquidationEngine(BaseEngine):
    """Liquidation Bot - Liquidate undercollateralized positions"""
    
    def __init__(self, name: str, chain_configs: Dict, treasury_addresses: Dict, capital_manager):
        super().__init__("liquidation_bot", {}, {}, None)
        self.name = "liquidation_bot"
        self.chain_configs = {}
        self.treasury_addresses = {}
        self.capital_manager = None
        self.web3_clients: Dict[int, Web3] = {}
        self.protocols = {}
        self.last_scan: Dict[str, datetime] = {}
        
    def initialize(self, chain_configs, treasury_addresses, capital_manager, rpc_manager):
        self.chain_configs = chain_configs
        self.treasury_addresses = treasury_addresses
        self.capital_manager = capital_manager
        self.rpc_manager = rpc_manager
        
        # Initialize Web3 clients
        for chain_name, config in chain_configs.items():
            if config.rpc_urls:
                w3 = Web3(Web3.HTTPProvider(config.rpc_urls[0]))
                if config.chain_id in [137, 42161, 8453]:
                    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                self.web3_clients[config.chain_id] = w3
        
        # Configure lending protocols
        self.protocols = {
            "aave_v3": {
                "ethereum": {
                    "pool": "0x87870B93F396E354563C7A16F91F7d2A0B3A7A1",
                    "liquidation_bonus_bps": 500,  # 5%
                    "ltv_threshold": 0.8
                },
                "base": {
                    "pool": "0x...",
                    "liquidation_bonus_bps": 500,
                    "ltv_threshold": 0.8
                },
                "arbitrum": {
                    "pool": "0x...",
                    "liquidation_bonus_bps": 500,
                    "ltv_threshold": 0.8
                },
                "polygon": {
                    "pool": "0x...",
                    "liquidation_bonus_bps": 500,
                    "ltv_threshold": 0.8
                }
            },
            "compound_v3": {
                "ethereum": {
                    "comptroller": "0x3d9819210A31b4961b30EF54bE2aeD79B9c9Cd3B",
                    "liquidation_incentive": 1.08,  # 8% bonus
                    "close_factor": 0.5
                },
                "base": {
                    "comptroller": "0x...",
                    "liquidation_incentive": 1.08,
                    "close_factor": 0.5
                }
            },
            "morpho_blue": {
                "ethereum": {
                    "blue": "0x...",
                    "liquidation_bonus_bps": 1000  # 10%
                },
                "base": {
                    "blue": "0x...",
                    "liquidation_bonus_bps": 1000
                }
            }
        }
    
    async def scan_opportunities(self) -> List:
        """Scan for liquidatable positions across protocols"""
        opportunities = []
        
        for protocol_name, chains in self.protocols.items():
            for chain_id, config in chains.items():
                if chain_id not in self.web3_clients:
                    continue
                
                w3 = self.web3_clients.get(chain_id)
                if not w3 or not w3.is_connected():
                    continue
                
                try:
                    if protocol_name == "aave_v3":
                        opportunities.extend(await self._scan_aave_liquidations(chain_id, config))
                    elif protocol_name == "compound_v3":
                        opportunities.extend(await self._scan_compound_liquidations(chain_id, config))
                    elif protocol_name == "morpho_blue":
                        opportunities.extend(await self._scan_morpho_liquidations(chain_id, config))
                        
                except Exception as e:
                    print(f"Error scanning {protocol_name} on {chain_id}: {e}")
        
        # Sort by net profit descending
        opportunities.sort(key=lambda x: x.net_profit_usd, reverse=True)
        
        # Filter profitable only
        return [o for o in opportunities if o.net_profit_usd > Decimal("10")]
    
    async def _scan_aave_liquidations(self, chain_id: int, config: Dict) -> List:
        """Scan Aave V3 for liquidatable positions"""
        opportunities = []
        
        # This would query the pool for users with health factor < 1
        # For now, return empty - would need event monitoring in production
        return []
    
    async def _scan_compound_liquidations(self, chain_id: int, config: Dict) -> List:
        """Scan Compound V3 for liquidatable positions"""
        return []
    
    async def _scan_morpho_liquidations(self, chain_id: int, config: Dict) -> List:
        """Scan Morpho Blue for liquidations"""
        return []
    
    def _calculate_liquidation_profit(
        self,
        collateral_amount: Decimal,
        debt_amount: Decimal,
        collateral_price_usd: Decimal,
        debt_price_usd: Decimal,
        liquidation_bonus_bps: int,
        gas_estimate_usd: Decimal
    ) -> Decimal:
        """Calculate net profit from liquidation"""
        # Liquidator receives collateral worth (debt * (1 + bonus))
        collateral_received_usd = debt_amount * debt_price_usd * (1 + Decimal(liquidation_bonus_bps) / Decimal("10000"))
        collateral_value_usd = collateral_amount * collateral_price_usd
        
        # Profit = value of collateral received - debt paid - gas
        # Actually: liquidator pays debt, receives collateral worth debt * (1 + bonus)
        profit_usd = (debt_amount * debt_price_usd * Decimal(liquidation_bonus_bps) / Decimal("10000")) - gas_estimate_usd
        
        return profit_usd
    
    async def execute(self, opportunity: Opportunity) -> bool:
        """Execute liquidation - placeholder"""
        print(f"Executing liquidation: {opportunity.id}")
        return False


def register_liquidation_engine(manager):
    """Register liquidation engine with manager"""
    engine = LiquidationEngine("liquidation_bot", {}, {}, None)
    manager.register_engine(engine)
#!/usr/bin/env python3
"""
Market Maker Engine - Provide liquidity and earn spreads/fees
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


# DEX ABIs
UNISWAP_V3_POOL_ABI = [
    {"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}, {"internalType": "uint16", "name": "observationIndex", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinality", "type": "uint16"}, {"internalType": "uint16", "name": "observationCardinalityNext", "type": "uint16"}, {"internalType": "bool", "name": "unlocked", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "liquidity", "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint128", "name": "amount", "type": "uint128"}, {"internalType": "address", "name": "recipient", "type": "address"}], "name": "mint", "outputs": [{"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint128", "name": "amount", "type": "uint128"}, {"internalType": "address", "name": "to", "type": "address"}], "name": "collect", "outputs": [{"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"internalType": "int24", "name": "tickLower", "type": "int24"}, {"internalType": "int24", "name": "tickUpper", "type": "int24"}, {"internalType": "uint128", "name": "liquidity", "type": "uint128"}], "name": "burn", "outputs": [{"internalType": "uint256", "name": "amount0", "type": "uint256"}, {"internalType": "uint256", "name": "amount1", "type": "uint256"}], "stateMutability": "nonpayable", "type": "function"}
]

UNISWAP_V3_FACTORY_ABI = [
    {"inputs": [{"internalType": "address", "name": "tokenA", "type": "address"}, {"internalType": "address", "name": "tokenB", "type": "address"}, {"internalType": "uint24", "name": "fee", "type": "uint24"}], "name": "getPool", "outputs": [{"internalType": "address", "name": "pool", "type": "address"}], "stateMutability": "view", "type": "function"}
]


@dataclass
class PoolConfig:
    """Pool configuration for market making"""
    chain_id: int
    pool_address: str
    token0: str
    token1: str
    fee: int  # fee tier (500, 3000, 10000)
    token0_address: str
    token1_address: str
    tick_spacing: int
    min_profit_bps: int = 10  # minimum profit in basis points
    max_position_usd: Decimal = Decimal("10000")
    rebalance_threshold_bps: int = 50  # rebalance if price moves 50 bps


@dataclass
class MMPosition:
    """Market maker position"""
    pool_address: str
    chain_id: int
    tick_lower: int
    tick_upper: int
    liquidity: int
    token0_amount: Decimal
    token1_amount: Decimal
    entry_price: Decimal
    current_price: Decimal
    fees_earned_0: Decimal = Decimal("0")
    fees_earned_1: Decimal = Decimal("0")
    created_at: datetime = field(default_factory=datetime.now)


class MarketMakerEngine(BaseEngine):
    """Market Maker Engine - Provide concentrated liquidity on Uniswap V3"""
    
    def __init__(self, name: str, chain_configs: Dict, treasury_addresses: Dict, capital_manager):
        super().__init__("market_maker", {}, {}, None)
        self.name = "market_maker"
        self.chain_configs = {}
        self.treasury_addresses = {}
        self.capital_manager = None
        self.web3_clients: Dict[int, Web3] = {}
        self.pools: Dict[str, PoolConfig] = {}
        self.positions: Dict[str, MMPosition] = {}
        self.last_rebalance: Dict[str, datetime] = {}
        
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
        
        # Configure pools for market making
        self._configure_pools()
    
    def _configure_pools(self):
        """Configure pools for market making"""
        # Ethereum mainnet pools
        self.pools["ethereum_weth_usdc_3000"] = PoolConfig(
            chain_id=1,
            pool_address="0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8",  # WETH/USDC 0.3%
            token0="WETH",
            token1="USDC",
            fee=3000,
            token0_address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            token1_address="0xA0b86a33E6441c8C06DD44B451D4A3b56e4e8D5B",
            tick_spacing=60,
            min_profit_bps=5,
            max_position_usd=Decimal("50000")
        )
        
        self.pools["ethereum_weth_usdc_500"] = PoolConfig(
            chain_id=1,
            pool_address="0x88e6A0c2dDD26F7b4C121072E5326e0E4E5b4F8E",  # WETH/USDC 0.05%
            token0="WETH",
            token1="USDC",
            fee=500,
            token0_address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            token1_address="0xA0b86a33E6441c8C06DD44B451D4A3b56e4e8D5B",
            tick_spacing=10,
            min_profit_bps=3,
            max_position_usd=Decimal("10000")
        )
        
        # Base pools
        self.pools["base_weth_usdc_3000"] = PoolConfig(
            chain_id=8453,
            pool_address="0x...",  # WETH/USDC 0.3% on Base
            token0="WETH",
            token1="USDC",
            fee=3000,
            token0_address="0x4200000000000000000000000000000000000006",
            token1_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            tick_spacing=60,
            min_profit_bps=5,
            max_position_usd=Decimal("20000")
        )
        
        # Arbitrum pools
        self.pools["arbitrum_weth_usdc_3000"] = PoolConfig(
            chain_id=42161,
            pool_address="0x...",  # WETH/USDC 0.3% on Arbitrum
            token0="WETH",
            token1="USDC",
            fee=3000,
            token0_address="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            token1_address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            tick_spacing=60,
            min_profit_bps=5,
            max_position_usd=Decimal("20000")
        )
    
    async def scan_opportunities(self) -> List:
        """Scan for market making opportunities"""
        opportunities = []
        
        for pool_key, pool in self.pools.items():
            if pool.chain_id not in self.web3_clients:
                continue
            
            w3 = self.web3_clients.get(pool.chain_id)
            if not w3 or not w3.is_connected():
                continue
            
            try:
                # Check if we have an active position
                position_key = f"{pool.chain_id}_{pool.pool_address}"
                
                if position_key in self.positions:
                    # Check if rebalance needed
                    if await self._needs_rebalance(pool):
                        from ..core.base import Opportunity
                        opp = Opportunity(
                            id=f"rebalance_{pool_key}_{int(time.time())}",
                            type="market_maker_rebalance",
                            chain=pool.chain_id,
                            dex_a="uniswap_v3",
                            dex_b="rebalance",
                            token_in=pool.token0,
                            token1=pool.token1,
                            amount_in=Decimal("0"),
                            expected_profit_usd=Decimal("50"),
                            gas_estimate_usd=Decimal("20"),
                            net_profit_usd=Decimal("30"),
                            confidence=0.9,
                            timestamp=datetime.now(),
                            execution_data={
                                "pool": pool_key,
                                "action": "rebalance",
                                "pool_address": pool.pool_address
                            }
                        )
                        opportunities.append(opp)
                else:
                    # Check if we should open new position
                    if await self._should_open_position(pool):
                        from ..core.base import Opportunity
                        opp = Opportunity(
                            id=f"open_mm_{pool_key}_{int(time.time())}",
                            type="market_maker_open",
                            chain=pool.chain_id,
                            dex_a="uniswap_v3",
                            dex_b="mint",
                            token_in=pool.token0,
                            token_out=pool.token1,
                            amount_in=pool.max_position_usd,
                            expected_profit_usd=Decimal("100"),
                            gas_estimate_usd=Decimal("30"),
                            net_profit_usd=Decimal("70"),
                            confidence=0.8,
                            timestamp=datetime.now(),
                            execution_data={
                                "pool": pool_key,
                                "action": "open_position",
                                "pool_address": pool.pool_address,
                                "tick_lower": 0,  # Would calculate based on current price
                                "tick_upper": 0
                            }
                        )
                        opportunities.append(opp)
                        
            except Exception as e:
                print(f"Error scanning {pool_key}: {e}")
        
        return opportunities
    
    async def _get_pool_price(self, pool: PoolConfig) -> Optional[Decimal]:
        """Get current pool price"""
        if pool.chain_id not in self.web3_clients:
            return None
        
        w3 = self.web3_clients[pool.chain_id]
        
        try:
            pool_contract = w3.eth.contract(
                address=pool.pool_address,
                abi=[{"inputs": [], "name": "slot0", "outputs": [{"internalType": "uint160", "name": "sqrtPriceX96", "type": "uint160"}, {"internalType": "int24", "name": "tick", "type": "int24"}], "stateMutability": "view", "type": "function"}]
            )
            
            slot0 = pool_contract.functions.slot0().call()
            sqrt_price_x96 = slot0[0]
            tick = slot0[1]
            
            # Convert sqrtPriceX96 to price
            price = (Decimal(sqrt_price_x96) / Decimal(2**96)) ** 2
            
            # Adjust for decimals (token0/token1)
            # For WETH/USDC: price is WETH per USDC, need USDC per WETH
            if pool.token0 == "WETH" and pool.token1 == "USDC":
                price = Decimal("1") / price
            
            return price
            
        except Exception as e:
            print(f"Error getting price for {pool.pool_address}: {e}")
            return None
    
    async def _needs_rebalance(self, pool: PoolConfig) -> bool:
        """Check if position needs rebalancing"""
        position_key = f"{pool.chain_id}_{pool.pool_address}"
        
        if position_key not in self.positions:
            return False
        
        position = self.positions[position_key]
        current_price = await self._get_pool_price(pool)
        
        if not current_price:
            return False
        
        # Check if price moved beyond rebalance threshold
        price_change_pct = abs(float(current_price - position.entry_price) / position.entry_price)
        threshold = pool.rebalance_threshold_bps / 10000
        
        return price_change_pct > threshold
    
    async def _should_open_position(self, pool: PoolConfig) -> bool:
        """Check if we should open a new market making position"""
        # Check if we have capital available
        # Check if pool has sufficient volume/fees
        # Check if not already have position
        
        position_key = f"{pool.chain_id}_{pool.pool_address}"
        if position_key in self.positions:
            return False
        
        # Check pool volume/fees (simplified)
        return True
    
    async def _calculate_ticks(self, pool: PoolConfig, current_price: Decimal, width_bps: int = 100) -> Tuple[int, int]:
        """Calculate tick range for position"""
        # Convert price to tick
        # tick = log(price) / log(1.0001)
        import math
        tick = int(math.log(float(current_price)) / math.log(1.0001))
        
        # Width in ticks
        width_ticks = int(width_bps / pool.tick_spacing)
        
        tick_lower = tick - width_ticks // 2
        tick_upper = tick + width_ticks // 2
        
        # Align to tick spacing
        tick_lower = (tick_lower // pool.tick_spacing) * pool.tick_spacing
        tick_upper = (tick_upper // pool.tick_spacing) * pool.tick_spacing
        
        return tick_lower, tick_upper
    
    async def execute(self, opportunity: Opportunity) -> bool:
        """Execute market making action"""
        print(f"Executing market maker: {opportunity.id}")
        
        if opportunity.type == "market_maker_open":
            # Open new concentrated liquidity position
            return await self._open_position(opportunity)
        elif opportunity.type == "market_maker_rebalance":
            # Rebalance existing position
            return await self._rebalance_position(opportunity)
        
        return False
    
    async def _open_position(self, opportunity: Opportunity) -> bool:
        """Open new concentrated liquidity position"""
        # Would call pool.mint() with calculated ticks
        print(f"Opening MM position: {opportunity.execution_data}")
        return True
    
    async def _rebalance_position(self, opportunity: Opportunity) -> bool:
        """Rebalance existing position"""
        # Would call pool.burn() + pool.mint() with new ticks
        print(f"Rebalancing MM position: {opportunity.execution_data}")
        return True
    
    async def execute(self, opportunity: Opportunity) -> bool:
        """Execute market making action"""
        if opportunity.type == "market_maker_open":
            return await self._open_position(opportunity)
        elif opportunity.type == "market_maker_rebalance":
            return await self._rebalance_position(opportunity)
        return False


def register_market_maker_engine(manager):
    """Register market maker engine with manager"""
    engine = MarketMakerEngine("market_maker", {}, {}, None)
    manager.register_engine(engine)
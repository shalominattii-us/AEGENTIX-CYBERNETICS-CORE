#!/usr/bin/env python3
"""
AEGENTIX Core Engine - Base classes for all revenue engines
"""

import asyncio
import asyncio
import json
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from pathlib import Path
import aiohttp
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ChainConfig:
    """Chain configuration with RPC endpoints"""
    name: str
    chain_id: int
    rpc_urls: List[str]
    ws_urls: List[str]
    native_token: str
    stablecoins: Dict[str, str]  # symbol -> contract
    dex_routers: Dict[str, str]  # name -> contract
    gas_token: str = "native"
    gas_multiplier: float = 1.1
    min_profit_usd: float = 10.0
    max_gas_usd: float = 50.0


@dataclass
class Opportunity:
    """Trading opportunity"""
    id: str
    type: str  # arbitrage, mev, liquidation, yield
    chain: str
    dex_a: str
    dex_b: str
    token_in: str
    token_out: str
    amount_in: Decimal
    expected_profit_usd: Decimal
    gas_estimate_usd: Decimal
    net_profit_usd: Decimal
    confidence: float
    timestamp: datetime
    execution_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Position:
    """Open position"""
    id: str
    engine: str
    chain: str
    token: str
    amount: Decimal
    entry_price: Decimal
    current_price: Decimal
    pnl_usd: Decimal
    opened_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PnLRecord:
    """Profit/Loss record"""
    timestamp: datetime
    engine: str
    chain: str
    gross_profit_usd: Decimal
    gas_cost_usd: Decimal
    net_profit_usd: Decimal
    tx_hash: str
    details: Dict[str, Any]


class RPCManager:
    """Manages RPC connections with failover"""
    
    def __init__(self, chain_configs: Dict[str, ChainConfig]):
        self.chain_configs = chain_configs
        self.sessions: Dict[str, aiohttp.ClientSession] = {}
        self.current_rpc: Dict[str, int] = {}  # chain -> index
        self.ws_connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        
    async def get_session(self, chain: str) -> aiohttp.ClientSession:
        """Get or create HTTP session for chain"""
        if chain not in self.sessions:
            config = self.chain_configs[chain]
            self.sessions[chain] = aiohttp.ClientSession()
            self.current_rpc[chain] = 0
        return self.sessions[chain]
    
    async def rpc_call(self, chain: str, method: str, params: List) -> Any:
        """Make RPC call with automatic failover"""
        config = self.chain_configs[chain]
        session = await self.get_session(chain)
        
        for i in range(len(config.rpc_urls)):
            idx = (self.current_rpc[chain] + i) % len(config.rpc_urls)
            url = config.rpc_urls[idx]
            
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": 1
                }
                async with session.post(url, json=payload, timeout=10) as resp:
                    data = await resp.json()
                    if "error" not in data:
                        self.current_rpc[chain] = idx
                        return data.get("result")
            except Exception as e:
                logger.warning(f"RPC {url} failed: {e}")
                continue
        
        raise Exception(f"All RPCs failed for {chain}")
    
    async def eth_call(self, chain: str, to: str, data: str, block: str = "latest") -> str:
        """Make eth_call"""
        result = await self.rpc_call(chain, "eth_call", [{"to": to, "data": data}, block])
        return result
    
    async def get_balance(self, chain: str, address: str, token: str = None) -> int:
        """Get token balance"""
        config = self.chain_configs[chain]
        
        if token is None or token == config.native_token:
            # Native token balance
            result = await self.rpc_call(chain, "eth_getBalance", [self.to_checksum(address), "latest"])
            return int(result, 16)
        else:
            # ERC20 balance
            token_contract = config.stablecoins.get(token)
            if not token_contract:
                raise ValueError(f"Token {token} not configured for {chain}")
            
            # balanceOf(address)
            data = "0x70a08231" + self.to_padded_hex(address)
            result = await self.eth_call(chain, token_contract, data)
            return int(result, 16)
    
    @staticmethod
    def to_checksum(address: str) -> str:
        """Convert to checksum address"""
        return address  # Simplified - use eth_utils in production
    
    @staticmethod
    def to_padded_hex(address: str) -> str:
        """Pad address to 32 bytes hex"""
        return address.lower().replace("0x", "").zfill(64)
    
    async def close(self):
        for session in self.sessions.values():
            await session.close()


class CapitalManager:
    """Manages capital allocation across engines"""
    
    def __init__(self, treasury_addresses: Dict[str, str], rpc_manager: RPCManager):
        self.treasury_addresses = treasury_addresses
        self.rpc_manager = rpc_manager
        self.allocations: Dict[str, Decimal] = {}  # engine -> allocated
        self.max_allocation_per_engine = Decimal("0.1")  # 10% max per engine
        self.reserve_ratio = Decimal("0.2")  # 20% reserve
    
    async def get_available_capital(self, chain: str) -> Decimal:
        """Get available capital on chain"""
        address = self.treasury_addresses.get(chain)
        if not address:
            return Decimal("0")
        
        balance = await self.rpc_manager.get_balance("ethereum", address)  # Simplified
        return Decimal(str(balance)) / Decimal("1e18")
    
    def allocate(self, engine: str, amount: Decimal) -> bool:
        """Allocate capital to engine"""
        current = self.allocations.get(engine, Decimal("0"))
        if current + amount > self.max_allocation_per_engine:
            return False
        self.allocations[engine] = current + amount
        return True
    
    def deallocate(self, engine: str, amount: Decimal):
        """Deallocate capital from engine"""
        current = self.allocations.get(engine, Decimal("0"))
        self.allocations[engine] = max(Decimal("0"), current - amount)


class BaseEngine(ABC):
    """Base class for all revenue engines"""
    
    def __init__(self, name: str, chain_configs: Dict[str, ChainConfig], 
                 treasury_addresses: Dict[str, str], capital_manager: CapitalManager):
        self.name = name
        self.chain_configs = chain_configs
        self.treasury_addresses = treasury_addresses
        self.capital_manager = capital_manager
        self.rpc_manager = None  # Set by EngineManager
        self.running = False
        self.positions: Dict[str, Position] = {}
        self.pnl_history: List[PnLRecord] = []
        self.last_error: Optional[str] = None
        self.total_profit_usd = Decimal("0")
        self.total_gas_usd = Decimal("0")
        self.trades_count = 0
    
    @abstractmethod
    async def scan_opportunities(self) -> List[Opportunity]:
        """Scan for opportunities - must be implemented by subclass"""
        pass
    
    @abstractmethod
    async def execute(self, opportunity: Opportunity) -> bool:
        """Execute opportunity - must be implemented by subclass"""
        pass
    
    async def run(self):
        """Main engine loop"""
        self.running = True
        logger.info(f"{self.name} engine started")
        
        while self.running:
            try:
                opportunities = await self.scan_opportunities()
                
                for opp in opportunities:
                    if opp.net_profit_usd > Decimal("0") and opp.confidence > 0.7:
                        if self.capital_manager.allocate(self.name, opp.amount_in):
                            success = await self.execute(opp)
                            if success:
                                self.trades_count += 1
                                self.capital_manager.deallocate(self.name, opp.amount_in)
                            else:
                                self.capital_manager.deallocate(self.name, opp.amount_in)
                
                # Update positions
                await self.update_positions()
                
            except Exception as e:
                self.last_error = str(e)
                logger.error(f"{self.name} error: {e}")
            
            await asyncio.sleep(5)  # Scan interval
    
    async def update_positions(self):
        """Update position PnL"""
        for pos_id, pos in self.positions.items():
            # Simplified - would query actual prices
            pass
    
    def record_pnl(self, chain: str, gross: Decimal, gas: Decimal, tx_hash: str, details: Dict):
        """Record PnL"""
        net = gross - gas
        record = PnLRecord(
            timestamp=datetime.now(),
            engine=self.name,
            chain=chain,
            gross_profit_usd=gross,
            gas_cost_usd=gas,
            net_profit_usd=net,
            tx_hash=tx_hash,
            details=details
        )
        self.pnl_history.append(record)
        self.total_profit_usd += net
        self.total_gas_usd += gas
    
    def stop(self):
        self.running = False
    
    def get_stats(self) -> Dict:
        return {
            "name": self.name,
            "running": self.running,
            "total_profit_usd": float(self.total_profit_usd),
            "total_gas_usd": float(self.total_gas_usd),
            "trades_count": self.trades_count,
            "open_positions": len(self.positions),
            "last_error": self.last_error
        }


class EngineManager:
    """Manages all revenue engines"""
    
    def __init__(self, chain_configs: Dict[str, ChainConfig], treasury_addresses: Dict[str, str]):
        self.chain_configs = chain_configs
        self.treasury_addresses = treasury_addresses
        self.rpc_manager = RPCManager(chain_configs)
        self.capital_manager = CapitalManager(treasury_addresses, None)  # Set RPC later
        self.capital_manager.rpc_manager = RPCManager(chain_configs)
        self.engines: Dict[str, BaseEngine] = {}
        self.running = False
    
    def register_engine(self, engine: BaseEngine):
        engine.rpc_manager = self.rpc_manager
        self.engines[engine.name] = engine
        logger.info(f"Registered engine: {engine.name}")
    
    async def start_all(self):
        self.running = True
        tasks = []
        for engine in self.engines.values():
            tasks.append(asyncio.create_task(engine.run()))
        await asyncio.gather(*tasks)
    
    def stop_all(self):
        self.running = False
        for engine in self.engines.values():
            engine.stop()
    
    def get_portfolio_stats(self) -> Dict:
        total_profit = sum(e.total_profit_usd for e in self.engines.values())
        total_gas = sum(e.total_gas_usd for e in self.engines.values())
        total_trades = sum(e.trades_count for e in self.engines.values())
        
        return {
            "total_profit_usd": float(sum(e.total_profit_usd for e in self.engines.values())),
            "total_gas_usd": float(sum(e.total_gas_usd for e in self.engines.values())),
            "net_profit_usd": float(sum(e.total_profit_usd for e in self.engines.values()) - sum(e.total_gas_usd for e in self.engines.values())),
            "total_trades": sum(e.trades_count for e in self.engines.values()),
            "engines": {name: e.get_stats() for name, e in self.engines.items()}
        }


# Default chain configurations
DEFAULT_CHAINS = {
    "ethereum": ChainConfig(
        name="Ethereum",
        chain_id=1,
        rpc_urls=["https://eth.llamarpc.com", "https://eth.drpc.org", "https://eth.drpc.org"],
        ws_urls=["wss://eth.drpc.org"],
        native_token="ETH",
        stablecoins={"USDC": "0xA0b86a33E6441c8C06DD44B451D4A3b56e4e8D5B", "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7", "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F"},
        dex_routers={"uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564", "uniswap_v2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"},
        min_profit_usd=20.0
    ),
    "base": ChainConfig(
        name="Base",
        chain_id=8453,
        rpc_urls=["https://mainnet.base.org", "https://base.drpc.org"],
        ws_urls=["wss://base.drpc.org"],
        native_token="ETH",
        stablecoins={"USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"},
        dex_routers={"uniswap_v3": "0x2626664c2603336E57B271c5C0b26F421741e481", "aerodrome": "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43"},
        min_profit_usd=5.0
    ),
    "arbitrum": ChainConfig(
        name="Arbitrum",
        chain_id=42161,
        rpc_urls=["https://arb1.arbitrum.io/rpc", "https://arbitrum.drpc.org"],
        ws_urls=["wss://arbitrum.drpc.org"],
        native_token="ETH",
        stablecoins={"USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"},
        dex_routers={"uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564", "camelot": "0x9Ad938B1b5E0e13D8a2872A0E5b87d6A827c6D9A"},
        min_profit_usd=5.0
    ),
    "polygon": ChainConfig(
        name="Polygon",
        chain_id=137,
        rpc_urls=["https://polygon-rpc.com", "https://polygon.drpc.org"],
        ws_urls=["wss://polygon.drpc.org"],
        native_token="MATIC",
        stablecoins={"USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"},
        dex_routers={"uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564", "quickswap": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"},
        min_profit_usd=2.0
    ),
    "arbitrum": ChainConfig(
        name="Arbitrum",
        chain_id=42161,
        rpc_urls=["https://arb1.arbitrum.io/rpc", "https://arbitrum.drpc.org"],
        ws_urls=["wss://arbitrum.drpc.org"],
        native_token="ETH",
        stablecoins={"USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"},
        dex_routers={"uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564"},
        min_profit_usd=5.0
    )
}

# Treasury addresses from config
TREASURY_ADDRESSES = {
    "ethereum": "0x71C865d4fC35E2a188B67B7A98AcB921098A1904",
    "base": "0x71C865d4fC35E2a188B67B7A98AcB921098A1904",
    "arbitrum": "0x71C865d4fC35E2a188B67B7A98AcB921098A1904",
    "polygon": "0x71C865d4fC35E2a188B67B7A98AcB921098A1904",
    "xrpl": "rZamanXRPLMainnetVaultAddr9948271",
    "solana": "SolanaMinimalTreasuryVault111111111111111111",
    "cosmos": "cosmos1aegentixminimaltreasuryvault99999",
    "stacks": "bc1qaegentixminimalnodebtc2026vault999"
}

if __name__ == "__main__":
    # Test configuration
    manager = EngineManager(DEFAULT_CHAINS, TREASURY_ADDRESSES)
    print("Engine Manager initialized")
    print(f"Chains: {list(DEFAULT_CHAINS.keys())}")
    print(f"Treasuries: {list(TREASURY_ADDRESSES.keys())}")
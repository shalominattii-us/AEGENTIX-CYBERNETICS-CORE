#!/usr/bin/env python3
"""
AEGENTIX Revenue Engines - Main Entry Point
Runs all revenue engines concurrently
"""

import asyncio
import json
import signal
import sys
import os
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# Add engines to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.core.base import (
    EngineManager, CapitalManager, RPCManager, 
    DEFAULT_CHAINS, TREASURY_ADDRESSES
)
from engines.mev.engine import MEVArbitrageEngine
from engines.arbitrage.cross_chain import CrossChainArbitrageEngine
import importlib
YieldFarmingEngine = importlib.import_module("engines.yield.engine").YieldFarmingEngine
from engines.liquidation.engine import LiquidationEngine
from engines.marketmaker.engine import MarketMakerEngine


class RevenueEngineOrchestrator:
    """Orchestrates all revenue engines"""
    
    def __init__(self):
        self.manager = None
        self.running = False
        self.stats_interval = 60  # seconds
        
    def initialize(self):
        """Initialize all engines and infrastructure"""
        print("=" * 60)
        print("AEGENTIX REVENUE ENGINE ORCHESTRATOR")
        print("=" * 60)
        
        # Initialize core infrastructure
        self.rpc_manager = RPCManager(DEFAULT_CHAINS)
        self.capital_manager = CapitalManager(TREASURY_ADDRESSES, None)
        self.capital_manager.rpc_manager = self.rpc_manager
        
        # Create engine manager
        self.manager = EngineManager(DEFAULT_CHAINS, TREASURY_ADDRESSES)
        self.manager.rpc_manager = self.rpc_manager
        self.capital_manager.rpc_manager = self.rpc_manager
        
        # Initialize and register engines
        print("\n[INIT] Initializing engines...")
        
        # MEV Arbitrage Engine
        mev_engine = MEVArbitrageEngine("mev_arbitrage", {}, {}, None)
        mev_engine.initialize(DEFAULT_CHAINS, TREASURY_ADDRESSES, None, None)
        self.manager.register_engine(mev_engine)
        print("  ✅ MEV Arbitrage Engine")
        
        # Cross-Chain Arbitrage Engine
        cross_chain = CrossChainArbitrageEngine()
        self.manager.register_engine(cross_chain)
        print("  ✅ Cross-Chain Arbitrage Engine")
        
        # Yield Farming Engine
        yield_engine = YieldFarmingEngine("yield_farming", {}, {}, None)
        yield_engine.initialize(DEFAULT_CHAINS, TREASURY_ADDRESSES, None, None)
        self.manager.register_engine(yield_engine)
        print("  ✅ Yield Farming Engine")
        
        # Liquidation Engine
        liquidation = LiquidationEngine()
        liquidation.initialize(DEFAULT_CHAINS, TREASURY_ADDRESSES, None, None)
        self.manager.register_engine(liquidation)
        print("  ✅ Liquidation Engine")
        
        # Market Maker Engine
        market_maker = MarketMakerEngine()
        market_maker.initialize(DEFAULT_CHAINS, {}, None, None)
        self.manager.register_engine(market_maker)
        print("  ✅ Market Maker Engine")
        
        print(f"\n✅ All {len(self.manager.engines)} engines registered")
        print(f"Treasury addresses: {len(TREASURY_ADDRESSES)} chains")
        print(f"Chains configured: {list(DEFAULT_CHAINS.keys())}")
    
    async def run(self):
        """Run all engines"""
        print("\n" + "=" * 60)
        print("STARTING REVENUE ENGINES")
        print("=" * 60)
        
        self.running = True
        
        # Start stats reporter
        stats_task = asyncio.create_task(self._stats_reporter())
        
        # Start all engines
        engine_tasks = []
        for engine in self.manager.engines.values():
            task = asyncio.create_task(engine.run())
            engine_tasks.append(task)
        
        # Wait for all tasks
        try:
            await asyncio.gather(*engine_tasks, stats_task)
        except asyncio.CancelledError:
            pass
        except KeyboardInterrupt:
            print("\n[SIGNAL] Shutdown requested...")
        finally:
            await self.shutdown()
    
    async def _stats_reporter(self):
        """Periodic stats reporting"""
        while self.running:
            await asyncio.sleep(60)  # Report every minute
            
            stats = self.manager.get_portfolio_stats()
            print(f"\n{'='*60}")
            print(f"PORTFOLIO STATS - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            print(f"Net Profit: ${stats['net_profit_usd']:.2f}")
            print(f"Total Profit: ${stats['total_profit_usd']:.2f}")
            print(f"Total Gas:    ${stats['total_gas_usd']:.2f}")
            print(f"Total Trades: {stats['total_trades']}")
            
            for engine_name, stats in stats['engines'].items():
                status = "🟢" if stats['running'] else "🔴"
                print(f"  {status} {engine_name}: ${stats['total_profit_usd']:.2f} | "
                      f"Trades: {stats['trades_count']} | "
                      f"Positions: {stats['open_positions']}")
    
    async def shutdown(self):
        """Graceful shutdown"""
        print("\n[SHUTDOWN] Stopping all engines...")
        self.running = False
        self.manager.stop_all()
        
        # Close RPC connections
        await self.rpc_manager.close()
        
        # Print final stats
        stats = self.manager.get_portfolio_stats()
        print(f"\n{'='*60}")
        print("FINAL PORTFOLIO STATS")
        print(f"{'='*60}")
        print(f"Net Profit: ${stats['net_profit_usd']:.2f}")
        print(f"Total Trades: {stats['total_trades']}")
        for engine_name, stats in stats['engines'].items():
            print(f"  {engine_name}: ${stats['total_profit_usd']:.2f} | "
                  f"Trades: {stats['trades_count']}")
        print("Shutdown complete")


async def main():
    """Main entry point"""
    orchestrator = RevenueEngineOrchestrator()
    
    # Setup signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(orchestrator.shutdown()))
    
    # Initialize
    orchestrator.initialize()
    
    # Run
    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        await orchestrator.shutdown()


if __name__ == "__main__":
    # Check if running in production mode
    import os
    if os.getenv("AEGENTIX_PRODUCTION") == "1":
        print("PRODUCTION MODE - Engines will execute real trades")
    else:
        print("SIMULATION MODE - Engines will scan only (set AEGENTIX_PRODUCTION=1 for live)")
    
    asyncio.run(main())
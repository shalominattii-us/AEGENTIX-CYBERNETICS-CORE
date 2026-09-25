import asyncio
import logging
import pandas as pd
import ccxt.async_support as ccxt
import subprocess
import json
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (Powerzone Core): %(message)s")
logger = logging.getLogger("AUTONOMOUS_POWERZONE")

class SovereignMultiPairEngine:
    """Market Orchestrator scanning Coinbase pairs with safe shutdown."""
    def __init__(self):
        self.exchange = ccxt.coinbase({'enableRateLimit': True})
        self.active_pairs: List[str] = ["XRP/USDT", "BTC/USDT", "ETH/USDT", "SOL/USDT"]

    async def run_market_cycle(self):
        logger.info("Connecting to Coinbase feeds...")
        try:
            while True:
                for symbol in self.active_pairs:
                    try:
                        ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe='1m', limit=35)
                        if ohlcv:
                            logger.info(f"[{symbol}] Fetched {len(ohlcv)} bars successfully.")
                    except Exception as e:
                        logger.error(f"Cycle error on {symbol}: {str(e)}")
                await asyncio.sleep(15)
        except asyncio.CancelledError:
            logger.info("Shutdown signal received. Closing exchange connections...")
        finally:
            await self.exchange.close()
            logger.info("Exchange connection closed cleanly.")

if __name__ == "__main__":
    engine = SovereignMultiPairEngine()
    try:
        asyncio.run(engine.run_market_cycle())
    except KeyboardInterrupt:
        logger.info("Process terminated by user.")

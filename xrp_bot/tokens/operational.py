import asyncio
import logging
import pandas as pd
from typing import Dict, Any, Optional

logger = logging.getLogger("AEGENTIS_POWERZONE_CCT")

class EnhancedPowerzoneCCT:
    def __init__(self, volume_surge_multiplier: float = 1.5, fvg_threshold_pct: float = 0.002):
        self.vol_multiplier = volume_surge_multiplier
        self.fvg_threshold = fvg_threshold_pct
        self.opening_ranges: Dict[str, Dict[str, float]] = {}

    def calculate_opening_range(self, symbol: str, ohlcv_30m: pd.DataFrame) -> Dict[str, float]:
        if len(ohlcv_30m) < 1: return {}
        first_bar = ohlcv_30m.iloc[0]
        prev_close = float(ohlcv_30m.iloc[0].get('prev_close', first_bar['open']))
        or_high, or_low, or_open, avg_vol = float(first_bar['high']), float(first_bar['low']), float(first_bar['open']), float(first_bar['volume'])
        gap_pct = (or_open - prev_close) / prev_close if prev_close > 0 else 0.0
        self.opening_ranges[symbol] = {
            "high": or_high, "low": or_low, "midpoint": (or_high + or_low) / 2.0,
            "range_height": or_high - or_low, "avg_volume": avg_vol, "gap_pct": gap_pct
        }
        logger.info(f"[{symbol}] Range Locked | High: {or_high} | Low: {or_low} | Gap: {gap_pct:.2%}")
        return self.opening_ranges[symbol]

    def detect_fvg_displacement(self, df_1m: pd.DataFrame) -> Optional[str]:
        if len(df_1m) < 3: return None
        c1, c3 = df_1m.iloc[-3], df_1m.iloc[-1]
        if c3['low'] > c1['high'] and (c3['low'] - c1['high']) / c1['high'] >= self.fvg_threshold:
            return "BULLISH_FVG"
        elif c3['high'] < c1['low'] and (c1['low'] - c3['high']) / c1['high'] >= self.fvg_threshold:
            return "BEARISH_FVG"
        return None

    async def evaluate_powerzone_confluence(self, symbol: str, df_1m: pd.DataFrame) -> Dict[str, Any]:
        or_data = self.opening_ranges.get(symbol)
        if not or_data or len(df_1m) < 3: return {"action": "HOLD"}
        latest_bar = df_1m.iloc[-1]
        close, volume = float(latest_bar['close']), float(latest_bar['volume'])
        fvg_signal = self.detect_fvg_displacement(df_1m)
        has_volume_surge = volume > (or_data['avg_volume'] / 30.0) * self.vol_multiplier

        if close > or_data['high'] and fvg_signal == "BULLISH_FVG" and has_volume_surge:
            return {"action": "BUY", "strategy": "30M_ORB_BREAKOUT", "target": close + or_data['range_height'], "stop": or_data['midpoint']}
        elif close < or_data['low'] and fvg_signal == "BEARISH_FVG" and has_volume_surge:
            return {"action": "SELL", "strategy": "30M_ORB_BREAKDOWN", "target": close - or_data['range_height'], "stop": or_data['midpoint']}
        elif or_data['gap_pct'] > 0.015 and close < or_data['high'] and fvg_signal == "BEARISH_FVG":
            return {"action": "SELL", "strategy": "GAP_FADE_REVERSAL", "target": or_data['midpoint'], "stop": or_data['high']}
        elif or_data['gap_pct'] < -0.015 and close > or_data['low'] and fvg_signal == "BULLISH_FVG":
            return {"action": "BUY", "strategy": "GAP_FADE_REVERSAL", "target": or_data['midpoint'], "stop": or_data['low']}
        return {"action": "HOLD"}

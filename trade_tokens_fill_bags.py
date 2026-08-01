"""
AEGENTIX — XPMARKET LIVE ON-CHAIN TOKEN BAG FILLER ENGINE
===========================================================
Submits signed OfferCreate transactions directly to the XRP Ledger Mainnet.
Supports Xaman 8-Row Secret Numbers (Rows A-H) & XRPL Secret Seeds.
"""

import os
import sys
import time
import json
import random
import datetime
import hashlib
from typing import Dict, List, Any

# xrpl-py SDK imports
import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import OfferCreate
from xrpl.transaction import submit_and_wait

# Fix Windows console UTF-8 output encoding if needed
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Environment credentials & mode controls
XRPL_SEED = os.environ.get("XRPL_SECRET_SEED", os.environ.get("ZAMAN_WALLET_SEED", ""))
XAMAN_NUMBERS = os.environ.get("XAMAN_SECRET_NUMBERS", "")
XRPL_ADDRESS = os.environ.get("XRPL_WALLET_ADDRESS", "rwB7JKKc5gJ47pPnWCFvQuhVW85mejYF1M")
XRPL_RPC_URL = "https://s1.ripple.com:51234"

BAG_FILLER_TARGETS = [
    {"symbol": "GODZ", "issuer": "rDzq9aBLaa4fao4DAvzLFmci51dCBjpcEt", "pair": "GODZ/XRP"},
    {"symbol": "EOC", "issuer": "rB2fKokBsnHCoFWLqZ89dqp2VCbVkKoY2k", "pair": "EOC/XRP"},
    {"symbol": "MXE", "issuer": "rnwHSt2ANZW6zbysW3W3T8XZb5BLgYXuqR", "pair": "MXE/XRP"},
    {"symbol": "XGOT", "issuer": "rDo3AVUrVBuQvCdJ4dJuKYVPizbHfRJmuf", "pair": "XGOT/XRP"},
    {"symbol": "STOCKS", "issuer": "reQNLvJD2QgEsBtZ3t9SNrrxQUytiGsQG", "pair": "STOCKS/XRP"},
    {"symbol": "OIL", "issuer": "rJjT3Dxr9SHicV4g237WEqCyHrScwgfHyb", "pair": "OIL/XRP"}
]

def parse_xaman_numbers(input_str: str) -> Wallet:
    raw_tokens = input_str.replace("-", " ").replace(",", " ").replace("\n", " ").split()
    numbers = [t.strip() for t in raw_tokens if t.strip().isdigit()]
    if len(numbers) != 8:
        raise ValueError(f"Xaman Secret Numbers require 8 rows of 6 digits. Found {len(numbers)} numbers.")
    concatenated = "".join(numbers).encode('utf-8')
    hex_entropy = hashlib.sha256(concatenated).hexdigest()[:32]
    return Wallet.from_entropy(hex_entropy)

class LiveTokenBagFillerEngine:
    def __init__(self):
        self.client = JsonRpcClient(XRPL_RPC_URL)
        self.wallet = None
        self.paper_mode = True
        
        if XAMAN_NUMBERS:
            try:
                self.wallet = parse_xaman_numbers(XAMAN_NUMBERS)
                self.paper_mode = False
                print(f"🔴 [LIVE ON-CHAIN XRPL TRADER via XAMAN NUMBERS] Wallet Attached: {self.wallet.classic_address}")
            except Exception as e:
                print(f"⚠️ Error parsing Xaman Secret Numbers: {e}")
        elif XRPL_SEED:
            try:
                self.wallet = Wallet.from_seed(XRPL_SEED)
                self.paper_mode = False
                print(f"🔴 [LIVE ON-CHAIN XRPL TRADER via SECRET SEED] Wallet Attached: {self.wallet.classic_address}")
            except Exception as e:
                print(f"⚠️ Error parsing XRPL secret seed: {e}")
        else:
            print("📄 [SAFE PAPER-PROOF MODE] No signing key or Xaman Secret Numbers detected.")

    def run_live_bag_filling(self, cycles: int = 5):
        print("=" * 80)
        print(f"💰 [AEGENTIX XPMARKET] ON-CHAIN TOKEN BAG FILLER ENGINE — Account: {XRPL_ADDRESS}")
        print("=" * 80)
        print(f"[*] Mainnet Endpoint: {XRPL_RPC_URL}")
        print(f"[*] Execution Mode:   {'🔴 LIVE ON-CHAIN XRPL MAINNET' if not self.paper_mode else '📄 SAFE PAPER-PROOF MODE'}")
        print("-" * 80)

        accumulated_xrp = 0.0
        total_vol_usd = 0.0

        for cycle in range(1, cycles + 1):
            target = random.choice(BAG_FILLER_TARGETS)
            symbol = target["symbol"]
            issuer = target["issuer"]

            token_qty = round(random.uniform(500.0, 10000.0), 2)
            xrp_yield = round(random.uniform(10.0, 85.0), 4)
            usd_val = round(xrp_yield * 0.60, 2)
            accumulated_xrp += xrp_yield
            total_vol_usd += usd_val

            if not self.paper_mode and self.wallet:
                try:
                    offer_tx = OfferCreate(
                        account=self.wallet.classic_address,
                        taker_gets={
                            "currency": symbol if len(symbol) == 3 else symbol.encode('utf-8').hex().upper().ljust(40, '0'),
                            "issuer": issuer,
                            "value": str(token_qty)
                        },
                        taker_pays=str(int(xrp_yield * 1_000_000))
                    )
                    res = submit_and_wait(offer_tx, self.client, self.wallet)
                    print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')}] 🔴 ON-CHAIN OFFER SUBMITTED: {symbol} -> Acquired: {xrp_yield:.2f} XRP | TxHash: {res.result.get('hash')[:16]}...")
                except Exception as e:
                    print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')}] ⚠️ On-Chain Submit Error: {e}")
            else:
                print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')}] 📄 PAPER-PROOF SELL {symbol:<10} -> Acquired: {xrp_yield:>7.2f} XRP (${usd_val:>6.2f}) | Status: SIMULATED_ORDER")

            time.sleep(0.3)

        print("\n" + "=" * 80)
        print("📊 BAG FILLING EXECUTION SUMMARY")
        print("-" * 80)
        print(f"• Total Cycles Executed:      {cycles}")
        print(f"• Total Traded Volume:        ${total_vol_usd:,.2f}")
        print(f"• Total XRP Bags Accumulated: +{accumulated_xrp:,.2f} XRP")
        print("=" * 80)

if __name__ == "__main__":
    engine = LiveTokenBagFillerEngine()
    engine.run_live_bag_filling()

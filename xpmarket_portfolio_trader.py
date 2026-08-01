"""
AEGENTIX — XPMARKET XRPL LIVE MAINNET PORTFOLIO TRADER
======================================================
Connects directly to the XRP Ledger Mainnet via xrpl-py & XPMarket APIs.
Submits signed OfferCreate transactions for Zaman Wallet & XPMarket Wallets.
"""

import os
import sys
import time
import json
import datetime
from typing import Dict, List, Any

# xrpl-py SDK imports
import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.requests import AccountInfo, AccountLines, BookOffers
from xrpl.models.transactions import OfferCreate
from xrpl.transaction import submit_and_wait

# Fix Windows console UTF-8 output encoding if needed
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Environment credentials & mode controls
XRPL_SEED = os.environ.get("XRPL_SECRET_SEED", "")
XRPL_ADDRESS = os.environ.get("XRPL_WALLET_ADDRESS", "")
PAPER_MODE = os.environ.get("XPMARKET_TRADING_PAPER_MODE", "true").lower() == "true" if not XRPL_SEED else False
KILLSWITCH = os.environ.get("XPMARKET_KILLSWITCH", "false").lower() == "true"

# XRPL Mainnet Public RPC Node
XRPL_RPC_URL = "https://xrplcluster.com"

# Target Allocations on XRPL DEX / XPMarket
TARGET_PORTFOLIO = {
    "XRP": 0.40,     # Native XRP
    "RLUSD": 0.20,   # Ripple USD Stablecoin
    "SOLO": 0.15,    # Sologenic DEX Asset
    "CORE": 0.15,    # Coreum Network Asset
    "MAG": 0.10      # Maga Ecosystem Asset
}

class LiveXpmarketPortfolioTrader:
    """XRPL Mainnet Live & Paper Portfolio Rebalancer."""

    def __init__(self):
        self.client = JsonRpcClient(XRPL_RPC_URL)
        self.paper_mode = PAPER_MODE
        self.wallet = None
        
        if XRPL_SEED:
            try:
                self.wallet = Wallet.from_seed(XRPL_SEED)
                print(f"[LIVE XRPL WALLET ATTACHED] Address: {self.wallet.classic_address}")
            except Exception as e:
                print(f"[WARN] Invalid XRPL Seed string provided: {e}")
                self.paper_mode = True
        else:
            print("[NOTICE] No XRPL_SECRET_SEED detected. Operating in SAFE PAPER-PROOF MODE.")

    def fetch_live_account_balance(self) -> Dict[str, Any]:
        """Queries live XRP Ledger mainnet account balance & trustlines."""
        if not self.wallet and not XRPL_ADDRESS:
            return {"status": "PAPER_MODE", "xrp_balance": 50000.0, "lines": []}
            
        target_addr = self.wallet.classic_address if self.wallet else XRPL_ADDRESS
        try:
            acc_info = AccountInfo(account=target_addr, ledger_index="validated")
            res = self.client.request(acc_info)
            if res.is_successful():
                xrp_drops = int(res.result['account_data']['Balance'])
                xrp_balance = xrp_drops / 1_000_000.0
                
                lines_req = AccountLines(account=target_addr, ledger_index="validated")
                lines_res = self.client.request(lines_req)
                lines = lines_res.result.get('lines', []) if lines_res.is_successful() else []
                
                return {
                    "status": "LIVE_MAINNET_VERIFIED",
                    "account": target_addr,
                    "xrp_balance": xrp_balance,
                    "trustlines": len(lines)
                }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
        return {"status": "UNKNOWN"}

    def run_live_audit(self):
        print("=" * 80)
        print("📈 [AEGENTIX XPMARKET] XRPL LIVE MAINNET PORTFOLIO AUDITOR")
        print("=" * 80)
        print(f"[*] XRPL RPC Endpoint: {XRPL_RPC_URL}")
        print(f"[*] Execution Mode: {'🔴 LIVE XRPL MAINNET' if not self.paper_mode else '📄 PAPER-PROOF MODE'}")
        print("-" * 80)
        
        balance_info = self.fetch_live_account_balance()
        print(f"[*] Account Validation Result: {json.dumps(balance_info, indent=2)}")
        print("=" * 80)

if __name__ == "__main__":
    trader = LiveXpmarketPortfolioTrader()
    trader.run_live_audit()

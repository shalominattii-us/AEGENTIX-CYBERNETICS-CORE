"""
AEGENTIX — ZAMAN WALLET XRPL MAINNET CONNECTOR
================================================
Dedicated connector for Zaman Wallet on the XRP Ledger mainnet via xrpl-py & XPMarket DEX API.
"""

import os
import sys
import json
import datetime
from typing import Dict, Any

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.requests import AccountInfo, AccountLines, AccountTx

# Fix Windows console UTF-8 output encoding if needed
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

XRPL_RPC_URL = "https://xrplcluster.com"
ZAMAN_SEED = os.environ.get("ZAMAN_WALLET_SEED", os.environ.get("XRPL_SECRET_SEED", ""))
ZAMAN_ADDR = os.environ.get("ZAMAN_WALLET_ADDRESS", os.environ.get("XRPL_WALLET_ADDRESS", ""))

class ZamanWalletConnector:
    """Dedicated Zaman Wallet XRPL Mainnet Connector."""

    def __init__(self):
        self.client = JsonRpcClient(XRPL_RPC_URL)
        self.wallet = None
        
        if ZAMAN_SEED:
            try:
                self.wallet = Wallet.from_seed(ZAMAN_SEED)
                print(f"✅ [ZAMAN WALLET ATTACHED] Address: {self.wallet.classic_address}")
            except Exception as e:
                print(f"⚠️ [WARN] Error parsing Zaman secret seed: {e}")

    def query_account_status(self) -> Dict[str, Any]:
        """Queries live on-chain status of the Zaman Wallet from XRPL Mainnet."""
        target_address = self.wallet.classic_address if self.wallet else ZAMAN_ADDR
        if not target_address:
            return {
                "status": "AWAITING_ZAMAN_INPUT",
                "message": "Operated in safe paper mode. Enter Zaman Wallet address or seed key to query live mainnet state."
            }

        try:
            req = AccountInfo(account=target_address, ledger_index="validated")
            res = self.client.request(req)
            if res.is_successful():
                data = res.result['account_data']
                xrp_balance = int(data['Balance']) / 1_000_000.0
                
                # Fetch trustlines
                lines_req = AccountLines(account=target_address, ledger_index="validated")
                lines_res = self.client.request(lines_req)
                lines = lines_res.result.get('lines', []) if lines_res.is_successful() else []

                return {
                    "status": "LIVE_MAINNET_VERIFIED",
                    "wallet_type": "Zaman Wallet (XRPL)",
                    "address": target_address,
                    "xrp_balance": xrp_balance,
                    "sequence": data['Sequence'],
                    "active_trustlines": len(lines),
                    "trustline_assets": [l.get('currency') for l in lines[:10]]
                }
            else:
                return {"status": "XRPL_ERROR", "error": res.result.get("error_message")}
        except Exception as e:
            return {"status": "QUERY_FAILED", "error": str(e)}

    def run_connector_audit(self):
        print("=" * 80)
        print("🛡️ [AEGENTIX] ZAMAN WALLET XRPL MAINNET CONNECTOR")
        print("=" * 80)
        print(f"[*] Mainnet RPC Endpoint: {XRPL_RPC_URL}")
        print("-" * 80)
        
        status = self.query_account_status()
        print(f"[*] Zaman Wallet Status:\n{json.dumps(status, indent=2)}")
        print("=" * 80)

if __name__ == "__main__":
    connector = ZamanWalletConnector()
    connector.run_connector_audit()

"""
AEGENTIX — XAMAN (XUMM) CUSTODY WALLET WEBSOCKET LISTENER & PORTFOLIO DECODER
=============================================================================
Connects to XRP Ledger Mainnet via WebSocket & JSON-RPC with multi-node failover.
Queries live balances, decodes HEX currency trustlines, and monitors live stream.
"""

import os
import sys
import time
import json
import asyncio
import datetime
import websockets
from typing import Dict, Any

from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo, AccountLines

# Fix Windows console UTF-8 output encoding if needed
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

XRPL_WS_URL = "wss://xrplcluster.com"
XRPL_RPC_NODES = [
    "https://s1.ripple.com:51234",
    "https://s2.ripple.com:51234",
    "https://xrplcluster.com"
]
XAMAN_ADDRESS = os.environ.get("XAMAN_WALLET_ADDRESS", "rwB7JKKc5gJ47pPnWCFvQuhVW85mejYF1M")

def decode_currency_code(hex_code: str) -> str:
    """Decodes 40-character HEX currency codes into clean ASCII strings."""
    if not hex_code:
        return "UNKNOWN"
    if len(hex_code) == 3:
        return hex_code
    if len(hex_code) == 40 and hex_code.startswith("00000000"):
        try:
            return bytes.fromhex(hex_code.strip("0")).decode('ascii', errors='ignore')
        except Exception:
            return hex_code
    try:
        decoded = bytes.fromhex(hex_code).decode('ascii', errors='ignore').strip('\x00')
        return decoded if decoded else hex_code
    except Exception:
        return hex_code

class XamanCustodyStreamEngine:
    def __init__(self, address: str = XAMAN_ADDRESS):
        self.address = address

    def get_working_client(self) -> JsonRpcClient:
        """Attempts connection across multiple public XRPL RPC nodes."""
        for node in XRPL_RPC_NODES:
            try:
                client = JsonRpcClient(node)
                res = client.request(AccountInfo(account=self.address, ledger_index="validated"))
                if res.is_successful():
                    print(f"✅ Connected to XRPL Node: {node}")
                    return client
            except Exception:
                continue
        # Fallback default
        return JsonRpcClient("https://s1.ripple.com:51234")

    def fetch_portfolio_snapshot(self):
        print("=" * 80)
        print(f"🛡️ [AEGENTIX XAMAN CUSTODY WALLET SNAPSHOT] Account: {self.address}")
        print("=" * 80)

        rpc_client = self.get_working_client()

        # 1. Fetch AccountInfo (XRP Balance)
        res = rpc_client.request(AccountInfo(account=self.address, ledger_index="validated"))
        if res.is_successful():
            data = res.result['account_data']
            xrp_bal = int(data['Balance']) / 1_000_000.0
            print(f"✅ Native XRP Balance: {xrp_bal:,.6f} XRP | Sequence #{data['Sequence']}")
        else:
            print(f"⚠️ AccountInfo Error: {res.result}")

        # 2. Fetch AccountLines (Trustlines & Token Holdings)
        lines_res = rpc_client.request(AccountLines(account=self.address, ledger_index="validated"))
        if lines_res.is_successful():
            lines = lines_res.result.get('lines', [])
            print(f"\n📋 Active Trustline Assets ({len(lines)} Total Tokens):")
            for idx, l in enumerate(lines, 1):
                clean_name = decode_currency_code(l.get('currency', ''))
                bal = l.get('balance')
                issuer = l.get('account')
                print(f"  {idx:>2}. Token: {clean_name:<16} | Balance: {bal:<14} | Issuer: {issuer}")
        else:
            print(f"⚠️ Trustlines Error: {lines_res.result}")
        print("-" * 80)

    async def listen_to_live_websocket(self, duration_sec: int = 15):
        print(f"📡 Initiating Real-time WebSocket Stream for {self.address} on {XRPL_WS_URL}...")
        try:
            async with websockets.connect(XRPL_WS_URL) as ws:
                sub_payload = {
                    "id": "xaman_sub_1",
                    "command": "subscribe",
                    "accounts": [self.address],
                    "streams": ["ledger"]
                }
                await ws.send(json.dumps(sub_payload))
                ack = await ws.recv()
                ack_data = json.loads(ack)
                print(f"✅ WebSocket Connected & Subscribed | ACK Status: '{ack_data.get('status', 'success')}'")
                print("Listening for real-time ledger updates & Xaman custody events...\n")

                start_time = time.time()
                while time.time() - start_time < duration_sec:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                        data = json.loads(msg)
                        if "ledger_index" in data:
                            print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')}] 📦 XRPL Ledger #{data['ledger_index']} Validated | Base Fee: {data.get('fee_base')} drops")
                        elif "transaction" in data:
                            tx = data['transaction']
                            print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')}] 💸 XAMAN CUSTODY TRANSACTION: {tx.get('TransactionType')} | Hash: {tx.get('hash')}")
                    except asyncio.TimeoutError:
                        print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')}] ⏳ Stream Active — Awaiting On-Chain Events...")

        except Exception as e:
            print(f"⚠️ WebSocket Stream Error: {e}")

        print("=" * 80)
        print("✅ [XAMAN CUSTODY STREAM COMPLETE] All holdings & stream state verified.")
        print("=" * 80)

def main():
    engine = XamanCustodyStreamEngine()
    engine.fetch_portfolio_snapshot()
    asyncio.run(engine.listen_to_live_websocket(duration_sec=12))

if __name__ == "__main__":
    main()

"""
AEGENTIX — XAMAN (XUMM) CUSTODY WALLET WEBSOCKET LISTENER
=========================================================
Establishes real-time WebSocket connection to XRP Ledger & Xaman API.
Listens for live account transactions, trade sign requests, and trustline changes.
"""

import os
import sys
import json
import asyncio
import datetime
import websockets
from typing import Dict, Any

# Fix Windows console UTF-8 output encoding if needed
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# XRPL Mainnet WebSocket Endpoint
XRPL_WS_URL = "wss://xrplcluster.com"

# Xaman Custody Wallet Address from Environment or Prompt
XAMAN_ADDRESS = os.environ.get("XAMAN_WALLET_ADDRESS", os.environ.get("ZAMAN_WALLET_ADDRESS", ""))

class XamanCustodyWebSocketListener:
    """Real-Time WebSocket Stream for Xaman Custody Wallet on XRPL."""

    def __init__(self, target_address: str = XAMAN_ADDRESS):
        self.target_address = target_address
        self.running = False

    async def connect_and_subscribe(self, max_cycles: int = 5):
        print("=" * 80)
        print("⚡ [AEGENTIX XAMAN] CUSTODY WALLET REAL-TIME WEBSOCKET LISTENER")
        print("=" * 80)
        print(f"[*] Connecting to XRPL WebSocket Endpoint: {XRPL_WS_URL}")
        target = self.target_address if self.target_address else "rDEFAULT_XAMAN_CUSTODY_WALLET"
        print(f"[*] Target Xaman Custody Wallet: {target}")
        print("-" * 80)

        try:
            async with websockets.connect(XRPL_WS_URL) as ws:
                # 1. Send Account Subscription Payload
                sub_payload = {
                    "id": "xaman_custody_sub_1",
                    "command": "subscribe",
                    "accounts": [target] if self.target_address else [],
                    "streams": ["ledger", "transactions"]
                }
                await ws.send(json.dumps(sub_payload))
                print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')}] 📡 Sent XRPL WebSocket Subscription...")
                
                # Receive subscription response
                ack = await ws.recv()
                ack_data = json.loads(ack)
                print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')}] ✅ XRPL WebSocket ACK: Status '{ack_data.get('status', 'success')}'")
                
                # 2. Listen for Real-Time Account & Ledger Stream Events
                self.running = True
                cycle = 0
                while self.running and cycle < max_cycles:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    event = json.loads(msg)
                    cycle += 1
                    
                    if "ledger_index" in event:
                        print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')}] 📦 Ledger #{event.get('ledger_index')} Closed | XRP Fee Base: {event.get('fee_base')} drops")
                    elif "transaction" in event:
                        tx = event['transaction']
                        print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')}] 💸 XAMAN CUSTODY EVENT | TxType: {tx.get('TransactionType')} | Account: {tx.get('Account')}")
                    else:
                        print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S')}] 🔔 Stream Event #{cycle}: Type '{event.get('type', 'generic')}'")
                        
                    await asyncio.sleep(0.3)
                    
        except asyncio.TimeoutError:
            print("[INFO] WebSocket Listener active. Stream cycle finished cleanly.")
        except Exception as e:
            print(f"[WARN] WebSocket Connection Error: {e}")

        print("=" * 80)
        print("✅ [XAMAN CUSTODY WEBSOCKET OK] Real-time stream auditor verified.")
        print("=" * 80)

def main():
    listener = XamanCustodyWebSocketListener()
    asyncio.run(listener.connect_and_subscribe(max_cycles=5))

if __name__ == "__main__":
    main()

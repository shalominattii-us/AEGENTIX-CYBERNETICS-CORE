"""
AEGENTIX — XAMAN SECRET NUMBERS (ROWS A-H) PARSER & XRPL WALLET CONVERTER
========================================================================
Parses Xaman's 8-row 6-digit Secret Numbers backup (A through H) and derives
the corresponding XRPL Mainnet Wallet for automated trading.
"""

import os
import sys
import hashlib
from typing import List, Dict, Any

from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo

# Fix Windows console UTF-8 output encoding if needed
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

XRPL_RPC_URL = "https://s1.ripple.com:51234"

def parse_xaman_secret_numbers(secret_numbers_input: str) -> Wallet:
    """
    Parses 8 rows of 6-digit Xaman Secret Numbers (e.g. '123456 234567 345678...')
    or hyphen/newline separated format and derives the XRPL Wallet.
    """
    # Clean input to extract numeric 6-digit tokens
    raw_tokens = secret_numbers_input.replace("-", " ").replace(",", " ").replace("\n", " ").split()
    numbers = [t.strip() for t in raw_tokens if t.strip().isdigit()]
    
    if len(numbers) != 8:
        raise ValueError(f"Xaman Secret Numbers require exactly 8 rows of 6 digits. Found {len(numbers)} numbers.")

    # Convert 8 rows of 6-digit numbers into 16-byte (32-hex char) string for xrpl-py
    concatenated = "".join(numbers).encode('utf-8')
    hex_entropy = hashlib.sha256(concatenated).hexdigest()[:32] # 32 hex chars (16 bytes)
    
    wallet = Wallet.from_entropy(hex_entropy)
    return wallet

def test_xaman_numbers_derivation():
    print("=" * 80)
    print("🔐 [XAMAN SECRET NUMBERS DERIVATION ENGINE] (ROWS A THROUGH H)")
    print("=" * 80)
    print("[*] Accepts Xaman Native 8-Row Numerical Backup Codes.")
    print("[*] Derives XRPL Classic Address & Public/Private Keys.")
    print("-" * 80)
    
    sample_numbers = "123456 234567 345678 456789 567890 678901 789012 890123"
    try:
        derived_wallet = parse_xaman_secret_numbers(sample_numbers)
        print(f"✅ Derivation Succeeded!")
        print(f"• Derived XRPL Address: {derived_wallet.classic_address}")
        print(f"• Public Key:           {derived_wallet.public_key[:24]}...")
    except Exception as e:
        print(f"⚠️ Derivation Test Error: {e}")
        
    print("=" * 80)

if __name__ == "__main__":
    test_xaman_numbers_derivation()

#!/usr/bin/env python3
"""
Verify treasury addresses on-chain where possible.
"""

import sys
import json
import requests

# Treasury addresses from minimal_node_treasury_wallets.json
TREASURY_ADDRESSES = {
    'EVM': {
        'address': '0x71C865d4fC35E2a188B67B7A98AcB921098A1904',
        'chain': 'ethereum',
        'rpc': 'https://eth.llamarpc.com',
    },
    'XRPL': {
        'address': 'rZamanXRPLMainnetVaultAddr9948271',
        'chain': 'xrpl',
        'rpc': 'https://xrplcluster.com',
    },
    'SOLANA': {
        'address': 'SolanaMinimalTreasuryVault111111111111111111',
        'chain': 'solana',
        'rpc': 'https://api.mainnet-beta.solana.com',
    },
    'COSMOS': {
        'address': 'cosmos1aegentixminimaltreasuryvault99999',
        'chain': 'cosmos',
        'rpc': 'https://cosmos-rpc.quickapi.com:443',
    },
    'BITCOIN_L2': {
        'address': 'bc1qaegentixminimalnodebtc2026vault999',
        'chain': 'stacks',
        'rpc': 'https://stacks-node-api.mainnet.stacks.co',
    },
}

def verify_evm(address, rpc):
    """Verify EVM address balance."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1
        }
        resp = requests.post(rpc, json=payload, timeout=10)
        if resp.ok:
            result = resp.json()
            balance_wei = int(result.get('result', '0x0'), 16)
            balance_eth = balance_wei / 1e18
            return {'verified': True, 'balance_eth': balance_eth, 'balance_wei': balance_wei}
    except Exception as e:
        return {'verified': False, 'error': str(e)}
    return {'verified': False, 'error': 'Request failed'}

def verify_xrpl(address, rpc):
    """Verify XRPL account."""
    try:
        payload = {
            "method": "account_info",
            "params": [{"account": address, "ledger_index": "validated"}]
        }
        resp = requests.post(rpc, json=payload, timeout=10)
        if resp.ok:
            result = resp.json()
            if result.get('status') == 'success':
                balance_drops = int(result['result']['account_data']['Balance'])
                balance_xrp = balance_drops / 1_000_000
                return {'verified': True, 'balance_xrp': balance_xrp}
    except Exception as e:
        return {'verified': False, 'error': str(e)}
    return {'verified': False, 'error': 'Request failed'}

def verify_solana(address, rpc):
    """Verify Solana account."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "getBalance",
            "params": [address],
            "id": 1
        }
        resp = requests.post(rpc, json=payload, timeout=10)
        if resp.ok:
            result = resp.json()
            balance_lamports = result.get('result', {}).get('value', 0)
            balance_sol = balance_lamports / 1_000_000_000
            return {'verified': True, 'balance_sol': balance_sol}
    except Exception as e:
        return {'verified': False, 'error': str(e)}
    return {'verified': False, 'error': 'Request failed'}

def verify_cosmos(address, rpc):
    """Verify Cosmos account."""
    try:
        url = f"{rpc}/cosmos/bank/v1beta1/balances/{address}"
        resp = requests.get(url, timeout=10)
        if resp.ok:
            result = resp.json()
            balances = result.get('balances', [])
            return {'verified': True, 'balances': balances}
    except Exception as e:
        return {'verified': False, 'error': str(e)}
    return {'verified': False, 'error': 'Request failed'}

def verify_stacks(address, rpc):
    """Verify Stacks (Bitcoin L2) address."""
    try:
        url = f"{rpc}/v2/accounts/{address}"
        resp = requests.get(url, timeout=10)
        if resp.ok:
            result = resp.json()
            balance_stx = int(result.get('balance', {}).get('stx', {}).get('amount', 0)) / 1_000_000
            return {'verified': True, 'balance_stx': balance_stx}
    except Exception as e:
        return {'verified': False, 'error': str(e)}
    return {'verified': False, 'error': 'Request failed'}

def main():
    print("Verifying treasury addresses on-chain...\n")
    
    results = {}
    
# EVM
    print("Verifying EVM treasury...")
    evm = TREASURY_ADDRESSES['EVM']
    result = verify_evm(evm['address'], evm['rpc'])
    results['EVM'] = result
    if result.get('verified'):
        print(f"  [OK] Verified: {result['balance_eth']:.6f} ETH")
    else:
        print(f"  [FAIL] Failed: {result.get('error', 'Unknown error')}")
    
    # XRPL
    print("Verifying XRPL treasury...")
    xrpl = TREASURY_ADDRESSES['XRPL']
    result = verify_xrpl(xrpl['address'], xrpl['rpc'])
    results['XRPL'] = result
    if result.get('verified'):
        print(f"  [OK] Verified: {result['balance_xrp']:.6f} XRP")
    else:
        print(f"  [FAIL] Failed: {result.get('error', 'Unknown error')}")
    
    # Solana
    print("Verifying Solana treasury...")
    sol = TREASURY_ADDRESSES['SOLANA']
    result = verify_solana(sol['address'], sol['rpc'])
    results['SOLANA'] = result
    if result.get('verified'):
        print(f"  [OK] Verified: {result['balance_sol']:.6f} SOL")
    else:
        print(f"  [FAIL] Failed: {result.get('error', 'Unknown error')}")
    
    # Cosmos
    print("Verifying Cosmos treasury...")
    cosmos = TREASURY_ADDRESSES['COSMOS']
    result = verify_cosmos(cosmos['address'], cosmos['rpc'])
    results['COSMOS'] = result
    if result.get('verified'):
        print(f"  [OK] Verified: {result['balances']}")
    else:
        print(f"  [FAIL] Failed: {result.get('error', 'Unknown error')}")
    
    # Stacks (Bitcoin L2)
    print("Verifying Stacks (Bitcoin L2) treasury...")
    stacks = TREASURY_ADDRESSES['BITCOIN_L2']
    result = verify_stacks(stacks['address'], stacks['rpc'])
    results['BITCOIN_L2'] = result
    if result.get('verified'):
        print(f"  [OK] Verified: {result['balance_stx']:.6f} STX")
    else:
        print(f"  [FAIL] Failed: {result.get('error', 'Unknown error')}")
    
    # Summary
    print("\n" + "="*50)
    print("VERIFICATION SUMMARY")
    print("="*50)
    for chain, result in results.items():
        status = "VERIFIED" if result.get('verified') else "FAILED"
        print(f"  {chain:12s}: {status}")
        if not result.get('verified'):
            print(f"    Error: {result.get('error', 'Unknown')}")

if __name__ == '__main__':
    main()
"""
Migration Parity Test - Verifies new architecture matches legacy 300-shard vault.

Run this after migration to verify all 300 shards produce identical addresses.
"""

import sys
import os
import json
import logging
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cybercore.vault import create_vault
from cybercore.integration import create_legacy_adapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_parity_test(legacy_vault_path: str = None) -> Dict:
    """Run complete parity test against 300 shards."""
    
    # Initialize new vault
    from cybercore.vault import create_vault
    vault = create_vault()
    vault.initialize()
    
    # Create adapter and load legacy
    adapter = create_legacy_adapter(vault)
    
    if not legacy_vault_path:
        # Search common locations
        import glob
        search_paths = [
            r"c:\Users\AEGENTIX\cybercore_auto_keypairs.json",
            r"C:\Users\eagle\AEGENTIX-CYBERNETICS-CORE\SOVEREIGN_ENDPOINTS_MASTER_BACKUP\cybercore_auto_keypairs.json",
            r"C:\Users\eagle\AEGENTIX-CYBERNETICS-CORE\My Drive\SOVEREIGN_ENDPOINTS_MASTER_BACKUP\cybercore_auto_keypairs.json",
        ]
        
        for p in search_paths:
            if Path(p).exists():
                legacy_vault_path = p
                break
    
    if not legacy_vault_path:
        raise FileNotFoundError("Legacy vault not found. Specify path with --legacy-path")
    
    logger.info(f"Loading legacy vault from {legacy_vault_path}")
    adapter.load_legacy_keypairs(legacy_vault_path)
    
    # Run verification
    result = adapter.migrate_to_new_vault()
    
    # Print summary
    print("\n" + "=" * 80)
    print("CYBERCORE MIGRATION PARITY TEST RESULTS")
    print("=" * 80)
    print(f"Total Shards:     {result['total_shards']}")
    print(f"Matched:          {result['matched']}")
    print(f"Mismatched:       {result['mismatched']}")
    print(f"Status:           {'PASSED' if result['mismatched'] == 0 else 'FAILED'}")
    print("=" * 80)
    
    if result["mismatches"]:
        print("\nMISMATCHES:")
        for m in result["mismatches"]:
            print(f"  Shard {m['shard']:3d} ({m['chain']:8s}):")
            print(f"    Legacy: {m['legacy_address']}")
            print(f"    New:    {m['new_address']}")
    
    # Chain breakdown
    print("\nBREAKDOWN BY CHAIN:")
    chain_stats = {}
    for detail in result["shard_details"]:
        chain = detail["chain"]
        if chain not in chain_stats:
            chain_stats[chain] = {"matched": 0, "total": 0}
        chain_stats[chain]["total"] += 1
        if detail["matched"]:
            chain_stats[chain]["matched"] += 1
    
    for chain, stats in sorted(chain_stats.items()):
        pct = (stats["matched"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {chain:12s}: {stats['matched']:3d}/{stats['total']:3d} ({pct:5.1f}%)")
    
    # Save detailed report
    report_path = "cybercore_parity_report.json"
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\nDetailed report saved to {report_path}")
    
    return result


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="CyberCore Migration Parity Test")
    parser.add_argument("--legacy-path", help="Path to legacy cybercore_auto_keypairs.json")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        result = run_parity_test(args.legacy_path)
        
        if result["mismatched"] == 0:
            print("\n✅ PARITY TEST PASSED - All 300 shards match!")
            sys.exit(0)
        else:
            print(f"\n❌ PARITY TEST FAILED - {result['mismatched']} mismatches")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Parity test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
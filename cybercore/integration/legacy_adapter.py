"""
Legacy Vault Adapter - Translates old cybercore_auto_node_keypair_vault.py calls
to new StatelessVault + Signing Oracle architecture.
"""

import json
import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from cybercore.vault import StatelessVault, create_vault
from cybercore.derivation import get_chain_registry, ChainRegistry

logger = logging.getLogger(__name__)


class LegacyVaultAdapter:
    """
    Adapter that mimics the old CyberCoreAutoKeypairVault interface
    but uses the new stateless vault underneath.
    
    Old interface:
    - vault.keypairs[i]["address"]
    - vault.keypairs[i]["private_key"]
    - vault.export_and_load_environment()
    
    New interface:
    - vault.derive_address(path, chain)
    - vault.sign(path, message, chain)
    - No private keys ever exposed!
    """
    
    def __init__(self, vault: StatelessVault = None):
        self.vault = vault or create_vault()
        self.registry = get_chain_registry()
        self._legacy_keypairs: List[Dict] = []
        self._migration_verified = False
    
    def load_legacy_keypairs(self, filepath: str) -> List[Dict]:
        """Load legacy keypairs from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self._legacy_keypairs = data.get("keypairs", [])
        logger.info(f"Loaded {len(self._legacy_keypairs)} legacy keypairs from {filepath}")
        return self._legacy_keypairs
    
    def get_legacy_keypair(self, index: int) -> Optional[Dict]:
        """Get legacy keypair by index (0-based)."""
        if 0 <= index < len(self._legacy_keypairs):
            return self._legacy_keypairs[index]
        return None
    
    def get_legacy_address(self, index: int) -> Optional[str]:
        """Get legacy address by index."""
        kp = self.get_legacy_keypair(index)
        return kp.get("address") if kp else None
    
    def get_legacy_private_key(self, index: int) -> Optional[str]:
        """
        DEPRECATED: Get legacy private key.
        WARNING: This exposes private key material!
        Only for migration verification - DO NOT USE IN PRODUCTION.
        """
        logger.warning("DEPRECATED: get_legacy_private_key() exposes private key!")
        kp = self.get_legacy_keypair(index)
        return kp.get("private_key") if kp else None
    
    def migrate_to_new_vault(self) -> Dict[str, Any]:
        """
        Migrate from legacy vault to new stateless vault.
        Verifies address parity for all 300 shards.
        """
        if not self._legacy_keypairs:
            raise ValueError("No legacy keypairs loaded. Call load_legacy_keypairs() first.")
        
        results = {
            "total_shards": len(self._legacy_keypairs),
            "matched": 0,
            "mismatched": 0,
            "mismatches": [],
            "shard_details": [],
        }
        
        for i, legacy_kp in enumerate(self._legacy_keypairs):
            shard_num = i + 1
            chain = legacy_kp.get("network_type", "EVM").lower()
            legacy_address = legacy_kp.get("address", "")
            
            # Derive new address using standard path
            if chain == "evm":
                path = self.registry.get_shard_wallet_path("ethereum", shard_num)
                new_address = self.vault.derive_address(path, "ethereum")
            elif chain == "xrpl":
                path = self.registry.get_shard_wallet_path("xrpl", shard_num)
                new_address = self.vault.derive_address(path, "xrpl")
            elif chain == "solana":
                path = self.registry.get_shard_wallet_path("solana", shard_num)
                new_address = self.vault.derive_address(path, "solana")
            elif chain == "cosmos":
                path = self.registry.get_shard_wallet_path("cosmos", shard_num)
                new_address = self.vault.derive_address(path, "cosmos")
            elif chain == "bitcoin_l2":
                path = self.registry.get_shard_wallet_path("stacks", shard_num)
                new_address = self.vault.derive_address(path, "stacks")
            else:
                logger.warning(f"Unknown chain {chain} for shard {shard_num}")
                continue
            
            # Normalize addresses for comparison
            legacy_norm = legacy_address.lower()
            new_norm = new_address.lower()
            
            matched = legacy_norm == new_norm
            
            detail = {
                "shard": shard_num,
                "chain": chain,
                "legacy_address": legacy_address,
                "new_address": new_address,
                "matched": matched,
            }
            
            if matched:
                results["matched"] += 1
            else:
                results["mismatched"] += 1
                results["mismatches"].append(detail)
                logger.error(f"SHARD {shard_num} MISMATCH: legacy={legacy_address}, new={new_address}")
            
            results["shard_details"].append(detail)
        
        self._migration_verified = (results["mismatched"] == 0)
        
        logger.info(f"Migration verification: {results['matched']}/{results['total_shards']} matched")
        
        return results
    
    def verify_address_parity(self, shard_num: int, chain: str) -> bool:
        """Verify single shard address matches legacy."""
        legacy_kp = self.get_legacy_keypair(shard_num - 1)
        if not legacy_kp:
            return False
        
        legacy_address = legacy_kp.get("address", "")
        path = self.registry.get_shard_wallet_path(chain, shard_num)
        new_address = self.vault.derive_address(path, chain)
        
        return legacy_address.lower() == new_address.lower()
    
    def get_new_shard_wallet(self, shard_num: int, chain: str) -> Dict[str, Any]:
        """Get new wallet info for shard (public only)."""
        path = self.registry.get_shard_wallet_path(chain, shard_num)
        info = self.vault.get_key_info(path, chain)
        
        return {
            "shard_id": f"shard-{shard_num:03d}",
            "chain": chain,
            "path": path,
            "address": info.address,
            "public_key": info.public_key.hex(),
            "curve": info.curve,
        }
    
    def get_new_agent_wallet(self, chain: str, shard: int, agent_id: int) -> Dict[str, Any]:
        """Get new agent wallet info."""
        path = self.registry.get_agent_wallet_path(chain, shard, agent_id)
        info = self.vault.get_key_info(path, chain)
        
        return {
            "chain": chain,
            "shard": shard,
            "agent_id": agent_id,
            "path": path,
            "address": info.address,
            "public_key": info.public_key.hex(),
            "curve": info.curve,
        }
    
    def sign_as_legacy_shard(self, shard_num: int, chain: str, message: bytes) -> bytes:
        """
        Sign message as legacy shard using new vault.
        """
        path = self.registry.get_shard_wallet_path(chain, shard_num)
        return self.vault.sign(path, message, chain)
    
    def export_environment_vars(self) -> Dict[str, str]:
        """
        Export environment variables for backward compatibility.
        Only exports PUBLIC addresses - NEVER private keys.
        """
        env = {}
        
        # Primary EVM treasury (shard 1)
        evm_info = self.get_new_shard_wallet(1, "ethereum")
        env["EVM_TREASURY_WALLET_ADDRESS"] = evm_info["address"]
        env["EVM_TREASURY_PUBLIC_KEY"] = evm_info["public_key"]
        
        # Primary XRPL (shard 151)
        xrpl_info = self.get_new_shard_wallet(151, "xrpl")
        env["XAMAN_WALLET_ADDRESS"] = xrpl_info["address"]
        env["XAMAN_WALLET_PUBLIC_KEY"] = xrpl_info["public_key"]
        env["XRPL_WALLET_ADDRESS"] = xrpl_info["address"]
        env["XRPL_WALLET_PUBLIC_KEY"] = xrpl_info["public_key"]
        
        # NOTE: We do NOT export private keys!
        # env["EVM_TREASURY_PRIVATE_KEY"] = "REDACTED - USE SIGNING ORACLE"
        # env["XRPL_SECRET_SEED"] = "REDACTED - USE SIGNING ORACLE"
        
        return env
    
    def generate_migration_report(self, output_path: str = None) -> str:
        """Generate migration verification report."""
        results = self.migrate_to_new_vault()
        
        report = "=" * 80 + "\n"
        report += "CYBERCORE VAULT MIGRATION VERIFICATION REPORT\n"
        report += "=" * 80 + "\n"
        report += f"Total Shards: {results['total_shards']}\n"
        report += f"Matched: {results['matched']}\n"
        report += f"Mismatched: {results['mismatched']}\n"
        report += f"Status: {'PASSED' if results['mismatched'] == 0 else 'FAILED'}\n"
        report += "=" * 80 + "\n\n"
        
        if results["mismatches"]:
            report += "MISMATCHES:\n"
            for m in results["mismatches"]:
                report += f"  Shard {m['shard']} ({m['chain']}):\n"
                report += f"  Legacy: {m['legacy_address']}\n"
                report += f"  New:    {m['new_address']}\n\n"
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report)
            logger.info(f"Migration report saved to {output_path}")
        
        return report


def create_legacy_adapter(vault: StatelessVault = None, 
                          legacy_keypairs_path: str = None) -> LegacyVaultAdapter:
    """Create and optionally load legacy adapter."""
    adapter = LegacyVaultAdapter(vault)
    if legacy_keypairs_path:
        adapter.load_legacy_keypairs(legacy_keypairs_path)
    return adapter
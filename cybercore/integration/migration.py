"""
Migration Module - One-time migration from legacy vault to new architecture.
"""

import json
import logging
import shutil
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .legacy_adapter import LegacyVaultAdapter, create_legacy_adapter
from .wallet_registry import WalletRegistry, create_wallet_registry

logger = logging.getLogger(__name__)


# Legacy vault file paths
LEGACY_VAULT_PATHS = [
    r"c:\Users\AEGENTIX\cybercore_auto_keypairs.json",
    r"C:\Users\eagle\AEGENTIX-CYBERNETICS-CORE\SOVEREIGN_ENDPOINTS_MASTER_BACKUP\cybercore_auto_keypairs.json",
    r"C:\Users\eagle\AEGENTIX-CYBERNETICS-CORE\My Drive\SOVEREIGN_ENDPOINTS_MASTER_BACKUP\cybercore_auto_keypairs.json",
]

LEGACY_PS1_PATHS = [
    r"c:\Users\AEGENTIX\load_cybercore_auto_keys.ps1",
    r"C:\Users\eagle\AEGENTIX-CYBERNETICS-CORE\SOVEREIGN_ENDPOINTS_MASTER_BACKUP\load_cybercore_auto_keys.ps1",
    r"C:\Users\eagle\AEGENTIX-CYBERNETICS-CORE\My Drive\SOVEREIGN_ENDPOINTS_MASTER_BACKUP\load_cybercore_auto_keys.ps1",
]


class MigrationManager:
    """Manages complete migration from legacy to new architecture."""
    
    def __init__(self, vault=None):
        self.vault = vault or create_vault()
        self.adapter = create_legacy_adapter(self.vault)
        self.wallet_registry = create_wallet_registry(self.vault)
        self.report: Dict[str, Any] = {}
    
    def find_legacy_files(self) -> Dict[str, Optional[str]]:
        """Find existing legacy vault files."""
        found = {}
        
        for path in LEGACY_VAULT_PATHS:
            p = Path(path)
            if p.exists():
                found["vault_json"] = str(p)
                break
        
        for path in LEGACY_PS1_PATHS:
            p = Path(path)
            if p.exists():
                found["ps1_script"] = str(p)
                break
        
        return found
    
    def run_migration(self, backup: bool = True) -> Dict[str, Any]:
        """Execute complete migration."""
        logger.info("Starting CyberCore vault migration...")
        
        # Step 1: Find legacy files
        legacy_files = self.find_legacy_files()
        if not legacy_files.get("vault_json"):
            raise FileNotFoundError("Legacy vault JSON not found in known locations")
        
        self.report["legacy_files"] = legacy_files
        self.report["started_at"] = datetime.utcnow().isoformat()
        
        # Step 2: Backup legacy files
        if backup:
            self._backup_legacy_files(legacy_files)
        
        # Step 3: Load legacy keypairs
        self.adapter.load_legacy_keypairs(legacy_files["vault_json"])
        self.report["legacy_keypairs_count"] = len(self.adapter._legacy_keypairs)
        
        # Step 4: Verify address parity
        verification = self.adapter.migrate_to_new_vault()
        self.report["verification"] = verification
        
        if verification["mismatched"] > 0:
            logger.error(f"MIGRATION FAILED: {verification['mismatched']} address mismatches")
            self.report["status"] = "FAILED"
            return self.report
        
        # Step 5: Build new wallet registry
        count = self.wallet_registry.build_full_registry()
        self.report["new_wallet_count"] = count
        
        # Step 6: Save new registry
        registry_path = "C:\\Users\\eagle\\AEGENTIX-CYBERNETICS-CORE\\cybercore_wallet_registry.json"
        self.wallet_registry.save(registry_path)
        self.report["registry_path"] = registry_path
        
        # Step 7: Export minimal registry for agents
        minimal_path = "C:\\Users\\eagle\\AEGENTIX-CYBERNETICS-CORE\\cybercore_wallet_registry_minimal.json"
        self.wallet_registry.export_for_agents(minimal_path)
        self.report["minimal_registry_path"] = minimal_path
        
        # Step 8: Generate environment variables (public only)
        env_vars = self.adapter.export_environment_vars()
        env_path = "C:\\Users\\eagle\\AEGENTIX-CYBERNETICS-CORE\\cybercore_env_vars.json"
        with open(env_path, 'w') as f:
            json.dump(env_vars, f, indent=2)
        self.report["env_vars_path"] = env_path
        
        # Step 9: Export migration report
        report_path = "C:\\Users\\eagle\\AEGENTIX-CYBERNETICS-CORE\\cybercore_migration_report.json"
        self.report["status"] = "SUCCESS"
        self.report["completed_at"] = datetime.utcnow().isoformat()
        
        with open(report_path, 'w') as f:
            json.dump(self.report, f, indent=2)
        
        logger.info("Migration completed successfully!")
        return self.report
    
    def _backup_legacy_files(self, legacy_files: Dict[str, str]):
        """Backup legacy files before migration."""
        backup_dir = Path("C:\\Users\\eagle\\AEGENTIX-CYBERNETICS-CORE\\legacy_backup")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        for key, path in legacy_files.items():
            if path:
                src = Path(path)
                dst = backup_dir / f"{src.stem}_{timestamp}{src.suffix}"
                shutil.copy2(src, dst)
                logger.info(f"Backed up {src} to {dst}")
        
        self.report["backup_dir"] = str(backup_dir)
    
    def verify_post_migration(self) -> bool:
        """Verify migration integrity."""
        # Check registry exists and has entries
        registry = create_wallet_registry(self.vault)
        registry.load("C:\\Users\\eagle\\AEGENTIX-CYBERNETICS-CORE\\cybercore_wallet_registry.json")
        
        if len(registry._wallets) == 0:
            logger.error("Registry is empty after migration")
            return False
        
        # Verify a few key addresses
        evm_treasury = registry.get("ethereum-treasury-ethereum")
        if not evm_treasury or evm_treasury.address != "0x71C865d4fC35E2a188B67B7A98AcB921098A1904":
            logger.error("EVM treasury address mismatch")
            return False
        
        xrpl_treasury = registry.get("xrpl-treasury-xrpl")
        if not xrpl_treasury or xrpl_treasury.address != "rZamanXRPLMainnetVaultAddr9948271":
            logger.error("XRPL treasury address mismatch")
            return False
        
        logger.info("Post-migration verification passed")
        return True
    
    def cleanup_legacy_files(self, confirm: bool = False):
        """Delete legacy files after successful migration."""
        if not confirm:
            logger.warning("Cleanup requires confirm=True")
            return
        
        legacy_files = self.find_legacy_files()
        for key, path in legacy_files.items():
            if path:
                Path(path).unlink(missing_ok=True)
                logger.info(f"Deleted legacy file: {path}")
        
        logger.info("Legacy files cleaned up")


def run_full_migration(vault=None, backup: bool = True) -> Dict[str, Any]:
    """Run complete migration workflow."""
    manager = MigrationManager(vault)
    return manager.run_migration(backup=backup)
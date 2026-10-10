"""
CyberCore Integration Module - Legacy migration and wallet registry.

Exports:
- LegacyVaultAdapter: Adapter for old vault interface
- WalletRegistry: Public wallet registry
- MigrationManager: Complete migration workflow
- create_legacy_adapter, create_wallet_registry, run_full_migration
"""

from .legacy_adapter import (
    LegacyVaultAdapter,
    create_legacy_adapter,
)

from .wallet_registry import (
    WalletRegistry,
    WalletEntry,
    create_wallet_registry,
)

from .migration import (
    MigrationManager,
    run_full_migration,
    LEGACY_VAULT_PATHS,
    LEGACY_PS1_PATHS,
)

__all__ = [
    "LegacyVaultAdapter",
    "create_legacy_adapter",
    "WalletRegistry",
    "WalletEntry",
    "create_wallet_registry",
    "MigrationManager",
    "run_full_migration",
    "LEGACY_VAULT_PATHS",
    "LEGACY_PS1_PATHS",
]
"""
CyberCore - Zero-Storage Deterministic Key Architecture for Sovereign Custody.

Architecture:
- Multi-backend entropy with jurisdictional exclusion (no Dubai/Islamic law)
- SLIP-0010/BIP32 deterministic derivation (zero private key storage)
- Stateless vault with automatic zeroization
- gRPC signing oracle with capability tokens
- Native AEGENTIX cyber-genetic stablecoin rewards
- Immutable audit logging with Merkle integrity

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "AEGENTIX Cybernetics"

# Core modules
from .entropy import (
    EntropyProvider,
    EntropyRegistry,
    TPMProvider,
    HSMProvider,
    ShamirProvider,
    Argon2Provider,
    get_global_registry,
    initialize_default_registry,
    validate_jurisdiction,
    JurisdictionalError,
)

from .derivation import (
    BIP32Deriver,
    SLIP10Deriver,
    parse_path,
    DerivationPath,
    CurveType,
    PathTemplates,
    ChainConfig,
    ChainFamily,
    ChainRegistry,
    get_chain_registry,
)

from .vault import (
    StatelessVault,
    VaultConfig,
    KeyInfo,
    SecureKey,
    create_vault,
    create_vault_from_seed,
    TREASURY_CHAINS,
)

from .oracle import (
    SigningOracleServicer,
    SigningOracleClient,
    AgentWallet,
    CapabilityManager,
    CapabilityToken,
    CapabilityType,
    create_grpc_server,
    run_server,
    run_unix_socket_server,
    create_agent_wallet,
)

from .rewards import (
    RewardEngine,
    RewardPricing,
    RewardTier,
    SettlementExecutor,
    SettlementMonitor,
    AEGENTIXStablecoin,
    ComputeReceipt,
    SettlementBatch,
    create_reward_engine,
)

from .integration import (
    LegacyVaultAdapter,
    WalletRegistry,
    MigrationManager,
    create_legacy_adapter,
    create_wallet_registry,
    run_full_migration,
)

from .audit import (
    AuditLogger,
    AuditVerifier,
    AuditEntry,
    AuditEventType,
    get_audit_logger,
    initialize_audit_logger,
)

try:
    from .hermes import (
        HermesClient,
        SyncHermesClient,
        HermesIntegratedVault,
        HermesMessage,
        HermesSubject,
        create_hermes_client,
    )
except ImportError:
    HermesClient = None
    SyncHermesClient = None
    HermesIntegratedVault = None
    HermesMessage = None
    HermesSubject = None
    create_hermes_client = None

try:
    from .metrics import (
        setup_metrics,
        start_metrics_server,
        get_collector,
        init_collector,
        REGISTRY,
        MetricsCollector,
        track_signing,
        track_key_derivation,
        track_grpc_request,
        track_hermes_publish,
    )
except ImportError:
    setup_metrics = None
    start_metrics_server = None
    get_collector = None
    init_collector = None
    REGISTRY = None
    MetricsCollector = None
    track_signing = None
    track_key_derivation = None
    track_grpc_request = None
    track_hermes_publish = None

__all__ = [
    # Version
    "__version__",
    # Entropy
    "EntropyProvider",
    "EntropyRegistry",
    "TPMProvider",
    "HSMProvider",
    "ShamirProvider",
    "Argon2Provider",
    "get_global_registry",
    "initialize_default_registry",
    "validate_jurisdiction",
    "JurisdictionalError",
    # Derivation
    "BIP32Deriver",
    "SLIP10Deriver",
    "parse_path",
    "DerivationPath",
    "CurveType",
    "PathTemplates",
    "ChainConfig",
    "ChainFamily",
    "ChainRegistry",
    "get_chain_registry",
    # Vault
    "StatelessVault",
    "VaultConfig",
    "KeyInfo",
    "SecureKey",
    "create_vault",
    "create_vault_from_seed",
    "TREASURY_CHAINS",
    # Oracle
    "SigningOracleServicer",
    "SigningOracleClient",
    "AgentWallet",
    "CapabilityManager",
    "CapabilityToken",
    "CapabilityType",
    "create_grpc_server",
    "run_server",
    "run_unix_socket_server",
    "create_agent_wallet",
    # Rewards
    "RewardEngine",
    "RewardPricing",
    "RewardTier",
    "SettlementExecutor",
    "SettlementMonitor",
    "AEGENTIXStablecoin",
    "ComputeReceipt",
    "SettlementBatch",
    "create_reward_engine",
    # Integration
    "LegacyVaultAdapter",
    "WalletRegistry",
    "MigrationManager",
    "create_legacy_adapter",
    "create_wallet_registry",
    "run_full_migration",
    # Audit
    "AuditLogger",
    "AuditVerifier",
    "AuditEntry",
    "AuditEventType",
    "get_audit_logger",
    "initialize_audit_logger",
    # Hermes
    "HermesClient",
    "SyncHermesClient",
    "HermesIntegratedVault",
    "HermesMessage",
    "HermesSubject",
    "create_hermes_client",
    # Metrics
    "setup_metrics",
    "start_metrics_server",
    "get_collector",
    "init_collector",
    "REGISTRY",
    "MetricsCollector",
    "track_signing",
    "track_key_derivation",
    "track_grpc_request",
    "track_hermes_publish",
]


def quick_start():
    """Quick start example."""
    from .vault import create_vault
    from .oracle import create_agent_wallet
    
    # 1. Create vault with entropy quorum
    vault = create_vault()
    
    # 2. Derive address for shard 1 on Ethereum
    address = vault.derive_address("m/44'/60'/0'/1/0", "ethereum")
    print(f"Shard 1 ETH address: {address}")
    
    # 3. Create agent wallet
    # agent = create_agent_wallet("ethereum", 1, 1, capability_token)
    # sig, addr = agent.sign(b"hello world")
    
    return vault


if __name__ == "__main__":
    quick_start()
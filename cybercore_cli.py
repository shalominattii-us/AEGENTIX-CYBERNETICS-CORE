"""
CyberCore CLI - Command-line interface for administration.
"""

import sys
import os
import json
import argparse
import logging
from typing: Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cybercore.vault import create_vault, StatelessVault
from cybercore.entropy import initialize_default_registry
from cybercore.derivation import get_chain_registry
from cybercore.integration import (
    create_legacy_adapter, create_wallet_registry, run_full_migration
)
from cybercore.audit import get_audit_logger

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cybercore.cli")


def cmd_init(args):
    """Initialize vault and entropy."""
    vault = create_vault()
    vault.initialize()
    print("Vault initialized successfully")
    
    registry = initialize_default_registry()
    healthy = registry.get_healthy_providers()
    print(f"Entropy providers: {[p.name for p in healthy]}")


def cmd_derive_address(args):
    """Derive address for path/chain."""
    vault = create_vault()
    vault.initialize()
    
    address = vault.derive_address(args.path, args.chain)
    print(f"Address: {address}")


def cmd_derive_public_key(args):
    """Derive public key for path/chain."""
    vault = create_vault()
    vault.initialize()
    
    pubkey = vault.derive_public_key(args.path, args.chain)
    print(f"Public Key: {pubkey.hex()}")


def cmd_sign(args):
    """Sign message with derived key."""
    vault = create_vault()
    vault.initialize()
    
    message = args.message.encode() if isinstance(args.message, str) else args.message
    signature = vault.sign(args.path, message, args.chain)
    print(f"Signature: {signature.hex()}")


def cmd_verify_address(args):
    """Verify address matches derivation."""
    vault = create_vault()
    vault.initialize()
    
    derived = vault.derive_address(args.path, args.chain)
    matches = derived.lower() == args.expected.lower()
    
    print(f"Derived: {derived}")
    print(f"Expected: {args.expected}")
    print(f"Match: {matches}")
    
    return matches


def cmd_list_chains(args):
    """List supported chains."""
    registry = get_chain_registry()
    
    for name, config in registry._chains.items():
        print(f"{name}: {config.name} ({config.family.value}) - "
              f"coin_type={config.coin_type}, curve={config.curve.value}")


def cmd_get_shard_wallet(args):
    """Get shard wallet info."""
    vault = create_vault()
    vault.initialize()
    
    info = vault.get_key_info(
        vault.chain_registry.get_shard_wallet_path(args.chain, args.shard),
        args.chain
    )
    print(json.dumps({
        "chain": info.chain,
        "shard": args.shard,
        "path": info.path,
        "address": info.address,
        "public_key": info.public_key.hex(),
        "curve": info.curve,
    }, indent=2))


def cmd_get_agent_wallet(args):
    """Get agent wallet info."""
    vault = create_vault()
    vault.initialize()
    
    info = vault.get_key_info(
        vault.chain_registry.get_agent_wallet_path(args.chain, args.shard, args.agent_id),
        args.chain
    )
    print(json.dumps({
        "chain": info.chain,
        "shard": args.shard,
        "agent_id": args.agent_id,
        "path": info.path,
        "address": info.address,
        "public_key": info.public_key.hex(),
        "curve": info.curve,
    }, indent=2))


def cmd_migrate(args):
    """Run migration from legacy vault."""
    vault = create_vault()
    vault.initialize()
    
    result = run_full_migration(vault)
    print(json.dumps(result, indent=2))


def cmd_verify(args):
    """Run migration parity verification."""
    vault = create_vault()
    vault.initialize()
    
    from cybercore.integration import create_legacy_adapter
    adapter = create_legacy_adapter(vault)
    
    import glob
    legacy_paths = glob.glob(r"C:\Users\**\cybercore_auto_keypairs.json")
    if not legacy_paths:
        print("No legacy vault found")
        return
    
    adapter.load_legacy_keypairs(legacy_paths[0])
    result = adapter.migrate_to_new_vault()
    
    print(json.dumps(result, indent=2))
    
    if result["mismatched"] > 0:
        sys.exit(1)


def cmd_build_registry(args):
    """Build wallet registry."""
    vault = create_vault()
    vault.initialize()
    
    from cybercore.integration import create_wallet_registry
    registry = create_wallet_registry(vault)
    count = registry.build_full_registry()
    
    output = args.output or "cybercore_wallet_registry.json"
    registry.save(output)
    print(f"Built registry with {count} entries, saved to {output}")


def cmd_audit_log(args):
    """Show recent audit log entries."""
    from cybercore.audit import get_audit_logger
    logger = get_audit_logger()
    
    entries = logger.get_entries(0, args.limit)
    for entry in entries:
        print(json.dumps(entry.to_dict(), indent=2))


def cmd_audit_verify(args):
    """Verify audit log integrity."""
    from cybercore.audit import get_audit_logger, AuditVerifier
    logger = get_audit_logger()
    verifier = AuditVerifier(logger)
    
    result = verifier.verify_full_log()
    print(json.dumps(result, indent=2))


def cmd_capability_issue(args):
    """Issue capability token for agent."""
    from cybercore.oracle import initialize_capability_manager, CapabilityType
    
    manager = initialize_capability_manager()
    
    capabilities = [CapabilityType(c) for c in args.capabilities.split(",")]
    
    token = manager.issue_token(
        agent_id=args.agent_id,
        allowed_paths=args.paths.split(","),
        allowed_chains=args.chains.split(","),
        capabilities=capabilities,
        ttl=args.ttl,
    )
    
    print(f"Token: {token.token}")
    print(f"Agent: {token.agent_id}")
    print(f"Expires: {token.expires_at}")


def cmd_health(args):
    """Check system health."""
    vault = create_vault()
    vault.initialize()
    
    from cybercore.entropy import get_global_registry
    entropy_registry = get_global_registry()
    
    print(f"Vault initialized: {vault.is_initialized}")
    print(f"Entropy providers: {len(entropy_registry.get_healthy_providers())} healthy")
    print(f"Cached public keys: {len(vault._public_key_cache)}")
    
    # Check audit logger
    from cybercore.audit import get_audit_logger
    audit_logger = get_audit_logger()
    print(f"Audit entries: {len(audit_logger._entries)}")


def main():
    parser = argparse.ArgumentParser(prog="cybercore", description="CyberCore CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # init
    subparsers.add_parser("init", help="Initialize vault and entropy")
    
    # derive-address
    p = subparsers.add_parser("derive-address", help="Derive address for path")
    p.add_argument("--path", required=True, help="Derivation path")
    p.add_argument("--chain", default="ethereum", help="Chain name")
    
    # derive-public-key
    p = subparsers.add_parser("derive-public-key", help="Derive public key")
    p.add_argument("--path", required=True)
    p.add_argument("--chain", default="ethereum")
    
    # sign
    p = subparsers.add_parser("sign", help="Sign message")
    p.add_argument("--path", required=True)
    p.add_argument("--message", required=True)
    p.add_argument("--chain", default="ethereum")
    
    # verify-address
    p = subparsers.add_parser("verify-address", help="Verify address matches derivation")
    p.add_argument("--path", required=True)
    p.add_argument("--chain", default="ethereum")
    p.add_argument("--expected", required=True, help="Expected address")
    
    # list-chains
    subparsers.add_parser("list-chains", help="List supported chains")
    
    # get-shard-wallet
    p = subparsers.add_parser("get-shard-wallet", help="Get shard wallet info")
    p.add_argument("--chain", default="ethereum")
    p.add_argument("--shard", type=int, required=True)
    
    # get-agent-wallet
    p = subparsers.add_parser("get-agent-wallet", help="Get agent wallet info")
    p.add_argument("--chain", default="ethereum")
    p.add_argument("--shard", type=int, required=True)
    p.add_argument("--agent-id", type=int, required=True)
    
    # migrate
    subparsers.add_parser("migrate", help="Run migration from legacy vault")
    
    # verify
    subparsers.add_parser("verify", help="Run migration parity verification")
    
    # build-registry
    p = subparsers.add_parser("build-registry", help="Build wallet registry")
    p.add_argument("--output", help="Output file path")
    
    # audit-log
    p = subparsers.add_parser("audit-log", help="Show audit log")
    p.add_argument("--limit", type=int, default=10)
    
    # audit-verify
    subparsers.add_parser("audit-verify", help="Verify audit log integrity")
    
    # capability-issue
    p = subparsers.add_parser("capability-issue", help="Issue capability token")
    p.add_argument("--agent-id", required=True)
    p.add_argument("--paths", default="*")
    p.add_argument("--chains", default="*")
    p.add_argument("--capabilities", default="sign,public_key,address")
    p.add_argument("--ttl", type=int, default=3600)
    
    # health
    subparsers.add_parser("health", help="Check system health")
    
    args = parser.parse_args()
    
    # Command dispatch
    commands = {
        "init": cmd_init,
        "derive-address": cmd_derive_address,
        "derive-public-key": cmd_derive_public_key,
        "sign": cmd_sign,
        "verify-address": cmd_verify_address,
        "list-chains": cmd_list_chains,
        "get-shard-wallet": cmd_get_shard_wallet,
        "get-agent-wallet": cmd_get_agent_wallet,
        "migrate": cmd_migrate,
        "verify": cmd_verify,
        "build-registry": cmd_build_registry,
        "audit-log": cmd_audit_log,
        "audit-verify": cmd_audit_verify,
        "capability-issue": cmd_capability_issue,
        "health": cmd_health,
    }
    
    if args.command not in commands:
        parser.print_help()
        sys.exit(1)
    
    try:
        commands[args.command](args)
    except Exception as e:
        logger.error(f"Command failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
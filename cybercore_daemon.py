"""
CyberCore Daemon - Main entry point for running all services.
"""

import sys
import os
import signal
import logging
import threading
import time
from typing: Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cybercore.entropy import initialize_default_registry
from cybercore.vault import create_vault
from cybercore.oracle import run_unix_socket_server, initialize_capability_manager
from cybercore.rewards import RewardEngine, create_reward_engine
from cybercore.audit import initialize_audit_logger
from cybercore.integration import run_full_migration


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('C:\\Users\\eagle\\AEGENTIX-CYBERNETICS-CORE\\cybercore_daemon.log')
    ]
)

logger = logging.getLogger("cybercore.daemon")


class CyberCoreDaemon:
    """Main daemon orchestrating all CyberCore services."""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.vault = None
        self.reward_engine = None
        self.capability_manager = None
        self.audit_logger = None
        self._shutdown = threading.Event()
        self._threads = []
    
    def initialize(self):
        """Initialize all components."""
        logger.info("Initializing CyberCore Daemon...")
        
        # 1. Initialize entropy registry
        logger.info("Initializing entropy providers...")
        try:
            entropy_registry = initialize_default_registry()
            healthy = entropy_registry.get_healthy_providers()
            logger.info(f"Registered {len(healthy)} healthy entropy providers: "
                       f"{[p.name for p in healthy]}")
        except Exception as e:
            logger.warning(f"Entropy initialization partial: {e}")
        
        # 2. Initialize vault
        logger.info("Initializing stateless vault...")
        self.vault = create_vault()
        self.vault.initialize()
        logger.info("Vault initialized")
        
        # 3. Initialize audit logger
        logger.info("Initializing audit logger...")
        self.audit_logger = initialize_audit_logger()
        self.audit_logger.log_vault_init(
            entropy_providers=[p.name for p in healthy] if 'healthy' in locals() else []
        )
        logger.info("Audit logger initialized")
        
        # 4. Initialize capability manager
        logger.info("Initializing capability manager...")
        self.capability_manager = initialize_capability_manager()
        logger.info("Capability manager initialized")
        
        # 5. Initialize reward engine
        logger.info("Initializing reward engine...")
        self.reward_engine = create_reward_engine(self.vault)
        self.reward_engine.start()
        logger.info("Reward engine initialized")
        
        logger.info("All components initialized successfully")
    
    def run_oracle(self, unix_socket: str = None):
        """Run the signing oracle server."""
        if unix_socket:
            logger.info(f"Starting Unix socket oracle on {unix_socket}")
            run_unix_socket_server(
                socket_path=unix_socket,
                vault=self.vault,
                capability_manager=self.capability_manager
            )
        else:
            logger.info("Starting TCP oracle on localhost:50051")
            from cybercore.oracle import run_server
            run_server(
                vault=self.vault,
                capability_manager=self.capability_manager,
                host="localhost",
                port=50051
            )
    
    def run_reward_engine(self):
        """Run reward engine (already started in initialize)."""
        # Reward engine runs in background thread
        # This just keeps the thread alive
        while not self._shutdown.is_set():
            time.sleep(60)
    
    def run_migration(self):
        """Run one-time migration from legacy vault."""
        logger.info("Running migration from legacy vault...")
        result = run_full_migration(self.vault)
        
        if result.get("status") == "SUCCESS":
            logger.info("Migration completed successfully")
            
            # Verify
            from cybercore.integration import MigrationManager
            manager = MigrationManager(self.vault)
            if manager.verify_post_migration():
                logger.info("Post-migration verification PASSED")
            else:
                logger.error("Post-migration verification FAILED")
        else:
            logger.error(f"Migration failed: {result}")
    
    def run_verification(self):
        """Run migration parity verification."""
        logger.info("Running migration parity test...")
        
        from cybercore.integration import create_legacy_adapter
        adapter = create_legacy_adapter(self.vault)
        
        # Find legacy file
        import glob
        legacy_paths = glob.glob(r"C:\Users\**\cybercore_auto_keypairs.json")
        if not legacy_paths:
            logger.error("No legacy vault found for verification")
            return False
        
        adapter.load_legacy_keypairs(legacy_paths[0])
        result = adapter.migrate_to_new_vault()
        
        logger.info(f"Verification: {result['matched']}/{result['total_shards']} matched")
        
        if result["mismatched"] > 0:
            for m in result["mismatches"]:
                logger.error(f"  MISMATCH Shard {m['shard']}: legacy={m['legacy_address']}, new={m['new_address']}")
            return False
        
        logger.info("Parity test PASSED")
        return True
    
    def shutdown(self):
        """Graceful shutdown."""
        logger.info("Shutting down CyberCore Daemon...")
        self._shutdown.set()
        
        if self.reward_engine:
            self.reward_engine.stop()
        
        if self.vault:
            self.vault.close()
        
        logger.info("Shutdown complete")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="CyberCore Daemon")
    parser.add_argument("command", choices=[
        "start", "oracle", "migrate", "verify", "daemon"
    ], help="Command to run")
    parser.add_argument("--unix-socket", default="/tmp/cybercore-oracle.sock",
                       help="Unix socket path for oracle")
    parser.add_argument("--migrate", action="store_true",
                       help="Run migration on startup")
    parser.add_argument("--verify", action="store_true",
                       help="Run parity verification")
    
    args = parser.parse_args()
    
    daemon = CyberCoreDaemon()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        daemon.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        daemon.initialize()
        
        if args.command == "migrate" or args.migrate:
            daemon.run_migration()
            return
        
        if args.command == "verify" or args.verify:
            success = daemon.run_verification()
            sys.exit(0 if success else 1)
        
        if args.command == "oracle":
            daemon.run_oracle(unix_socket=args.unix_socket)
            return
        
        if args.command == "daemon":
            # Run all services
            import threading
            
            # Start oracle in thread
            oracle_thread = threading.Thread(
                target=daemon.run_oracle,
                args=(args.unix_socket,),
                daemon=True
            )
            oracle_thread.start()
            
            # Keep main thread alive
            while not daemon._shutdown.is_set():
                time.sleep(1)
            
            return
        
        # Default: start oracle
        daemon.run_oracle(unix_socket=args.unix_socket)
        
    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as e:
        logger.error(f"Daemon error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        daemon.shutdown()


if __name__ == "__main__":
    main()
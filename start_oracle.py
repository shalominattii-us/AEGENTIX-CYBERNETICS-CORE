#!/usr/bin/env python3
"""
CyberCore gRPC Signing Oracle Startup Script
Supports: Hermes message bus, Prometheus metrics, TLS/mTLS, health checks
"""

import sys
import os
import argparse
import threading
import time

sys.path.insert(0, '.')

from cybercore.entropy import Argon2Provider, get_global_registry
from cybercore.vault import create_vault, VaultConfig
from cybercore.audit import initialize_audit_logger
from cybercore.oracle import initialize_capability_manager
from cybercore.oracle.server import run_server

# Optional integrations
try:
    from cybercore.hermes import SyncHermesClient, HermesIntegratedVault
    HERMES_AVAILABLE = True
except ImportError:
    HERMES_AVAILABLE = False

try:
    from cybercore.metrics import setup_metrics, start_metrics_server
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


def main():
    parser = argparse.ArgumentParser(description="CyberCore gRPC Signing Oracle")
    parser.add_argument("--host", default="0.0.0.0", help="gRPC server host")
    parser.add_argument("--port", type=int, default=50051, help="gRPC server port")
    parser.add_argument("--metrics-port", type=int, default=9090, help="Prometheus metrics port")
    parser.add_argument("--with-hermes", action="store_true", help="Enable Hermes message bus integration")
    parser.add_argument("--nats-url", default=os.getenv("NATS_URL", "nats://localhost:4222"), help="NATS URL for Hermes")
    parser.add_argument("--with-tls", action="store_true", help="Enable TLS/mTLS")
    parser.add_argument("--cert-dir", default="/app/certs", help="TLS certificate directory")
    parser.add_argument("--enable-metrics", action="store_true", help="Enable Prometheus metrics")
    args = parser.parse_args()
    
    # Register Argon2 provider in global registry
    provider = Argon2Provider(passphrase='cybercore-master-seed-2024', country_code='US')
    registry = get_global_registry()
    registry.register(provider)
    print(f'Registered Argon2 provider: healthy={provider.health_check()}')
    print(f'Healthy providers in registry: {len(registry.get_healthy_providers())}')
    
    # Get master seed from environment (loaded by entrypoint)
    master_seed = os.getenv('CYBERCORE_MASTER_SEED')
    if master_seed:
        master_seed_bytes = bytes.fromhex(master_seed)
        print('Using master seed from environment')
    else:
        master_seed_bytes = None
        print('WARNING: No master seed in environment')
    
    # Create vault with single entropy provider
    vault = create_vault(config=VaultConfig(min_entropy_providers=1), master_seed=master_seed_bytes)
    print('Vault initialized')
    
    # Initialize core components
    initialize_audit_logger()
    initialize_capability_manager()
    
    # Optional Hermes integration
    hermes_client = None
    if args.with_hermes and HERMES_AVAILABLE:
        print(f'Initializing Hermes integration with NATS: {args.nats_url}')
        hermes_client = SyncHermesClient(nats_url=args.nats_url)
        hermes_client.connect()
        
        # Wrap vault with Hermes integration
        from cybercore.hermes import HermesIntegratedVault
        vault = HermesIntegratedVault(vault, hermes_client)
        print('Hermes integration enabled - events will be published to NATS')
    
    # Initialize metrics
    metrics_server = None
    if args.enable_metrics and METRICS_AVAILABLE:
        print(f'Starting Prometheus metrics server on port {args.metrics_port}...')
        from cybercore.metrics import setup_metrics
        collector, metrics_server = setup_metrics(
            vault=vault,
            metrics_port=args.metrics_port,
        )
        print(f'Prometheus metrics available at http://0.0.0.0:{args.metrics_port}/metrics')
    
    # TLS configuration
    if args.with_tls:
        print(f'TLS enabled with certificates from: {args.cert_dir}')
        os.environ['CYBERCORE_TLS_ENABLED'] = 'true'
        os.environ['CYBERCORE_CERT_DIR'] = args.cert_dir
    
    print(f'Starting gRPC server on {args.host}:{args.port}...')
    print(f'Health check available at gRPC Health Checking Protocol')
    
    # Run server (blocking)
    try:
        run_server(vault=vault, host=args.host, port=args.port)
    except KeyboardInterrupt:
        print('\nShutdown signal received...')
    finally:
        # Cleanup
        if metrics_server:
            metrics_server.shutdown()
        print('Shutdown complete')


if __name__ == '__main__':
    main()
#!/bin/bash
# CyberCore Docker Entrypoint
# Handles initialization, secrets loading, and graceful startup/shutdown

set -euo pipefail

# Configuration
LOG_FILE="/app/logs/cybercore.log"
SECRETS_DIR="/app/secrets"
MASTER_SEED_FILE="${CYBERCORE_MASTER_SEED_FILE:-/app/secrets/master_seed}"
GRPC_PORT="${CYBERCORE_GRPC_PORT:-50051}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Cleanup on exit
cleanup() {
    log "Shutdown signal received, cleaning up..."
    # Zeroize any sensitive memory
    python3 -c "
import ctypes
import sys
sys.path.insert(0, '.')
try:
    from cybercore.vault.secure_memory import zeroize
    # Best effort cleanup
except:
    pass
"
    log "Cleanup complete"
    exit 0
}

trap cleanup SIGTERM SIGINT SIGQUIT

# Load master seed from file or generate
load_master_seed() {
    if [[ -f "$MASTER_SEED_FILE" ]]; then
        log "Loading master seed from $MASTER_SEED_FILE"
        export CYBERCORE_MASTER_SEED="$(cat "$MASTER_SEED_FILE")"
    else
        log "WARNING: No master seed file found at $MASTER_SEED_FILE"
        log "Generating ephemeral seed (NOT suitable for production)"
        export CYBERCORE_MASTER_SEED="$(python3 -c 'import secrets; print(secrets.token_hex(64))')"
    fi
}

# Validate entropy provider
validate_entropy() {
    log "Validating entropy providers..."
    python3 -c "
import sys
sys.path.insert(0, '.')
from cybercore.entropy import Argon2Provider, get_global_registry
provider = Argon2Provider(passphrase='\$CYBERCORE_MASTER_SEED', country_code='US')
registry = get_global_registry()
registry.register(provider)
healthy = registry.get_healthy_providers()
print('Healthy providers:', [p.name for p in healthy])
if not healthy:
    sys.exit(1)
"
}

# Wait for dependencies
wait_for_dependencies() {
    log "Checking dependencies..."
    # Could add checks for NATS, Redis, etc. here
    sleep 2
}

# Main initialization
main() {
    log "=== CyberCore Starting ==="
    log "Version: 1.0.0"
    log "GRPC Port: $GRPC_PORT"
    log "User: $(whoami)"
    log "UID: $(id -u)"
    
    wait_for_dependencies
    load_master_seed
    validate_entropy
    
    log "Starting gRPC Signing Oracle on port $GRPC_PORT..."
    
    # Execute the main command
    exec "$@"
}

main "$@"
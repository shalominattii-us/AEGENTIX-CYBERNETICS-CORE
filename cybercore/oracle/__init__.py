"""
CyberCore Oracle Module - gRPC Signing Oracle with Capability Tokens.

Exports:
- SigningOracleServicer: gRPC server implementation
- SigningOracleClient: Agent client SDK
- AgentWallet: High-level agent wallet interface
- CapabilityManager: Token issuance/validation
- CapabilityToken: Token data structure
- create_grpc_server, run_server, run_unix_socket_server
- create_agent_wallet
"""

from .server import (
    SigningOracleServicer,
    create_grpc_server,
    run_server,
    run_unix_socket_server,
)

from .client import (
    SigningOracleClient,
    AgentWallet,
    create_agent_wallet,
)

from .capability import (
    CapabilityManager,
    CapabilityToken,
    CapabilityType,
    get_capability_manager,
    initialize_capability_manager,
)

__all__ = [
    # Server
    "SigningOracleServicer",
    "create_grpc_server",
    "run_server",
    "run_unix_socket_server",
    # Client
    "SigningOracleClient",
    "AgentWallet",
    "create_agent_wallet",
    # Capability
    "CapabilityManager",
    "CapabilityToken",
    "CapabilityType",
    "get_capability_manager",
    "initialize_capability_manager",
]
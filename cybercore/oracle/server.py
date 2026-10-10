"""
gRPC Signing Oracle Server Implementation.
"""

import time
import logging
import threading
from typing import Dict, Optional
from concurrent import futures

import grpc
from grpc import StatusCode

from cybercore.oracle.capability import CapabilityManager, CapabilityToken, CapabilityType, get_capability_manager
from cybercore.vault import StatelessVault, create_vault, VaultConfig
from cybercore.audit import AuditLogger, get_audit_logger

logger = logging.getLogger(__name__)

# Import generated gRPC code (will be generated from service.proto)
try:
    from . import service_pb2
    from . import service_pb2_grpc
except ImportError:
    logger.warning("gRPC stubs not generated. Run: python -m grpc_tools.protoc --proto_path=. --python_out=. --grpc_python_out=. service.proto")
    service_pb2 = None
    service_pb2_grpc = None


class SigningOracleServicer:
    """gRPC servicer for Signing Oracle."""
    
    def __init__(self, vault: StatelessVault = None, capability_manager: CapabilityManager = None):
        self.vault = vault or create_vault()
        self.capability_manager = capability_manager or get_capability_manager()
        self.audit_logger = get_audit_logger()
        self._start_time = time.time()
        self._lock = threading.RLock()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def _cleanup_loop(self):
        """Periodic cleanup of expired tokens."""
        while True:
            time.sleep(300)  # Every 5 minutes
            try:
                self.capability_manager.cleanup_expired()
            except Exception as e:
                logger.warning(f"Capability cleanup failed: {e}")
    
    def _verify_capability(self, token_str: str, required_cap: CapabilityType, 
                          path: str = None, chain: str = None) -> CapabilityToken:
        """Verify capability token and check permissions."""
        if not token_str:
            raise grpc.RpcError("Missing capability token")
        
        token = self.capability_manager.verify_token(token_str)
        if not token:
            raise grpc.RpcError("Invalid or revoked capability token")
        
        if token.is_expired():
            raise grpc.RpcError("Capability token expired")
        
        if not token.has_capability(required_cap):
            raise grpc.RpcError(f"Capability {required_cap.value} not granted")
        
        if path and not token.allows_path(path):
            raise grpc.RpcError(f"Path {path} not allowed by capability")
        
        if chain and not token.allows_chain(chain):
            raise grpc.RpcError(f"Chain {chain} not allowed by capability")
        
        return token
    
    def _build_audit_context(self, token: CapabilityToken, method: str, **kwargs) -> Dict:
        """Build audit log context."""
        return {
            "agent_id": token.agent_id,
            "method": method,
            "nonce": token.nonce,
            **kwargs,
        }
    
    def Sign(self, request, context):
        """Sign a message with derived key."""
        try:
            token = self._verify_capability(
                request.capability.token,
                CapabilityType.SIGN,
                request.path,
                request.chain
            )
            
            # Sign message
            signature, address = self.vault.sign_and_get_address(
                request.path,
                request.message,
                request.chain
            )
            
            # Audit log
            try:
                self.audit_logger.log_sign(
                    agent_id=token.agent_id,
                    chain=request.chain,
                    path=request.path,
                    signature=signature,
                    address=address,
                )
            except Exception as audit_err:
                logger.warning(f"Audit log failed: {audit_err}")
            
            return service_pb2.SignResponse(
                signature=signature,
                address=address,
                chain=request.chain,
                timestamp=int(time.time()),
                request_id=token.nonce,
            )
            
        except grpc.RpcError:
            raise
        except Exception as e:
            logger.error(f"Sign error: {e}")
            context.set_code(StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.SignResponse()
    
    def GetPublicKey(self, request, context):
        """Get public key for derivation path."""
        try:
            token = self._verify_capability(
                request.capability.token,
                CapabilityType.PUBLIC_KEY,
                request.path,
                request.chain
            )
            
            info = self.vault.get_key_info(request.path, request.chain)
            
            return service_pb2.PublicKeyResponse(
                public_key=info.public_key,
                address=info.address,
                chain=info.chain,
                curve=info.curve,
                depth=info.depth,
            )
            
        except grpc.RpcError:
            raise
        except Exception as e:
            logger.error(f"GetPublicKey error: {e}")
            context.set_code(StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.PublicKeyResponse()
    
    def DeriveAddress(self, request, context):
        """Derive address for path."""
        try:
            token = self._verify_capability(
                request.capability.token,
                CapabilityType.ADDRESS,
                request.path,
                request.chain
            )
            
            address = self.vault.derive_address(request.path, request.chain)
            
            return service_pb2.AddressResponse(
                address=address,
                chain=request.chain,
            )
            
        except grpc.RpcError:
            raise
        except Exception as e:
            logger.error(f"DeriveAddress error: {e}")
            context.set_code(StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.AddressResponse()
    
    def Health(self, request, context):
        """Health check endpoint."""
        try:
            entropy_providers = [
                p.name for p in self.vault.entropy_registry.get_healthy_providers()
            ]
            
            return service_pb2.HealthResponse(
                healthy=True,
                version="1.0.0",
                uptime_seconds=int(time.time() - self._start_time),
                entropy_providers=entropy_providers,
                cached_keys=len(self.vault._public_key_cache),
            )
        except Exception as e:
            logger.error(f"Health error: {e}")
            return service_pb2.HealthResponse(healthy=False)
    
    def ListChains(self, request, context):
        """List supported chains."""
        try:
            chains = []
            for config in self.vault.chain_registry.all():
                chains.append(service_pb2.ChainInfo(
                    name=config.name,
                    family=config.family.value,
                    curve=config.curve.value,
                    native_token=config.native_token,
                    chain_id=config.chain_id,
                    is_testnet=config.is_testnet,
                ))
            
            return service_pb2.ListChainsResponse(chains=chains)
            
        except Exception as e:
            logger.error(f"ListChains error: {e}")
            context.set_code(StatusCode.INTERNAL)
            context.set_details(str(e))
            return service_pb2.ListChainsResponse()


def create_grpc_server(
    vault: StatelessVault = None,
    capability_manager: CapabilityManager = None,
    host: str = "localhost",
    port: int = 50051,
    max_workers: int = 10,
) -> grpc.Server:
    """Create and configure gRPC server."""
    if service_pb2_grpc is None:
        raise RuntimeError("gRPC stubs not available. Generate with grpc_tools.protoc")
    
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    
    servicer = SigningOracleServicer(vault, capability_manager)
    service_pb2_grpc.add_SigningOracleServicer_to_server(servicer, server)
    
    server.add_insecure_port(f"{host}:{port}")
    
    return server


def run_server(
    vault: StatelessVault = None,
    capability_manager: CapabilityManager = None,
    host: str = "localhost",
    port: int = 50051,
    unix_socket: str = None,
):
    """Run gRPC server (blocking)."""
    server = create_grpc_server(vault, capability_manager, host, port)
    
    if unix_socket:
        server.add_insecure_port(f"unix:{unix_socket}")
    
    server.start()
    logger.info(f"Signing Oracle started on {host}:{port}" + (f" + unix:{unix_socket}" if unix_socket else ""))
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.stop(5)


# Unix socket server for local agent communication
def run_unix_socket_server(
    socket_path: str = "/tmp/cybercore-oracle.sock",
    vault: StatelessVault = None,
    capability_manager: CapabilityManager = None,
):
    """Run gRPC server on Unix socket only."""
    server = create_grpc_server(vault, capability_manager, unix_socket=socket_path)
    server.start()
    logger.info(f"Signing Oracle started on unix:{socket_path}")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.stop(5)
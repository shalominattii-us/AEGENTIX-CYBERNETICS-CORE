"""
gRPC Client for Signing Oracle - Agent SDK.
"""

import grpc
import time
import logging
from typing import Optional

from cybercore.oracle.capability import CapabilityManager, CapabilityToken, CapabilityType, get_capability_manager

logger = logging.getLogger(__name__)

# Import generated gRPC code
try:
    from . import service_pb2
    from . import service_pb2_grpc
except ImportError:
    logger.warning("gRPC stubs not generated")
    service_pb2 = None
    service_pb2_grpc = None


class SigningOracleClient:
    """Client for CyberCore Signing Oracle."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        unix_socket: str = None,
        capability_token: str = None,
        agent_id: str = None,
    ):
        self.host = host
        self.port = port
        self.unix_socket = unix_socket
        self.agent_id = agent_id
        self._capability_token = capability_token
        self._channel = None
        self._stub = None
        self._connect()
    
    def _connect(self):
        """Establish gRPC connection."""
        if self.unix_socket:
            target = f"unix:{self.unix_socket}"
        else:
            target = f"{self.host}:{self.port}"
        
        self._channel = grpc.insecure_channel(target)
        if service_pb2_grpc:
            self._stub = service_pb2_grpc.SigningOracleStub(self._channel)
        else:
            raise RuntimeError("gRPC stubs not available")
        
        logger.info(f"Connected to Signing Oracle at {target}")
    
    def set_capability_token(self, token: str):
        """Set capability token for requests."""
        self._capability_token = token
    
    def _make_capability(self) -> 'service_pb2.CapabilityToken':
        """Create capability token protobuf."""
        if not self._capability_token:
            raise ValueError("No capability token set")
        
        return service_pb2.CapabilityToken(token=self._capability_token)
    
    def sign(self, path: str, message: bytes, chain: str = "ethereum") -> tuple:
        """
        Sign a message.
        Returns (signature: bytes, address: str)
        """
        if not self._stub:
            raise RuntimeError("Not connected")
        
        request = service_pb2.SignRequest(
            capability=self._make_capability(),
            path=path,
            message=message,
            chain=chain,
            agent_id=self.agent_id or "",
            nonce=int(time.time() * 1000),
        )
        
        response = self._stub.Sign(request)
        
        return response.signature, response.address
    
    def get_public_key(self, path: str, chain: str = "ethereum") -> dict:
        """Get public key info for path."""
        if not self._stub:
            raise RuntimeError("Not connected")
        
        request = service_pb2.PublicKeyRequest(
            capability=self._make_capability(),
            path=path,
            chain=chain,
        )
        
        response = self._stub.GetPublicKey(request)
        
        return {
            "public_key": response.public_key,
            "address": response.address,
            "chain": response.chain,
            "curve": response.curve,
            "depth": response.depth,
        }
    
    def derive_address(self, path: str, chain: str = "ethereum") -> str:
        """Derive address for path."""
        if not self._stub:
            raise RuntimeError("Not connected")
        
        request = service_pb2.AddressRequest(
            capability=self._make_capability(),
            path=path,
            chain=chain,
        )
        
        response = self._stub.DeriveAddress(request)
        return response.address
    
    def health_check(self) -> dict:
        """Check oracle health."""
        if not self._stub:
            raise RuntimeError("Not connected")
        
        request = service_pb2.HealthRequest()
        response = self._stub.Health(request)
        
        return {
            "healthy": response.healthy,
            "version": response.version,
            "uptime_seconds": response.uptime_seconds,
            "entropy_providers": list(response.entropy_providers),
            "cached_keys": response.cached_keys,
        }
    
    def list_chains(self) -> list:
        """List supported chains."""
        if not self._stub:
            raise RuntimeError("Not connected")
        
        request = service_pb2.ListChainsRequest()
        response = self._stub.ListChains(request)
        
        return [
            {
                "name": c.name,
                "family": c.family,
                "curve": c.curve,
                "native_token": c.native_token,
                "chain_id": c.chain_id,
                "is_testnet": c.is_testnet,
            }
            for c in response.chains
        ]
    
    def close(self):
        """Close connection."""
        if self._channel:
            self._channel.close()
            self._channel = None
            self._stub = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class AgentWallet:
    """High-level agent wallet interface."""
    
    def __init__(
        self,
        client: SigningOracleClient,
        chain: str,
        shard: int,
        agent_id: int,
    ):
        self.client = client
        self.chain = chain
        self.shard = shard
        self.agent_id = agent_id
        self.nonce = 0
        
        from cybercore.derivation import get_chain_registry
        self.registry = get_chain_registry()
    
    def _get_path(self, nonce: int = None) -> str:
        """Get derivation path for this agent."""
        return self.registry.get_agent_wallet_path(
            self.chain, self.shard, self.agent_id, nonce or self.nonce
        )
    
    def sign(self, message: bytes, nonce: int = None) -> tuple:
        """Sign message as this agent."""
        path = self._get_path(nonce)
        sig, addr = self.client.sign(path, message, self.chain)
        if nonce is None:
            self.nonce += 1
        return sig, addr
    
    def get_address(self, nonce: int = None) -> str:
        """Get agent's address."""
        path = self._get_path(nonce)
        return self.client.derive_address(path, self.chain)
    
    def get_public_key(self, nonce: int = None) -> dict:
        """Get agent's public key."""
        path = self._get_path(nonce)
        return self.client.get_public_key(path, self.chain)
    
    def increment_nonce(self):
        """Increment nonce for next operation."""
        self.nonce += 1


def create_agent_wallet(
    chain: str,
    shard: int,
    agent_id: int,
    capability_token: str,
    host: str = "localhost",
    port: int = 50051,
    unix_socket: str = None,
    agent_id_str: str = None,
) -> AgentWallet:
    """Create agent wallet with client."""
    client = SigningOracleClient(
        host=host,
        port=port,
        unix_socket=unix_socket,
        capability_token=capability_token,
        agent_id=agent_id_str or f"agent-{agent_id}",
    )
    return AgentWallet(client, chain, shard, agent_id)
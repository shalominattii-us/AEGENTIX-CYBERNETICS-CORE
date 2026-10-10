"""
CyberCore Hermes Integration Layer
===================================
Integrates CyberCore with the Hermes message bus (NATS-based) for 
inter-service communication, event streaming, and distributed coordination.

Architecture:
- CyberCore publishes signing events, key derivations, audit logs to Hermes
- CyberCore subscribes to: key rotation requests, policy updates, capability revocations
- Hermes provides: pub/sub, request/reply, stream persistence, JetStream
"""

import asyncio
import json
import logging
import os
import signal
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

import nats
from nats.aio.client import Client as NATS
from nats.js.api import ConsumerConfig, StreamConfig

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cybercore.vault import create_vault, VaultConfig
from cybercore.entropy import Argon2Provider, get_global_registry
from cybercore.audit import get_audit_logger

logger = logging.getLogger(__name__)


class HermesSubject(Enum):
    """Hermes subject hierarchy for CyberCore events."""
    # Published by CyberCore
    SIGNING_REQUEST = "cybercore.signing.request"
    SIGNING_RESPONSE = "cybercore.signing.response"
    KEY_DERIVED = "cybercore.key.derived"
    AUDIT_LOG = "cybercore.audit.log"
    HEALTH_STATUS = "cybercore.health.status"
    
    # Subscribed by CyberCore
    KEY_ROTATION_REQUEST = "cybercore.key.rotation.request"
    POLICY_UPDATE = "cybercore.policy.update"
    CAPABILITY_REVOKE = "cybercore.capability.revoke"
    VAULT_CONFIG_CHANGE = "cybercore.vault.config.change"
    
    # System
    NODE_STATUS = "hermes.node.status"
    CLUSTER_SYNC = "hermes.cluster.sync"


@dataclass
class HermesMessage:
    """Standard Hermes message envelope."""
    subject: str
    payload: Dict[str, Any]
    correlation_id: str = ""
    timestamp: str = ""
    source: str = "cybercore"
    version: str = "1.0"
    
    def __post_init__(self):
        if not self.correlation_id:
            self.correlation_id = str(uuid4())
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, data: str) -> 'HermesMessage':
        d = json.loads(data)
        return cls(**d)


class HermesClient:
    """CyberCore Hermes integration client."""
    
    def __init__(
        self,
        nats_url: str = "nats://localhost:4222",
        vault: Optional[Any] = None,
        stream_name: str = "CYBERCORE_EVENTS",
    ):
        self.nats_url = nats_url
        self.vault = vault
        self.stream_name = stream_name
        
        self.nc: Optional[NATS] = None
        self.js = None  # JetStream context
        self._subscriptions: List[Any] = []
        self._handlers: Dict[str, Callable] = {}
        self._running = False
        self._audit_logger = get_audit_logger()
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default message handlers."""
        self._handlers[HermesSubject.KEY_ROTATION_REQUEST.value] = self._handle_key_rotation
        self._handlers[HermesSubject.POLICY_UPDATE.value] = self._handle_policy_update
        self._handlers[HermesSubject.CAPABILITY_REVOKE.value] = self._handle_capability_revoke
        self._handlers[HermesSubject.VAULT_CONFIG_CHANGE.value] = self._handle_vault_config_change
    
    async def connect(self):
        """Connect to NATS and initialize JetStream."""
        self.nc = await nats.connect(self.nats_url)
        self.js = self.nc.jetstream()
        
        # Create stream for CyberCore events
        try:
            await self.js.add_stream(StreamConfig(
                name=self.stream_name,
                subjects=[
                    "cybercore.>",
                    "hermes.>",
                ],
                retention="limits",
                max_msgs=100000,
                max_bytes=1024 * 1024 * 100,  # 100MB
                max_age=86400,  # 24 hours
                storage="file",
            ))
            logger.info(f"Created JetStream stream: {self.stream_name}")
        except Exception as e:
            logger.warning(f"Stream may already exist: {e}")
        
        # Subscribe to command subjects
        await self._subscribe_commands()
        
        # Publish startup event
        await self.publish(HermesMessage(
            subject=HermesSubject.HEALTH_STATUS.value,
            payload={"status": "started", "version": "1.0.0"}
        ))
        
        logger.info(f"Hermes client connected to {self.nats_url}")
    
    async def _subscribe_commands(self):
        """Subscribe to command subjects."""
        command_subjects = [
            HermesSubject.KEY_ROTATION_REQUEST.value,
            HermesSubject.POLICY_UPDATE.value,
            HermesSubject.CAPABILITY_REVOKE.value,
            HermesSubject.VAULT_CONFIG_CHANGE.value,
        ]
        
        for subject in command_subjects:
            sub = await self.js.subscribe(
                subject,
                durable=f"cybercore-{subject.replace('.', '-')}",
                cb=self._message_handler,
                config=ConsumerConfig(
                    ack_policy="explicit",
                    max_deliver=3,
                    ack_wait=30,
                )
            )
            self._subscriptions.append(sub)
            logger.info(f"Subscribed to {subject}")
    
    async def _message_handler(self, msg):
        """Handle incoming messages."""
        try:
            data = json.loads(msg.data.decode())
            hermes_msg = HermesMessage.from_json(json.dumps(data))
            
            handler = self._handlers.get(hermes_msg.subject)
            if handler:
                await handler(hermes_msg)
                await msg.ack()
            else:
                logger.warning(f"No handler for subject: {hermes_msg.subject}")
                await msg.nak()
                
        except Exception as e:
            logger.error(f"Message handler error: {e}")
            await msg.nak()
    
    async def publish(self, message: HermesMessage):
        """Publish message to Hermes."""
        if not self.js:
            raise RuntimeError("Not connected to NATS")
        
        await self.js.publish(
            message.subject,
            message.to_json().encode(),
            stream=self.stream_name,
        )
        
        # Also log to audit
        self._audit_logger.log_event(
            event_type="hermes.publish",
            agent_id="cybercore",
            chain="",
            path=message.subject,
            metadata={"message": message.payload},
        )
    
    async def _handle_key_rotation(self, msg: HermesMessage):
        """Handle key rotation request."""
        logger.info(f"Key rotation requested: {msg.payload}")
        # Implementation: derive new keys, update vault, publish response
        await self.publish(HermesMessage(
            subject=HermesSubject.SIGNING_RESPONSE.value,
            payload={
                "request_id": msg.correlation_id,
                "status": "rotation_initiated",
                "new_keys": msg.payload.get("key_ids", []),
            }
        ))
    
    async def _handle_policy_update(self, msg: HermesMessage):
        """Handle policy update."""
        logger.info(f"Policy update: {msg.payload}")
        # Update vault configuration, capability manager, etc.
        await self.publish(HermesMessage(
            subject=HermesSubject.SIGNING_RESPONSE.value,
            payload={"request_id": msg.correlation_id, "status": "policy_updated"},
        ))
    
    async def _handle_capability_revoke(self, msg: HermesMessage):
        """Handle capability revocation."""
        logger.info(f"Capability revocation: {msg.payload}")
        # Revoke tokens in capability manager
        await self.publish(HermesMessage(
            subject=HermesSubject.SIGNING_RESPONSE.value,
            payload={"request_id": msg.correlation_id, "status": "revoked"},
        ))
    
    async def _handle_vault_config_change(self, msg: HermesMessage):
        """Handle vault configuration change."""
        logger.info(f"Vault config change: {msg.payload}")
        # Reload vault configuration
        await self.publish(HermesMessage(
            subject=HermesSubject.SIGNING_RESPONSE.value,
            payload={"request_id": msg.correlation_id, "status": "config_reloaded"},
        ))
    
    async def publish_signing_event(
        self,
        path: str,
        chain: str,
        signature: bytes,
        address: str,
        agent_id: str,
    ):
        """Publish signing event to Hermes."""
        await self.publish(HermesMessage(
            subject=HermesSubject.SIGNING_RESPONSE.value,
            payload={
                "path": path,
                "chain": chain,
                "signature": signature.hex(),
                "address": address,
                "agent_id": agent_id,
            }
        ))
    
    async def publish_key_derived(self, path: str, chain: str, address: str, agent_id: str):
        """Publish key derivation event."""
        await self.publish(HermesMessage(
            subject=HermesSubject.KEY_DERIVED.value,
            payload={
                "path": path,
                "chain": chain,
                "address": address,
                "agent_id": agent_id,
            }
        ))
    
    async def publish_audit_log(self, event_type: str, metadata: Dict[str, Any]):
        """Publish audit log to Hermes."""
        await self.publish(HermesMessage(
            subject=HermesSubject.AUDIT_LOG.value,
            payload={
                "event_type": event_type,
                "metadata": metadata,
            }
        ))
    
    async def close(self):
        """Close connections gracefully."""
        self._running = False
        
        # Drain subscriptions
        for sub in self._subscriptions:
            await sub.drain()
        
        if self.nc:
            await self.nc.drain()
            await self.nc.close()
        
        logger.info("Hermes client closed")


# Convenience function for quick integration
async def create_hermes_client(
    nats_url: str = None,
    vault=None,
) -> HermesClient:
    """Create and connect Hermes client."""
    nats_url = nats_url or os.getenv("NATS_URL", "nats://localhost:4222")
    
    client = HermesClient(nats_url=nats_url, vault=vault)
    await client.connect()
    return client


# Synchronous wrapper for non-async contexts
class SyncHermesClient:
    """Synchronous wrapper for Hermes client."""
    
    def __init__(self, nats_url: str = None, vault=None):
        self.nats_url = nats_url or os.getenv("NATS_URL", "nats://localhost:4222")
        self.vault = vault
        self._client: Optional[HermesClient] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    def _get_loop(self):
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop
    
    def connect(self):
        """Connect to Hermes."""
        loop = self._get_loop()
        self._client = HermesClient(nats_url=self.nats_url, vault=self.vault)
        loop.run_until_complete(self._client.connect())
    
    def publish(self, message: HermesMessage):
        """Publish message synchronously."""
        loop = self._get_loop()
        loop.run_until_complete(self._client.publish(message))
    
    def publish_signing(self, path: str, chain: str, signature: bytes, address: str, agent_id: str):
        """Publish signing event."""
        loop = self._get_loop()
        loop.run_until_complete(
            self._client.publish_signing_event(path, chain, signature, address, agent_id)
        )
    
    def publish_key_derived(self, path: str, chain: str, address: str, agent_id: str):
        """Publish key derived event."""
        loop = self._get_loop()
        loop.run_until_complete(
            self._client.publish_key_derived(path, chain, address, agent_id)
        )
    
    def publish_audit(self, event_type: str, metadata: Dict[str, Any]):
        """Publish audit log."""
        loop = self._get_loop()
        loop.run_until_complete(self._client.publish_audit_log(event_type, metadata))
    
    def close(self):
        """Close connection."""
        if self._client and self._loop:
            self._loop.run_until_complete(self._client.close())


# Integration with CyberCore Vault
class HermesIntegratedVault:
    """Vault wrapper that publishes events to Hermes."""
    
    def __init__(self, vault, hermes_client: SyncHermesClient):
        self.vault = vault
        self.hermes = hermes_client
    
    def sign(self, path: str, message: bytes, chain: str = "ethereum") -> bytes:
        """Sign and publish event."""
        signature = self.vault.sign(path, message, chain)
        address = self.vault.derive_address(path, chain)
        
        # Publish to Hermes
        self.hermes.publish_signing(path, chain, signature, address, "vault-agent")
        
        return signature
    
    def derive_address(self, path: str, chain: str = "ethereum") -> str:
        """Derive address and publish event."""
        address = self.vault.derive_address(path, chain)
        self.hermes.publish_key_derived(path, chain, address, "vault-agent")
        return address
    
    def __getattr__(self, name):
        """Delegate other methods to underlying vault."""
        return getattr(self.vault, name)


# Main entry point for testing
async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Create vault
    from cybercore.vault import create_vault, VaultConfig
    from cybercore.entropy import Argon2Provider, get_global_registry
    
    provider = Argon2Provider(passphrase="cybercore-master-seed-2024", country_code="US")
    registry = get_global_registry()
    registry.register(provider)
    
    vault = create_vault(VaultConfig(min_entropy_providers=1))
    vault.initialize()
    
    # Create Hermes client
    hermes = HermesClient(vault=vault)
    await hermes.connect()
    
    # Test publishing
    await hermes.publish_signing_event(
        path="m/44'/60'/0'/1/0",
        chain="ethereum",
        signature=b"test_sig",
        address="0x123...",
        agent_id="test-agent",
    )
    
    print("Hermes integration test complete")
    
    await hermes.close()


if __name__ == "__main__":
    asyncio.run(main())
"""AEGENTIX CyberDAW — Hermes NATS Integration.

Links CyberDAW to the AEGENTIS Hermes message bus for distributed multi-agent
coordination, live performance cue distribution, and audit logging.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import nats
    from nats.aio.client import Client as NATS
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False


class CyberDAWHermesBridge:
    """Pub/Sub connector bridging CyberDAW with Hermes NATS message bus."""

    def __init__(self, nats_url: str = "nats://127.0.0.1:4222", enabled: bool = True):
        self.nats_url = nats_url
        self.enabled = enabled and NATS_AVAILABLE
        self.nc: Optional[Any] = None
        self._connected = False
        self._command_callbacks: list[Callable[[dict[str, Any]], None]] = []

    async def connect(self) -> bool:
        if not self.enabled:
            logger.info("NATS not available or disabled; running CyberDAW in local loopback mode.")
            return False

        try:
            self.nc = await nats.connect(self.nats_url, connect_timeout=2.0)
            self._connected = True
            logger.info("Connected to Hermes NATS at %s", self.nats_url)

            # Subscribe to inbound agent commands
            await self.nc.subscribe("cyberdaw.command.inbound", cb=self._on_command_received)
            return True
        except Exception as e:
            logger.warning("Could not connect to Hermes NATS (%s); running local fallback.", e)
            self._connected = False
            return False

    async def _on_command_received(self, msg):
        try:
            data = json.loads(msg.data.decode("utf-8"))
            for cb in self._command_callbacks:
                cb(data)
        except Exception as e:
            logger.error("Error processing inbound CyberDAW command: %s", e)

    def register_command_handler(self, callback: Callable[[dict[str, Any]], None]):
        self._command_callbacks.append(callback)

    async def publish_telemetry(self, payload: dict[str, Any]):
        if self._connected and self.nc:
            try:
                data = json.dumps(payload).encode("utf-8")
                await self.nc.publish("cyberdaw.telemetry", data)
            except Exception as e:
                logger.error("Failed to publish telemetry to Hermes: %s", e)

    async def publish_cue(self, scene_name_or_index: Any, metadata: Optional[dict[str, Any]] = None):
        if self._connected and self.nc:
            try:
                event = {
                    "event": "SWARM_CUE_DISPATCH",
                    "target": str(scene_name_or_index),
                    "metadata": metadata or {},
                }
                await self.nc.publish("cyberdaw.cue", json.dumps(event).encode("utf-8"))
            except Exception as e:
                logger.error("Failed to publish cue to Hermes: %s", e)

    async def publish_emergency_stop(self, reason: str = "EMERGENCY_STOP"):
        if self._connected and self.nc:
            try:
                event = {"event": "EMERGENCY_STOP", "reason": reason}
                await self.nc.publish("cyberdaw.emergency_stop", json.dumps(event).encode("utf-8"))
            except Exception as e:
                logger.error("Failed to publish emergency stop to Hermes: %s", e)

    async def close(self):
        if self._connected and self.nc:
            try:
                await self.nc.drain()
                await self.nc.close()
            except Exception:
                pass
            self._connected = False

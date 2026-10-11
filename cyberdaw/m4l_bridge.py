from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Optional
import uuid

COMMANDS = {
    "transport", "tempo", "scene", "clip", "device", "parameter",
    "telemetry", "record", "stop",
}


def is_iso8601(value: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    candidate = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(candidate)
    except ValueError:
        return False
    return True


def validate_envelope(data: Any) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return False, ["envelope must be an object"]

    for field in ("version", "id", "timestamp", "source", "command"):
        if field not in data:
            errors.append(f"missing required field: {field}")

    if data.get("version") != "1.0":
        errors.append("version must be '1.0'")
    if not isinstance(data.get("id"), str) or not data.get("id"):
        errors.append("id must be a non-empty string")
    if not is_iso8601(str(data.get("timestamp", ""))):
        errors.append("timestamp must be an ISO-8601 string")
    if data.get("source") != "aegentix":
        errors.append("source must be 'aegentix'")

    command = data.get("command")
    if not isinstance(command, dict):
        errors.append("command must be an object")
    else:
        if "name" not in command:
            errors.append("command.name is required")
        elif command["name"] not in COMMANDS:
            errors.append(f"command.name '{command['name']}' is not supported")
        if "target" in command and command["target"] is not None and not isinstance(command["target"], str):
            errors.append("command.target must be a string or null")
        if "args" in command and not isinstance(command["args"], dict):
            errors.append("command.args must be an object")
        if "name" in command and command["name"] in {"telemetry", "record"} and "args" not in command:
            errors.append(f"command '{command['name']}' requires args")

    return not errors, errors


@dataclass(frozen=True)
class BridgeEnvelope:
    command: str
    args: dict[str, Any]
    target: Optional[str] = None
    envelope_id: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": "1.0",
            "id": self.envelope_id or str(uuid.uuid4()),
            "timestamp": self.timestamp or datetime.now(timezone.utc).isoformat(),
            "source": "aegentix",
            "command": {
                "name": self.command,
                "target": self.target,
                "args": self.args,
            },
        }


def make_envelope(command: str, args: Optional[dict[str, Any]] = None, target: Optional[str] = None) -> dict[str, Any]:
    if command not in COMMANDS:
        raise ValueError(f"unsupported command: {command}")
    return BridgeEnvelope(command=command, args=args or {}, target=target).to_dict()


@dataclass
class MaxForLiveBridgeAdapter:
    """Production-only adapter for the Max-for-Live bridge.

    Like AbletonProductionAdapter, this never infers success from a Trial
    process or endpoint. It accepts only explicit verified evidence.
    """

    name: str = "maxforlive_bridge"
    bridge_verified: bool = False
    evidence: Optional[str] = None

    def probe(self) -> Any:
        from .adapters import Availability, Capability

        if self.bridge_verified:
            return Capability(self.name, Availability.ONLINE, self.evidence or "bridge evidence supplied")
        return Capability(self.name, Availability.OFFLINE, "Max-for-Live bridge not verified")

    def verify(self) -> Any:
        from .adapters import Availability, Capability

        if self.bridge_verified and self.evidence:
            return Capability(self.name, Availability.VERIFIED, f"M4L bridge verified: {self.evidence}")
        return Capability(self.name, Availability.OFFLINE, "requires verified production Max-for-Live bridge")

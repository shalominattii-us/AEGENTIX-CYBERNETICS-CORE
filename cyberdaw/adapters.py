from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class Availability(str, Enum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    CONNECTED = "CONNECTED"
    VERIFIED = "VERIFIED"


@dataclass(frozen=True)
class Capability:
    name: str
    availability: Availability
    detail: str = ""


class Adapter(Protocol):
    name: str

    def probe(self) -> Capability: ...

    def verify(self) -> Capability: ...


class DevelopmentAdapter:
    def __init__(self, name: str, detail: str = "development/simulation") -> None:
        self.name = name
        self.detail = detail

    def probe(self) -> Capability:
        return Capability(self.name, Availability.ONLINE, self.detail)

    def verify(self) -> Capability:
        return Capability(self.name, Availability.VERIFIED, self.detail)


class AbletonProductionAdapter:
    """Production-only adapter contract.

    This intentionally never infers Suite/Max-for-Live availability from a Trial
    process or from an HTTP endpoint. The production environment must supply an
    explicit functional verification token/evidence.
    """

    name = "ableton_production"

    def __init__(self, suite_verified: bool = False, m4l_verified: bool = False, bridge_verified: bool = False) -> None:
        self.suite_verified = suite_verified
        self.m4l_verified = m4l_verified
        self.bridge_verified = bridge_verified

    def probe(self) -> Capability:
        return Capability(self.name, Availability.ONLINE if any((self.suite_verified, self.m4l_verified, self.bridge_verified)) else Availability.OFFLINE)

    def verify(self) -> Capability:
        if self.suite_verified and self.m4l_verified and self.bridge_verified:
            return Capability(self.name, Availability.VERIFIED, "Suite + Max for Live + bridge verified")
        return Capability(self.name, Availability.OFFLINE, "production Ableton environment not fully verified")


def capability_to_dict(cap: Capability) -> dict[str, Any]:
    return {"name": cap.name, "availability": cap.availability.value, "detail": cap.detail}

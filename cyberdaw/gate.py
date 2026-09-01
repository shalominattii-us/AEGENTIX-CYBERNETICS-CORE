from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class GateState(str, Enum):
    OFFLINE = "OFFLINE"
    BOOTING = "BOOTING"
    DEVELOPMENT = "DEVELOPMENT"
    VALIDATING = "VALIDATING"
    PRODUCTION_BLOCKED = "PRODUCTION_BLOCKED"
    PRODUCTION_READY = "PRODUCTION_READY"
    LIVE_PA_READY = "LIVE_PA_READY"
    DEGRADED = "DEGRADED"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    FAULT = "FAULT"


@dataclass(frozen=True)
class Check:
    name: str
    required: bool = True
    verified: bool = False
    detail: str = ""


REQUIRED_CHECKS: tuple[str, ...] = (
    "orbital",
    "ableton_production",
    "maxforlive_bridge",
    "obs",
    "audio_interface",
    "pa_routing",
    "recording",
    "stream",
    "swarm_cue",
    "emergency_stop",
    "watchdog",
    "resource_headroom",
    "offline_operation",
)


class ProductionGate:
    """Fail-closed production authorization.

    The gate deliberately separates service reachability from functional verification.
    Missing/unknown evidence is never promoted to success.
    """

    def __init__(self, checks: Iterable[Check] = ()) -> None:
        self._checks = {c.name: c for c in checks}
        self.emergency_latched = False

    def set_check(self, name: str, verified: bool, detail: str = "") -> None:
        self._checks[name] = Check(name=name, verified=verified, detail=detail)

    def checks(self) -> dict[str, Check]:
        return {name: self._checks.get(name, Check(name)) for name in REQUIRED_CHECKS}

    def production_blockers(self) -> list[str]:
        return [name for name, check in self.checks().items() if not check.verified]

    @property
    def production_ready(self) -> bool:
        return not self.emergency_latched and not self.production_blockers()

    @property
    def state(self) -> GateState:
        if self.emergency_latched:
            return GateState.EMERGENCY_STOP
        if self.production_ready:
            return GateState.LIVE_PA_READY
        return GateState.PRODUCTION_BLOCKED

    def emergency_stop(self, reason: str = "operator") -> None:
        self.emergency_latched = True
        self._checks["emergency_stop"] = Check("emergency_stop", verified=True, detail=f"latched: {reason}")

    def reset_emergency(self) -> None:
        self.emergency_latched = False

    def report(self) -> dict:
        checks = self.checks()
        return {
            "state": self.state.value,
            "production_ready": self.production_ready,
            "emergency_latched": self.emergency_latched,
            "checks": {
                name: {"verified": check.verified, "detail": check.detail}
                for name, check in checks.items()
            },
            "blockers": self.production_blockers(),
        }

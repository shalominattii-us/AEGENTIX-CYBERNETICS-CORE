"""Immersive access tiers and procedural gating model.

Versions/tiers define how deep a principal can see/control ("into the hoods") and what
cryptographic/authentication gates apply. Architecture is complete and enforceable in-code;
external filings/certifications are handled when those validity points arrive.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, FrozenSet, List, Optional, Set


class ImmersiveVersion(IntEnum):
    L0_OBSERVE = 0      # public/limited status
    L1_OPERATOR = 1     # local operator, basic controls
    L2_ENGINEER = 2     # engineering viewport, diagnostics, non-destructive ops
    L3_HYPERVISOR = 3   # deep "into the hoods" viewport, privileged controls
    L4_SOVEREIGN = 4    # sovereign root/architectural control (procedural multi-gate)


@dataclass(frozen=True)
class GateProfile:
    version: ImmersiveVersion
    name: str
    scopes: FrozenSet[str]
    requires_token: bool
    requires_encrypted_envelope: bool
    requires_procedural_steps: int  # number of procedural gate confirmations/challenges
    min_key_bits: int
    allow_local_noauth: bool  # honored only when global local-noauth policy allows
    description: str = ""


PROFILES: Dict[ImmersiveVersion, GateProfile] = {
    ImmersiveVersion.L0_OBSERVE: GateProfile(
        ImmersiveVersion.L0_OBSERVE, "observe", frozenset({"status.read", "hud.heartbeat.read"}),
        requires_token=False, requires_encrypted_envelope=False, requires_procedural_steps=0,
        min_key_bits=0, allow_local_noauth=True, description="Read-only limited status",
    ),
    ImmersiveVersion.L1_OPERATOR: GateProfile(
        ImmersiveVersion.L1_OPERATOR, "operator", frozenset({"status.read", "hud.read", "hud.heartbeat.read", "mcp.info", "mcp.list", "mcp.call.safe", "viewport.read"}),
        requires_token=True, requires_encrypted_envelope=False, requires_procedural_steps=1,
        min_key_bits=128, allow_local_noauth=True, description="Operator safe tools and limited viewport",
    ),
    ImmersiveVersion.L2_ENGINEER: GateProfile(
        ImmersiveVersion.L2_ENGINEER, "engineer", frozenset({"status.read", "hud.read", "hud.heartbeat.read", "mcp.info", "mcp.list", "mcp.call.safe", "mcp.*", "viewport.read", "viewport.summary", "diagnostics.read", "harness.read"}),
        requires_token=True, requires_encrypted_envelope=True, requires_procedural_steps=2,
        min_key_bits=256, allow_local_noauth=False, description="Engineering/hood diagnostics viewport (encrypted)",
    ),
    ImmersiveVersion.L3_HYPERVISOR: GateProfile(
        ImmersiveVersion.L3_HYPERVISOR, "hypervisor", frozenset({"*read", "viewport.*", "swarm.control", "orchestrator.dispatch", "config.read"}),
        requires_token=True, requires_encrypted_envelope=True, requires_procedural_steps=3,
        min_key_bits=256, allow_local_noauth=False, description="Hypervisor viewport into hoods with gated control",
    ),
    ImmersiveVersion.L4_SOVEREIGN: GateProfile(
        ImmersiveVersion.L4_SOVEREIGN, "sovereign", frozenset({"*"}),
        requires_token=True, requires_encrypted_envelope=True, requires_procedural_steps=4,
        min_key_bits=256, allow_local_noauth=False, description="Sovereign procedural multi-gate architecture control",
    ),
}

SCOPE_TO_MIN_VERSION = {
    "status.read": ImmersiveVersion.L0_OBSERVE,
    "hud.heartbeat.read": ImmersiveVersion.L0_OBSERVE,
    "mcp.info": ImmersiveVersion.L1_OPERATOR,
    "mcp.list": ImmersiveVersion.L1_OPERATOR,
    "mcp.call.safe": ImmersiveVersion.L1_OPERATOR,
    "mcp.call": ImmersiveVersion.L2_ENGINEER,
    "viewport.read": ImmersiveVersion.L1_OPERATOR,
    "viewport.summary": ImmersiveVersion.L2_ENGINEER,
    "viewport.hoods": ImmersiveVersion.L3_HYPERVISOR,
    "orchestrator.dispatch": ImmersiveVersion.L3_HYPERVISOR,
    "swarm.control": ImmersiveVersion.L3_HYPERVISOR,
    "admin.*": ImmersiveVersion.L4_SOVEREIGN,
}


def profile_for(version: int | ImmersiveVersion) -> GateProfile:
    try:
        v = ImmersiveVersion(int(version))
    except Exception:
        v = ImmersiveVersion.L1_OPERATOR
    return PROFILES[v]


def min_version_for_scope(scope: str) -> ImmersiveVersion:
    if scope in SCOPE_TO_MIN_VERSION:
        return SCOPE_TO_MIN_VERSION[scope]
    if scope.endswith(".read"):
        return ImmersiveVersion.L1_OPERATOR
    if "control" in scope or "dispatch" in scope or "admin" in scope:
        return ImmersiveVersion.L3_HYPERVISOR
    return ImmersiveVersion.L2_ENGINEER


def scope_allowed(profile: GateProfile, scope: str) -> bool:
    s = profile.scopes
    if "*" in s or scope in s:
        return True
    for pat in s:
        if pat.endswith("*") and scope.startswith(pat[:-1]):
            return True
        if pat.startswith("*") and scope.endswith(pat[1:]):
            return True
    head = scope.split(".", 1)[0] + ".*"
    return head in s

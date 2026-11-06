"""
Origin Dynamic Model Router & Policy Dispatcher
===============================================
Selects and dispatches model execution based on:
1. Security clearance level (enforces sovereign data privacy).
2. Latency budget (sub-50ms routes to bare-metal C / local NPU).
3. Network availability (offline air-gap fallback).
4. Cost & token budget constraints.
5. Registry-driven fast-task routing and sensitivity policy.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from core.gateway.config import MODEL_PROFILES, ModelProfile
from core.gateway.ringbuffer_adapter import (
    RingBufferAdapter,
    MSG_TYPE_INFER_REQ,
    MSG_TYPE_TOKEN,
    MSG_TYPE_EOS
)

try:
    from core.models.registry import get_model_registry
except Exception:
    get_model_registry = None  # type: ignore


@dataclass
class ModelRequest:
    prompt: str
    security_clearance: int = 1  # 1 to 5
    max_latency_ms: Optional[int] = None
    offline_mode: bool = False
    prefer_cloud: bool = False
    token_budget: Optional[int] = None
    task_type: Optional[str] = None  # "routine", "complex", "extraction", "sorting", "planning"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelRouteDecision:
    selected_model: str
    profile: ModelProfile
    fallback_chain: List[str]
    reason: str


class ModelRouter:
    """Intelligent router selecting the optimal execution engine."""

    def __init__(self, profiles: Optional[Dict[str, ModelProfile]] = None, routing: Optional[Dict[str, Any]] = None):
        self.profiles = profiles or MODEL_PROFILES
        self.routing = routing or {}
        if not self.routing and get_model_registry:
            try:
                self.routing = get_model_registry().routing() or {}
            except Exception:
                self.routing = {}

    def _local_fallbacks(self, req: ModelRequest) -> List[str]:
        # Prefer native/local tiers for sensitive/offline paths.
        locals_ = [k for k, p in self.profiles.items() if getattr(p, "tier", "").startswith("edge")]
        # stable preference
        order = ["titan-c-native", "sparkx", "spark-x2.6-1.7b", "titan-local", "laya", "qwen2.5:1.5b", "qwen2.5:7b"]
        out = [m for m in order if m in self.profiles]
        out += [m for m in locals_ if m not in out]
        if req.security_clearance >= 4 or req.offline_mode:
            # avoid cloud fallbacks entirely in sensitive/offline mode
            return out[:4] or ["titan-c-native"]
        return out[:4]

    def _is_sensitive(self, req: ModelRequest) -> bool:
        min_clr = int(self.routing.get("sensitive_clearance_min", 4) or 4)
        prefer_local = bool(self.routing.get("prefer_local_for_sensitive", True))
        return bool(req.offline_mode or req.security_clearance >= min_clr or (prefer_local and req.security_clearance >= max(1, min_clr - 1)))

    def _pick_local(self, req: ModelRequest, preferred: Optional[List[str]] = None) -> ModelRouteDecision:
        candidates = []
        for name in (preferred or []):
            if name in self.profiles:
                candidates.append(name)
        candidates += self._local_fallbacks(req)
        # de-dupe preserving order
        seen = set(); chain = []
        for c in candidates:
            if c not in seen and c in self.profiles:
                seen.add(c); chain.append(c)
        selected = chain[0] if chain else "titan-local"
        if selected not in self.profiles and self.profiles:
            selected = next(iter(self.profiles.keys()))
        return ModelRouteDecision(
            selected_model=selected,
            profile=self.profiles[selected],
            fallback_chain=[c for c in chain[1:5] if c != selected],
            reason="Local/sensitive policy enforced" + (" (offline)" if req.offline_mode else "") + (f" clearance={req.security_clearance}" if req.security_clearance else ""),
        )

    def route(self, req: ModelRequest) -> ModelRouteDecision:
        # Rule 0: registry-driven fast-task routing, but never leak sensitive/offline tasks to cloud.
        fast_map = self.routing.get("task_fast_models") or {}
        if req.task_type:
            fast = fast_map.get(req.task_type)
            if fast and fast in self.profiles:
                prof = self.profiles[fast]
                if not self._is_sensitive(req) and not getattr(prof, "tier", "").startswith("edge"):
                    pass  # cloud fast model allowed only when not sensitive
                else:
                    # if sensitive/offline and fast is non-local, force local; else use fast
                    if self._is_sensitive(req) and not getattr(prof, "tier", "").startswith("edge"):
                        return self._pick_local(req, preferred=self._local_fallbacks(req))
                    return ModelRouteDecision(
                        selected_model=fast,
                        profile=prof,
                        fallback_chain=[m for m in self._local_fallbacks(req) if m != fast][:4],
                        reason=f"Registry fast-task routing for {req.task_type}"
                    )
            # Backward-compatible fast path
            if req.task_type in ("routine", "extraction", "sorting", "planning", "tool_routing") and "sparkx" in self.profiles:
                if self._is_sensitive(req):
                    # sparkx is local; OK
                    pass
                return self._pick_local(req, preferred=["sparkx"] if self._is_sensitive(req) else ["sparkx"]) if self._is_sensitive(req) else ModelRouteDecision(
                    selected_model="sparkx",
                    profile=self.profiles["sparkx"],
                    fallback_chain=[m for m in self._local_fallbacks(req) if m != "sparkx"][:4],
                    reason=f"Fast-task routing for {req.task_type}"
                )

        # Rule 1: Sovereign Confidentiality / Air-gap / sensitive policy
        if self._is_sensitive(req):
            if req.max_latency_ms and req.max_latency_ms <= 50 and "titan-c-native" in self.profiles:
                return ModelRouteDecision(
                    "titan-c-native",
                    self.profiles["titan-c-native"],
                    [m for m in self._local_fallbacks(req) if m != "titan-c-native"][:4],
                    "Sensitive/low-latency local enforcement",
                )
            return self._pick_local(req)

        # Rule 2: Ultra-low latency edge requirement (<50ms)
        if req.max_latency_ms is not None and req.max_latency_ms <= 50:
            selected = "titan-c-native"
            fallback = ["titan-local"]
            reason = f"Latency budget of {req.max_latency_ms}ms demands bare-metal C edge inference"
            return ModelRouteDecision(
                selected_model=selected,
                profile=self.profiles[selected],
                fallback_chain=fallback,
                reason=reason
            )

        # Rule 3: Complex reasoning cloud preference with budget
        if req.prefer_cloud and not req.offline_mode:
            selected = "gemini"
            fallback = ["claude", "titan-local"]
            reason = "Cloud reasoning requested for extended context"
            return ModelRouteDecision(
                selected_model=selected,
                profile=self.profiles[selected],
                fallback_chain=fallback,
                reason=reason
            )

        # Rule 4: Balanced default
        selected = "gemini" if not req.offline_mode else "titan-local"
        fallback = ["titan-local", "titan-c-native"]
        reason = "Default balanced routing"
        return ModelRouteDecision(
            selected_model=selected,
            profile=self.profiles[selected],
            fallback_chain=fallback,
            reason=reason
        )

    def execute_mock_edge_infer(self, prompt: str, rb_adapter: Optional[RingBufferAdapter] = None) -> str:
        """
        Executes mock edge inference directly over shared-memory ring buffer or synthetic streaming,
        for development and CI validation without requiring GGUF weights.
        """
        tokens = ["Synthesizing", " edge", " context:", f" processed '{prompt[:20]}...'", " [EXEC_OK]"]
        if rb_adapter:
            for tok in tokens:
                rb_adapter.push(MSG_TYPE_TOKEN, tok.encode("utf-8"))
            rb_adapter.push(MSG_TYPE_EOS, b"")
        return "".join(tokens)

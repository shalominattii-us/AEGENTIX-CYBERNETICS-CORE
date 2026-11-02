"""
Origin Dynamic Model Router & Policy Dispatcher
===============================================
Selects and dispatches model execution based on:
1. Security clearance level (enforces sovereign data privacy).
2. Latency budget (sub-50ms routes to bare-metal C / local NPU).
3. Network availability (offline air-gap fallback).
4. Cost & token budget constraints.
5. SparkX 2.6-1.7B Tier 1 fast execution for routine tasks.
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

    def __init__(self, profiles: Optional[Dict[str, ModelProfile]] = None):
        self.profiles = profiles or MODEL_PROFILES

    def route(self, req: ModelRequest) -> ModelRouteDecision:
        # Rule 0: SparkX Tier 1 fast execution for routine tasks
        if req.task_type in ("routine", "extraction", "sorting", "planning", "tool_routing"):
            if "sparkx" in self.profiles:
                fallback = ["titan-local", "laya"]
                if req.security_clearance >= 4 or req.offline_mode:
                    fallback = ["titan-c-native"]
                return ModelRouteDecision(
                    selected_model="sparkx",
                    profile=self.profiles["sparkx"],
                    fallback_chain=fallback,
                    reason=f"SparkX Tier 1 fast execution for {req.task_type} task"
                )

        # Rule 1: Sovereign Confidentiality / Air-gap
        if req.security_clearance >= 4 or req.offline_mode:
            # Force local edge execution only
            if req.max_latency_ms and req.max_latency_ms <= 50:
                selected = "titan-c-native"
                fallback = ["titan-local"]
                reason = "Sovereign high-security clearance & low latency constraint enforced"
            else:
                selected = "titan-local" if "titan-local" in self.profiles else "titan-c-native"
                fallback = ["titan-c-native"]
                reason = "Sovereign high-security clearance enforced local execution"
            return ModelRouteDecision(
                selected_model=selected,
                profile=self.profiles[selected],
                fallback_chain=fallback,
                reason=reason
            )

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

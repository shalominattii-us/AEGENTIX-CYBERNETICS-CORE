"""
Aegentix Gateway Model Configuration & Execution Profiles
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ModelProfile:
    name: str
    endpoint: str
    tier: str  # "edge_native", "edge_local", "cloud_frontier"
    max_latency_ms: int
    security_clearance_min: int  # 1 (public) to 5 (top-secret sovereign)
    supports_streaming: bool = True
    context_window: int = 4096
    cost_per_million_tokens: float = 0.0


MODEL_PROFILES: Dict[str, ModelProfile] = {
    "titan-c-native": ModelProfile(
        name="titan-c-native",
        endpoint="shm://aegentix_ipc_ringbuf",
        tier="edge_native",
        max_latency_ms=25,
        security_clearance_min=4,
        supports_streaming=True,
        context_window=4096,
        cost_per_million_tokens=0.0,
    ),
    "titan-local": ModelProfile(
        name="titan-local",
        endpoint="local-radeon-890m",
        tier="edge_local",
        max_latency_ms=150,
        security_clearance_min=3,
        supports_streaming=True,
        context_window=8192,
        cost_per_million_tokens=0.0,
    ),
    "sparkx": ModelProfile(
        name="sparkx",
        endpoint="http://127.0.0.1:11434",
        tier="edge_local",
        max_latency_ms=50,
        security_clearance_min=3,
        supports_streaming=True,
        context_window=262144,
        cost_per_million_tokens=0.0,
    ),
    "spark-x2.6-1.7b": ModelProfile(
        name="spark-x2.6-1.7b",
        endpoint="http://127.0.0.1:11434",
        tier="edge_local",
        max_latency_ms=50,
        security_clearance_min=3,
        supports_streaming=True,
        context_window=262144,
        cost_per_million_tokens=0.0,
    ),
    "laya": ModelProfile(
        name="laya",
        endpoint="http://127.0.0.1:11434/v1/chat/completions",
        tier="edge_local",
        max_latency_ms=300,
        security_clearance_min=3,
        supports_streaming=True,
        context_window=16384,
        cost_per_million_tokens=0.0,
    ),
    "gemini": ModelProfile(
        name="gemini",
        endpoint="gemini-2.5-flash",
        tier="cloud_frontier",
        max_latency_ms=1200,
        security_clearance_min=1,
        supports_streaming=True,
        context_window=1000000,
        cost_per_million_tokens=0.15,
    ),
    "claude": ModelProfile(
        name="claude",
        endpoint="claude-3-5-sonnet",
        tier="cloud_frontier",
        max_latency_ms=2000,
        security_clearance_min=1,
        supports_streaming=True,
        context_window=200000,
        cost_per_million_tokens=3.0,
    ),
}

# Legacy mapping for backwards compatibility
AVAILABLE_MODELS = {k: v.endpoint for k, v in MODEL_PROFILES.items()}


# --- AEGENTIX model housing registry merge (backward compatible) ---
try:
    from core.models.registry import get_model_registry
    _reg = get_model_registry()
    for _mid, _d in _reg.to_profiles_dict().items():
        try:
            _existing = MODEL_PROFILES.get(_mid)
            _name = _d.get('name') or _mid
            _ep = _d.get('endpoint') or (_existing.endpoint if _existing else '')
            _tier = _d.get('tier') or (_existing.tier if _existing else 'edge_local')
            _lat = int(_d.get('max_latency_ms') or (_existing.max_latency_ms if _existing else 500))
            _clr = int(_d.get('security_clearance_min') or (_existing.security_clearance_min if _existing else 1))
            _stream = bool(_d.get('supports_streaming', _existing.supports_streaming if _existing else True))
            _ctx = int(_d.get('context_window') or (_existing.context_window if _existing else 4096))
            _cost = float(_d.get('cost_per_million_tokens') if _d.get('cost_per_million_tokens') is not None else (_existing.cost_per_million_tokens if _existing else 0.0))
            MODEL_PROFILES[_mid] = ModelProfile(name=_name, endpoint=_ep, tier=_tier, max_latency_ms=_lat, security_clearance_min=_clr, supports_streaming=_stream, context_window=_ctx, cost_per_million_tokens=_cost)
        except Exception:
            pass
    AVAILABLE_MODELS = {k: v.endpoint for k, v in MODEL_PROFILES.items()}
except Exception:
    pass

from __future__ import annotations
import json, os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass
class ModelSpec:
    id: str
    provider: str = 'unknown'
    tier: str = 'edge_local'
    max_latency_ms: int = 500
    security_clearance_min: int = 1
    supports_streaming: bool = True
    context_window: int = 4096
    cost_per_million_tokens: float = 0.0
    endpoint: str = ''
    ollama_model: str = ''
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

class ModelRegistry:
    def __init__(self, path: Optional[str]=None):
        self.path = Path(path or os.environ.get('AEGENTIX_MODEL_REGISTRY', r'C:\AEGENTIX-CYBERNETICS-CORE\config\models.registry.json'))
        self._data: Dict[str, Any] = {}
        self._models: Dict[str, ModelSpec] = {}
        self.reload()

    def reload(self) -> None:
        self._data = {}
        self._models = {}
        try:
            if self.path.exists():
                self._data = json.loads(self.path.read_text(encoding='utf-8-sig'))
        except Exception:
            self._data = {}
        for m in (self._data.get('models') or []):
            if not isinstance(m, dict) or not m.get('id'): continue
            known = {f.name for f in ModelSpec.__dataclass_fields__.values()}  # type: ignore
            spec = ModelSpec(**{k:v for k,v in m.items() if k in known})
            spec.extra = {k:v for k,v in m.items() if k not in known}
            self._models[spec.id] = spec

    def list(self, enabled_only: bool=False) -> List[ModelSpec]:
        items = list(self._models.values())
        if enabled_only:
            items = [m for m in items if m.enabled]
        return sorted(items, key=lambda m: m.id)

    def get(self, model_id: str) -> Optional[ModelSpec]:
        return self._models.get(model_id)

    def providers(self) -> Dict[str, Any]:
        return dict(self._data.get('providers') or {})

    def routing(self) -> Dict[str, Any]:
        return dict(self._data.get('routing') or {})

    def to_profiles_dict(self) -> Dict[str, Dict[str, Any]]:
        # Shape compatible with gateway ModelProfile construction.
        out = {}
        for m in self.list():
            out[m.id] = {
                'name': m.id, 'endpoint': m.endpoint or m.ollama_model or '', 'tier': m.tier,
                'max_latency_ms': m.max_latency_ms, 'security_clearance_min': m.security_clearance_min,
                'supports_streaming': m.supports_streaming, 'context_window': m.context_window,
                'cost_per_million_tokens': m.cost_per_million_tokens,
            }
        return out

_singleton: Optional[ModelRegistry] = None

def get_model_registry() -> ModelRegistry:
    global _singleton
    if _singleton is None:
        _singleton = ModelRegistry()
    return _singleton

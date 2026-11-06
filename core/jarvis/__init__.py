"""JARVIS integration: HUD resolver, stratus/memory bridges, Infinite Brain OS facade."""

__all__ = [
    "InfiniteBrainOS",
    "get_infinite_brain_os",
    "load_manifest",
    "resolve_hud",
]

try:
    from .infinite_brain_os import InfiniteBrainOS, get_infinite_brain_os
except Exception:  # pragma: no cover
    InfiniteBrainOS = None  # type: ignore
    get_infinite_brain_os = None  # type: ignore

try:
    from .resolve_hud import load_manifest, resolve_hud
except Exception:  # pragma: no cover
    load_manifest = None  # type: ignore
    resolve_hud = None  # type: ignore

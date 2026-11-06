"""AEGENTIX model housing: registry, profiles, provider adapters (core plumbing layer)."""
from .registry import ModelRegistry, get_model_registry
__all__ = ["ModelRegistry", "get_model_registry"]

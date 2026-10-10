"""
Abstract base class and registry for entropy providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List
import threading
import logging

from .jurisdiction import validate_jurisdiction, JurisdictionalError

logger = logging.getLogger(__name__)


class EntropyProvider(ABC):
    """Base class for all entropy providers."""
    
    def __init__(self, name: str, country_code: str = "US", region: str = "", entity_name: str = ""):
        self.name = name
        self.country_code = country_code
        self.region = region
        self.entity_name = entity_name
        self._lock = threading.RLock()
        
        # Validate jurisdiction at init
        if not validate_jurisdiction(country_code, region, entity_name):
            raise JurisdictionalError(
                f"Provider {name} excluded by jurisdictional policy: "
                f"country={country_code}, region={region}, entity={entity_name}"
            )
    
    @abstractmethod
    def get_entropy(self, length: int = 64) -> bytes:
        """Get cryptographically secure entropy bytes."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Check if provider is healthy and available."""
        pass
    
    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Return provider type identifier."""
        pass


class EntropyRegistry:
    """Registry for managing multiple entropy providers with quorum."""
    
    def __init__(self, min_providers: int = 2):
        self._providers: Dict[str, EntropyProvider] = {}
        self._min_providers = min_providers
        self._lock = threading.RLock()
    
    def register(self, provider: EntropyProvider) -> None:
        with self._lock:
            self._providers[provider.name] = provider
            logger.info(f"Registered entropy provider: {provider.name} ({provider.provider_type})")
    
    def unregister(self, name: str) -> None:
        with self._lock:
            if name in self._providers:
                del self._providers[name]
                logger.info(f"Unregistered entropy provider: {name}")
    
    def get_provider(self, name: str) -> Optional[EntropyProvider]:
        with self._lock:
            return self._providers.get(name)
    
    def list_providers(self) -> List[EntropyProvider]:
        with self._lock:
            return list(self._providers.values())
    
    def get_healthy_providers(self) -> List[EntropyProvider]:
        with self._lock:
            return [p for p in self._providers.values() if p.health_check()]
    
    def get_entropy_quorum(self, length: int = 64) -> bytes:
        """
        Get entropy from multiple providers and XOR combine.
        Requires minimum number of healthy providers.
        """
        healthy = self.get_healthy_providers()
        if len(healthy) < self._min_providers:
            raise RuntimeError(
                f"Insufficient healthy entropy providers: "
                f"{len(healthy)}/{self._min_providers} minimum"
            )
        
        # Get entropy from all healthy providers
        entropy_chunks = []
        for provider in healthy:
            try:
                entropy = provider.get_entropy(length)
                entropy_chunks.append(entropy)
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
        
        if len(entropy_chunks) < self._min_providers:
            raise RuntimeError("Failed to get entropy from quorum")
        
        # XOR combine all entropy sources
        combined = bytearray(length)
        for chunk in entropy_chunks:
            for i in range(length):
                combined[i] ^= chunk[i]
        
        return bytes(combined)
    
    def get_single_entropy(self, provider_name: str, length: int = 64) -> bytes:
        """Get entropy from a specific provider."""
        with self._lock:
            provider = self._providers.get(provider_name)
            if not provider:
                raise KeyError(f"Provider not found: {provider_name}")
            if not provider.health_check():
                raise RuntimeError(f"Provider unhealthy: {provider_name}")
            return provider.get_entropy(length)


# Global registry instance
_global_registry: Optional[EntropyRegistry] = None


def get_global_registry() -> EntropyRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = EntropyRegistry()
        initialize_default_registry(_global_registry)
    return _global_registry


def initialize_default_registry(registry: EntropyRegistry = None) -> EntropyRegistry:
    """Initialize registry with available providers."""
    if registry is None:
        registry = get_global_registry()
    
    # Try to register each provider type if not already registered
    for provider_class in [TPMProvider, HSMProvider, ShamirProvider, Argon2Provider]:
        try:
            provider = provider_class()
            if provider.name not in registry._providers:
                registry.register(provider)
        except Exception as e:
            logger.warning(f"Failed to initialize {provider_class.__name__}: {e}")
    
    return registry


# Import concrete providers (lazy to avoid circular imports)
def _import_providers():
    global TPMProvider, HSMProvider, ShamirProvider, Argon2Provider
    from .tpm_provider import TPMProvider
    from .hsm_provider import HSMProvider
    from .shamir_provider import ShamirProvider
    from .argon2_provider import Argon2Provider

_import_providers()
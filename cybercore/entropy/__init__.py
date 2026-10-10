"""
CyberCore Entropy Module - Multi-backend entropy with jurisdictional exclusion.

Exports:
- EntropyProvider (abstract base)
- EntropyRegistry (quorum manager)
- TPMProvider, HSMProvider, ShamirProvider, Argon2Provider
- Jurisdictional validation
"""

from .provider import (
    EntropyProvider,
    EntropyRegistry,
    get_global_registry,
    initialize_default_registry,
)

from .jurisdiction import (
    validate_jurisdiction,
    enforce_jurisdiction,
    is_excluded_country,
    is_excluded_region,
    is_sharia_compliant_entity,
    JurisdictionalError,
    EXCLUDED_COUNTRIES,
    EXCLUDED_REGIONS,
)

from .tpm_provider import (
    TPMProvider,
    TPM2PyTSSProvider,
    create_tpm_provider,
)

from .hsm_provider import (
    HSMProvider,
    create_hsm_provider,
)

from .shamir_provider import (
    ShamirProvider,
    ShamirShare,
    ShamirSecretSharing,
    create_shamir_provider,
    generate_shamir_shares,
)

from .argon2_provider import (
    Argon2Provider,
    create_argon2_provider,
    prompt_passphrase,
)

__all__ = [
    # Base
    "EntropyProvider",
    "EntropyRegistry",
    "get_global_registry",
    "initialize_default_registry",
    # Jurisdiction
    "validate_jurisdiction",
    "enforce_jurisdiction",
    "is_excluded_country",
    "is_excluded_region",
    "is_sharia_compliant_entity",
    "JurisdictionalError",
    "EXCLUDED_COUNTRIES",
    "EXCLUDED_REGIONS",
    # Providers
    "TPMProvider",
    "TPM2PyTSSProvider",
    "create_tpm_provider",
    "HSMProvider",
    "create_hsm_provider",
    "ShamirProvider",
    "ShamirShare",
    "ShamirSecretSharing",
    "create_shamir_provider",
    "generate_shamir_shares",
    "Argon2Provider",
    "create_argon2_provider",
    "prompt_passphrase",
]
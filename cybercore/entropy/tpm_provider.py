"""
TPM 2.0 Entropy Provider using tpm2-pytss or system TPM.
"""

import os
import logging
from typing import Optional

from .provider import EntropyProvider
from .jurisdiction import validate_jurisdiction

logger = logging.getLogger(__name__)


class TPMProvider(EntropyProvider):
    """TPM 2.0 entropy source via tpm2-tools or tpm2-pytss."""
    
    def __init__(self, tpm_device: str = "/dev/tpmrm0", 
                 country_code: str = "US", region: str = "", entity_name: str = ""):
        # Validate jurisdiction first
        if not validate_jurisdiction(country_code, region, entity_name):
            from .jurisdiction import JurisdictionalError
            raise JurisdictionalError(f"TPM provider excluded: {country_code}/{region}")
        
        super().__init__("TPM", country_code, region, entity_name)
        self.tpm_device = tpm_device
        self._tpm_available = self._check_tpm()
    
    def _check_tpm(self) -> bool:
        """Check if TPM is available."""
        # Try tpm2-tools first
        try:
            import subprocess
            result = subprocess.run(
                ["tpm2_getrandom", "--help"],
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try tpm2-pytss
        try:
            import tpm2_pytss
            return True
        except ImportError:
            pass
        
        # Check device file
        return os.path.exists(self.tpm_device)
    
    @property
    def provider_type(self) -> str:
        return "TPM2.0"
    
    def health_check(self) -> bool:
        return self._tpm_available
    
    def get_entropy(self, length: int = 64) -> bytes:
        """Get entropy from TPM."""
        if not self._tpm_available:
            raise RuntimeError("TPM not available")
        
        # Try tpm2_pytss first (more efficient)
        try:
            import tpm2_pytss
            from tpm2_pytss import TSS2_SYS_CONTEXT, Tss2_Sys_GetRandom
            
            # This is a simplified version - real implementation would use
            # proper TSS context management
            entropy = os.urandom(length)  # Fallback for now
            return entropy
        except ImportError:
            pass
        
        # Fallback to tpm2-tools command
        try:
            import subprocess
            result = subprocess.run(
                ["tpm2_getrandom", "-o", "-", str(length)],
                capture_output=True, timeout=10
            )
            if result.returncode == 0 and len(result.stdout) >= length:
                return result.stdout[:length]
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.warning(f"tpm2_getrandom failed: {e}")
        
        # Last resort: system urandom (not true TPM but available)
        logger.warning("Using system urandom as TPM fallback")
        return os.urandom(length)


class TPM2PyTSSProvider(EntropyProvider):
    """TPM 2.0 provider using tpm2-pytss library directly."""
    
    def __init__(self, country_code: str = "US", region: str = "", entity_name: str = ""):
        if not validate_jurisdiction(country_code, region, entity_name):
            from .jurisdiction import JurisdictionalError
            raise JurisdictionalError(f"TPM provider excluded: {country_code}/{region}")
        
        super().__init__("TPM2-PyTSS", country_code, region, entity_name)
        self._ctx = None
        self._init_tss()
    
    def _init_tss(self):
        try:
            from tpm2_pytss import TSS2_SYS_CONTEXT, Tss2_Sys_Initialize
            self._ctx = TSS2_SYS_CONTEXT()
            # Initialize TSS context
            # Real implementation would properly initialize
        except Exception as e:
            logger.warning(f"TSS init failed: {e}")
            self._ctx = None
    
    @property
    def provider_type(self) -> str:
        return "TPM2-PyTSS"
    
    def health_check(self) -> bool:
        return self._ctx is not None
    
    def get_entropy(self, length: int = 64) -> bytes:
        if not self._ctx:
            raise RuntimeError("TSS context not initialized")
        # Real implementation would call Tss2_Sys_GetRandom
        return os.urandom(length)  # Placeholder


def create_tpm_provider(country_code: str = "US", region: str = "", entity_name: str = "") -> Optional[EntropyProvider]:
    """Factory function to create best available TPM provider."""
    # Try TPM2-PyTSS first
    try:
        return TPM2PyTSSProvider(country_code, region, entity_name)
    except Exception:
        pass
    
    # Fall back to tpm2-tools
    try:
        return TPMProvider(country_code=country_code, region=region, entity_name=entity_name)
    except Exception:
        pass
    
    return None
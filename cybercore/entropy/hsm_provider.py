"""
HSM Entropy Provider for PKCS#11 compatible HSMs.
Supports: AWS CloudHSM, Azure Dedicated HSM, YubiHSM, Thales, Utimaco, etc.
"""

import os
import logging
from typing import Optional, List
import ctypes
import ctypes.util

from .provider import EntropyProvider
from .jurisdiction import validate_jurisdiction, JurisdictionalError

logger = logging.getLogger(__name__)

# PKCS#11 constants
CKR_OK = 0x00000000
CKF_RNG = 0x00000200
CKM_AES_KEY_GEN = 0x000010D0


class HSMProvider(EntropyProvider):
    """PKCS#11 HSM entropy provider."""
    
    def __init__(self, library_path: str = None, slot: int = 0, 
                 pin: str = None, label: str = None,
                 country_code: str = "US", region: str = "", entity_name: str = ""):
        if not validate_jurisdiction(country_code, region, entity_name):
            raise JurisdictionalError(f"HSM provider excluded: {country_code}/{region}")
        
        super().__init__("HSM-PKCS11", country_code, region, entity_name)
        self.library_path = library_path or self._find_pkcs11_lib()
        self.slot = slot
        self.pin = pin
        self.label = label
        self._lib = None
        self._session = None
        self._initialized = False
        
        if self.library_path:
            self._initialize()
    
    def _find_pkcs11_lib(self) -> Optional[str]:
        """Find PKCS#11 library on system."""
        candidates = [
            # AWS CloudHSM
            "/opt/cloudhsm/lib/libcloudhsm_pkcs11.so",
            # Azure Dedicated HSM (SafeNet Luna)
            "/usr/safenet/lunaclient/lib/libCryptoki2_64.so",
            # YubiHSM
            "/usr/lib/yubihsm-pkcs11.so",
            # Thales nShield
            "/opt/nfast/toolkits/pkcs11/libcknfast.so",
            # Utimaco
            "/usr/lib/libcs2_pkcs11.so",
            # Generic OpenSC
            "/usr/lib/opensc-pkcs11.so",
            "/usr/local/lib/opensc-pkcs11.so",
            # Windows
            "C:\\Program Files\\Amazon\\CloudHSM\\lib\\cloudhsm_pkcs11.dll",
            "C:\\Program Files\\SafeNet\\LunaClient\\cryptoki.dll",
            "C:\\Program Files\\Yubico\\YubiHSM\\bin\\yubihsm_pkcs11.dll",
        ]
        
        for path in candidates:
            if os.path.exists(path):
                return path
        
        # Try ctypes.util.find_library
        return ctypes.util.find_library("pkcs11")
    
    def _initialize(self) -> bool:
        """Initialize PKCS#11 library and open session."""
        try:
            self._lib = ctypes.CDLL(self.library_path)
            
            # Define function signatures
            self._lib.C_Initialize.argtypes = [ctypes.c_void_p]
            self._lib.C_Initialize.restype = ctypes.c_ulong
            
            self._lib.C_Finalize.argtypes = [ctypes.c_void_p]
            self._lib.C_Finalize.restype = ctypes.c_ulong
            
            self._lib.C_GetSlotList.argtypes = [
                ctypes.c_ubyte, ctypes.POINTER(ctypes.c_ulong), ctypes.POINTER(ctypes.c_ulong)
            ]
            self._lib.C_GetSlotList.restype = ctypes.c_ulong
            
            self._lib.C_OpenSession.argtypes = [
                ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)
            ]
            self._lib.C_OpenSession.restype = ctypes.c_ulong
            
            self._lib.C_CloseSession.argtypes = [ctypes.c_ulong]
            self._lib.C_CloseSession.restype = ctypes.c_ulong
            
            self._lib.C_Login.argtypes = [
                ctypes.c_ulong, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_ulong
            ]
            self._lib.C_Login.restype = ctypes.c_ulong
            
            self._lib.C_GenerateRandom.argtypes = [
                ctypes.c_ulong, ctypes.c_void_p, ctypes.c_ulong
            ]
            self._lib.C_GenerateRandom.restype = ctypes.c_ulong
            
            # Initialize
            rv = self._lib.C_Initialize(None)
            if rv != CKR_OK:
                logger.error(f"C_Initialize failed: 0x{rv:08X}")
                return False
            
            # Get slot list
            slot_count = ctypes.c_ulong(0)
            rv = self._lib.C_GetSlotList(True, None, ctypes.byref(slot_count))
            if rv != CKR_OK or slot_count.value == 0:
                logger.error(f"No slots available: 0x{rv:08X}")
                return False
            
            slots = (ctypes.c_ulong * slot_count.value)()
            rv = self._lib.C_GetSlotList(True, slots, ctypes.byref(slot_count))
            if rv != CKR_OK:
                logger.error(f"C_GetSlotList failed: 0x{rv:08X}")
                return False
            
            # Use specified slot or first available
            target_slot = self.slot if self.slot < slot_count.value else slots[0]
            
            # Open session
            session = ctypes.c_ulong(0)
            rv = self._lib.C_OpenSession(
                target_slot, CKF_RNG, None, None, ctypes.byref(session)
            )
            if rv != CKR_OK:
                logger.error(f"C_OpenSession failed: 0x{rv:08X}")
                return False
            
            self._session = session.value
            
            # Login if PIN provided
            if self.pin:
                rv = self._lib.C_Login(
                    self._session, 1,  # CKU_USER = 1
                    self.pin.encode(), len(self.pin)
                )
                if rv != CKR_OK:
                    logger.error(f"C_Login failed: 0x{rv:08X}")
                    return False
            
            self._initialized = True
            logger.info(f"HSM initialized: {self.library_path}, slot {target_slot}")
            return True
            
        except Exception as e:
            logger.error(f"HSM initialization failed: {e}")
            return False
    
    @property
    def provider_type(self) -> str:
        return "HSM-PKCS11"
    
    def health_check(self) -> bool:
        if not self._initialized or not self._session:
            return False
        try:
            # Test with small entropy request
            test_buf = ctypes.create_string_buffer(32)
            rv = self._lib.C_GenerateRandom(self._session, test_buf, 32)
            return rv == CKR_OK
        except Exception:
            return False
    
    def get_entropy(self, length: int = 64) -> bytes:
        if not self._initialized:
            raise RuntimeError("HSM not initialized")
        if not self._session:
            raise RuntimeError("No active HSM session")
        
        buf = ctypes.create_string_buffer(length)
        rv = self._lib.C_GenerateRandom(self._session, buf, length)
        if rv != CKR_OK:
            raise RuntimeError(f"C_GenerateRandom failed: 0x{rv:08X}")
        
        return bytes(buf.raw)
    
    def close(self):
        """Close session and finalize."""
        if self._session and self._lib:
            self._lib.C_CloseSession(self._session)
            self._session = None
        if self._lib:
            self._lib.C_Finalize(None)
            self._lib = None
        self._initialized = False
    
    def __del__(self):
        self.close()


def create_hsm_provider(country_code: str = "US", region: str = "", entity_name: str = "") -> Optional[EntropyProvider]:
    """Factory for HSM provider."""
    try:
        return HSMProvider(country_code=country_code, region=region, entity_name=entity_name)
    except Exception as e:
        logger.warning(f"HSM provider creation failed: {e}")
        return None
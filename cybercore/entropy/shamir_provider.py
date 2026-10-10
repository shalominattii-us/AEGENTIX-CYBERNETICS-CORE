"""
Shamir Secret Sharing Entropy Provider for distributed entropy reconstruction.
Threshold k-of-n shares from geo-distributed parties.
"""

import os
import json
import hashlib
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import secrets

from .provider import EntropyProvider
from .jurisdiction import validate_jurisdiction, JurisdictionalError

logger = logging.getLogger(__name__)


@dataclass
class ShamirShare:
    """A single Shamir share."""
    index: int  # x coordinate (1-based)
    value: bytes  # y coordinate (secret share)
    threshold: int
    total_shares: int
    metadata: Dict


class ShamirSecretSharing:
    """Shamir's Secret Sharing over GF(2^8) for byte-wise sharing."""
    
    @staticmethod
    def _gf256_add(a: int, b: int) -> int:
        return a ^ b
    
    @staticmethod
    def _gf256_mul(a: int, b: int) -> int:
        """Multiply in GF(2^8) with irreducible polynomial x^8 + x^4 + x^3 + x + 1 (0x11b)."""
        result = 0
        for _ in range(8):
            if b & 1:
                result ^= a
            hi_bit = a & 0x80
            a = (a << 1) & 0xFF
            if hi_bit:
                a ^= 0x1B
            b >>= 1
        return result
    
    @staticmethod
    def _gf256_div(a: int, b: int) -> int:
        """Divide in GF(2^8) using extended Euclidean algorithm."""
        if b == 0:
            raise ZeroDivisionError
        if a == 0:
            return 0
        
        # Find multiplicative inverse of b
        inv = ShamirSecretSharing._gf256_inv(b)
        return ShamirSecretSharing._gf256_mul(a, inv)
    
    @staticmethod
    def _gf256_inv(a: int) -> int:
        """Multiplicative inverse in GF(2^8)."""
        if a == 0:
            raise ZeroDivisionError
        # a^254 = a^-1 in GF(256)
        result = 1
        for _ in range(254):
            result = ShamirSecretSharing._gf256_mul(result, a)
        return result
    
    @classmethod
    def split_secret(cls, secret: bytes, threshold: int, total_shares: int) -> List[ShamirShare]:
        """
        Split secret into shares using Shamir's Secret Sharing.
        Each byte of secret is shared independently.
        """
        if threshold > total_shares:
            raise ValueError("Threshold cannot exceed total shares")
        if threshold < 2:
            raise ValueError("Threshold must be at least 2")
        if total_shares > 255:
            raise ValueError("Maximum 255 shares (GF(256) limit)")
        
        shares = []
        for share_idx in range(1, total_shares + 1):
            shares.append(ShamirShare(
                index=share_idx,
                value=bytes(),
                threshold=threshold,
                total_shares=total_shares,
                metadata={}
            ))
        
        # Process each byte of secret
        for byte_pos, secret_byte in enumerate(secret):
            # Generate random polynomial coefficients (threshold-1 random, constant = secret_byte)
            coeffs = [secret_byte] + [secrets.randbits(8) for _ in range(threshold - 1)]
            
            # Evaluate polynomial at x = 1, 2, ..., total_shares
            for share in shares:
                x = share.index
                y = 0
                x_pow = 1
                for coeff in coeffs:
                    y = cls._gf256_add(y, cls._gf256_mul(coeff, x_pow))
                    x_pow = cls._gf256_mul(x_pow, x)
                share.value += bytes([y])
        
        return shares
    
    @classmethod
    def reconstruct_secret(cls, shares: List[ShamirShare]) -> bytes:
        """Reconstruct secret from shares using Lagrange interpolation."""
        if len(shares) < shares[0].threshold:
            raise ValueError(f"Insufficient shares: {len(shares)} < {shares[0].threshold}")
        
        threshold = shares[0].threshold
        secret_len = len(shares[0].value)
        secret = bytearray(secret_len)
        
        # For each byte position
        for byte_pos in range(secret_len):
            # Lagrange interpolation at x=0
            y_vals = [share.value[byte_pos] for share in shares[:threshold]]
            x_vals = [share.index for share in shares[:threshold]]
            
            result = 0
            for i in range(threshold):
                # Compute Lagrange basis polynomial L_i(0)
                xi = x_vals[i]
                yi = y_vals[i]
                
                numerator = 1
                denominator = 1
                for j in range(threshold):
                    if i != j:
                        xj = x_vals[j]
                        numerator = cls._gf256_mul(numerator, xj)  # 0 - xj = xj in GF(256)
                        denominator = cls._gf256_mul(denominator, cls._gf256_add(xi, xj))
                
                lagrange_coeff = cls._gf256_div(numerator, denominator)
                result = cls._gf256_add(result, cls._gf256_mul(yi, lagrange_coeff))
            
            secret[byte_pos] = result
        
        return bytes(secret)


class ShamirProvider(EntropyProvider):
    """
    Shamir Secret Sharing entropy provider.
    Reconstructs master entropy from distributed shares.
    """
    
    def __init__(self, shares: List[ShamirShare] = None, 
                 share_files: List[str] = None,
                 threshold: int = 3, total_shares: int = 5,
                 country_code: str = "US", region: str = "", entity_name: str = ""):
        if not validate_jurisdiction(country_code, region, entity_name):
            raise JurisdictionalError(f"Shamir provider excluded: {country_code}/{region}")
        
        super().__init__("Shamir-SSS", country_code, region, entity_name)
        self.threshold = threshold
        self.total_shares = total_shares
        self._master_entropy = None
        self._shares = shares or []
        
        if share_files:
            self._load_shares_from_files(share_files)
        
        if self._shares:
            self._reconstruct()
    
    def _load_shares_from_files(self, files: List[str]):
        """Load shares from JSON files."""
        for f in files:
            try:
                with open(f, 'r') as fp:
                    data = json.load(fp)
                share = ShamirShare(
                    index=data['index'],
                    value=bytes.fromhex(data['value']),
                    threshold=data['threshold'],
                    total_shares=data['total_shares'],
                    metadata=data.get('metadata', {})
                )
                self._shares.append(share)
            except Exception as e:
                logger.warning(f"Failed to load share from {f}: {e}")
    
    def _reconstruct(self):
        """Reconstruct master entropy from shares."""
        if len(self._shares) < self.threshold:
            raise ValueError(f"Insufficient shares: {len(self._shares)} < {self.threshold}")
        self._master_entropy = ShamirSecretSharing.reconstruct_secret(self._shares)
        logger.info(f"Reconstructed master entropy from {len(self._shares)} shares")
    
    def add_share(self, share: ShamirShare):
        """Add a share and attempt reconstruction."""
        self._shares.append(share)
        if len(self._shares) >= self.threshold and self._master_entropy is None:
            self._reconstruct()
    
    @property
    def provider_type(self) -> str:
        return "Shamir-SSS"
    
    def health_check(self) -> bool:
        return self._master_entropy is not None
    
    def get_entropy(self, length: int = 64) -> bytes:
        if self._master_entropy is None:
            raise RuntimeError("Master entropy not reconstructed (insufficient shares)")
        
        # Use master entropy as seed for HKDF to derive requested length
        import hmac
        from hashlib import sha256
        
        # HKDF-Extract
        salt = b"CyberCore-Shamir-Entropy"
        prk = hmac.new(salt, self._master_entropy, sha256).digest()
        
        # HKDF-Expand
        okm = bytearray()
        counter = 1
        while len(okm) < length:
            info = f"entropy-{counter}".encode()
            h = hmac.new(prk, info + b'\x00', sha256)
            okm.extend(h.digest())
            counter += 1
        
        return bytes(okm[:length])


def create_shamir_provider(share_files: List[str] = None,
                          threshold: int = 3, total_shares: int = 5,
                          country_code: str = "US", region: str = "", entity_name: str = "") -> Optional[EntropyProvider]:
    """Factory for Shamir provider."""
    try:
        return ShamirProvider(
            share_files=share_files,
            threshold=threshold,
            total_shares=total_shares,
            country_code=country_code,
            region=region,
            entity_name=entity_name
        )
    except Exception as e:
        logger.warning(f"Shamir provider creation failed: {e}")
        return None


def generate_shamir_shares(master_entropy: bytes, threshold: int, total_shares: int,
                          output_dir: str = None) -> List[ShamirShare]:
    """Generate and optionally save Shamir shares from master entropy."""
    shares = ShamirSecretSharing.split_secret(master_entropy, threshold, total_shares)
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        for share in shares:
            filepath = os.path.join(output_dir, f"shamir_share_{share.index:03d}.json")
            with open(filepath, 'w') as f:
                json.dump({
                    'index': share.index,
                    'value': share.value.hex(),
                    'threshold': share.threshold,
                    'total_shares': share.total_shares,
                    'metadata': share.metadata
                }, f, indent=2)
    
    return shares
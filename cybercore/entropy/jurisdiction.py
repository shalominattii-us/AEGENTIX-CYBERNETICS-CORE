"""
Jurisdictional Exclusion Enforcement for CyberCore Entropy Providers.

Hard-coded deny-list: UAE, Dubai, SA, QA, KW, BH, OM, IR, PK, AF, BD, MY, ID,
any Sharia-compliant financial jurisdiction.
"""

from typing import Set, Optional
import ipaddress


EXCLUDED_COUNTRIES: Set[str] = {
    "AE", "ARE", "SA", "SAU", "QA", "QAT", "KW", "KWT",
    "BH", "BHR", "OM", "OMN", "IR", "IRN", "PK", "PAK",
    "AF", "AFG", "BD", "BGD", "MY", "MYS", "ID", "IDN",
    "JO", "JOR", "LB", "LBN", "SY", "SYR", "IQ", "IRQ",
    "YE", "YEM", "PS", "PSE", "EG", "EGY", "LY", "LBY",
    "TN", "TUN", "DZ", "DZA", "MA", "MAR", "MR", "MRT",
    "SO", "SOM", "DJ", "DJI", "KM", "COM",
}

EXCLUDED_REGIONS: Set[str] = {
    "dubai", "abu dhabi", "riyadh", "jeddah", "doha",
    "kuwait city", "manama", "muscat", "tehran", "islamabad",
    "kabul", "dhaka", "kuala lumpur", "jakarta",
}

SHARIA_COMPLIANT_KEYWORDS: Set[str] = {
    "sharia", "shariah", "islamic finance", "islamic banking",
    "takaful", "sukuk", "murabaha", "mudaraba", "musharaka",
    "ijara", "istisna", "salam", "riba-free",
}


def is_excluded_country(country_code: str) -> bool:
    """Check if country code is in excluded list."""
    return country_code.upper() in EXCLUDED_COUNTRIES


def is_excluded_region(region: str) -> bool:
    """Check if region name contains excluded jurisdiction."""
    region_lower = region.lower()
    return any(excl in region_lower for excl in EXCLUDED_REGIONS)


def is_sharia_compliant_entity(name: str) -> bool:
    """Check if entity name suggests Sharia-compliant finance."""
    name_lower = name.lower()
    return any(kw in name_lower for kw in SHARIA_COMPLIANT_KEYWORDS)


def validate_jurisdiction(country_code: str, region: str = "", entity_name: str = "") -> bool:
    """
    Validate that entropy source jurisdiction is allowed.
    Returns True if allowed, False if excluded.
    """
    if is_excluded_country(country_code):
        return False
    if region and is_excluded_region(region):
        return False
    if entity_name and is_sharia_compliant_entity(entity_name):
        return False
    return True


def get_geoip_country(ip: str) -> Optional[str]:
    """
    Get country code from IP address.
    In production, use a GeoIP database (MaxMind, ipapi, etc.).
    """
    try:
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback:
            return "LOCAL"
    except ValueError:
        pass
    return None


class JurisdictionalError(Exception):
    """Raised when entropy source fails jurisdictional validation."""
    pass


def enforce_jurisdiction(country_code: str, region: str = "", entity_name: str = "") -> None:
    """Enforce jurisdictional policy, raise if excluded."""
    if not validate_jurisdiction(country_code, region, entity_name):
        raise JurisdictionalError(
            f"Entropy source excluded: country={country_code}, region={region}, entity={entity_name}"
        )
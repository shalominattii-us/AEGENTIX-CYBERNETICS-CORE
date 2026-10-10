"""
CyberCore Audit Module - Immutable audit logging with Merkle integrity.

Exports:
- AuditLogger: Append-only audit logger
- AuditVerifier: Integrity verification
- AuditEntry: Log entry structure
- AuditEventType: Event type enumeration
- get_audit_logger, initialize_audit_logger
"""

from .logger import (
    AuditLogger,
    AuditEntry,
    AuditEventType,
    MerkleTree,
    get_audit_logger,
    initialize_audit_logger,
)

from .verifier import (
    AuditVerifier,
    verify_audit_log,
)

__all__ = [
    "AuditLogger",
    "AuditEntry",
    "AuditEventType",
    "MerkleTree",
    "get_audit_logger",
    "initialize_audit_logger",
    "AuditVerifier",
    "verify_audit_log",
]
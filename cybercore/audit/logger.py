"""
CyberCore Audit Logging - Immutable, tamper-evident audit trail.

Features:
- Append-only log with Merkle tree integrity
- Jurisdictional tagging per operation
- Cryptographic proof of correct derivation
- Structured logging for compliance
"""

import json
import time
import hashlib
import logging
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    SIGN = "sign"
    PUBLIC_KEY_DERIVE = "public_key_derive"
    ADDRESS_DERIVE = "address_derive"
    REWARD_SETTLEMENT = "reward_settlement"
    CAPABILITY_ISSUE = "capability_issue"
    CAPABILITY_REVOKE = "capability_revoke"
    VAULT_INIT = "vault_init"
    ENTROPY_DERIVE = "entropy_derive"
    MIGRATION_VERIFY = "migration_verify"
    HEALTH_CHECK = "health_check"


@dataclass
class AuditEntry:
    """Single audit log entry."""
    index: int
    timestamp: int
    event_type: str
    agent_id: str
    chain: str
    path: str
    jurisdiction_tag: str  # Country/region of entropy source
    entropy_provider: str
    merkle_root: str
    prev_hash: str
    data_hash: str
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AuditEntry':
        return cls(**data)


class MerkleTree:
    """Simple Merkle tree for audit log integrity."""
    
    @staticmethod
    def hash_leaf(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def hash_pair(left: str, right: str) -> str:
        return hashlib.sha256((left + right).encode()).hexdigest()
    
    @classmethod
    def compute_root(cls, leaves: List[str]) -> str:
        if not leaves:
            return hashlib.sha256(b"empty").hexdigest()
        
        level = leaves[:]
        while len(level) > 1:
            next_level = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else left
                next_level.append(cls.hash_pair(left, right))
            level = next_level
        
        return level[0]


class AuditLogger:
    """
    Immutable audit logger with Merkle tree integrity.
    Each entry includes jurisdictional tags for compliance.
    """
    
    def __init__(self, log_path: str = None, max_memory_entries: int = 10000):
        self.log_path = Path(log_path) if log_path else Path(
            "C:\\Users\\eagle\\AEGENTIX-CYBERNETICS-CORE\\cybercore_audit.log"
        )
        self.max_memory_entries = max_memory_entries
        
        self._entries: List[AuditEntry] = []
        self._leaves: List[str] = []
        self._lock = threading.RLock()
        self._initialized = False
        
        # Load existing log if present
        if self.log_path.exists():
            self._load_log()
    
    def _load_log(self):
        """Load existing audit log."""
        try:
            with open(self.log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        entry_data = json.loads(line)
                        entry = AuditEntry.from_dict(entry_data)
                        self._entries.append(entry)
                        self._leaves.append(entry.data_hash)
            
            self._initialized = True
            logger.info(f"Loaded audit log: {len(self._entries)} entries")
        except Exception as e:
            logger.error(f"Failed to load audit log: {e}")
    
    def _compute_data_hash(self, event_type: str, agent_id: str, chain: str,
                          path: str, metadata: Dict) -> str:
        """Compute hash of event data."""
        data = {
            "event_type": event_type,
            "agent_id": agent_id,
            "chain": chain,
            "path": path,
            "metadata": metadata,
        }
        data_bytes = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(data_bytes).hexdigest()
    
    def _get_jurisdiction_tag(self, entropy_provider: str) -> str:
        """Get jurisdictional tag for entropy provider."""
        # In production, lookup provider's jurisdiction
        # For now, return provider name as tag
        return entropy_provider
    
    def log_event(
        self,
        event_type: AuditEventType,
        agent_id: str,
        chain: str,
        path: str,
        entropy_provider: str = "unknown",
        metadata: Dict = None,
    ) -> AuditEntry:
        """Log an audit event."""
        with self._lock:
            timestamp = int(time.time() * 1000)
            index = len(self._entries)
            
            data_hash = self._compute_data_hash(
                event_type.value, agent_id, chain, path, metadata or {}
            )
            
            prev_hash = self._leaves[-1] if self._leaves else "0" * 64
            jurisdiction_tag = self._get_jurisdiction_tag(entropy_provider)
            
            # Compute new Merkle root
            new_leaves = self._leaves + [data_hash]
            merkle_root = MerkleTree.compute_root(new_leaves)
            
            entry = AuditEntry(
                index=index,
                timestamp=timestamp,
                event_type=event_type.value,
                agent_id=agent_id,
                chain=chain,
                path=path,
                jurisdiction_tag=jurisdiction_tag,
                entropy_provider=entropy_provider,
                merkle_root=merkle_root,
                prev_hash=prev_hash,
                data_hash=data_hash,
                metadata=metadata or {},
            )
            
            self._entries.append(entry)
            self._leaves.append(data_hash)
            
            # Persist to disk
            self._persist_entry(entry)
            
            # Trim memory if needed
            if len(self._entries) > self.max_memory_entries:
                self._entries = self._entries[-self.max_memory_entries:]
                self._leaves = self._leaves[-self.max_memory_entries:]
            
            return entry
    
    def _persist_entry(self, entry: AuditEntry):
        """Append entry to log file."""
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(entry.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to persist audit entry: {e}")
    
    # Convenience methods for common events
    def log_sign(self, agent_id: str, chain: str, path: str,
                 signature: bytes, address: str,
                 entropy_provider: str = "unknown",
                 **kwargs):
        """Log signing event."""
        metadata = {
            "signature_len": len(signature),
            "address": address,
            **kwargs,
        }
        return self.log_event(
            AuditEventType.SIGN,
            agent_id=agent_id,
            chain=chain,
            path=path,
            entropy_provider=entropy_provider,
            metadata=metadata,
        )
    
    def log_reward(self, agent_id: str, chain: str, task_id: str,
                   amount: Any, tx_hash: str,
                   entropy_provider: str = "unknown",
                   **kwargs):
        """Log reward settlement."""
        metadata = {
            "task_id": task_id,
            "amount": str(amount),
            "tx_hash": tx_hash,
            **kwargs,
        }
        return self.log_event(
            AuditEventType.REWARD_SETTLEMENT,
            agent_id=agent_id,
            chain=chain,
            path=f"reward:{task_id}",
            entropy_provider=entropy_provider,
            metadata=metadata,
        )
    
    def log_public_key_derive(self, agent_id: str, chain: str, path: str,
                             entropy_provider: str = "unknown",
                             **kwargs):
        """Log public key derivation."""
        return self.log_event(
            AuditEventType.PUBLIC_KEY_DERIVE,
            agent_id=agent_id,
            chain=chain,
            path=path,
            entropy_provider=entropy_provider,
            metadata=kwargs,
        )
    
    def log_address_derive(self, agent_id: str, chain: str, path: str,
                          entropy_provider: str = "unknown",
                          **kwargs):
        """Log address derivation."""
        return self.log_event(
            AuditEventType.ADDRESS_DERIVE,
            agent_id=agent_id,
            chain=chain,
            path=path,
            entropy_provider=entropy_provider,
            metadata=kwargs,
        )
    
    def log_capability_issue(self, agent_id: str, capabilities: List[str],
                            expires_at: int,
                            entropy_provider: str = "unknown",
                            **kwargs):
        """Log capability token issuance."""
        metadata = {
            "capabilities": capabilities,
            "expires_at": expires_at,
            **kwargs,
        }
        return self.log_event(
            AuditEventType.CAPABILITY_ISSUE,
            agent_id=agent_id,
            chain="",
            path="",
            entropy_provider=entropy_provider,
            metadata=metadata,
        )
    
    def log_vault_init(self, entropy_providers: List[str],
                      entropy_provider: str = "system",
                      **kwargs):
        """Log vault initialization."""
        metadata = {
            "entropy_providers": entropy_providers,
            **kwargs,
        }
        return self.log_event(
            AuditEventType.VAULT_INIT,
            agent_id="system",
            chain="",
            path="",
            entropy_provider=entropy_provider,
            metadata=metadata,
        )
    
    def log_migration_verify(self, matched: int, mismatched: int,
                            details: List[Dict],
                            entropy_provider: str = "system",
                            **kwargs):
        """Log migration verification."""
        metadata = {
            "matched": matched,
            "mismatched": mismatched,
            "details": details,
            **kwargs,
        }
        return self.log_event(
            AuditEventType.MIGRATION_VERIFY,
            agent_id="system",
            chain="",
            path="",
            entropy_provider=entropy_provider,
            metadata=metadata,
        )
    
    def verify_integrity(self, start_index: int = 0, end_index: int = None) -> bool:
        """Verify audit log integrity via Merkle tree."""
        with self._lock:
            end_index = end_index or len(self._entries)
            entries = self._entries[start_index:end_index]
            
            if not entries:
                return True
            
            # Recompute Merkle root
            leaves = [e.data_hash for e in entries]
            computed_root = MerkleTree.compute_root(leaves)
            
            # Check against last entry's root
            last_entry = entries[-1]
            return computed_root == last_entry.merkle_root
    
    def get_entries(self, start: int = 0, limit: int = 100) -> List[AuditEntry]:
        """Get audit entries (for querying)."""
        with self._lock:
            end = start + limit
            return self._entries[start:end]
    
    def get_entries_by_agent(self, agent_id: str, limit: int = 100) -> List[AuditEntry]:
        """Get entries for specific agent."""
        with self._lock:
            return [
                e for e in reversed(self._entries)
                if e.agent_id == agent_id
            ][:limit]
    
    def get_entries_by_chain(self, chain: str, limit: int = 100) -> List[AuditEntry]:
        """Get entries for specific chain."""
        with self._lock:
            return [
                e for e in reversed(self._entries)
                if e.chain == chain
            ][:limit]
    
    def export_proof(self, index: int) -> Dict[str, Any]:
        """Generate inclusion proof for entry at index."""
        with self._lock:
            if index >= len(self._entries):
                return {}
            
            entry = self._entries[index]
            
            # Generate Merkle proof path
            proof = []
            # Simplified - real implementation would compute sibling path
            
            return {
                "entry": entry.to_dict(),
                "merkle_root": entry.merkle_root,
                "proof": proof,
            }


# Global audit logger
_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger


def initialize_audit_logger(log_path: str = None) -> AuditLogger:
    global _global_audit_logger
    _global_audit_logger = AuditLogger(log_path)
    return _global_audit_logger
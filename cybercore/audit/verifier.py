"""
Audit Verifier - Verifies integrity of audit logs and derives proof.
"""

import json
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path

from .logger import AuditEntry, AuditLogger, MerkleTree


class AuditVerifier:
    """Verifies audit log integrity and generates proofs."""
    
    def __init__(self, logger: AuditLogger):
        self.logger = logger
    
    def verify_full_log(self) -> Dict[str, Any]:
        """Verify entire audit log integrity."""
        entries = self.logger._entries
        if not entries:
            return {"valid": True, "entries": 0, "errors": []}
        
        errors = []
        
        # Check Merkle root consistency
        for i, entry in enumerate(entries):
            # Verify data hash
            computed_hash = self.logger._compute_data_hash(
                entry.event_type, entry.agent_id, entry.chain,
                entry.path, entry.metadata
            )
            if computed_hash != entry.data_hash:
                errors.append(f"Entry {i}: data hash mismatch")
            
            # Verify Merkle root (from index 0 to i)
            leaves = [e.data_hash for e in entries[:i+1]]
            expected_root = MerkleTree.compute_root(leaves)
            if expected_root != entry.merkle_root:
                errors.append(f"Entry {i}: Merkle root mismatch")
            
            # Verify prev_hash chain
            if i > 0:
                if entry.prev_hash != entries[i-1].data_hash:
                    errors.append(f"Entry {i}: prev_hash chain broken")
            else:
                if entry.prev_hash != "0" * 64:
                    errors.append(f"Entry 0: invalid prev_hash")
        
        return {
            "valid": len(errors) == 0,
            "entries_checked": len(entries),
            "errors": errors,
            "final_merkle_root": entries[-1].merkle_root if entries else None,
        }
    
    def verify_entry_inclusion(self, index: int) -> Dict[str, Any]:
        """Verify specific entry is included in log."""
        entries = self.logger._entries
        
        if index >= len(entries):
            return {"valid": False, "error": "Index out of range"}
        
        entry = entries[index]
        
        # Verify data hash
        computed_hash = self.logger._compute_data_hash(
            entry.event_type, entry.agent_id, entry.chain,
            entry.path, entry.metadata
        )
        hash_valid = computed_hash == entry.data_hash
        
        # Verify Merkle inclusion
        leaves = [e.data_hash for e in entries[:index+1]]
        merkle_root = MerkleTree.compute_root(leaves)
        merkle_valid = merkle_root == entry.merkle_root
        
        # Verify chain
        chain_valid = True
        if index > 0:
            chain_valid = entry.prev_hash == entries[index-1].data_hash
        elif entry.prev_hash != "0" * 64:
            chain_valid = False
        
        return {
            "valid": hash_valid and merkle_valid and chain_valid,
            "index": index,
            "hash_valid": hash_valid,
            "merkle_valid": merkle_valid,
            "chain_valid": chain_valid,
            "merkle_root": entry.merkle_root,
        }
    
    def verify_jurisdictional_compliance(
        self,
        excluded_countries: List[str] = None,
        excluded_keywords: List[str] = None
    ) -> Dict[str, Any]:
        """Verify all entropy sources comply with jurisdictional policy."""
        from cybercore.entropy.jurisdiction import (
            validate_jurisdiction, EXCLUDED_COUNTRIES, SHARIA_COMPLIANT_KEYWORDS
        )
        
        excluded = set(excluded_countries) if excluded_countries else EXCLUDED_COUNTRIES
        keywords = set(excluded_keywords) if excluded_keywords else SHARIA_COMPLIANT_KEYWORDS
        
        violations = []
        
        for entry in self.logger._entries:
            # Check entropy provider jurisdiction
            # In production, would lookup provider's actual jurisdiction
            provider = entry.entropy_provider
            
            # Check for excluded keywords in provider name
            provider_lower = provider.lower()
            for kw in keywords:
                if kw in provider_lower:
                    violations.append({
                        "entry_index": entry.index,
                        "event_type": entry.event_type,
                        "provider": provider,
                        "violation": f"Sharia-compliant keyword: {kw}",
                    })
        
        return {
            "compliant": len(violations) == 0,
            "total_entries": len(self.logger._entries),
            "violations": violations,
        }
    
    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate full compliance report."""
        integrity = self.verify_full_log()
        jurisdiction = self.verify_jurisdictional_compliance()
        
        # Event type distribution
        event_types = {}
        for entry in self.logger._entries:
            event_types[entry.event_type] = event_types.get(entry.event_type, 0) + 1
        
        # Chain distribution
        chains = {}
        for entry in self.logger._entries:
            if entry.chain:
                chains[entry.chain] = chains.get(entry.chain, 0) + 1
        
        # Agent activity
        agents = {}
        for entry in self.logger._entries:
            agents[entry.agent_id] = agents.get(entry.agent_id, 0) + 1
        
        return {
            "timestamp": int(time.time()),
            "total_entries": len(self.logger._entries),
            "integrity": integrity,
            "jurisdictional_compliance": jurisdiction,
            "event_distribution": event_types,
            "chain_distribution": chains,
            "top_agents": sorted(agents.items(), key=lambda x: -x[1])[:10],
            "time_range": {
                "start": self.logger._entries[0].timestamp if self.logger._entries else None,
                "end": self.logger._entries[-1].timestamp if self.logger._entries else None,
            },
        }
    
    def export_verification_proof(self, output_path: str):
        """Export machine-readable verification proof."""
        report = self.generate_compliance_report()
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report


def verify_audit_log(log_path: str) -> Dict[str, Any]:
    """Standalone function to verify an audit log file."""
    logger = AuditLogger(log_path)
    verifier = AuditVerifier(logger)
    return verifier.verify_full_log()


# Import time for compliance report
import time
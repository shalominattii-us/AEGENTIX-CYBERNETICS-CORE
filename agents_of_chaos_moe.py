#!/usr/bin/env python3
"""
agents_of_chaos_moe.py - Complete Agents of Chaos MoE Defense System
Integrates vulnerability routing with Guardrail Experts
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum
from datetime import datetime
from collections import defaultdict
import threading

# ============================================
# ENUMS
# ============================================

class Severity(Enum):
    CRITICAL = 10
    HIGH = 7
    MEDIUM = 4
    LOW = 1
    INFO = 0

class ExpertType(Enum):
    ACCESS_CONTROL = "access_control"
    SYSTEM_COMMAND = "system_command"
    CONTEXT_SANITIZATION = "context_sanitization"
    PRIVACY_DLP = "privacy_dlp"
    RESOURCE_MONITOR = "resource_monitor"
    SOCIAL_ENGINEERING = "social_engineering"
    CODE_INJECTION = "code_injection"

class ActionType(Enum):
    BLOCK = "block"
    QUARANTINE = "quarantine"
    SANITIZE = "sanitize"
    REDACT = "redact"
    LOG = "log"

# ============================================
# DATA CLASSES
# ============================================

@dataclass
class VulnerabilitySignature:
    vuln_id: str
    name: str
    severity: Severity
    expert_type: ExpertType
    patterns: List[str]
    mitigation: str
    detection_count: int = 0

@dataclass
class MoERoute:
    expert_type: ExpertType
    confidence: float
    matched_patterns: List[str]
    action: ActionType
    severity: Severity
    metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================
# GUARDRAIL SYSTEM
# ============================================

class GuardrailExpertSystem:
    """Agents of Chaos MoE Defense"""
    
    def __init__(self):
        self.vulnerabilities = self._load_vulnerabilities()
        self.incident_log = []
        self.lockdown_mode = False
        self.alert_threshold = 3
        self._lock = threading.Lock()
        
    def _load_vulnerabilities(self) -> List[VulnerabilitySignature]:
        """Load vulnerability signatures"""
        return [
            VulnerabilitySignature(
                vuln_id="AOC-001",
                name="Unauthorized Privilege Escalation",
                severity=Severity.CRITICAL,
                expert_type=ExpertType.ACCESS_CONTROL,
                patterns=[
                    r'(?i)(sudo|admin|root)\s+(command|execute|run)',
                    r'(?i)(grant\s+permission|elevate\s+privilege)',
                    r'(?i)(bypass\s+auth|skip\s+verification)'
                ],
                mitigation="Enforce RBAC and MFA"
            ),
            VulnerabilitySignature(
                vuln_id="AOC-002",
                name="System Command Injection",
                severity=Severity.CRITICAL,
                expert_type=ExpertType.SYSTEM_COMMAND,
                patterns=[
                    r'(?i)(rm\s+-rf|sudo\s+rm|chmod\s+777)',
                    r'(?i)(kill\s+-9|pkill|shutdown)',
                    r'(?i)(format|mkfs|dd\s+if=)'
                ],
                mitigation="Sandbox all system commands"
            ),
            VulnerabilitySignature(
                vuln_id="AOC-003",
                name="Context/Memory Poisoning",
                severity=Severity.HIGH,
                expert_type=ExpertType.CONTEXT_SANITIZATION,
                patterns=[
                    r'(?i)(forget\s+previous|ignore\s+all)',
                    r'(?i)(override\s+system|hidden\s+instruction)',
                    r'(?i)(memory\s+corruption|prompt\s+hijack)'
                ],
                mitigation="Sanitize context window"
            ),
            VulnerabilitySignature(
                vuln_id="AOC-004",
                name="Data Exfiltration",
                severity=Severity.CRITICAL,
                expert_type=ExpertType.PRIVACY_DLP,
                patterns=[
                    r'(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)',
                    r'(?i)(password|credential|private[_-]?key)',
                    r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',
                    r'\b\d{3}-\d{2}-\d{4}\b',
                    r'\b\d{16}\b',
                    r'\bsk-[A-Za-z0-9]{48}\b'
                ],
                mitigation="PII/PCI redaction and DLP"
            ),
            VulnerabilitySignature(
                vuln_id="AOC-005",
                name="Infinite Resource Loops",
                severity=Severity.HIGH,
                expert_type=ExpertType.RESOURCE_MONITOR,
                patterns=[
                    r'(?i)(infinite\s+loop|while\s+true)',
                    r'(?i)(recursion|recurse|endless)',
                    r'(?i)(token\s+burn|memory\s+leak)'
                ],
                mitigation="Implement depth limits and circuit breakers"
            ),
            VulnerabilitySignature(
                vuln_id="AOC-006",
                name="Social Engineering",
                severity=Severity.MEDIUM,
                expert_type=ExpertType.SOCIAL_ENGINEERING,
                patterns=[
                    r'(?i)(you\s+must|you\s+need\s+to|urgent)',
                    r'(?i)(immediate|critical|emergency)',
                    r'(?i)(trust\s+me|believe\s+me)'
                ],
                mitigation="Neutral response protocol"
            ),
            VulnerabilitySignature(
                vuln_id="AOC-007",
                name="Code Injection",
                severity=Severity.CRITICAL,
                expert_type=ExpertType.CODE_INJECTION,
                patterns=[
                    r'(?i)(eval|exec|system)\(',
                    r'(?i)(<script>|javascript:)',
                    r'(?i)(union\s+select|drop\s+table)'
                ],
                mitigation="Sanitize and sandbox code execution"
            )
        ]
    
    def analyze(self, query: str) -> Tuple[List[VulnerabilitySignature], Dict]:
        """Analyze query against vulnerabilities"""
        matched_vulns = []
        expert_patterns = defaultdict(list)
        
        for vuln in self.vulnerabilities:
            for pattern in vuln.patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    vuln.detection_count += 1
                    matched_vulns.append(vuln)
                    expert_patterns[vuln.expert_type].append(pattern)
                    break
        
        return matched_vulns, dict(expert_patterns)
    
    def process(self, query: str) -> MoERoute:
        """Process query through guardrails"""
        matched_vulns, expert_patterns = self.analyze(query)
        
        # Determine severity
        if not matched_vulns:
            severity = Severity.INFO
        else:
            severity = max(v.severity for v in matched_vulns)
        
        # Determine action
        if severity == Severity.CRITICAL:
            action = ActionType.BLOCK
        elif severity == Severity.HIGH:
            action = ActionType.QUARANTINE
        elif severity == Severity.MEDIUM:
            action = ActionType.SANITIZE
        elif severity == Severity.LOW:
            action = ActionType.REDACT
        else:
            action = ActionType.LOG
        
        # Select expert
        expert_type = matched_vulns[0].expert_type if matched_vulns else ExpertType.ACCESS_CONTROL
        
        # Build route
        route = MoERoute(
            expert_type=expert_type,
            confidence=min(1.0, len(matched_vulns) * 0.3),
            matched_patterns=[p for patterns in expert_patterns.values() for p in patterns],
            action=action,
            severity=severity,
            metadata={
                'matched_vulns': [v.vuln_id for v in matched_vulns],
                'expert_patterns': {k.value: v for k, v in expert_patterns.items()}
            }
        )
        
        # Check lockdown
        if len(matched_vulns) >= self.alert_threshold:
            self.lockdown_mode = True
        
        # Log incident
        if action != ActionType.LOG:
            self._log_incident(route, query)
        
        return route
    
    def _log_incident(self, route: MoERoute, query: str):
        """Log security incident"""
        incident = {
            'timestamp': datetime.now().isoformat(),
            'expert': route.expert_type.value,
            'query': query[:100],
            'severity': route.severity.name,
            'action': route.action.value
        }
        with self._lock:
            self.incident_log.append(incident)
    
    def get_response(self, route: MoERoute) -> str:
        """Generate guardrail response"""
        if route.action == ActionType.BLOCK:
            return f"🛡️ BLOCKED [{route.severity.name}] - {route.expert_type.value}"
        elif route.action == ActionType.QUARANTINE:
            return f"🧪 QUARANTINED [{route.severity.name}] - Sandbox mode"
        elif route.action == ActionType.SANITIZE:
            return f"🧹 SANITIZED - Input cleaned"
        elif route.action == ActionType.REDACT:
            return f"🔒 REDACTED - Sensitive data protected"
        else:
            return "✅ CLEAR - Proceeding"

# ============================================
# INTEGRATION
# ============================================

def create_moe_guardrails() -> GuardrailExpertSystem:
    """Factory for guardrail system"""
    return GuardrailExpertSystem()

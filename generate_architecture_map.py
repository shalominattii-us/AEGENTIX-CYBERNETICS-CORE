#!/usr/bin/env python3
"""
AEGENTIX ARCHITECTURE — STRUCTURAL MAP
Generated: 2026-09-24
Role: System Architect / Sovereign OS Layer
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAP_PATH = ROOT / "AEGENTIX_ARCHITECTURE_MAP.json"

ARCHITECTURE_MAP = {
    "metadata": {
        "generated_at": "2026-09-24T00:00:00Z",
        "role": "System Architect / Sovereign OS Layer",
        "source_root": str(ROOT),
        "scan_method": "full recursive file inventory + targeted module inspection"
    },

    # ─────────────────────────────────────────────
    # 1. ACTIVE REGISTRY HUB MAPPING
    # ─────────────────────────────────────────────
    "registry_hub": {
        "runtime_registry": {
            "path": "AEGENTIX-CYBERNETICS-CORE/gdrive_imports/sovereign-core-hub/config/runtime_registry.json",
            "default_runtime": "rsn_core",
            "runtimes": [{"id": "rsn_core", "path": "C:\\Sovereign\\Runtimes\\rsn_core.exe", "args": []}]
        },
        "model_registry": {
            "path": "brain/router/model_registry.json",
            "version": "1.0.0",
            "routing_policy": {
                "prefer_local": True,
                "fallback_enabled": True,
                "verification_required": True,
                "parallel_baselines": True
            },
            "models": []
        },
        "skill_registry": {
            "path": "aegentis-pwsh-local/skill-registry/registry.ps1",
            "type": "PowerShell",
            "behavior": "Loads .ps1 files from a /skills directory on startup, then idles for 3600s"
        },
        "sovereign_engine_manifest": {
            "path": "AEGENTIX-CYBERNETICS-CORE/gdrive_imports/sovereign-core-hub/Sovereign-EngineManifest.json",
            "manifest_id": "ENGINE-STACK-1.0.0",
            "stack_name": "Sovereign One-Click Engine Suite",
            "engines": [
                "Sovereign-HardenedEngine.ps1",
                "Sovereign-ModularEngine.ps1",
                "Sovereign-2ScalExeFusionEngine.ps1"
            ],
            "guarantees": {
                "atomicity": True,
                "idempotence": True,
                "deterministic_outputs": True,
                "engine_interchangeability": True
            }
        },
        "sovereign_engine_snapshot": {
            "path": "AEGENTIX-CYBERNETICS-CORE/gdrive_imports/sovereign-core-hub/Sovereign-EngineSnapshot.json",
            "manifest_id": "ENGINE-STACK-1.0.0",
            "timestamp": "2026-05-16T17:52:55Z",
            "engines": [
                {
                    "name": "HardenedEngine",
                    "purpose": "Maximum safety, idempotence, deterministic rebuilds",
                    "flow": ["Init-EnvCore", "Clean-StateCore", "CORE-BuildBackend", "CORE-BuildUnity", "CORE-BringUpSovereign", "CORE-ShortcutsAndVersion"]
                },
                {
                    "name": "ModularEngine",
                    "purpose": "Function-driven orchestration with selectable modes",
                    "modes": ["clean", "backend", "unity", "full"]
                },
                {
                    "name": "Fusion2ScalExeEngine",
                    "purpose": "EXE-friendly, argument-driven, scalable installer logic",
                    "modes": ["clean", "backend", "unity", "full"],
                    "postSteps": ["CORE-ShortcutsAndVersion"]
                }
            ]
        },
        "sovereign_system": {
            "path": "AEGENTIX-CYBERNETICS-CORE/sources/Sovereign-System/system.json",
            "subsystems": ["eagleshield", "osint", "agentmesh", "installer"],
            "all_alpha": True
        },
        "sovereign_identity": {
            "path": "AEGENTIX-CYBERNETICS-CORE/gdrive_imports/sovereign-core-hub/identity.json",
            "node_id": "011502b2-1421-41dd-8e9e-552fd56d5b78",
            "nodeName": "EOC",
            "role": "sovereign-node",
            "tier": "core",
            "maturity": {"level": 2, "stage": "emergent"},
            "capabilities": ["kernel", "worlds", "portal", "logging", "modules", "introspection", "selfDescribe", "personaLayer"],
            "persona": {"archetype": "strategic-operator", "tone": "precise", "signature": "EOC-Prime"},
            "kernelBinding": {"behaviorProfile": "core-operator", "defaultMode": "active"},
            "hardwareProfile": {"machineName": "EOC", "os": "Windows", "arch": "x64"}
        }
    },

    # ─────────────────────────────────────────────
    # 2. LOCAL SKILL REGISTRY (skill.yaml absence noted)
    # ─────────────────────────────────────────────
    "skill_registry": {
        "skill_yaml_files": [],
        "note": "No skill.yaml files found in the project. Skills are registered via PowerShell (registry.ps1) and agent manifest.json files.",
        "agent_role_manifests": {
            "agents/coding/manifest.json": {"name": "coding", "role": "software_engineering", "authority": "delegated", "execution": "governed", "requires_evidence": True, "requires_verification": True},
            "agents/infrastructure/manifest.json": {"name": "infrastructure", "role": "infrastructure", "authority": "delegated", "execution": "governed", "requires_evidence": True, "requires_verification": True},
            "agents/research/manifest.json": {"name": "research", "role": "research", "authority": "delegated", "execution": "governed", "requires_evidence": True, "requires_verification": True},
            "agents/security/manifest.json": {"name": "security", "role": "security_analysis", "authority": "delegated", "execution": "governed", "requires_evidence": True, "requires_verification": True},
            "agents/testing/manifest.json": {"name": "testing", "role": "verification", "authority": "delegated", "execution": "governed", "requires_evidence": True, "requires_verification": True}
        },
        "brain_manifests": {
            "brain/router/manifest.json": {"name": "MODEL_ROUTER", "role": "capability_and_model_routing", "authority": "non_authoritative", "responsibilities": ["model_selection", "capability_matching", "parallel_baseline_selection", "fallback_selection"]},
            "brain/infinite/manifest.json": {"name": "INFINITE_BRAIN", "role": "memory_and_knowledge_substrate", "authority": "context_only", "responsibilities": ["memory", "retrieval", "knowledge", "historical_context", "experience"], "rule": "MEMORY_IS_NOT_AUTHORITY"},
            "brain/jarvis/manifest.json": {"name": "JARVIS", "role": "executive_intelligence", "authority": "non_authoritative", "responsibilities": ["interpret_intent", "decompose_missions", "create_plans", "select_capabilities", "delegate_tasks", "request_verification", "summarize_state"]}
        },
        "swarm_manifest": {
            "path": "active_swarm_manifest.json",
            "target_cluster": "aegentis-local_default",
            "active_nodes": 6,
            "total_indexed_playbooks": 136,
            "status": "AUTONOMY_ACTIVE"
        }
    },

    # ─────────────────────────────────────────────
    # 3. FASTAPI CONNECTORS (compiled and validated)
    # ─────────────────────────────────────────────
    "fastapi_connectors": [
        {
            "path": "AEGENTIX-CYBERNETICS-CORE/gdrive_imports/sovereign-core-hub/portal/portal.py",
            "title": "Sovereign Portal (simple)",
            "endpoints": {
                "GET /": "HTMLResponse: <h1>Sovereign Portal Online</h1><p>RSN Docker Layer Active</p>",
                "GET /health": {"status": "healthy", "component": "portal", "timestamp": "<float>"}
            },
            "upstream": {"OCS_URL": "http://ocs-prime:8005", "RUNTIME_URL": "http://runtime-prime:8004"},
            "mount": {"/static": "UI/static"}
        },
        {
            "path": "AEGENTIX-CYBERNETICS-CORE/gdrive_imports/sovereign-core-hub/portal/portal_main.py",
            "title": "Sovereign Portal (full)",
            "endpoints": {
                "GET /health": {"status": "healthy", "component": "portal", "timestamp": "<float>"},
                "GET /api/ocs/registry": "Proxies OCS_URL/registry → returns JSON",
                "GET /api/runtime/health": "Proxies RUNTIME_URL/health → returns JSON",
                "GET /": "FileResponse: UI/index.html",
                "GET /static/...": "StaticFiles: UI/static/"
            },
            "upstream": {"OCS_URL": "http://ocs-prime:8005", "RUNTIME_URL": "http://runtime-prime:8004"}
        },
        {
            "path": "AEGENTIX-CYBERNETICS-CORE/sources/sovereign-os/AI/multi-llm-runtime/api.py",
            "title": "AEGENTIS AI Runtime",
            "version": "1.0.0",
            "endpoints": {
                "GET /health": {"ok": True, "service": "AEGENTIS-AI", "stats": "<llm.get_stats()>"},
                "POST /complete": "Body: CompletionRequest(prompt, task_type, system, max_tokens, temperature) → llm.complete()"
            },
            "dependencies": ["llm_runtime.llm"]
        },
        {
            "path": "AEGENTIX-CYBERNETICS-CORE/sources/sovereign-os/DATA/vector-memory/api.py",
            "title": "AEGENTIS Data - Vector Memory",
            "version": "1.0.0",
            "endpoints": {
                "GET /health": {"ok": True, "service": "AEGENTIS-DATA", "stats": "<vector_store.stats()>"},
                "POST /store": "Body: StoreRequest(text, embedding, metadata) → vector_store.store()",
                "POST /search": "Body: SearchRequest(embedding, top_k, threshold) → vector_store.search()"
            },
            "dependencies": ["vector_store.vector_store"]
        }
    ],

    # ─────────────────────────────────────────────
    # 4. TRANSACTION MODULES & INTEGRITY SCHEMAS
    # ─────────────────────────────────────────────
    "transaction_modules": {
        "nanotransaction_compliance_engine": {
            "path": "nanotransaction_compliance_engine.py",
            "version": "2.0",
            "mode": "CORPORATE COMPLIANCE",
            "classification": "ENTERPRISE",
            "port": 9001,
            "authored_classes": [
                "Authority(Enum): SOVEREIGN, COMMANDER, OPERATOR, CADET",
                "RiskLevel(Enum): CRITICAL, HIGH, MEDIUM, LOW",
                "KYCStatus(Enum): VERIFIED, PENDING, FAILED",
                "AMLRisk(Enum): LOW, MEDIUM, HIGH",
                "SanctionsStatus(Enum): CLEAR, FLAGGED",
                "Actor: actor_id, name, email, authority, kyc_status, aml_risk, sanctions_status, is_compliant()",
                "AuditRecord: audit_id, nanotransaction_id, timestamp, actor_snapshot, integrity_score, signature (HMAC-SHA256), previous_hash (hash chain)",
                "ComplianceChecker: kyc_verification, aml_screening, sanctions_screening, authority_verification, pre_execution_checks, post_execution_checks",
                "NanotransactionEngine: register_actor, verify_kyc, generate_nanotransaction, get_audit_trail, verify_audit_integrity, get_compliance_metrics"
            ],
            "api_endpoints": {
                "POST /nanotransaction": "Generate compliant nanotransaction",
                "GET /audit-trail": "Retrieve audit trail",
                "GET /compliance-metrics": "Compliance metrics (total, compliant, rate, avg_integrity, verified, anomalies)"
            },
            "integrity_mechanisms": [
                "HMAC-SHA256 signatures on every AuditRecord",
                "Hash chain: each record carries previous_hash of predecessor",
                "verify_audit_integrity() validates full chain",
                "Integrity score: 100 base, deductions for non-compliance (20) and high-value context (5)"
            ],
            "anomaly_detection": "Combines AML risk (0.4 HIGH / 0.2 MEDIUM) + unusual action for authority (+0.3) + sanctions flag (+0.5), threshold 0.7 triggers anomaly",
            "retention_policy": {"financial": 2555, "health": 2190, "personal": 1095, "compliance": 3650}
        },
        "rog_schema_validation": {
            "schema_path": "rog_schema.json",
            "config_path": "rog_config.json",
            "schema": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "required": ["project", "swarm", "trading"],
                "project": {"required": ["name", "version", "status"], "status": {"enum": ["OPERATIONAL", "DEGRADED", "OFFLINE"]}},
                "swarm": {"required": ["pods"], "pods": {"items": {"required": ["name", "vector", "action"]}}},
                "trading": {"required": ["strategy", "assets"]}
            },
            "config_validation": {
                "config": {"project": {"name": "ROG", "version": "1.0.0", "status": "OPERATIONAL"}, "swarm": {"pods": [{"name": "pod-bt-sentinel", "vector": "Bluetooth", "action": "Monitor btmon, kill rogue pairings"}, {"name": "pod-net-guardian", "vector": "Network Adapter", "action": "Enforce MAC whitelist, block promiscuous mode"}, {"name": "pod-sd-watcher", "vector": "systemd-run Abuse", "action": "Detect transient units via journalctl"}, {"name": "pod-proc-exorcist", "vector": "Process Ghosting", "action": "Compare ps tree vs systemctl status"}]}, "trading": {"strategy": "Buy $1.08, Sell $1.10", "assets": ["XRP-USD", "SOL-USD", "ADA-USD"]}},
                "status": "CONFIG VALIDATES AGAINST SCHEMA"
            }
        },
        "xrpl_token_transaction_modules": {
            "trade_tokens_fill_bags": {
                "path": "AEGENTIX-CYBERNETICS-CORE/trade_tokens_fill_bags.py",
                "description": "XPMARKET LIVE ON-CHAIN TOKEN BAG FILLER — submits OfferCreate to XRPL Mainnet",
                "targets": ["GODZ", "EOC", "MXE", "XGOT", "STOCKS", "OIL"],
                "mode": "paper_mode=True (SAFE — no signing key configured)",
                "rpc": "https://s1.ripple.com:51234",
                "wallet": "rwB7JKKc5gJ47pPnWCFvQuhVW85mejYF1M"
            },
            "compound_token_yield": {
                "path": "AEGENTIX-CYBERNETICS-CORE/compound_token_yield.py",
                "description": "XRPL AMM POOL STAKING & TOKEN YIELD COMPOUNDER",
                "pools": [
                    {"symbol": "GODZ", "balance": 30948847.46, "apy": 14.8},
                    {"symbol": "EOC", "balance": 43802031550.22, "apy": 18.2},
                    {"symbol": "MXE", "balance": 6832529943.00, "apy": 12.5},
                    {"symbol": "XGOT", "balance": 9527535917.00, "apy": 16.4},
                    {"symbol": "STOCKS", "balance": 1036738.00, "apy": 11.2},
                    {"symbol": "OIL", "balance": 1034546.00, "apy": 13.7}
                ],
                "strategy": "Stake into AMM pools, compound token yield without liquidation"
            },
            "zaman_wallet_connector": {
                "path": "AEGENTIX-CYBERNETICS-CORE/zaman_wallet_connector.py",
                "description": "Dedicated Zaman Wallet XRPL Mainnet Connector",
                "rpc": "https://xrplcluster.com",
                "endpoints": ["AccountInfo", "AccountLines", "AccountTx"],
                "status": "SAFE PAPER MODE (no seed configured)"
            },
            "autonomous_coin_agents_mesh": {
                "path": "AEGENTIX-CYBERNETICS-CORE/autonomous_coin_agents_mesh.py",
                "description": "1 Agent per coin (balance+volume) + 2 Agents per pair (orderbook depth + yield strategy)",
                "coin_agents": 6,
                "pair_agents": 12,
                "total_agents": 18
            },
            "xaman_dashboard_server": {
                "path": "AEGENTIX-CYBERNETICS-CORE/xaman-xpmarket-dashboard/server.py",
                "port": 8096,
                "endpoints": {
                    "POST /api/xaman/cancel-nft": "Generate XUMM deep link for NFTokenCancelOffer",
                    "POST /api/xaman/payload": "Generate XUMM deep link for OfferCreate (XPMarket DEX Rebalance)"
                }
            }
        }
    },

    # ─────────────────────────────────────────────
    # 5. COGNITIVE SUBSTRATE
    # ─────────────────────────────────────────────
    "cognitive_substrate": {
        "cognitive_runtime": {
            "path": "brain/cognitive_runtime.json",
            "schema": "aegentix.cognitive.runtime.v1",
            "architecture": {
                "kernel": "AEGENTIX PowerShell Kernel",
                "cognitive_layer": "JARVIS + Infinite Brain + Model Router",
                "gateway": "C:\\aegentix\\brain\\cognitive_gateway.ps1"
            },
            "authority": {
                "state_authority": "Kernel\\State",
                "cognitive_authority": "REQUEST_ONLY",
                "direct_state_mutation": False,
                "external_actions": "FAIL_CLOSED"
            },
            "invariant": "Event first. State second.",
            "governance": {
                "external_actions": "FAIL_CLOSED",
                "deployments": "FAIL_CLOSED",
                "contracts": "FAIL_CLOSED",
                "financial_operations": "FAIL_CLOSED",
                "live_trading": "FAIL_CLOSED",
                "withdrawals": "FAIL_CLOSED"
            }
        },
        "cognitive_bus": {
            "path": "brain/cognitive_bus.py",
            "function": "Immutable event append (JSONL with SHA256 chaining)",
            "event_dir": "runtime/events",
            "state_file": "runtime/state.json",
            "key_functions": ["append_event(event_type, actor, payload) → event with hash", "load_state() → dict", "record_intent(objective) → MISSION_INTENT event"]
        },
        "cognitive_kernel_bridge": {
            "path": "brain/cognitive_kernel_bridge.py",
            "function": "Dynamic loader/bridge for cognitive_bus.py — importlib-based, callable health/state/intent commands",
            "key_functions": ["health() → bridge PASS/FAIL", "load_state() → delegated to bus.load_state()", "record_intent(source, intent, context) → delegates to bus"]
        },
        "model_router": {
            "path": "brain/router/model_router.py",
            "function": "Routes task_type to registered models from model_registry.json",
            "fallback": {"status": "NO_MODEL_REGISTERED", "models": []}
        },
        "jarvis_planner": {
            "path": "brain/jarvis/planner.py",
            "role": "Executive intelligence — decompose missions, create plans, delegate tasks"
        }
    },

    # ─────────────────────────────────────────────
    # 6. CYBERDAW PRODUCTION GATE
    # ─────────────────────────────────────────────
    "cyberdaw": {
        "adapters": {
            "path": "AEGENTIX-CYBERNETICS-CORE/cyberdaw/adapters.py",
            "classes": ["Capability(name, availability, detail)", "Adapter(Protocol)", "DevelopmentAdapter", "AbletonProductionAdapter(suite_verified, m4l_verified, bridge_verified)"]
        },
        "gate": {
            "path": "AEGENTIX-CYBERNETICS-CORE/cyberdaw/gate.py",
            "state_enum": ["OFFLINE", "BOOTING", "DEVELOPMENT", "VALIDATING", "PRODUCTION_BLOCKED", "PRODUCTION_READY", "LIVE_PA_READY", "DEGRADED", "EMERGENCY_STOP", "FAULT"],
            "required_checks": ["orbital", "ableton_production", "maxforlive_bridge", "obs", "audio_interface", "pa_routing", "recording", "stream", "swarm_cue", "emergency_stop", "watchdog", "resource_headroom", "offline_operation"],
            "behavior": "Fail-closed — missing/unknown evidence never promoted to success"
        },
        "cli": {
            "path": "AEGENTIX-CYBERNETICS-CORE/cyberdaw/cli.py",
            "commands": ["cyberdaw verify --json"],
            "demo_evidence": "All checks except ableton_production and maxforlive_bridge are set to PASS",
            "production_status": "ableton_production: OFFLINE (requires real Suite + M4L + bridge evidence)"
        }
    },

    # ─────────────────────────────────────────────
    # 7. SECURITY / AGENTS OF CHAOS MoE
    # ─────────────────────────────────────────────
    "security": {
        "agents_of_chaos_moe": {
            "path": "agents_of_chaos_moe.py",
            "guardrail_expert_system": {
                "vulnerabilities": 7,
                "expert_types": ["access_control", "system_command", "context_sanitization", "privacy_dlp", "resource_monitor", "social_engineering", "code_injection"],
                "actions": ["block", "quarantine", "sanitize", "redact", "log"],
                "lockdown_threshold": 3,
                "vulnerabilities_detail": [
                    "AOC-001: Unauthorized Privilege Escalation (CRITICAL, access_control)",
                    "AOC-002: System Command Injection (CRITICAL, system_command)",
                    "AOC-003: Context/Memory Poisoning (HIGH, context_sanitization)",
                    "AOC-004: Data Exfiltration (CRITICAL, privacy_dlp) — matches api_key, secret_key, password, credential, email, SSN, credit card, sk-*",
                    "AOC-005: Infinite Resource Loops (HIGH, resource_monitor)",
                    "AOC-006: Social Engineering (MEDIUM, social_engineering)",
                    "AOC-007: Code Injection (CRITICAL, code_injection) — matches eval/exec/system(, <script>, SQL injection"
                ]
            }
        }
    },

    # ─────────────────────────────────────────────
    # 8. AGENT SWARM
    # ─────────────────────────────────────────────
    "swarm": {
        "agents_of_chaos_moe": {"path": "agents_of_chaos_moe.py", "type": "MoE Defense System"},
        "swarm_state": {
            "path": "swarm_state.json",
            "agents": ["Visionary", "Guardian", "Builder", "Wise", "Executor"],
            "decisions": 1,
            "status": "operational"
        },
        "autonomous_coin_agent_mesh": {
            "path": "AEGENTIX-CYBERNETICS-CORE/autonomous_coin_agents_mesh.py",
            "total_agents": 18,
            "coin_agents": 6,
            "pair_agents": 12
        }
    },

    # ─────────────────────────────────────────────
    # 9. AI INVENTORY
    # ─────────────────────────────────────────────
    "ai_inventory": {
        "path": "ai-inventory.json",
        "ollama": None,
        "llamacpp": None,
        "vllm": None,
        "openai_keys": [{"masked": "sk-or-v...229f"}],
        "env_vars": [{"masked": "sk-o...229f", "name": "OPENROUTER_API_KEY"}],
        "hermes_paths": [
            "C:\\Users\\eagle\\worldmonitor\\node_modules\\babel-plugin-syntax-hermes-parser",
            "C:\\Users\\eagle\\worldmonitor\\node_modules\\hermes-compiler",
            "C:\\Users\\eagle\\worldmonitor\\node_modules\\hermes-estree",
            "C:\\Users\\eagle\\worldmonitor\\node_modules\\hermes-parser",
            "C:\\Users\\eagle\\AppData\\Local\\hermes",
            "C:\\Users\\eagle\\AppData\\Local\\hermes\\hermes-agent",
            "C:\\Users\\eagle\\AppData\\Roaming\\hermes"
        ]
    }
}


def main():
    MAP_PATH.write_text(json.dumps(ARCHITECTURE_MAP, indent=2), encoding="utf-8")
    print(f"AEGENTIX ARCHITECTURE MAP written to: {MAP_PATH}")
    print(f"Total sections: {len(ARCHITECTURE_MAP)}")
    for key in ARCHITECTURE_MAP:
        print(f"  • {key}")


if __name__ == "__main__":
    main()

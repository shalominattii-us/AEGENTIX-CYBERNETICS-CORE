#!/usr/bin/env python3
"""
AEGENTIX C DRIVE — UNIFIED STRUCTURAL MAP
Generated: 2026-09-24 | Full C drive inventory assimilated
Source: session_scan + manual deep-dive verification

This file is the canonical structural map of the entire C drive.
It catalogs every layer, workspace root, trust boundary, runtime,
and cross-cutting architectural principle for assimilation.
"""

import json
from pathlib import Path

MAP = {
    "generated": "2026-09-24T00:00:00Z",
    "scope": "C:\\\\-full-inventory",
    "one_line_summary": (
        "Multi-layer sovereign workspace: 4 workspace roots, "
        "5 LLM runtimes, DENY_BY_DEFAULT trust architecture replicated "
        "across ASSR/nanotransaction/Sovereign bridge, 13-check fail-closed "
        "CyberDAW gate (3/13 cleared), massive voice/audio subsystem, "
        "300-blockchain node mesh, dual XRPL/Xaman + OmniCyberDEX trading layers."
    ),

    # ── LAYER 0: TRUST ARCHITECTURE (replicated across 3 subsystems) ──
    "trust_architecture": {
        "pattern": "DENY_BY_DEFAULT, tiered trust, foreign=discovery-only",
        "subsystems": [
            {
                "name": "ASSR Trust Policy",
                "file": "C:\\AEGENTIS_WORKSPACE\\assr\\policy\\trust\\trust-policy.json",
                "rules": {
                    "foreign_classification": "EXTERNAL_REFLECTION",
                    "foreign_trusted": False,
                    "foreign_authority_route": False,
                    "foreign_sovereign_route": False,
                    "foreign_omega_route": False,
                    "foreign_execution_input": False,
                    "foreign_control_input": False,
                    "permitted_foreign_ops": [
                        "DISCOVERY", "COMPARISON", "CROSS_VALIDATION",
                        "ANOMALY_DETECTION", "MIRROR_ADJUSTMENT",
                        "GAP_ANALYSIS", "REFLECTION"
                    ],
                    "prohibited_foreign_ops": [
                        "TRUST_ROOT", "AUTHORITY", "POLICY_AUTHORITY",
                        "SOVEREIGN", "OMEGA", "EXECUTION", "CONTROL",
                        "AUTHORITY_TRANSFER", "SILENT_OVERWRITE"
                    ],
                    "sovereign_rule": "trusted_route_required=True, external_reflection_allowed=False",
                    "omega_rule": "trusted_route_required=True, external_reflection_allowed=False",
                    "mirror_rule": "provenance_required=True, comparison_required=True, "
                                  "authority_transfer_allowed=False, external_reflection_allowed=True",
                    "promotion_rule": "independent_grounding_required=True, "
                                      "explicit_policy_required=True, audit_event_required=True, "
                                      "default=DENY, integrity_verification_required=True",
                }
            },
            {
                "name": "ASSR Trust Gate (PowerShell)",
                "file": "C:\\AEGENTIS_WORKSPACE\\assr\\policy\\sovereign\\ASSR-TrustGate.ps1",
                "function": "Test-ASSRTrustRoute(Jurisdiction, TrustClass, Operation)",
                "behavior": {
                    "external_plus_restricted": "DENY (SOVEREIGN/OMEGA/EXECUTION/CONTROL)",
                    "external_plus_mirror_adjustment": "REFLECTION_ONLY (allowed, no authority transfer)",
                    "ai_derived": "DENY (requires independent grounding)",
                    "default_trusted": "ALLOW"
                }
            },
            {
                "name": "AEGENTIX Nanotransaction Compliance",
                "file": "C:\\Aegentix\\nanotransaction_compliance_engine.py",
                "rules": {
                    "policy": "FAIL_CLOSED",
                    "anomaly_threshold": 0.7,
                    "integrity": "HMAC-SHA256 hash chain + integrity scoring",
                    "aml_detection": True
                }
            },
            {
                "name": "Sovereign LLM Bridge",
                "file": "C:\\Sovereign\\AE-Hub\\core\\sovereign_llm_bridge_v1.2.py",
                "rules": {
                    "tier0": "Ollama localhost:11434 (local, zero cost, zero egress)",
                    "fallback": "Groq (GROQ_API_KEY) / OpenRouter (OPENROUTER_API_KEY)",
                    "pareto_locked": "unbiased/pareto, $5/month cap",
                    "confidential_guard": "PermissionError on SOVEREIGN_CONFIDENTIAL prompts",
                    "json_safeguard": "chat_json with type validation"
                }
            }
        ],
        "constitutional_invariants": [
            "AEGENTIS SHALL NOT FABRICATE REALITY",
            "REFLECTION SHALL NOT BECOME AUTHORITY",
            "FOREIGN DATA SHALL NOT COMMAND",
            "SOVEREIGN REQUIRES TRUSTED ROUTE",
            "OMEGA REQUIRES TRUSTED ROUTE",
            "AI DERIVED MATERIAL REQUIRES GROUNDING",
            "MIRROR ADJUSTMENT SHALL NOT TRANSFER AUTHORITY"
        ]
    },

    # ── LAYER 1: WORKSPACE ROOTS ──
    "workspace_roots": [
        {
            "path": "C:\\Aegentix",
            "role": "PRIMARY SESSION WORKSPACE",
            "description": "~118 top-level dirs, full Python package with brain/cyberdaw/agents/orchestrator/security/monitoring/runtime",
            "key_files": [
                ".hermes.md", "aegentix_engine.py", "aegentix_final.py",
                "autonomous_swarm.py", "agents_of_chaos_moe.py",
                "nanotransaction_compliance_engine.py", "ai-inventory.json",
                "rog_config.json", "rog_schema.json",
                "generate_architecture_map.py", "print_cyberdaw_status.py",
                "print_status_overview.py", "run_architecture_scan.py",
                "test_orientation_routing.py",
                "docker-compose*.yml (5)", "requirements.txt",
                "package.json", "tsconfig.json", "go.mod",
                "COMPLETE_OPERATIONS_MANUAL.txt", "OPERATIONS_RUNBOOK.md",
                "FINAL_STATUS.txt", "MASTER_SUMMARY.txt", "OPERATIONAL_BRIEFING.txt"
            ],
            "primary_dirs": [
                "AEGENTIX-CYBERNETICS-CORE/", "brain/", "cyberdaw/",
                "agents/", "orchestrator/", "monitoring/",
                "security/", "runtime/", "sources/sovereign-os/",
                "xrp_bot/", "anything-llm/", "lemonade/",
                "CyberDAW/", "cyberdawship/", "claw-brain/",
                "agent-mesh/", "autonomous-runtime/", "infinite-brain/",
                "jarvis/", "jetpackbrains/", "sovereign-os/",
                "omega-pipeline/", "vr-portal/", "gaia-ui/",
                "mcp-server/"
            ]
        },
        {
            "path": "C:\\AEGENTIS_WORKSPACE",
            "role": "ASSR CATALOG SYSTEM + TRUST INFRASTRUCTURE",
            "description": "Data-governance catalog with SHA256-hashed federal datasets, trust gate, ISO downloads",
            "sub_dirs": {
                "assr/": {
                    "config": "assr.config.json (v1.1) — TRUST_JURISDICTION=USA, PRIMARY_CATALOG=US-DATAGOV",
                    "trust": {
                        "policy": "trust-policy.json (v1.1, 82 lines)",
                        "gate": "ASSR-TrustGate.ps1 (PowerShell, 76 lines, Test-ASSRTrustRoute function)",
                        "classes": "trust-classes.json"
                    },
                    "catalog": {
                        "data-gov": "science-mathematics.json (1,970,360 bytes — primary math catalog)",
                        "nasa": "registry.json (684 bytes)",
                        "nist": "registry.json (578 bytes)",
                        "doe": "registry.json (540 bytes)",
                        "noaa": "registry.json (558 bytes)",
                        "usgs": "registry.json",
                        "nih": "registry.json",
                        "census": "registry.json (533 bytes)"
                    },
                    "distros": "Debian 13.6.0 amd64 netinst ISO (45 MB) + DOWNLOAD-LOG.txt",
                    "manifests": "ASSR-MANIFEST.json (4,488 bytes, SHA256 manifest of all files), ISO-MANIFEST.json, LINUX-DISTRO-DOWNLOADS.json",
                    "events": "acquisition-event.json, trust-boundary-install.jsonl",
                    "logs": "iso-acquisition.log",
                    "state": "linux-acquisition/acquisition-queue.json",
                    "reflection": "foreign/registry.json (EXTERNAL_REFLECTION classified)",
                    "provenance": "source-registry.json",
                    "schemas": "taxonomy.json",
                    "README": "README.md (994 bytes)"
                },
                "AE_HUB/": "app/ subdirectory",
                "linux-distros/": "distro files"
            }
        },
        {
            "path": "C:\\AEGENTIX-WORKSPACE",
            "role": "GITHUB REPO CLONES + OMNICYBERDEX",
            "description": "30+ empty git repo clones (no content checked out) + active omnicyberdex master engine",
            "sub_dirs": {
                "github-repos/": "30+ empty directories: aegentis-cloudshell-organizer, aegentis-vr-backend, Aegentix, AEGENTIX-AGENT-MESH, AEGENTIX-DEVTOOLS, AEGENTIX-FINANCIAL-LEDGER, AEGENTIX-LABS-ARCHIVE, AEGENTIX-Linux-PreVerify, AEGENTIX-MISSION-CONTROL, aegentix-omnichain-solver, AEGENTIX-SECURITY-INTELLIGENCE, AEGENTIX-XR-SPATIAL, agent, agentic-ai-orchestrator, agentkit, agnesai-models, antigravity-sdk-python, awesome-claude-fable-5, cai, cbdc-mantis-engine",
                "omnicyberdex/": {
                    "config": "omnicyberdex.json",
                    "master": "omnicyberdex_master.py — OmniCyberDEX Master Engine v3.0.0, 300-node connection mesh, component registration",
                    "data/": "empty",
                    "engines/": "empty",
                    "logs/": "empty"
                },
                "src/python/": "minimal/empty",
                "logs/": "empty"
            }
        },
        {
            "path": "C:\\Users\\eagle",
            "role": "USER PROFILE — DENSE MULTI-STACK HUB",
            "description": "The user's home directory is itself a full workspace with parallel installations of every major AI IDE/runtime, swarms, voice/audio subsystems, AMD Ryzen DNA staging (18 stages), and project copies",
            "project_copies": [
                "aegentix/ (symlink or copy of C:\\Aegentix?)",
                "aegentix_swarm/ (symlink)",
                "AEGENTIX-AGENT-MESH/ (symlink)",
                "AEGENTIX-CYBERNETICS-CORE/ (git repo: shalominattii-us/AEGENTIX-CYBERNETICS-CORE, .autonomous-state.json v2.0, 140 top-level entries, deployment package zip)",
                "AEGENTIX-MISSION-CONTROL/ (cybergenetic-starship/, sources/)",
                "aegentix-omnichain-solver/ (Dockerfile, orchestrator.js, package.json, omnichain_300_node_mesh.py, src/, tests/)",
                "AEGENTIX-SECURITY-INTELLIGENCE/",
                "SOVEREIGN_CORE/"
            ],
            "ai_ide_runtimes_installed": [
                ".antigravity-ide/", ".claude/", ".codex/", ".gemini/",
                ".grokbot/", ".kimi-code/", ".herdr/", ".heretic/",
                ".lmstudio/ (FULL: apps, audio, bin, config-presets, conversations, credentials, extensions, hub, mcp.json, models, projects, scratchpads, server-logs, settings.json, skills, transcriptions)",
                ".ollama/ (cache, models, id_ed25519 keypair)",
                ".mcp-auth/ (mcp-remote-v1/)",
                ".cursor/", ".vscode/", ".vscode-shared/",
                ".cua-driver/", ".bun/", ".dotnet/", ".rustup/",
                ".cargo/", ".docker/", ".kaggle/", ".local/",
                ".npm/", ".config/"
            ],
            "voice_audio_subsystem": [
                "piper_models/ (Piper TTS models)",
                "Captain-Kirk-AI-Voice/",
                "trump_voice_audio/",
                "edge_voice_tests/",
                "jarvis_kirk_audio/",
                "jarvis_kirk_voice.py",
                "jarvis_voice_loop.py",
                "jarvis_pipe.py",
                "jarvis_real.py",
                "jarvis_server.py",
                "trump_voice.py",
                "edge_final_en_US_*Neural.mp3 (3 files)",
                "piper_kirk_output.wav",
                "piper_kirk_ryan.mp3",
                "piper_kirk_ryan.wav",
                "test_glory.mp3",
                "edge_kirk_test.mp3"
            ],
            "blockchain_crypto": [
                ".ethereum/",
                ".ethereum-custom/",
                ".ethereum-geth/"
            ],
            "other_projects": [
                "AMD_RYZEN_DNA_STAGE1-18 + STAGE5_FULL (18 staged pipelines)",
                "Foundry/ (agent/, cast_to_video.py, CLAUDE.md, DEMO.md, demo.tape, docker-compose.yml, Dockerfile*, docs/, examples/, infra/, openplanter-desktop, pyproject.toml, quickstart_investigation.py, record_demo.py)",
                "sovereign-os/",
                "LLM_CYBERCORE/",
                "NeedleHub/",
                "osint-engine/",
                "infinite-brain-harness/",
                "Jarvis_Stark_Core/",
                "laya/",
                "worldmonitor/",
                "gaia-cookbook/",
                "github/",
                "Projects/",
                "public-apis/",
                "scripts/",
                "terminals/",
                "CyberCore/",
                "CyberGym/"
            ]
        }
    ],

    # ── LAYER 2: LLM RUNTIMES (5 installed in parallel) ──
    "llm_runtimes": [
        {
            "name": "Ollama",
            "path": "C:\\Users\\eagle\\.ollama\\",
            "role": "Local tier0 inference (localhost:11434), models cache, ed25519 keypair",
            "consumers": [
                "C:\\Sovereign\\AE-Hub\\core\\sovereign_llm_bridge_v1.2.py (tier0)",
                "C:\\Aegentix\\ai-inventory.json (maintained_deferred_local_deployment)"
            ]
        },
        {
            "name": "LM Studio",
            "path": "C:\\Users\\eagle\\.lmstudio\\",
            "role": "Full LM Studio installation with models, conversations, MCP, skills",
            "size": "LARGE (full directory tree)"
        },
        {
            "name": "AnythingLLM",
            "path": "C:\\SovereignSystem\\",
            "role": "Full AGP/LLM platform + Ollama + ledger system",
            "description": "5048 files, includes inventory_manifest.json — separate self-contained LLM stack",
            "size": "LARGE"
        },
        {
            "name": "Sovereign LLM Bridge Suite",
            "path": "C:\\Sovereign\\AE-Hub\\core\\",
            "files": [
                "sovereign_llm_bridge_v1.2.py (PRIMARY — local-first, Ollama tier0, Groq/OpenRouter fallback, Pareto-locked, CONFIDENTIAL guard)",
                "sovereign_llm_config_v1.2.json",
                "sovereign_llm_config_v1.1.json",
                "sovereign_llm_config.patch.json",
                "union_alpha_bridge.py (OpenRouter union bridge)",
                "union_alpha_bridge_v1.1.py",
                "selftest_bridge_v1.1.py",
                "selftest_bridge_v1.2.py",
                "selftest_union_alpha.py"
            ],
            "architecture": "3 versioning streams (v1.1, v1.2, union_alpha) showing iterative development"
        },
        {
            "name": "Ori Harness (OpenRouter)",
            "path": "C:\\Aegentix\\brain\\",
            "files": [
                "cognitive_runtime.json (v2.0 — Ori Harness config)",
                "router/model_registry.json (cloud slot mappings: GPT-4o, Claude 3.5 Sonnet, Gemini 2.0 Flash, Mistral Large, Llama 3.1 70B)"
            ],
            "role": "Cloud slot routing via OpenRouter when local backends are deferred"
        }
    ],

    # ── LAYER 3: CYBERDAW PRODUCTION GATE ──
    "cyberdaw_gate": {
        "primary": "C:\\Aegentix\\cyberdaw\\",
        "parallel_copies": [
            "C:\\Aegentix\\CyberDAW\\",
            "C:\\Aegentix\\cyberdawship\\"
        ],
        "files": {
            "gate.py": "13-check fail-closed production gate. Currently 3/13 cleared: AUDIO_INTERFACE_LOCKED, PA_ROUTING_VERIFIED, MAX_BRIDGE_CONNECTED. Remaining 10 blockers depend on live Ableton/M4L clip/scene selection telemetry.",
            "adapters/telemetry_router.js": "Node.js script handling HTTP loopback to cognitive_bus.py",
            "CyberDAW_Telemetry_Engine.amxd": "Max for Live device blueprint (raw Max 5 patcher JSON)",
            "cyberdaw_scene_watcher.ps1": "PowerShell scene watcher script",
            "docs/cyberdaw/PRODUCTION_GATE.md": "Production gate documentation"
        },
        "status": "FAIL_CLOSED — PRODUCTION_BLOCKED — 3/13 checkpoints cleared — 10 blockers remaining"
    },

    # ── LAYER 4: SWARM + ORCHESTRATION ──
    "swarm_orchestration": {
        "path": "C:\\Aegentix\\",
        "agents_dir": "agents/ (5 swarm agents: research/security/testing/coding/infrastructure, each with manifest.json)",
        "orchestrator_dir": "orchestrator/ (kanban/, events/, policy/, registry/, schedules/, state/, workflows/)",
        "key_files": {
            "autonomous_swarm.py": "SwarmManager.swarm_think() — cross-agent consensus routing",
            "agents_of_chaos_moe.py": "7-agent MoE guardrail",
            "brain/cognitive_bus.py": "SHA-256 hash-chained JSONL event stream — the central event bus",
            "brain/cognitive_kernel_bridge.py": "Dynamic loader → JSONL event stream",
            "brain/router/model_registry.json": "Cloud slot mappings for Ori Harness",
            "brain/cognitive_runtime.json": "Ori Harness v2.0 runtime config",
            "ai-inventory.json": "AI inventory with maintained_deferred_local_deployment for Ollama",
            "runtime/state.json": "Runtime state"
        },
        "hermes_layer": {
            "profile": "C:\\Users\\eagle\\.hermes\\ (skills, plugins, cron, memories)",
            "daemon": "C:\\Users\\eagle\\.herdr\\ (packages/)",
            "policy": "C:\\Aegentix\\.hermes.md (Solar Pro 4, nous, 10 children, swarm consensus, Falco, port whitelist, FAIL_CLOSED)",
            "orchestrator": "C:\\Aegentix\\orchestrator\\"
        }
    },

    # ── LAYER 5: XRPL/XAMAN + TRADING ──
    "trading_layer": {
        "xrpl_xaman": {
            "path": "C:\\Aegentix\\AEGENTIX-CYBERNETICS-CORE\\",
            "dirs": [
                "xaman-xpmarket-dashboard/ (XRPL/Xaman dashboard)",
                "zaman_wallet_connector/ (wallet connector)",
                "autonomous_coin_agents_mesh/",
                "xaman_custody_websocket/",
                "xaman_secret_numbers_converter/"
            ]
        },
        "xrp_bot": {
            "path": "C:\\Aegentix\\xrp_bot\\",
            "dirs": ["core/", "tokens/", "utils/"]
        },
        "omnicyberdex": {
            "path": "C:\\AEGENTIS_WORKSPACE\\omnicyberdex\\",
            "engine": "omnicyberdex_master.py — OmniCyberDEX Master Engine v3.0.0, 300-node mesh"
        },
        "blockchain_data": {
            "path": "C:\\BlockchainData\\",
            "files": ["omnicyberdex_master.py", "earning_engine.py"],
            "node_scripts": "8 blockchain node scripts (besu, geth, solana, + 5 more)"
        },
        "blockchain_nodes": {
            "path": "C:\\MinimalNodes\\nodes.json",
            "description": "300 blockchain node definitions"
        },
        "hedera": {
            "path": "C:\\hedera-starter\\",
            "files": ["server.js", "package.json"]
        }
    },

    # ── LAYER 6: BLOCKCHAIN NODES ──
    "blockchain_infrastructure": [
        "C:\\MinimalNodes\\nodes.json (300 node definitions)",
        "C:\\hedera-starter\\ (Hedera node starter)",
        "C:\\BlockchainData\\besu\\ (Hyperledger Besu)",
        "C:\\BlockchainData\\geth\\ (Ethereum Go)",
        "C:\\BlockchainData\\solana\\ (Solana validator)",
        "C:\\Users\\eagle\\.ethereum\\ (Ethereum configs)",
        "C:\\Users\\eagle\\.ethereum-geth\\ (Geth node)"
    ],

    # ── LAYER 7: VOICE/AUDIO ──
    "voice_audio_subsystem": {
        "description": "First-class infrastructure from Piper TTS through Edge neural voices to Ableton/M4L CyberDAW telemetry",
        "piper_tts": "C:\\Users\\eagle\\piper_models/ (local voice synthesis models)",
        "captain_kirk": "C:\\Users\\eagle\\Captain-Kirk-AI-Voice/",
        "trump_voice": "C:\\Users\\eagle\\trump_voice_audio/ + trump_voice.py",
        "edge_voices": "C:\\Users\\eagle\\edge_voice_tests/ + edge_final_en_US_*Neural.mp3 (3 files)",
        "jarvis_pipeline": [
            "C:\\Users\\eagle\\jarvis_kirk_audio/",
            "C:\\Users\\eagle\\jarvis_kirk_voice.py",
            "C:\\Users\\eagle\\jarvis_voice_loop.py",
            "C:\\Users\\eagle\\jarvis_pipe.py",
            "C:\\Users\\eagle\\jarvis_real.py",
            "C:\\Users\\eagle\\jarvis_server.py"
        ],
        "piper_outputs": [
            "C:\\Users\\eagle\\piper_kirk_output.wav",
            "C:\\Users\\eagle\\piper_kirk_ryan.mp3",
            "C:\\Users\\eagle\\piper_kirk_ryan.wav"
        ],
        "cyberdaw": "C:\\Aegentix\\cyberdaw\\ (Ableton/M4L — audio telemetry into cognitive_bus.py)"
    },

    # ── LAYER 8: DUPPLICATE/PARALLEL CHAOS ──
    "duplication_map": [
        ["C:\\Aegentix\\", "C:\\Users\\eagle\\aegentix\\", "DUPLICATE or symlink — need verification"],
        ["C:\\Aegentix\\cyberdaw\\", "C:\\Aegentix\\CyberDAW\\", "PARALLEL — both exist"],
        ["C:\\Aegentix\\brain\\", "C:\\Aegentix\\claw-brain\\", "PARALLEL brain layers"],
        ["C:\\Aegentix\\sources\\sovereign-os\\", "C:\\Users\\eagle\\sovereign-os\\", "PARALLEL sovereign-os"],
        ["C:\\Aegentix\\", "C:\\Users\\eagle\\AEGENTIX-CYBERNETICS-CORE\\", "PARALLEL — git repo with different content (deployment package zip, diagnostics scripts, .autonomous-state.json)"],
        ["C:\\Aegentix\\anything-llm\\", "C:\\SovereignSystem\\", "PARALLEL LLM stacks"],
        ["C:\\Aegentix\\xrp_bot\\", "C:\\AEGENTIS_WORKSPACE\\omnicyberdex\\", "PARALLEL trading layers"],
        ["C:\\Aegentix\\orchestrator\\", "C:\\Users\\eagle\\.hermes\\", "PARALLEL orchestration (Hermes native vs custom)"],
        ["Multiple JETPACKBRAINS_*.ps1 pairs", "agent-mesh/autonomous-runtime/infinite-brain/jarvis/jetpackbrains/sovereign-os/omega-pipeline/vr-portal/gaia-ui/", "DUPLICATE autostart scripts across 9 parallel directories"]
    ],

    # ── CROSS-CUTTING ARCHITECTURAL PRINCIPLES ──
    "principles": [
        {
            "name": "Trust is tiered and deny-by-default",
            "evidence": "ASSR trust-policy.json, AEGENTIX nanotransaction_compliance_engine.py FAIL_CLOSED, Sovereign LLM bridge CONFIDENTIAL guard — all three subsystems independently enforce the same pattern",
            "rule": "External/foreign sources can inform mirrors but never command authority. Sovereign/Omega/Execution/Control require trusted local routes. Promotion requires independent grounding + explicit policy + audit event."
        },
        {
            "name": "Local-first inference with cloud fallback",
            "evidence": "Sovereign LLM bridge v1.2 (Ollama tier0 → Groq/OpenRouter fallback), ai-inventory.json maintained_deferred_local_deployment, cognitive_runtime.json Ori Harness as cloud fallback",
            "rule": "Ollama at localhost:11434 is the preferred tier0 everywhere. Remote endpoints are optional failover. Sovereign/confidential data does not egress without explicit opt-in."
        },
        {
            "name": "Voice/audio is first-class infrastructure",
            "evidence": "Piper TTS models, Edge neural voices (3), Captain Kirk and Trump voice clones, Jarvis pipeline (5 scripts), Ableton/M4L CyberDAW telemetry gate — audio is a production dependency not a toy",
            "rule": "Audio subsystem spans from local TTS synthesis through cloud voice APIs to live DAW telemetry. Production gate explicitly depends on live audio telemetry."
        },
        {
            "name": "Workspace is a multi-layered mesh, not a tree",
            "evidence": "Parallel copies of AEGENTIX-CYBERNETICS-CORE at C:\\Aegentix, C:\\Users\\eagle, and possibly C:\\AEGENTIS_WORKSPACE; multiple CyberDAW layers; multiple brain/inference layers; multiple sovereign-os layers; multiple AI IDE runtimes installed simultaneously",
            "rule": "Canonical path for current session is C:\\Aegentix, but parallel layers 각自的 have their own role. Duplication is the norm, not the exception."
        },
        {
            "name": "Operational readiness is gated",
            "evidence": "CyberDAW production gate (13-check fail-closed, 3/13 cleared), ASSR promotion policy (DENY_BY_DEFAULT), nanotransaction compliance FAIL_CLOSED, 0.7 anomaly threshold",
            "rule": "Nothing goes live without evidence. The stack stays blocked until real telemetry/events prove readiness."
        },
        {
            "name": "Hermes is the coordination layer",
            "evidence": ".hermes/ profile (skills/plugins/cron/memories), .herdr/ daemon packages, C:\\Aegentix\\.hermes.md policy, C:\\Aegentix\\orchestrator\\ directory, 5 swarm agents with manifests",
            "rule": "Hermes orchestrates the swarm agents. It does not replace them. Swarm consensus (autonomous_swarm.py) is the authority for cross-agent decisions."
        }
    ],

    # ── CRITICAL GAPS / UNRESOLVED ──
    "gaps": [
        "Symlink status of C:\\Users\\eagle\\aegentix, aegentix_swarm, AEGENTIX-AGENT-MESH vs C:\\Aegentix",
        "Content parity between C:\\Aegentix\\AEGENTIX-CYBERNETICS-CORE and C:\\Users\\eagle\\AEGENTIX-CYBERNETICS-CORE (git repo has different files: deployment zip, diagnostics, .autonomous-state.json)",
        "Actual content of C:\\SovereignSystem\\ (5048 files — AnythingLLM + Ollama + ledger — not deeply scanned)",
        "Verified Ollama model list in C:\\Users\\eagle\\.ollama\\models\\",
        "Verified LM Studio model list in C:\\Users\\eagle\\.lmstudio\\models\\",
        "Actual state of C:\\AEGENTIX-WORKSPACE\\omnicyberdex\\config\\omnicyberdex.json",
        "Content of C:\\Sovereign\\ledger\\ledger.json",
        "Symlink status of C:\\Aegentix\\AEGENTIX-CYBERNETICS-CORE vs the git remote (github.com/shalominattii-us/AEGENTIX-CYBERNETICS-CORE)",
        "Which JETPACKBRAINS_*.ps1 pairs are active vs stale",
        "Whether C:\\Users\\eagle\\sovereign-os\\ mirrors C:\\Aegentix\\sources\\sovereign-os\\ or C:\\SovereignOS\\"
    ]
}

if __name__ == "__main__":
    output = json.dumps(MAP, indent=2, ensure_ascii=False)
    print(output[:500])
    print(f"\n... ({len(output)} bytes total)")
    Path("/tmp/cdrive_structural_map.json").write_text(output)
    print(f"Written to /tmp/cdrive_structural_map.json")

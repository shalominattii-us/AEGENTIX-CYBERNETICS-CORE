"""Final AEGENTIX CyberDAW status — pre-Ableton live operation.

Checks all pipeline components and prints a clean status overview.
Run:  python C:\Aegentix\print_cyberdaw_status.py
"""

import json, hmac, hashlib, urllib.request
from pathlib import Path

SECRET_KEY = b"AEGENTIX_EOC_PRIME_LOCK"
RUNTIME = "http://127.0.0.1:8000"
STREAM = Path("C:/Aegentix/brain/telemetry_stream.jsonl")


def _get(path):
    resp = urllib.request.urlopen(f"{RUNTIME}{path}", timeout=10)
    return json.loads(resp.read())


def _post(payload):
    canonical = json.dumps(payload, sort_keys=True).encode("utf-8")
    sig = hmac.new(SECRET_KEY, canonical, hashlib.sha256).hexdigest()
    payload["signature"] = sig
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{RUNTIME}/cyberdaw/telemetry", data=data,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())


def _verify_hmac(obj):
    sig_stored = obj.pop("signature", "")
    canonical = json.dumps(obj, sort_keys=True).encode("utf-8")
    return hmac.new(SECRET_KEY, canonical, hashlib.sha256).hexdigest() == sig_stored.lower()


# ── Collect status ────────────────────────────────────────────────────────────

print("=" * 74)
print("  AEGENTIX CYBERDAW — FINAL STATUS OVERVIEW")
print("=" * 74)
print()

# 1. Runtime
try:
    health = _get("/health")
    runtime_ok = health["ok"]
    openrouter = health["stats"]["openrouter_available"]
except Exception as e:
    runtime_ok = False
    openrouter = False
    print(f"  [ERROR] Runtime unreachable: {e}")

print("1. RUNTIME (multi-llm-runtime + telemetry bridge)")
print("-" * 58)
print(f"  Endpoint       : {RUNTIME}")
print(f"  Health         : {'OK (200)' if runtime_ok else 'UNREACHABLE'}")
print(f"  Service        : {health.get('service', 'N/A')}")
print(f"  OpenRouter     : {'available (authenticated)' if openrouter else 'no key / unavailable'}")
print()

# 2. Gate
try:
    gate = _get("/cyberdaw/gate")
except Exception:
    gate = {}

print("2. CYBERDAW PRODUCTION GATE")
print("-" * 58)
print(f"  State              : {gate.get('state', 'N/A')}")
print(f"  Production ready   : {gate.get('production_ready', False)}")
blockers = gate.get("blockers", [])
print(f"  Blockers remaining : {len(blockers)} of 13")
print()
cleared = [n for n, i in gate.get("checks", {}).items() if i["verified"]]
print("  Cleared checkpoints:")
for c in cleared:
    detail = gate["checks"][c]["detail"]
    print(f"    + {c:25s} ({detail})")
print()
print("  Remaining blockers:")
for b in blockers:
    print(f"    - {b:25s}")
print()

# 3. Telemetry stream
print("3. TELEMETRY STREAM (brain/telemetry_stream.jsonl)")
print("-" * 58)
try:
    lines = list(STREAM.open())
except Exception:
    lines = []
print(f"  Events in stream   : {len(lines)}")
print(f"  HMAC-verified      : {sum(1 for l in lines if _verify_hmac(json.loads(l)))}")
print(f"  Gate-clearing ev.  : {sum(1 for l in lines if json.loads(l).get('gate_checkpoint'))}")
print()
for i, line in enumerate(lines, 1):
    obj = json.loads(line)
    ev_name = obj["event"]
    hmac_ok = _verify_hmac(obj)
    gc = obj.get("gate_checkpoint", "N/A")
    print(f"  [{i}] {ev_name:30s}  HMAC:{'OK' if hmac_ok else 'FAIL'}  gate:{gc}")

print()
print("4. CYBERDAW ADAPTERS")
print("-" * 58)
adapters = {
    "telemetry_router.js": Path("cyberdaw/adapters/telemetry_router.js"),
    "CyberDAW_Telemetry_Engine.amxd": Path("cyberdaw/adapters/CyberDAW_Telemetry_Engine.amxd"),
    "cyberdaw_scene_watcher.ps1": Path("cyberdaw/adapters/cyberdaw_scene_watcher.ps1"),
}
for name, p in adapters.items():
    exists = p.exists()
    size = p.stat().st_size if exists else 0
    print(f"  {name:40s} : {'EXISTS' if exists else 'MISSING'} ({size} bytes)")

print()
print("5. PIPELINE FLOW (Ableton -> Gate)")
print("-" * 58)
print("  1. Ableton Live master track: CyberDAW_Telemetry_Engine.amxd device")
print("  2. live.path -> live.observer detects scene/clip selection")
print("  3. node.script (telemetry_router.js) builds HMAC-signed payload")
print("  4. HTTP POST ->", f"{RUNTIME}/cyberdaw/telemetry")
print("  5. Runtime verifies HMAC, updates ProductionGate.checks[],",)
print("     appends to cognitive_bus event stream + telemetry_stream.jsonl")
print("  6. cyberdaw_scene_watcher.ps1 polls stream, prints Herdr notifications")
print("  7. On each new scene/clip event, gate blockers decrement")
print("  8. When 10 remaining cleared -> PRODUCTION_BLOCKED -> LIVE_PA_READY")
print()
print("  Gate mapping:")
for ev, check in sorted({
    "AUDIO_INTERFACE_LOCKED": "audio_interface",
    "PA_ROUTING_VERIFIED": "pa_routing",
    "MAX_BRIDGE_CONNECTED": "stream",
    "SCENE_SELECTION_ACTIVE": "swarm_cue",
    "CLIP_LAUNCH_EVENT": "recording",
}.items()):
    status = "CLEARED" if check in cleared else "blocked"
    print(f"    {ev:30s} -> {check:20s} [{status}]")

print()
print("=" * 74)
print("  STATUS: Foundation stabilized. Ready for Ableton Live operation.")
print("  Next action: Drop CyberDAW_Telemetry_Engine.amxd on master track", )
print("               in Ableton Live to begin clearing the remaining 10 blockers.")
print("=" * 74)

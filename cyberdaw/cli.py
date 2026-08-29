from __future__ import annotations

import argparse
import json

from .adapters import AbletonProductionAdapter, DevelopmentAdapter
from .gate import ProductionGate


def build_gate() -> ProductionGate:
    gate = ProductionGate()

    # Development/demo evidence is explicit. The Trial target can verify the
    # development adapter, but it is never mapped to ableton_production.
    demo = {
        "orbital": "Orbital supervisor available",
        "obs": "OBS adapter contract available",
        "audio_interface": "audio interface verification hook available",
        "pa_routing": "PA routing verification hook available",
        "recording": "recording verification hook available",
        "stream": "stream verification hook available",
        "swarm_cue": "Swarm cue engine available",
        "emergency_stop": "hard stop path available",
        "watchdog": "watchdog policy available",
        "resource_headroom": "resource headroom policy available",
        "offline_operation": "offline-first policy available",
    }
    for name, detail in demo.items():
        gate.set_check(name, True, detail)

    # Production Ableton remains blocked until real Suite + Max for Live + M4L
    # bridge evidence is supplied by the production environment.
    ableton = AbletonProductionAdapter().verify()
    gate.set_check("ableton_production", ableton.availability.value == "VERIFIED", ableton.detail)
    gate.set_check("maxforlive_bridge", False, "requires verified production Max-for-Live bridge")
    return gate


def main() -> int:
    parser = argparse.ArgumentParser(prog="cyberdaw")
    parser.add_argument("command", choices=["verify"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_gate().report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("AEGENTIX CYBERDAW PRODUCTION GATE")
        print("=" * 38)
        for name, result in report["checks"].items():
            print(f"{name:24} {'PASS' if result['verified'] else 'BLOCKED'}")
        print("-" * 38)
        print(f"STATE: {report['state']}")
        print(f"LIVE PA READY: {'YES' if report['production_ready'] else 'NO'}")
        if report["blockers"]:
            print("BLOCKERS: " + ", ".join(report["blockers"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

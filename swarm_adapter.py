#!/usr/bin/env python3
"""
Swarm Adapter — Hermes ↔ Python Swarm Bridge

Given a situation dict, loads swarm_state.json + active_swarm_manifest.json,
imports SwarmManager from autonomous_swarm, calls swarm_think(situation), and
returns consensus + per-agent decisions as a structured dict suitable for a
Hermes delegate to act on.

Usage:
    echo '{"issue":"...","risk":"..."}' | python swarm_adapter.py
    python swarm_adapter.py --situation-file path/to/situation.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

# Paths are anchored to the project root so the adapter is relocatable.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SWARM_STATE_PATH = os.path.join(PROJECT_ROOT, "swarm_state.json")
MANIFEST_PATH = os.path.join(PROJECT_ROOT, "active_swarm_manifest.json")
SWARM_MODULE = os.path.join(PROJECT_ROOT, "autonomous_swarm.py")


def load_json(path: str, label: str) -> Dict[str, Any]:
    """Load and return a JSON file, exiting hard on failure."""
    if not os.path.isfile(path):
        print(f"ERROR: {label} not found at {path}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"ERROR: Cannot read {label} ({path}): {exc}", file=sys.stderr)
        sys.exit(1)


def import_swarm_manager() -> "SwarmManager":
    """Import SwarmManager from the project's autonomous_swarm module."""
    import importlib.util

    if not os.path.isfile(SWARM_MODULE):
        print(f"ERROR: autonomous_swarm.py not found at {SWARM_MODULE}", file=sys.stderr)
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("autonomous_swarm", SWARM_MODULE)
    if spec is None or spec.loader is None:
        print("ERROR: Failed to build module spec for autonomous_swarm.py", file=sys.stderr)
        sys.exit(1)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "SwarmManager"):
        print("ERROR: autonomous_swarm.py does not expose SwarmManager", file=sys.stderr)
        sys.exit(1)

    return module.SwarmManager


def run(situation: Dict[str, Any]) -> Dict[str, Any]:
    """Run the full adapter pipeline and return a Hermes-ready result dict."""
    # Load supporting state that Hermes delegates are expected to read first.
    swarm_state = load_json(SWARM_STATE_PATH, "swarm_state.json")
    manifest = load_json(MANIFEST_PATH, "active_swarm_manifest.json")

    # Import and invoke the swarm.
    SwarmManager = import_swarm_manager()
    manager = SwarmManager()
    manager.create_default_swarm()
    swarm_result = manager.swarm_think(situation)

    # Flatten into a stable schema a Hermes delegate can consume without
    # knowing the internals of autonomous_swarm.py.
    return {
        "timestamp": datetime.now().isoformat(),
        "situation": situation,
        "swarm_state": swarm_state,
        "manifest": manifest,
        "consensus": swarm_result.get("consensus", "no_consensus"),
        "decisions": {
            agent_name: {
                "decision": d.get("decision"),
                "rationale": d.get("rationale"),
                "timestamp": d.get("timestamp"),
            }
            for agent_name, d in swarm_result.get("decisions", {}).items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hermes ↔ Python Swarm bridge. Reads a situation and returns swarm consensus as JSON."
    )
    parser.add_argument(
        "--situation-file",
        type=str,
        default=None,
        help="Path to a JSON file containing the situation dict. Overrides stdin.",
    )
    args = parser.parse_args()

    if args.situation_file:
        situation = load_json(args.situation_file, "situation file")
    else:
        raw = sys.stdin.read()
        if not raw.strip():
            print("ERROR: No situation provided on stdin and no --situation-file given", file=sys.stderr)
            sys.exit(1)
        try:
            situation = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"ERROR: stdin is not valid JSON: {exc}", file=sys.stderr)
            sys.exit(1)

    result = run(situation)
    json.dump(result, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

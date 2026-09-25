from __future__ import annotations

import json
import os
import platform
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\aegentix")
ORG = ROOT / "organism"
SELF_DIR = ORG / "self-awareness"

MODEL = SELF_DIR / "self-model.json"
EVENTS = SELF_DIR / "self-awareness.jsonl"

STATE = ORG / "state" / "organism-state.json"
POLICY = ORG / "control-plane" / "organism-policy.json"
RECOVERY = ORG / "state" / "recovery.json"
HEARTBEAT = ORG / "state" / "heartbeat.json"

INDEX = ORG / "state" / "opportunity-index.json"
DNA = ORG / "queue" / "dna.jsonl"
OPPORTUNITIES = ORG / "ledger" / "opportunities.jsonl"
EVENT_LEDGER = ORG / "ledger" / "organism-events.jsonl"
COMMAND_FEED = ORG / "telemetry" / "command-center-feed.jsonl"


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path):
    if not path.exists():
        return {}

    try:
        return json.loads(
            path.read_text(encoding="utf-8-sig")
        )
    except Exception as exc:
        return {
            "_error": str(exc),
            "_path": str(path),
        }


def count_jsonl(path: Path):
    if not path.exists():
        return 0

    try:
        with path.open(
            "r",
            encoding="utf-8-sig"
        ) as handle:
            return sum(
                1
                for line in handle
                if line.strip()
            )
    except Exception:
        return 0


def artifact(path: Path):
    if not path.exists():
        return {
            "exists": False,
            "path": str(path),
        }

    try:
        stat = path.stat()

        return {
            "exists": True,
            "path": str(path),
            "bytes": stat.st_size,
            "modified_utc": datetime.fromtimestamp(
                stat.st_mtime,
                timezone.utc
            ).isoformat(),
        }

    except Exception as exc:
        return {
            "exists": True,
            "path": str(path),
            "error": str(exc),
        }


def get_processes():
    result = []

    command = (
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,Name,CommandLine | "
        "ConvertTo-Json -Depth 6"
    )

    try:
        raw = subprocess.check_output(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                command,
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )

        data = json.loads(raw)

        if isinstance(data, dict):
            data = [data]

        for item in data:
            cmd = item.get("CommandLine") or ""
            low = cmd.lower()

            if (
                "c:\\aegentix\\organism" in low
                or "c:\\aegentix\\runtime" in low
                or "c:\\aegentix\\moe" in low
            ):
                result.append(
                    {
                        "pid": item.get("ProcessId"),
                        "name": item.get("Name"),
                        "command": cmd,
                    }
                )

    except Exception as exc:
        result.append(
            {
                "error": str(exc)
            }
        )

    return result


def count_organism_files():
    if not ORG.exists():
        return 0

    count = 0

    for path in ORG.rglob("*"):
        if not path.is_file():
            continue

        if "__pycache__" in path.parts:
            continue

        count += 1

    return count


def build_self_model():
    state = read_json(STATE)
    policy = read_json(POLICY)
    recovery = read_json(RECOVERY)
    heartbeat = read_json(HEARTBEAT)
    index = read_json(INDEX)

    processes = get_processes()

    files = {
        "state": artifact(STATE),
        "policy": artifact(POLICY),
        "recovery": artifact(RECOVERY),
        "heartbeat": artifact(HEARTBEAT),
        "opportunity_index": artifact(INDEX),
        "dna_queue": artifact(DNA),
        "opportunity_ledger": artifact(OPPORTUNITIES),
        "event_ledger": artifact(EVENT_LEDGER),
        "command_feed": artifact(COMMAND_FEED),
        "persistent_runtime": artifact(
            ORG / "start-persistent-organism.ps1"
        ),
        "organism_coordinator": artifact(
            ORG / "coordinator" / "continuous.py"
        ),
        "moe_directive": artifact(
            ROOT / "moe" / "ORGANISM_MOE_INSTRUCTION.md"
        ),
    }

    missing = [
        key
        for key, value in files.items()
        if not value.get("exists")
    ]

    ledger_counts = {
        "events": count_jsonl(EVENT_LEDGER),
        "opportunities": count_jsonl(OPPORTUNITIES),
        "dna": count_jsonl(DNA),
        "command_feed": count_jsonl(COMMAND_FEED),
    }

    state_opportunities = int(
        state.get("discovered", 0) or 0
    )

    index_opportunities = int(
        index.get("discovered", 0) or 0
    )

    unique_opportunities = int(
        index.get("count", 0) or 0
    )

    dna_count = ledger_counts["dna"]

    completed = len(
        [
            item
            for item in load_jsonl(DNA)
            if item.get("state") == "COMPLETED"
        ]
    )

    failed = len(
        [
            item
            for item in load_jsonl(DNA)
            if item.get("state") == "FAILED"
        ]
    )

    runtime_detected = any(
        item.get("pid")
        for item in processes
    )

    online_declared = (
        str(
            state.get(
                "runtime_status",
                ""
            )
        ).upper()
        == "ONLINE"
    )

    if online_declared and runtime_detected:
        runtime_truth = "ONLINE_CONFIRMED"
    elif online_declared and not runtime_detected:
        runtime_truth = "DECLARED_ONLINE_BUT_PROCESS_MISSING"
    elif runtime_detected and not online_declared:
        runtime_truth = "PROCESS_RUNNING_BUT_STATE_NOT_ONLINE"
    else:
        runtime_truth = "OFFLINE"

    counter_sync = (
        state_opportunities == index_opportunities
        and unique_opportunities == ledger_counts["opportunities"]
    )

    # HEALTHY means observed state is internally coherent.
    # Empty workload is not itself a failure.
    health = "HEALTHY"

    if missing:
        health = "DEGRADED"

    if runtime_truth != "ONLINE_CONFIRMED":
        health = "DEGRADED"

    if not counter_sync:
        health = "DEGRADED"

    model = {
        "schema": "aegentix.self-model.v3",
        "generated_at": now(),

        "identity": {
            "organism_id": state.get("organism_id"),
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "root": str(ROOT),
            "organism_root": str(ORG),
        },

        "canonical_metrics": {
            "health": health,
            "runtime": runtime_truth,
            "opportunities": unique_opportunities,
            "dna": dna_count,
            "completed": completed,
            "failed": failed,
            "counter_sync": counter_sync,
        },

        "opportunities": {
            "discovered": state_opportunities,
            "unique": unique_opportunities,
            "deduplicated": int(
                index.get("deduplicated", 0) or 0
            ),
            "dna_created": dna_count,
            "completed": completed,
            "failed": failed,
        },

        "dna": {
            "total": dna_count,
            "completed": completed,
            "failed": failed,
            "ready": len(
                [
                    item
                    for item in load_jsonl(DNA)
                    if item.get("state") == "READY"
                ]
            ),
            "running": len(
                [
                    item
                    for item in load_jsonl(DNA)
                    if item.get("state")
                    in ("RUNNING", "EXECUTING")
                ]
            ),
        },

        "runtime": {
            "declared": state.get("runtime_status"),
            "truth": runtime_truth,
            "process_count": len(processes),
            "processes": processes,
        },

        "persistence": {
            "state": files["state"],
            "policy": files["policy"],
            "recovery": files["recovery"],
            "heartbeat": files["heartbeat"],
            "opportunity_index": files["opportunity_index"],
            "dna_queue": files["dna_queue"],
            "opportunity_ledger": files["opportunity_ledger"],
            "event_ledger": files["event_ledger"],
            "command_feed": files["command_feed"],
            "persistent_runtime": files["persistent_runtime"],
        },

        "ledger_counts": ledger_counts,

        "composition": {
            "organism_files": count_organism_files(),
        },

        "reconciliation": {
            "missing_artifacts": missing,
            "counter_sync": counter_sync,
            "status": (
                "COHERENT"
                if not missing and counter_sync
                else "REQUIRES_ATTENTION"
            ),
        },

        "governance": {
            "external_actions": (
                policy.get("governance", {})
                .get("external_actions", "UNKNOWN")
            ),
            "ableton_mutation": (
                policy.get("governance", {})
                .get("ableton_mutation", "UNKNOWN")
            ),
            "purchases": (
                policy.get("governance", {})
                .get("purchases", "UNKNOWN")
            ),
            "publishing": (
                policy.get("governance", {})
                .get("publishing", "UNKNOWN")
            ),
            "deletion": (
                policy.get("governance", {})
                .get("deletion", "UNKNOWN")
            ),
            "operator_approval": (
                policy.get("governance", {})
                .get("operator_approval", "UNKNOWN")
            ),
        },

        "self_diagnosis": {
            "overall": health,
            "runtime_truth": runtime_truth,
            "counter_consistency": counter_sync,
            "missing_artifacts": missing,
        },
    }

    return model


def load_jsonl(path: Path):
    if not path.exists():
        return []

    items = []

    try:
        with path.open(
            "r",
            encoding="utf-8-sig"
        ) as handle:

            for line in handle:
                line = line.strip()

                if not line:
                    continue

                try:
                    obj = json.loads(line)

                    if isinstance(obj, dict):
                        items.append(obj)

                except Exception:
                    continue

    except Exception:
        return []

    return items


def persist(model):
    SELF_DIR.mkdir(parents=True, exist_ok=True)

    temp = MODEL.with_suffix(".tmp")

    temp.write_text(
        json.dumps(
            model,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    os.replace(
        temp,
        MODEL
    )

    event = {
        "schema": "aegentix.self-awareness.event.v3",
        "timestamp": now(),
        "health": model["canonical_metrics"]["health"],
        "runtime": model["canonical_metrics"]["runtime"],
        "opportunities": model["canonical_metrics"]["opportunities"],
        "dna": model["canonical_metrics"]["dna"],
        "completed": model["canonical_metrics"]["completed"],
        "failed": model["canonical_metrics"]["failed"],
        "counter_sync": model["canonical_metrics"]["counter_sync"],
    }

    with EVENTS.open(
        "a",
        encoding="utf-8"
    ) as handle:
        handle.write(
            json.dumps(
                event,
                separators=(",", ":")
            ) + "\n"
        )


def main():
    model = build_self_model()
    persist(model)

    metrics = model["canonical_metrics"]

    print("=" * 60)
    print(" AEGENTIX SELF-AWARENESS")
    print("=" * 60)
    print(f"Health            : {metrics['health']}")
    print(f"Runtime           : {metrics['runtime']}")
    print(f"Opportunities     : {metrics['opportunities']}")
    print(f"DNA               : {metrics['dna']}")
    print(f"Completed         : {metrics['completed']}")
    print(f"Failed            : {metrics['failed']}")
    print(f"Counter Sync      : {metrics['counter_sync']}")
    print(
        f"Organism Files    : "
        f"{model['composition']['organism_files']}"
    )
    print(
        f"Processes         : "
        f"{model['runtime']['process_count']}"
    )
    print(
        f"Missing Artifacts : "
        f"{len(model['reconciliation']['missing_artifacts'])}"
    )
    print("-" * 60)
    print(f"SELF_MODEL        : {MODEL}")
    print(f"SELF_EVENTS       : {EVENTS}")
    print("=" * 60)


if __name__ == "__main__":
    main()

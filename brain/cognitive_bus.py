import json
import hashlib
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVENT_DIR = ROOT / "runtime" / "events"
STATE_FILE = ROOT / "runtime" / "state.json"

EVENT_DIR.mkdir(parents=True, exist_ok=True)


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def append_event(event_type, actor, payload):
    files = sorted(EVENT_DIR.glob("*.jsonl"))

    previous_hash = ""

    if files:
        last = files[-1]
        lines = last.read_text(encoding="utf-8").splitlines()
        if lines:
            previous = json.loads(lines[-1])
            previous_hash = previous.get("hash", "")

    event = {
        "timestamp": time.time(),
        "event_type": event_type,
        "actor": actor,
        "payload": payload,
        "previous_hash": previous_hash
    }

    canonical = json.dumps(event, sort_keys=True)
    event["hash"] = sha256(canonical)

    filename = EVENT_DIR / f"{int(time.time() * 1000)}.jsonl"

    with filename.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")

    return event


def load_state():
    if not STATE_FILE.exists():
        return {}

    return json.loads(STATE_FILE.read_text(encoding="utf-8"))


def record_intent(objective):
    return append_event(
        "MISSION_INTENT",
        "JARVIS",
        {"objective": objective}
    )


if __name__ == "__main__":
    import sys

    objective = " ".join(sys.argv[1:]).strip()

    if not objective:
        print("Usage: python cognitive_bus.py <objective>")
        raise SystemExit(1)

    event = record_intent(objective)

    print(json.dumps({
        "accepted": True,
        "event_hash": event["hash"],
        "objective": objective,
        "authority": "AEGENTIX"
    }, indent=2))

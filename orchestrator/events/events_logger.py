"""
EventsLogger — Hermes-native structured event log.

Legacy format
-------------
orchestrator/events/events.log (plain-text, free-form lines) is LEGACY.
It is being migrated to Hermes session transcripts and this JSONL format.

Hermes-native format
--------------------
orchestrator/events/events.jsonl — one JSON object per line. Each event
carries:

    * timestamp   — ISO-8601 UTC
    * source_agent — name of the agent that emitted the event
    * event_type  — e.g. "card.created", "card.moved", "swarm.consensus"
    * payload     — arbitrary dict with event-specific details

Append-only; readers can tail the file or seek to the end for the latest
events. No locking — each write is a single atomic append on POSIX/NTFS.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any

EVENTS_PATH = os.path.join(os.path.dirname(__file__), "events.jsonl")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventsLogger:
    """Append-only structured event logger writing JSONL."""

    def __init__(self, events_path: str = EVENTS_PATH) -> None:
        self._events_path = events_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(events_path), exist_ok=True)

    def log(self, event_dict: dict[str, Any]) -> None:
        """Append *event_dict* as a single JSON line to the events file.

        The dict should contain at least ``source_agent`` and ``event_type``.
        ``timestamp`` is added automatically if missing.
        """
        event = dict(event_dict)
        event.setdefault("timestamp", _now_iso())
        line = json.dumps(event, ensure_ascii=False)
        with open(self._events_path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

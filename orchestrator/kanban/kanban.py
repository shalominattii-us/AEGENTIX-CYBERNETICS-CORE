"""
KanbanBoard — durable work queue for the Hermes orchestration layer.

Replaces legacy orchestrator/workflows/workflow-*.json and the empty
orchestrator/ directories with a column-based card pipeline:

    Inbox → Swarm Consensus → Execution → Verification → Security →
    Observability → Done

Cards carry: id, title, description, column, owner (agent name from the
5-agent swarm or infra agent roles), evidence (path or null), verification
(bool), created_at, moved_at.

Every mutation persists to orchestrator/kanban/state.json via an atomic
write (write-to-tmpfile-then-rename) so concurrent readers never see a
half-written file.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

STATE_PATH = os.path.join(os.path.dirname(__file__), "state.json")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict:
    if not os.path.exists(STATE_PATH):
        return {"columns": {}, "meta": {"version": "1.0-hermes", "swappable_columns": []}}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(state: dict) -> None:
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp, STATE_PATH)


class KanbanBoard:
    """In-memory view of the Kanban board with atomic persistence."""

    def __init__(self, state_path: str = STATE_PATH) -> None:
        self._state_path = state_path
        self._state = _load()
        # Ensure column dicts exist even if state.json was hand-edited
        for col in self._state.get("meta", {}).get("swappable_columns", []):
            self._state.setdefault("columns", {}).setdefault(col, [])

    # -- mutations -----------------------------------------------------------

    def add_card(self, column: str, card_dict: dict[str, Any]) -> str:
        """Add a card to *column*, return its id.

        card_dict may supply any card fields; missing fields get defaults.
        A unique id is always generated here.
        """
        card: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "title": card_dict.get("title", "(untitled)"),
            "description": card_dict.get("description", ""),
            "column": column,
            "owner": card_dict.get("owner", "unassigned"),
            "evidence": card_dict.get("evidence", None),
            "verification": card_dict.get("verification", False),
            "created_at": _now_iso(),
            "moved_at": _now_iso(),
        }
        self._state.setdefault("columns", {}).setdefault(column, [])
        self._state["columns"][column].append(card)
        _save(self._state)
        return card["id"]

    def move_card(self, card_id: str, to_column: str) -> bool:
        """Move *card_id* to *to_column*. Returns True on success."""
        columns = self._state.get("columns", {})
        for src_col, cards in columns.items():
            for card in cards:
                if card["id"] == card_id:
                    card["column"] = to_column
                    card["moved_at"] = _now_iso()
                    columns.setdefault(to_column, [])
                    columns[to_column].append(card)
                    cards.remove(card)
                    _save(self._state)
                    return True
        return False

    # -- reads --------------------------------------------------------------

    def get_cards(self, column: str) -> list[dict[str, Any]]:
        """Return a shallow copy of the cards in *column*."""
        return list(self._state.get("columns", {}).get(column, []))

    def get_all(self) -> dict[str, Any]:
        """Return the full state snapshot (columns + meta)."""
        return {
            "columns": {col: list(cards) for col, cards in self._state.get("columns", {}).items()},
            "meta": dict(self._state.get("meta", {})),
        }

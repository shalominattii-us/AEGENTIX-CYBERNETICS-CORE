import json
import os
import time
from typing import Dict, List, Any, Optional

class StateReplayEngine:
    def __init__(self, log_path: str = "storage/replay_log.jsonl") -> None:
        self.log_path = log_path
        self.node_role: str = "STANDBY"  # Node starts in STANDBY mode
        self.replayed_height: int = 0
        self.last_replayed_root: str = "0x" + "0" * 64

    def log_block(self, block_data: Dict[str, Any]) -> None:
        """Appends a committed block record to the persistent WAL (Write-Ahead Log)."""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(block_data) + "\n")

    def fetch_replay_log(self) -> List[Dict[str, Any]]:
        """Reads all recorded blocks from the local storage log."""
        if not os.path.exists(self.log_path):
            return []
        blocks = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    blocks.append(json.loads(line))
        return blocks

    def replay_from_genesis(self, ledger_engine: Any) -> Dict[str, Any]:
        """
        Reconstructs state from genesis through all sequential block records.
        Verifies that recomputed roots match committed state roots.
        """
        blocks = self.fetch_replay_log()
        replayed_count = 0
        verified_roots = []

        for b in blocks:
            # Re-anchor transaction payload to calculate new state root
            recomputed = ledger_engine.anchor_state_root(b.get("tx_receipt", {}))
            
            # Verify calculated state root against recorded state root
            if b.get("state_root") and recomputed["state_root"] != b.get("state_root"):
                raise ValueError(
                    f"State drift detected at block {b.get('block_height')}! "
                    f"Expected: {b.get('state_root')}, Calculated: {recomputed['state_root']}"
                )
            
            self.replayed_height = recomputed["block_index"]
            self.last_replayed_root = recomputed["state_root"]
            verified_roots.append(self.last_replayed_root)
            replayed_count += 1

        return {
            "status": "STATE_PARITY_VERIFIED",
            "replayed_blocks": replayed_count,
            "final_height": self.replayed_height,
            "state_root": self.last_replayed_root,
        }

    def promote_to_active(self) -> Dict[str, Any]:
        """Promotes node from STANDBY to ACTIVE after state replay validation."""
        self.node_role = "ACTIVE"
        return {
            "node_role": self.node_role,
            "promoted_at": time.time(),
            "active_height": self.replayed_height,
            "state_root": self.last_replayed_root
        }

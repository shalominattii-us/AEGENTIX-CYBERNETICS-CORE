import hashlib
import json
import time
from typing import Dict, Any

class LedgerAnchorWriter:
    def __init__(self) -> None:
        self.block_height = 0
        self.last_state_root = "0x" + "0" * 64

    def anchor_state_root(self, tx_receipt: Dict[str, Any]) -> Dict[str, Any]:
        self.block_height += 1
        serialized = json.dumps(tx_receipt, sort_keys=True)
        merkle_leaf = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        
        hasher = hashlib.sha256()
        hasher.update(self.last_state_root.encode("utf-8"))
        hasher.update(merkle_leaf.encode("utf-8"))
        new_state_root = "0x" + hasher.hexdigest()
        self.last_state_root = new_state_root

        return {
            "block_index": self.block_height,
            "state_root": new_state_root,
            "signature_proof": f"0xsig_stub_{new_state_root[:16]}",
            "timestamp": time.time(),
        }

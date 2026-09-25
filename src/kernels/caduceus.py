import time
import uuid
from typing import Dict, Any

class CaduceusTelemetryModule:
    @staticmethod
    def map_to_fhir_audit_event(tx_receipt: Dict[str, Any]) -> Dict[str, Any]:
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return {
            "resourceType": "AuditEvent",
            "id": str(uuid.uuid4()),
            "recorded": now,
            "outcome": "0",
            "sender": tx_receipt.get("sender_wallet"),
            "receiver": tx_receipt.get("receiver_wallet"),
            "amount": tx_receipt.get("amount"),
        }

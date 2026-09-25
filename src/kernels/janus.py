from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class AccountLinker:
    links: Dict[str, str] = field(default_factory=dict)

    def link_account(self, wallet: str, treasury_account: str) -> None:
        self.links[wallet] = treasury_account

    def resolve(self, wallet: str) -> str:
        return self.links.get(wallet, f"MOCK_ACC_{wallet[:8]}")

class JanusUniversalOrchestrator:
    def __init__(self) -> None:
        self.us_treasury_fed = AccountLinker()

    def process_intent_route(
        self,
        route_key: str,
        sender: str,
        receiver: str,
        amount: float,
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        sender_acc = self.us_treasury_fed.resolve(sender)
        receiver_acc = self.us_treasury_fed.resolve(receiver)

        return {
            "route_key": route_key,
            "sender_wallet": sender,
            "receiver_wallet": receiver,
            "sender_account": sender_acc,
            "receiver_account": receiver_acc,
            "amount": amount,
            "metadata": metadata or {},
            "status": "COMMITTED",
        }

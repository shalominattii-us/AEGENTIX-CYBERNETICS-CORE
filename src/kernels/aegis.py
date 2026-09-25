from typing import Set

class AegisSanctionsEngine:
    def __init__(self) -> None:
        self._sanctioned: Set[str] = set()

    def add_sanctioned(self, wallet: str) -> None:
        self._sanctioned.add(wallet)

    def is_sanctioned(self, wallet: str) -> bool:
        return wallet in self._sanctioned

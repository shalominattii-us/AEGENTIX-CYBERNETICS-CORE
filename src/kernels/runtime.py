import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict

from src.kernels.janus import JanusUniversalOrchestrator
from src.kernels.aegis import AegisSanctionsEngine
from src.kernels.caduceus import CaduceusTelemetryModule
from src.kernels.ledger import LedgerAnchorWriter
from src.kernels.sovereign import SovereignIdentitySubstrate
from src.kernels.replay import StateReplayEngine

@dataclass
class KernelConfig:
    telemetry_workers: int = 22

@dataclass
class KernelRuntime:
    config: KernelConfig = field(default_factory=KernelConfig)
    janus: JanusUniversalOrchestrator = field(default_factory=JanusUniversalOrchestrator)
    aegis: AegisSanctionsEngine = field(default_factory=AegisSanctionsEngine)
    caduceus: CaduceusTelemetryModule = field(default_factory=CaduceusTelemetryModule)
    ledger: LedgerAnchorWriter = field(default_factory=LedgerAnchorWriter)
    sovereign: SovereignIdentitySubstrate = field(default_factory=SovereignIdentitySubstrate)
    replay: StateReplayEngine = field(default_factory=StateReplayEngine)

    def bootstrap(self) -> None:
        self.janus.us_treasury_fed.link_account("0xSovereignOwner", "TREASURY_ACC_992182")
        self.janus.us_treasury_fed.link_account("0xAlliedSettlement", "TREASURY_ACC_104928")

class TelemetrySwarm:
    def __init__(self, runtime: KernelRuntime) -> None:
        self.runtime = runtime
        self.queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._tasks: list[asyncio.Task] = []

    async def start(self) -> None:
        for i in range(self.runtime.config.telemetry_workers):
            self._tasks.append(asyncio.create_task(self._worker(i)))

    async def stop(self) -> None:
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def submit(self, tx_receipt: Dict[str, Any]) -> None:
        await self.queue.put(tx_receipt)

    async def _worker(self, worker_id: int) -> None:
        while True:
            tx = await self.queue.get()
            try:
                bundle = self.runtime.caduceus.map_to_fhir_audit_event(tx)
                _ = bundle
            finally:
                self.queue.task_done()

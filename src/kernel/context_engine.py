from __future__ import annotations
import time
from typing import TYPE_CHECKING
from contracts.context import GlobalContextSnapshot, InferenceContext
from contracts.event import Event, EventType

if TYPE_CHECKING:
    from .scheduler import Scheduler

class ContextEngine:
    def __init__(self, scheduler: Scheduler):
        self.scheduler = scheduler

    async def execute_tick(self):
        # 1. Demande de contexte à tous les composants
        # (via événement CONTEXT_REQUEST broadcast)
        await self.scheduler.event_bus.publish(
            Event(EventType.CONTEXT_REQUEST, source="scheduler", dest="*")
        )
        # 2. Les composants répondent via CONTEXT_REPLY (collectés par le bus)
        # Dans cette version, on simule une collecte directe via les proxies
        components = self.scheduler.registry.all()
        contexts = {}
        for name, proxy in components.items():
            contexts[name] = await proxy.context()
        # 3. Réduction / Snapshot
        snapshot = GlobalContextSnapshot(timestamp=time.time(), components=contexts)
        # 4. Transformation en InferenceContext (simplifié)
        inf_ctx = InferenceContext(
            features={"load": 0.5},
            priorities={name: 0 for name in contexts}
        )
        # 5. Application des décisions (exemple : ajustement des priorités)
        for name in contexts:
            # On pourrait modifier les priorités dans la queue
            pass

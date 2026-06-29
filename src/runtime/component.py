# runtime/component.py

from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING, Any
from contracts.component import Component
from contracts.event import Event, EventType

if TYPE_CHECKING:
    from kernel.scheduler import Scheduler

class ComponentProxy:
    """Encapsule un composant réel, intercepte les accès et notifie le Scheduler."""
    def __init__(self, real: Component, scheduler: Scheduler):
        self._real = real
        self.name = real.__class__.__name__
        self.scheduler = scheduler
        self._tick_task = None
        self._context_cache = {}

    async def start(self):
        # Émet LOAD puis lance la boucle tick
        await self.scheduler.emit(Event(EventType.LOAD, source=self.name))
        self._tick_task = asyncio.create_task(self._tick_loop())
        await self.scheduler.emit(Event(EventType.START, source=self.name))

    async def _tick_loop(self):
        """Boucle principale : exécute le générateur tick() du composant réel."""
        gen = self._real.tick()
        try:
            event = await gen.__anext__()
            while True:
                # Envoie l'événement au Scheduler et récupère le résultat
                result = await self._dispatch_event(event)
                event = await gen.asend(result)
        except StopAsyncIteration:
            await self.scheduler.emit(Event(EventType.STOP, source=self.name))

    async def _dispatch_event(self, event: Event) -> Any:
        """Attache un Future à l'événement et attend la réponse du Scheduler."""
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        event = Event(
            type=event.type,
            source=event.source,
            dest=event.dest,
            payload=(event.payload, future)  # astuce pour passer le future
        )
        await self.scheduler.emit(event)
        return await future

    async def context(self) -> dict:
        """Retourne l'état du composant (pour le Context Engine)."""
        # On pourrait appeler self._real.context() directement
        return await self._real.context()

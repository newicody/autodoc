# kernel/scheduler.py
import asyncio
import time
from .queue import PriorityQueue
from .dispatcher import Dispatcher
from .event_bus import EventBus
from contracts.event import Event, EventType
from contracts.scheduler import SchedulerContract
from .context_engine import ContextEngine

class Scheduler(SchedulerContract):
    def __init__(self, queue: PriorityQueue, dispatcher: Dispatcher, event_bus: EventBus):
        self.queue = queue
        self.dispatcher = dispatcher
        self.event_bus = event_bus
        self._running = False
        self._context_engine = ContextEngine(self)

    async def emit(self, event: Event) -> None:
        await self.queue.put(event.priority, event)

    async def run(self):
        self._running = True
        # Tâche de fond pour le tick d’horloge (toutes les N secondes)
        async def clock():
            while self._running:
                await asyncio.sleep(1)  # période de tick
                await self._context_engine.execute_tick()

        asyncio.create_task(clock())

        while self._running:
            _, event = await self.queue.get()
            if event.type == EventType.SHUTDOWN:
                self._running = False
                break
            # Politique : ici toujours autorisé (à raffiner)
            await self.dispatcher.dispatch(event)
        await self._finalize()

    async def shutdown(self):
        await self.emit(Event(EventType.SHUTDOWN, source="kernel", dest="scheduler"))

    async def _finalize(self):
        # Propage l’arrêt aux composants
        pass

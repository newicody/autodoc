from __future__ import annotations

import asyncio
from contextlib import suppress

from contracts.event import Event, EventType
from contracts.scheduler import SchedulerContract
from .context_engine import ContextEngine
from .dispatcher import Dispatcher
from .event_bus import EventBus
from .queue import PriorityQueue
from .registry import Registry


class Scheduler(SchedulerContract):
    """Interpréteur central du micro-kernel coopératif."""

    def __init__(
        self,
        queue: PriorityQueue,
        dispatcher: Dispatcher,
        event_bus: EventBus,
        registry: Registry,
        context_interval: float = 1.0,
    ) -> None:
        self.queue = queue
        self.dispatcher = dispatcher
        self.event_bus = event_bus
        self.registry = registry
        self.context_interval = context_interval
        self.context_engine = ContextEngine(registry, event_bus)
        self._running = False
        self._clock_task: asyncio.Task[None] | None = None

    async def emit(self, event: Event) -> None:
        await self.queue.put(event.priority, event)

    async def run(self) -> None:
        self._running = True
        self._clock_task = asyncio.create_task(self._clock(), name="missipy-context-clock")

        try:
            while self._running:
                _, event = await self.queue.get()
                try:
                    if event.type == EventType.SHUTDOWN:
                        self._running = False
                        await self.event_bus.publish(event)
                        self._resolve_request(event, {"ok": True, "shutdown": True})
                        break

                    await self.dispatcher.dispatch(event)
                finally:
                    self.queue.task_done()
        finally:
            await self._finalize()

    async def shutdown(self) -> None:
        await self.emit(Event(EventType.SHUTDOWN, source="kernel", dest="scheduler", priority=999))

    async def _clock(self) -> None:
        while self._running:
            await asyncio.sleep(self.context_interval)
            if self.registry.all():
                await self.context_engine.execute_tick()

    async def _finalize(self) -> None:
        self._running = False
        if self._clock_task is not None:
            self._clock_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._clock_task

    @staticmethod
    def _resolve_request(event: Event, result: object) -> None:
        if event.request and event.request.reply and not event.request.reply.done():
            event.request.reply.set_result(result)

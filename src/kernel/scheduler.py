from __future__ import annotations

import asyncio
from contextlib import suppress

from context.engine import ContextEngine
from contracts.event import Event, EventType
from contracts.policy import Decision
from contracts.scheduler import SchedulerContract
from policy.engine import PolicyEngine

from .dispatcher import Dispatcher
from .event_bus import EventBus
from .queue import PriorityQueue
from .registry import Registry


class Scheduler(SchedulerContract):
    """Interpréteur central du micro-kernel coopératif.

    Le Scheduler ne contient aucune logique métier. Il orchestre la queue,
    délègue les décisions d'autorisation au PolicyEngine, déclenche le contexte
    global, délègue au Dispatcher et arrête proprement les tâches internes.
    """

    SHUTDOWN_PRIORITY = 1_000_000

    def __init__(
        self,
        queue: PriorityQueue,
        dispatcher: Dispatcher,
        event_bus: EventBus,
        registry: Registry,
        context_interval: float = 1.0,
        policy_engine: PolicyEngine | None = None,
    ) -> None:
        self.queue = queue
        self.dispatcher = dispatcher
        self.event_bus = event_bus
        self.registry = registry
        self.context_interval = context_interval
        self.policy_engine = policy_engine or PolicyEngine()
        self.context_engine = ContextEngine(registry, self, event_bus)
        self._running = False
        self._clock_task: asyncio.Task[None] | None = None

    @property
    def running(self) -> bool:
        return self._running

    async def emit(self, event: Event) -> None:
        decision = self.policy_engine.decide(event, self.registry.all().keys())
        if decision.allowed:
            await self.queue.put(event.priority, event)
            return

        await self._deny_event(event, decision)

    async def run(self) -> None:
        self._running = True
        self._clock_task = asyncio.create_task(
            self._clock(),
            name="missipy-context-clock",
        )
        try:
            while self._running:
                _priority, event = await self.queue.get()
                try:
                    if event.type is EventType.SHUTDOWN:
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
        await self.emit(
            Event(
                EventType.SHUTDOWN,
                source="kernel",
                dest="scheduler",
                priority=self.SHUTDOWN_PRIORITY,
            )
        )

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

    async def _deny_event(self, event: Event, decision: Decision) -> None:
        await self.event_bus.publish(
            Event(
                EventType.POLICY_DENIED,
                source="policy.engine",
                dest=event.source,
                payload=decision,
                priority=event.priority,
                correlation_id=event.id,
            )
        )
        self._resolve_request(event, decision)

    @staticmethod
    def _resolve_request(event: Event, result: object) -> None:
        if event.request and event.request.reply and not event.request.reply.done():
            event.request.reply.set_result(result)

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol

from contracts.event import Event, EventType, Request
from kernel.event_bus import EventBus
from kernel.registry import Registry


class EventEmitter(Protocol):
    """Surface minimale attendue par le collector.

    Le collector ne connaît pas le Scheduler concret : il connaît seulement un
    objet capable d'injecter un Event dans la file d'exécution.
    """

    async def emit(self, event: Event) -> None: ...


@dataclass(slots=True)
class ContextCollector:
    """Collecte le contexte via le chemin événementiel du kernel."""

    registry: Registry
    emitter: EventEmitter
    event_bus: EventBus
    timeout: float = 5.0

    async def collect(self) -> dict[str, dict[str, object]]:
        contexts: dict[str, dict[str, object]] = {}

        for component_name in self.registry.all():
            context = await self._collect_component(component_name)
            contexts[component_name] = context

        return contexts

    async def _collect_component(self, component_name: str) -> dict[str, object]:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[object] = loop.create_future()

        await self.emitter.emit(
            Event(
                EventType.CONTEXT_REQUEST,
                source="context.collector",
                dest=component_name,
                request=Request(reply=future, timeout=self.timeout),
            )
        )

        result = await asyncio.wait_for(future, timeout=self.timeout)
        context = self._extract_context(component_name, result)

        await self.event_bus.publish(
            Event(
                EventType.CONTEXT_REPLY,
                source=component_name,
                dest="context.collector",
                payload=context,
            )
        )

        return context

    @staticmethod
    def _extract_context(component_name: str, result: object) -> dict[str, object]:
        if not isinstance(result, dict):
            return {"error": "invalid_context_result", "component": component_name}

        if result.get("ok") is not True:
            return {"error": "context_request_failed", "component": component_name, "result": result}

        context = result.get("context")
        if not isinstance(context, dict):
            return {"error": "missing_context", "component": component_name, "result": result}

        return context

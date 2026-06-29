from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

from contracts.context import GlobalContextSnapshot, InferenceContext, freeze_mapping
from contracts.event import Event, EventType, Request

from .dispatcher import Dispatcher
from .event_bus import EventBus
from .registry import Registry

Emit = Callable[[Event], Awaitable[None]]


class ContextRequestHandler:
    """Handler interne de collecte contextuelle par événement."""

    def __init__(self, registry: Registry) -> None:
        self.registry = registry

    async def handle(self, event: Event) -> dict[str, Any]:
        if event.dest == "*":
            return {
                name: await proxy.context()
                for name, proxy in self.registry.all().items()
            }

        proxy = self.registry.get(event.dest)
        return {event.dest: await proxy.context()}


class ContextCollector:
    """Collecte les réponses contextuelles sans appeler les composants directs."""

    def __init__(self, registry: Registry, emit: Emit, event_bus: EventBus) -> None:
        self.registry = registry
        self.emit = emit
        self.event_bus = event_bus

    async def collect(self, timeout: float = 5.0) -> dict[str, dict[str, Any]]:
        contexts: dict[str, dict[str, Any]] = {}

        for name in self.registry.all():
            loop = asyncio.get_running_loop()
            future: asyncio.Future[Any] = loop.create_future()
            request = Request(reply=future, timeout=timeout)
            event = Event(
                EventType.CONTEXT_REQUEST,
                source="context_engine",
                dest=name,
                request=request,
            )

            await self.emit(event)
            reply = await asyncio.wait_for(future, timeout=timeout)
            if not isinstance(reply, Mapping):
                raise TypeError(f"Invalid context reply from {name}: {reply!r}")

            raw_context = reply.get(name, reply)
            if not isinstance(raw_context, Mapping):
                raise TypeError(f"Invalid context payload from {name}: {raw_context!r}")

            context_dict = dict(raw_context)
            contexts[name] = context_dict

            await self.event_bus.publish(
                Event(
                    EventType.CONTEXT_REPLY,
                    source=name,
                    dest="context_engine",
                    payload=context_dict,
                    correlation_id=event.id,
                )
            )

        return contexts


class ContextReducer:
    """Transforme les contextes collectés en snapshots immuables."""

    def reduce(self, contexts: Mapping[str, Mapping[str, Any]]) -> GlobalContextSnapshot:
        frozen_components = {
            name: freeze_mapping(dict(context))
            for name, context in contexts.items()
        }
        return GlobalContextSnapshot(
            timestamp=time.time(),
            components=freeze_mapping(frozen_components),
        )

    def to_inference_context(
        self,
        snapshot: GlobalContextSnapshot,
    ) -> InferenceContext:
        return InferenceContext(
            features=freeze_mapping({"component_count": len(snapshot.components)}),
            priorities=freeze_mapping(
                {name: 0 for name in snapshot.components}
            ),
        )


class ContextEngine:
    """Construit périodiquement la vision globale du micro-kernel.

    Phase 1.2bis : la collecte passe par CONTEXT_REQUEST / Request.reply. Le
    ComponentProxy reste la seule surface touchant directement le composant réel.
    """

    def __init__(self, registry: Registry, emit: Emit, event_bus: EventBus) -> None:
        self.registry = registry
        self.event_bus = event_bus
        self.collector = ContextCollector(registry, emit, event_bus)
        self.reducer = ContextReducer()
        self.last_snapshot: GlobalContextSnapshot | None = None
        self.last_inference_context: InferenceContext | None = None

    def register_handlers(self, dispatcher: Dispatcher) -> None:
        dispatcher.register(EventType.CONTEXT_REQUEST, ContextRequestHandler(self.registry))

    async def execute_tick(self) -> GlobalContextSnapshot:
        contexts = await self.collector.collect()
        snapshot = self.reducer.reduce(contexts)
        inference_context = self.reducer.to_inference_context(snapshot)
        self.last_snapshot = snapshot
        self.last_inference_context = inference_context
        return snapshot

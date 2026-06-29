from __future__ import annotations

import time
from typing import Any

from contracts.context import GlobalContextSnapshot, InferenceContext, freeze_mapping
from contracts.event import Event, EventType
from .event_bus import EventBus
from .registry import Registry


class ContextEngine:
    """Collecte Phase 1 du contexte global.

    Mode actuel : collecte directe via Registry -> ComponentProxy.context().
    Mode cible : CONTEXT_REQUEST -> CONTEXT_REPLY -> Collector -> Reducer.
    """

    def __init__(self, registry: Registry, event_bus: EventBus) -> None:
        self.registry = registry
        self.event_bus = event_bus
        self.last_snapshot: GlobalContextSnapshot | None = None
        self.last_inference_context: InferenceContext | None = None

    async def execute_tick(self) -> GlobalContextSnapshot:
        await self.event_bus.publish(Event(EventType.CONTEXT_REQUEST, source="scheduler", dest="*"))

        contexts: dict[str, dict[str, Any]] = {}
        for name, proxy in self.registry.all().items():
            contexts[name] = await proxy.context()

        frozen_components = {name: freeze_mapping(ctx) for name, ctx in contexts.items()}
        snapshot = GlobalContextSnapshot(timestamp=time.time(), components=freeze_mapping(frozen_components))
        inference_context = InferenceContext(
            features=freeze_mapping({"component_count": len(contexts)}),
            priorities=freeze_mapping({name: 0 for name in contexts}),
        )

        self.last_snapshot = snapshot
        self.last_inference_context = inference_context
        return snapshot

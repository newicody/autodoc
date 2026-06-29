from __future__ import annotations

from dataclasses import dataclass, field

from contracts.context import GlobalContextSnapshot, InferenceContext
from kernel.event_bus import EventBus
from kernel.registry import Registry

from .builder import InferenceContextBuilder
from .collector import ContextCollector, EventEmitter
from .reducer import ContextReducer


@dataclass(slots=True)
class ContextEngine:
    """Pipeline contexte Phase 1.3.

    Le moteur ne collecte plus directement via ``proxy.context()``. Il délègue
    au ``ContextCollector``, qui injecte des ``CONTEXT_REQUEST`` dans la file du
    Scheduler. Le seul accès au proxy est contenu dans ``ContextRequestHandler``.
    """

    registry: Registry
    emitter: EventEmitter
    event_bus: EventBus
    timeout: float = 5.0
    collector: ContextCollector = field(init=False)
    reducer: ContextReducer = field(init=False)
    builder: InferenceContextBuilder = field(init=False)
    last_snapshot: GlobalContextSnapshot | None = field(default=None, init=False)
    last_inference_context: InferenceContext | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.collector = ContextCollector(self.registry, self.emitter, self.event_bus, self.timeout)
        self.reducer = ContextReducer()
        self.builder = InferenceContextBuilder()

    async def execute_tick(self) -> GlobalContextSnapshot:
        contexts = await self.collector.collect()
        snapshot = self.reducer.reduce(contexts)
        inference_context = self.builder.build(snapshot)

        self.last_snapshot = snapshot
        self.last_inference_context = inference_context
        return snapshot

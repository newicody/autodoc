from __future__ import annotations

from typing import Any, AsyncGenerator

import pytest

from contracts.component import Component
from contracts.event import Event, EventType
from kernel.context_engine import ContextEngine
from kernel.event_bus import EventBus
from kernel.registry import Registry
from runtime.component import ComponentProxy
from kernel.dispatcher import Dispatcher
from kernel.queue import PriorityQueue
from kernel.scheduler import Scheduler


class ContextComponent(Component):
    name = "Ctx"

    async def tick(self) -> AsyncGenerator[Event, Any]:
        yield Event(EventType.TICK, source=self.name)

    async def context(self) -> dict[str, Any]:
        return {"status": "ok", "load": 1}


@pytest.mark.asyncio
async def test_context_engine_collects_proxy_context_snapshot() -> None:
    registry = Registry()
    bus = EventBus()
    scheduler = Scheduler(PriorityQueue(), Dispatcher(bus), bus, registry, context_interval=60.0)
    proxy = ComponentProxy(ContextComponent(), scheduler)
    registry.register(proxy.name, proxy)
    engine = ContextEngine(registry, bus)

    snapshot = await engine.execute_tick()

    assert "Ctx" in snapshot.components
    assert snapshot.components["Ctx"]["proxy_state"] == "CREATED"
    assert snapshot.components["Ctx"]["component"]["status"] == "ok"
    assert engine.last_inference_context is not None
    assert engine.last_inference_context.features["component_count"] == 1

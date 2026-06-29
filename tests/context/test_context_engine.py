from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator

import pytest

from context.engine import ContextEngine
from context.handlers import ContextRequestHandler
from contracts.component import Component
from contracts.event import Event, EventType
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler
from runtime.component import ComponentProxy


class ContextComponent(Component):
    name = "Ctx"

    async def tick(self) -> AsyncGenerator[Event, Any]:
        yield Event(EventType.TICK, source=self.name)

    async def context(self) -> dict[str, Any]:
        return {"status": "ok", "load": 1}


@pytest.mark.asyncio
async def test_context_engine_uses_event_path_for_snapshot() -> None:
    registry = Registry()
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, registry, context_interval=60.0)
    dispatcher.register(EventType.CONTEXT_REQUEST, ContextRequestHandler(registry))

    proxy = ComponentProxy(ContextComponent(), scheduler)
    registry.register(proxy.name, proxy)
    replies = bus.subscribe(EventType.CONTEXT_REPLY)

    scheduler_task = asyncio.create_task(scheduler.run())
    try:
        engine = ContextEngine(registry, scheduler, bus)
        snapshot = await engine.execute_tick()
        reply_event = await asyncio.wait_for(replies.get(), timeout=1.0)

        assert "Ctx" in snapshot.components
        assert snapshot.components["Ctx"]["proxy_state"] == "CREATED"
        assert snapshot.components["Ctx"]["component"]["status"] == "ok"
        assert reply_event.type == EventType.CONTEXT_REPLY
        assert reply_event.source == "Ctx"
        assert engine.last_inference_context is not None
        assert engine.last_inference_context.features["component_count"] == 1
    finally:
        await scheduler.shutdown()
        await scheduler_task

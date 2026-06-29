from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator

import pytest

from contracts.component import Component
from contracts.event import Event, EventType
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.lifecycle import LifecycleManager
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
async def test_context_engine_collects_context_via_events() -> None:
    registry = Registry()
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    LifecycleManager().register_handlers(dispatcher)
    scheduler = Scheduler(
        PriorityQueue(),
        dispatcher,
        bus,
        registry,
        context_interval=60.0,
    )
    proxy = ComponentProxy(ContextComponent(), scheduler)
    registry.register(proxy.name, proxy)
    observed_replies = bus.subscribe(EventType.CONTEXT_REPLY)
    scheduler_task = asyncio.create_task(scheduler.run())

    snapshot = await scheduler.context_engine.execute_tick()
    reply_event = await observed_replies.get()
    await scheduler.shutdown()
    await scheduler_task

    assert "Ctx" in snapshot.components
    assert snapshot.components["Ctx"]["proxy_state"] == "CREATED"
    assert snapshot.components["Ctx"]["component"]["status"] == "ok"
    assert reply_event.source == "Ctx"
    assert scheduler.context_engine.last_inference_context is not None
    assert scheduler.context_engine.last_inference_context.features["component_count"] == 1

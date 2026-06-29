from __future__ import annotations

from typing import Any, AsyncGenerator

import asyncio
import pytest

from contracts.component import Component
from contracts.event import Event, EventType
from contracts.lifecycle import ComponentState
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.lifecycle import LifecycleManager
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler
from runtime.component import ComponentProxy


class OneShotComponent(Component):
    name = "OneShot"

    def __init__(self) -> None:
        self.result: Any = None

    async def tick(self) -> AsyncGenerator[Event, Any]:
        self.result = yield Event(EventType.TICK, source=self.name, payload="ping")

    async def context(self) -> dict[str, Any]:
        return {"result": self.result}


class UnknownEventComponent(Component):
    name = "UnknownEvent"

    def __init__(self) -> None:
        self.result: Any = None

    async def tick(self) -> AsyncGenerator[Event, Any]:
        self.result = yield Event(EventType.INFERENCE_REQUEST, source=self.name, payload="future")

    async def context(self) -> dict[str, Any]:
        return {"result": self.result}


class FailingComponent(Component):
    name = "Failing"

    async def tick(self) -> AsyncGenerator[Event, Any]:
        raise RuntimeError("boom")
        yield Event(EventType.TICK, source=self.name)  # pragma: no cover

    async def context(self) -> dict[str, Any]:
        return {"status": "broken"}


async def build_kernel() -> tuple[Scheduler, Registry, LifecycleManager, EventBus]:
    registry = Registry()
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    lifecycle = LifecycleManager()
    lifecycle.register_handlers(dispatcher)
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, registry, context_interval=60.0)
    return scheduler, registry, lifecycle, bus


@pytest.mark.asyncio
async def test_component_proxy_tick_roundtrip() -> None:
    scheduler, registry, lifecycle, _ = await build_kernel()
    component = OneShotComponent()
    proxy = ComponentProxy(component, scheduler)
    registry.register(proxy.name, proxy)

    scheduler_task = asyncio.create_task(scheduler.run())
    await proxy.start()
    await proxy.wait()
    await scheduler.shutdown()
    await scheduler_task

    assert component.result["ok"] is True
    assert component.result["handled"] == "TICK"
    assert proxy.state is ComponentState.STOPPED
    assert lifecycle.state_of("OneShot") is ComponentState.STOPPED


@pytest.mark.asyncio
async def test_unknown_event_returns_explicit_unhandled_result() -> None:
    scheduler, registry, _, _ = await build_kernel()
    component = UnknownEventComponent()
    proxy = ComponentProxy(component, scheduler)
    registry.register(proxy.name, proxy)

    scheduler_task = asyncio.create_task(scheduler.run())
    await proxy.start()
    await proxy.wait()
    await scheduler.shutdown()
    await scheduler_task

    assert component.result["ok"] is True
    assert component.result["handled"] is False
    assert component.result["event"] == "INFERENCE_REQUEST"
    assert proxy.state is ComponentState.STOPPED


@pytest.mark.asyncio
async def test_failing_component_emits_error_and_does_not_block_kernel() -> None:
    scheduler, registry, lifecycle, bus = await build_kernel()
    observed_errors = bus.subscribe(EventType.ERROR)
    component = FailingComponent()
    proxy = ComponentProxy(component, scheduler)
    registry.register(proxy.name, proxy)

    scheduler_task = asyncio.create_task(scheduler.run())
    await proxy.start()
    await proxy.wait()
    error_event = await observed_errors.get()
    await scheduler.shutdown()
    await scheduler_task

    assert error_event.source == "Failing"
    assert "boom" in error_event.payload["error"]
    assert proxy.state is ComponentState.ERROR
    assert lifecycle.errors["Failing"]["class"] == "RuntimeError"

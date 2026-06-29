from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator

import pytest

from contracts.component import Component
from contracts.event import Event, EventType, Request
from contracts.inference import InferenceRequest
from contracts.policy import Decision
from inference.adapter import InferenceAdapter
from inference.backend import DummyInferenceBackend
from inference.handlers import InferenceRequestHandler
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.lifecycle import LifecycleManager
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler
from runtime.component import ComponentProxy


class DeniedInferenceComponent(Component):
    name = "DeniedInference"

    def __init__(self) -> None:
        self.result: Decision | None = None

    async def tick(self) -> AsyncGenerator[Event, Any]:
        self.result = yield Event(
            EventType.INFERENCE_REQUEST,
            source=self.name,
            dest="inference",
            payload=InferenceRequest(prompt="ping", model="forbidden"),
        )

    async def context(self) -> dict[str, Any]:
        return {"has_result": self.result is not None}


@pytest.mark.asyncio
async def test_scheduler_policy_denial_resolves_request_without_queueing() -> None:
    registry = Registry()
    bus = EventBus()
    denied = bus.subscribe(EventType.POLICY_DENIED)
    scheduler = Scheduler(PriorityQueue(), Dispatcher(bus), bus, registry, context_interval=60.0)
    loop = asyncio.get_running_loop()
    future: asyncio.Future[object] = loop.create_future()
    event = Event(
        EventType.INFERENCE_REQUEST,
        source="component",
        dest="inference",
        payload=InferenceRequest(prompt="hello", model="missing"),
        request=Request(reply=future),
    )

    await scheduler.emit(event)
    denial_event = await asyncio.wait_for(denied.get(), timeout=1.0)
    decision = future.result()

    assert isinstance(decision, Decision)
    assert decision.allowed is False
    assert decision.rule == "inference.model.denied"
    assert denial_event.type is EventType.POLICY_DENIED
    assert denial_event.dest == "component"
    assert denial_event.correlation_id == event.id


@pytest.mark.asyncio
async def test_component_receives_policy_denial_as_explicit_decision() -> None:
    registry = Registry()
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    lifecycle = LifecycleManager()
    lifecycle.register_handlers(dispatcher)
    adapter = InferenceAdapter(DummyInferenceBackend())
    dispatcher.register(EventType.INFERENCE_REQUEST, InferenceRequestHandler(adapter, bus))
    denied = bus.subscribe(EventType.POLICY_DENIED)
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, registry, context_interval=60.0)
    component = DeniedInferenceComponent()
    proxy = ComponentProxy(component, scheduler)
    registry.register(proxy.name, proxy)
    scheduler_task = asyncio.create_task(scheduler.run())

    await proxy.start()
    await proxy.wait()
    denial_event = await denied.get()
    await scheduler.shutdown()
    await scheduler_task

    assert isinstance(component.result, Decision)
    assert component.result.allowed is False
    assert component.result.rule == "inference.model.denied"
    assert denial_event.dest == component.name
    assert proxy.state.name == "STOPPED"

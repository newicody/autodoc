from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator

import pytest

from contracts.component import Component
from contracts.event import Event, EventType, Request
from contracts.inference import InferenceRequest
from contracts.policy import Decision
from contracts.telemetry import TelemetrySnapshot
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.lifecycle import LifecycleManager
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler
from observability.telemetry import KernelTelemetry
from runtime.component import ComponentProxy


class TelemetryProbe(Component):
    name = "TelemetryProbe"

    def __init__(self) -> None:
        self.result: Any = None

    async def tick(self) -> AsyncGenerator[Event, Any]:
        self.result = yield Event(EventType.TICK, source=self.name, payload="ping")

    async def context(self) -> dict[str, Any]:
        return {"has_result": self.result is not None}


@pytest.mark.asyncio
async def test_kernel_telemetry_records_component_roundtrip() -> None:
    registry = Registry()
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    lifecycle = LifecycleManager()
    lifecycle.register_handlers(dispatcher)
    telemetry = KernelTelemetry()
    scheduler = Scheduler(
        PriorityQueue(),
        dispatcher,
        bus,
        registry,
        context_interval=60.0,
        telemetry=telemetry,
    )
    component = TelemetryProbe()
    proxy = ComponentProxy(component, scheduler)
    registry.register(proxy.name, proxy)
    scheduler_task = asyncio.create_task(scheduler.run())

    await proxy.start()
    await proxy.wait()
    await scheduler.shutdown()
    await scheduler_task

    snapshot = telemetry.snapshot(scheduler.queue.qsize())

    assert isinstance(snapshot, TelemetrySnapshot)
    assert snapshot.events_enqueued >= 4
    assert snapshot.events_dequeued >= 4
    assert snapshot.events_dispatched >= 4
    assert snapshot.events_failed == 0
    assert snapshot.max_queue_size >= 1
    assert snapshot.current_queue_size == 0
    assert snapshot.average_queue_latency_ns >= 0
    assert snapshot.average_dispatch_latency_ns >= 0


@pytest.mark.asyncio
async def test_scheduler_telemetry_records_policy_denial_without_queueing() -> None:
    registry = Registry()
    bus = EventBus()
    telemetry = KernelTelemetry()
    scheduler = Scheduler(
        PriorityQueue(),
        Dispatcher(bus),
        bus,
        registry,
        context_interval=60.0,
        telemetry=telemetry,
    )
    loop = asyncio.get_running_loop()
    future: asyncio.Future[object] = loop.create_future()
    event = Event(
        EventType.INFERENCE_REQUEST,
        source="probe",
        dest="inference",
        payload=InferenceRequest(prompt="hello", model="forbidden"),
        request=Request(reply=future),
    )

    await scheduler.emit(event)

    decision = future.result()
    snapshot = telemetry.snapshot(scheduler.queue.qsize())

    assert isinstance(decision, Decision)
    assert decision.allowed is False
    assert snapshot.events_denied == 1
    assert snapshot.events_enqueued == 0
    assert snapshot.last_denial_rule == "inference.model.denied"
    assert snapshot.last_event_type == "INFERENCE_REQUEST"

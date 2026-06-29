from __future__ import annotations

import asyncio
from typing import Any, AsyncGenerator

import pytest

from contracts.component import Component
from contracts.event import Event, EventType
from contracts.replay import EventLogSnapshot, EventRecord
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.lifecycle import LifecycleManager
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler
from observability.recorder import EventRecorder
from runtime.component import ComponentProxy


@pytest.mark.asyncio
async def test_event_recorder_captures_event_bus_without_request_channel() -> None:
    bus = EventBus()
    recorder = EventRecorder(bus)
    await recorder.start()

    event = Event(EventType.TICK, source="probe", payload={"value": 1})
    await bus.publish(event)
    await recorder.wait_for_count(1)
    await recorder.stop()

    snapshot = recorder.snapshot()

    assert isinstance(snapshot, EventLogSnapshot)
    assert snapshot.count == 1
    assert snapshot.last_event_type == "TICK"
    assert isinstance(snapshot.records[0], EventRecord)
    assert snapshot.records[0].id == event.id
    assert snapshot.records[0].type == "TICK"
    assert snapshot.records[0].source == "probe"
    assert snapshot.records[0].payload_repr == "{'value': 1}"


@pytest.mark.asyncio
async def test_event_recorder_caps_records() -> None:
    bus = EventBus()
    recorder = EventRecorder(bus, max_records=2)
    await recorder.start()

    await bus.publish(Event(EventType.LOAD, source="a"))
    await bus.publish(Event(EventType.START, source="b"))
    await bus.publish(Event(EventType.STOP, source="c"))
    await recorder.wait_for_count(2)
    await asyncio.sleep(0)
    await recorder.stop()

    records = recorder.snapshot().records

    assert len(records) == 2
    assert [record.source for record in records] == ["b", "c"]


class RecorderProbe(Component):
    name = "RecorderProbe"

    async def tick(self) -> AsyncGenerator[Event, Any]:
        yield Event(EventType.TICK, source=self.name, payload="record me")

    async def context(self) -> dict[str, Any]:
        return {"name": self.name}


@pytest.mark.asyncio
async def test_event_recorder_observes_scheduler_roundtrip() -> None:
    registry = Registry()
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    lifecycle = LifecycleManager()
    lifecycle.register_handlers(dispatcher)
    recorder = EventRecorder(bus)
    scheduler = Scheduler(
        PriorityQueue(),
        dispatcher,
        bus,
        registry,
        context_interval=60.0,
    )
    component = RecorderProbe()
    proxy = ComponentProxy(component, scheduler)
    registry.register(proxy.name, proxy)

    await recorder.start()
    scheduler_task = asyncio.create_task(scheduler.run())
    await proxy.start()
    await proxy.wait()
    await scheduler.shutdown()
    await scheduler_task
    await recorder.wait_for_count(4)
    await recorder.stop()

    event_types = [record.type for record in recorder.snapshot().records]

    assert "LOAD" in event_types
    assert "START" in event_types
    assert "TICK" in event_types
    assert "STOP" in event_types

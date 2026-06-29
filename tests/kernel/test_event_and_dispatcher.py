from __future__ import annotations

import asyncio

import pytest

from contracts.event import Event, EventType, Request
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue


@pytest.mark.asyncio
async def test_event_ids_are_unique() -> None:
    ids = {Event(EventType.TICK, source="test").id for _ in range(1000)}
    assert len(ids) == 1000


@pytest.mark.asyncio
async def test_dispatcher_resolves_unhandled_event_without_blocking() -> None:
    bus = EventBus()
    observed = bus.subscribe(None)
    dispatcher = Dispatcher(bus)

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    event = Event(EventType.INFERENCE_REQUEST, source="test", request=Request(reply=future))

    result = await dispatcher.dispatch(event)

    assert result["ok"] is True
    assert result["handled"] is False
    assert result["event"] == "INFERENCE_REQUEST"
    assert future.result() == result
    assert (await observed.get()).id == event.id


@pytest.mark.asyncio
async def test_priority_queue_is_fifo_for_same_priority() -> None:
    queue = PriorityQueue()
    first = Event(EventType.TICK, source="first", priority=0)
    second = Event(EventType.TICK, source="second", priority=0)

    await queue.put(first.priority, first)
    await queue.put(second.priority, second)

    _, got_first = await queue.get()
    queue.task_done()
    _, got_second = await queue.get()
    queue.task_done()

    assert got_first is first
    assert got_second is second

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

import pytest

from contracts.context import GlobalContextSnapshot
from contracts.event import Event, EventType
from kernel.event_bus import EventBus
from runtime.bus_visualization_adapter import (
    BUS_VISUALIZATION_SCHEMA,
    BUS_VISUALIZATION_SOURCE,
    attach_existing_bus_visualization_tap,
    build_existing_bus_visualization_snapshot,
    drain_existing_event_bus_reader,
    read_existing_bus_visualization_snapshot,
)


@dataclass(slots=True)
class ExistingContextSource:
    last_snapshot: GlobalContextSnapshot | None


def _event(event_type: EventType, source: str, *, payload: object | None = None) -> Event:
    return Event(
        event_type,
        source=source,
        dest="vis.observer",
        payload=payload,
        priority=7,
        correlation_id="corr-1",
        metadata=MappingProxyType({"lane": "event.bus", "nested": {"value": 1}}),
        timestamp_ns=123,
        id=f"event-{source}",
    )


@pytest.mark.asyncio
async def test_adapter_reads_existing_event_bus_and_existing_context_source() -> None:
    event_bus = EventBus()
    context_source = ExistingContextSource(
        last_snapshot=GlobalContextSnapshot(
            timestamp=1.0,
            components={
                "worker.b": {"ready": False},
                "worker.a": {"ready": True, "depth": 2},
            },
        )
    )
    tap = attach_existing_bus_visualization_tap(
        event_bus,
        context_source=context_source,
    )

    await event_bus.publish(_event(EventType.CONTEXT_REQUEST, "scheduler"))
    await event_bus.publish(_event(EventType.POLICY_DENIED, "policy"))

    snapshot = read_existing_bus_visualization_snapshot(tap, max_events=8)

    assert snapshot.schema == BUS_VISUALIZATION_SCHEMA
    assert snapshot.source == BUS_VISUALIZATION_SOURCE
    assert snapshot.event_count == 2
    assert snapshot.component_count == 2
    assert [component.name for component in snapshot.components] == ["worker.a", "worker.b"]

    mapping = snapshot.to_mapping()
    assert mapping["events"][0]["event_type"] == "CONTEXT_REQUEST"
    assert mapping["events"][0]["has_payload"] is False
    assert mapping["events"][1]["event_type"] == "POLICY_DENIED"
    assert mapping["components"][0]["fields"] == {"ready": True, "depth": 2}


@pytest.mark.asyncio
async def test_adapter_uses_existing_subscription_without_replacing_bus() -> None:
    event_bus = EventBus()
    tap = attach_existing_bus_visualization_tap(event_bus)

    await event_bus.publish(_event(EventType.CONTEXT_REPLY, "component.a", payload={"ok": True}))
    await event_bus.publish(_event(EventType.ERROR, "component.b"))

    snapshot = read_existing_bus_visualization_snapshot(tap, max_events=4)

    assert snapshot.event_count == 2
    assert snapshot.events[0].event_type == "CONTEXT_REPLY"
    assert snapshot.events[0].has_payload is True
    assert snapshot.events[1].event_type == "ERROR"


@pytest.mark.asyncio
async def test_drain_existing_event_bus_reader_respects_max_events() -> None:
    event_bus = EventBus()
    tap = attach_existing_bus_visualization_tap(event_bus)
    for index in range(3):
        await event_bus.publish(_event(EventType.TICK, f"component.{index}"))

    drained = drain_existing_event_bus_reader(tap.event_reader, max_events=2)

    assert [event.source for event in drained] == ["component.0", "component.1"]
    assert not tap.event_reader.empty()

    snapshot = read_existing_bus_visualization_snapshot(tap, max_events=1)
    assert snapshot.event_limit_reached is False
    assert snapshot.events[0].source == "component.2"


def test_build_existing_bus_visualization_snapshot_accepts_snapshot_mapping() -> None:
    snapshot = build_existing_bus_visualization_snapshot(
        [_event(EventType.LOAD, "loader")],
        context_source={"component.a": {"ready": True}},
        max_events=3,
    )

    assert snapshot.event_count == 1
    assert snapshot.component_count == 1
    assert snapshot.components[0].to_mapping() == {
        "name": "component.a",
        "fields": {"ready": True},
    }


@pytest.mark.parametrize("max_events", [0, -1, False])
def test_existing_bus_visualization_adapter_rejects_invalid_max_events(max_events: int) -> None:
    with pytest.raises(ValueError, match="max_events must be a positive integer"):
        build_existing_bus_visualization_snapshot([], max_events=max_events)

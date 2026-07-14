from __future__ import annotations

import asyncio
from pathlib import Path
from types import MappingProxyType

from context.cell_snapshot import CellSnapshot
from context.event_bus_cell_lens_live_bridge_0284 import (
    EventBusCellLensLiveBridge,
    event_lifecycle_state,
    event_to_cell_observation_event,
)
from contracts.event import Event, EventType
from kernel.event_bus import EventBus


def test_event_projection_reuses_existing_cell_contract() -> None:
    event = Event(
        EventType.START,
        source="scheduler",
        correlation_id="task-0284",
        priority=7,
        metadata=MappingProxyType(
            {
                "specialist_ref": "specialist:fake-1",
                "source_class": "specialist",
                "age": 2,
                "cost": 3,
            }
        ),
    )

    observation = event_to_cell_observation_event(
        event,
        observed_at="2026-07-14T18:00:00Z",
    )
    snapshot = observation.to_cell_snapshot()

    assert event_lifecycle_state(event) == "running"
    assert snapshot.cell_id == "specialist:fake-1"
    assert snapshot.source_task_id == "task-0284"
    assert snapshot.source_component_id == "scheduler"
    assert snapshot.source_class == "specialist"
    assert snapshot.lifecycle_state == "running"
    assert snapshot.score == 7.0
    assert snapshot.age == 2.0
    assert snapshot.cost == 3.0


def test_live_bridge_observes_real_event_bus_and_appends_journal(tmp_path: Path) -> None:
    journal_path = tmp_path / "cell-lens" / "cells.jsonl"

    async def scenario() -> EventBusCellLensLiveBridge:
        event_bus = EventBus()
        bridge = EventBusCellLensLiveBridge(
            event_bus,
            journal_path,
            clock=lambda: "2026-07-14T18:00:01Z",
        )
        await bridge.start()
        await event_bus.publish(
            Event(
                EventType.INFERENCE_RESULT,
                source="inference-adapter",
                correlation_id="task-result-1",
                metadata=MappingProxyType({"cell_kind": "openvino"}),
            )
        )
        await bridge.flush()
        await bridge.stop()
        return bridge

    bridge = asyncio.run(scenario())
    lines = journal_path.read_text(encoding="utf-8").splitlines()
    snapshot = CellSnapshot.from_json_line(lines[0])

    assert len(lines) == 1
    assert snapshot.cell_id == "task:task-result-1"
    assert snapshot.source_component_id == "inference-adapter"
    assert snapshot.source_class == "openvino"
    assert snapshot.lifecycle_state == "completed"
    assert snapshot.observed_at == "2026-07-14T18:00:01Z"
    assert bridge.stats.observed_count == 1
    assert bridge.stats.written_count == 1
    assert bridge.stats.dropped_count == 0
    assert bridge.stats.ok is True


def test_live_bridge_write_failure_never_propagates_to_event_producer(tmp_path: Path) -> None:
    journal_path = tmp_path / "journal-is-a-directory"
    journal_path.mkdir()

    async def scenario() -> EventBusCellLensLiveBridge:
        event_bus = EventBus()
        bridge = EventBusCellLensLiveBridge(event_bus, journal_path)
        await bridge.start()
        await event_bus.publish(Event(EventType.ERROR, source="component-a"))
        await bridge.flush()
        await bridge.stop()
        return bridge

    bridge = asyncio.run(scenario())

    assert bridge.stats.observed_count == 1
    assert bridge.stats.written_count == 0
    assert bridge.stats.dropped_count == 1
    assert bridge.stats.ok is False
    assert bridge.stats.errors


def test_explicit_valid_lifecycle_wins_and_negative_visual_costs_are_clamped() -> None:
    event = Event(
        EventType.TICK,
        source="component-b",
        metadata=MappingProxyType(
            {
                "lifecycle_state": "waiting",
                "age": -1,
                "cost": -2,
            }
        ),
    )

    snapshot = event_to_cell_observation_event(
        event,
        observed_at="2026-07-14T18:00:02Z",
    ).to_cell_snapshot()

    assert snapshot.lifecycle_state == "waiting"
    assert snapshot.age == 0.0
    assert snapshot.cost == 0.0

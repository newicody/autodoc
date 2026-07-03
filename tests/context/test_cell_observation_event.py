from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from context.cell_observation_event import (
    CELL_OBSERVATION_EVENT_SCHEMA,
    CellObservationEvent,
    derive_cell_snapshots_from_observation_events,
)


def _event(event_type: str = "task.running") -> CellObservationEvent:
    return CellObservationEvent(
        event_id="event-1",
        event_type=event_type,
        source_task_id="task-1",
        source_component_id="component-1",
        source_class="llm.answer",
        score=0.8,
        age=4.0,
        cost=2.0,
        observed_at="2026-07-03T10:00:00Z",
    )


def test_cell_observation_event_uses_versioned_schema() -> None:
    assert _event().schema == CELL_OBSERVATION_EVENT_SCHEMA
    assert _event().schema == "missipy.cell_observation_event.v1"


def test_cell_observation_event_is_immutable() -> None:
    event = _event()
    with pytest.raises(FrozenInstanceError):
        event.score = 0.0  # type: ignore[misc]


def test_cell_observation_event_derives_cell_snapshot() -> None:
    snapshot = _event("task.completed").to_cell_snapshot()
    assert snapshot.schema == "missipy.cell.v1"
    assert snapshot.cell_id == "task:task-1"
    assert snapshot.lifecycle_state == "completed"


def test_cell_observation_event_explicit_cell_id_wins() -> None:
    event = CellObservationEvent(
        event_id="event-1",
        event_type="component.observed",
        cell_id="cell-explicit",
        source_class="recorder.write",
        score=1.0,
        age=1.0,
        cost=0.5,
        observed_at="2026-07-03T10:00:00Z",
    )
    assert event.to_cell_snapshot().cell_id == "cell-explicit"


def test_cell_observation_event_round_trips_json_line() -> None:
    event = _event("task.waiting")
    assert CellObservationEvent.from_json_line(event.to_json_line()) == event


def test_cell_observation_event_rejects_unknown_schema() -> None:
    with pytest.raises(ValueError, match="unsupported cell observation event schema"):
        CellObservationEvent.from_mapping(
            {
                "schema": "missipy.cell_observation_event.v2",
                "event_id": "event-1",
                "event_type": "task.running",
                "source_class": "llm.answer",
                "score": 0.5,
                "age": 0,
                "cost": 0,
                "observed_at": "2026-07-03T10:00:00Z",
            }
        )


def test_cell_observation_event_rejects_unknown_event_type() -> None:
    with pytest.raises(ValueError, match="unsupported event_type"):
        CellObservationEvent(
            event_id="event-1",
            event_type="task.mutate",
            source_class="llm.answer",
            score=0.5,
            age=0,
            cost=0,
            observed_at="2026-07-03T10:00:00Z",
        )


def test_cell_observation_event_batch_derivation() -> None:
    snapshots = derive_cell_snapshots_from_observation_events([_event("task.running"), _event("task.completed")])
    assert [snapshot.lifecycle_state for snapshot in snapshots] == ["running", "completed"]

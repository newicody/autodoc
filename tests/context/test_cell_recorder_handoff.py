from __future__ import annotations

from pathlib import Path

from context.cell_observation_event import CellObservationEvent
from context.cell_recorder_handoff import (
    CELL_RECORDER_HANDOFF_SCHEMA,
    read_recorded_cell_observation_events,
    run_cell_recorder_handoff_dry_run,
)


def _event(index: int, event_type: str = "task.running") -> CellObservationEvent:
    return CellObservationEvent(
        event_id=f"event-{index}",
        event_type=event_type,
        source_task_id=f"task-{index}",
        source_component_id="component-a",
        source_class="scheduler.short_task",
        score=1.0,
        age=float(index),
        cost=0.5,
        observed_at=f"2026-07-03T10:00:0{index}Z",
    )


def test_handoff_reads_recorded_events(tmp_path: Path) -> None:
    input_path = tmp_path / "events.jsonl"
    input_path.write_text(_event(1).to_json_line() + _event(2).to_json_line(), encoding="utf-8")

    events = read_recorded_cell_observation_events(input_path)

    assert [event.event_id for event in events] == ["event-1", "event-2"]


def test_handoff_dry_run_writes_and_replays_same_count(tmp_path: Path) -> None:
    input_path = tmp_path / "events.jsonl"
    output_path = tmp_path / "cells.jsonl"
    input_path.write_text(
        _event(1, "task.created").to_json_line()
        + _event(2, "task.completed").to_json_line(),
        encoding="utf-8",
    )

    result = run_cell_recorder_handoff_dry_run(input_path, output_path)

    assert result.schema == CELL_RECORDER_HANDOFF_SCHEMA
    assert result.ok is True
    assert result.event_count == 2
    assert result.snapshot_count == 2
    assert result.replay_count == 2
    assert output_path.exists()


def test_handoff_dry_run_reports_invalid_input_best_effort(tmp_path: Path) -> None:
    input_path = tmp_path / "events.jsonl"
    output_path = tmp_path / "cells.jsonl"
    input_path.write_text(_event(1).to_json_line() + "not-json\n", encoding="utf-8")

    result = run_cell_recorder_handoff_dry_run(input_path, output_path)

    assert result.event_count == 1
    assert result.snapshot_count == 1
    assert result.replay_count == 1

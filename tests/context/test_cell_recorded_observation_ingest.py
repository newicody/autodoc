from __future__ import annotations

import json
from pathlib import Path

from context.cell_observation_event import CellObservationEvent
from context.cell_recorded_observation_ingest import (
    CELL_RECORDED_OBSERVATION_INGEST_SCHEMA,
    CELL_RECORDED_OBSERVATION_STATE_SCHEMA,
    ingest_recorded_observation_events_to_cell_journal,
    load_recorded_observation_ingest_state,
    read_recorded_observation_events_from_offset,
)
from context.cell_snapshot_journal_reader import read_cell_snapshot_jsonl


def _event(index: int, event_type: str = "task.running") -> CellObservationEvent:
    return CellObservationEvent(
        event_id=f"event-{index}",
        event_type=event_type,
        source_task_id=f"task-{index}",
        source_class="scheduler.short_task",
        score=1.0,
        age=float(index),
        cost=0.5,
        observed_at=f"2026-07-03T10:00:0{index}Z",
    )


def test_recorded_observation_ingest_writes_journal_and_state(tmp_path: Path) -> None:
    source = tmp_path / "observations.jsonl"
    journal = tmp_path / "cells.jsonl"
    state = tmp_path / "state.json"
    source.write_text(_event(1).to_json_line() + _event(2, "task.completed").to_json_line(), encoding="utf-8")

    result = ingest_recorded_observation_events_to_cell_journal(source, journal, state)

    replay = read_cell_snapshot_jsonl(journal)
    saved_state = json.loads(state.read_text(encoding="utf-8"))

    assert result.schema == CELL_RECORDED_OBSERVATION_INGEST_SCHEMA
    assert result.ok is True
    assert result.event_count == 2
    assert result.written_count == 2
    assert len(replay.snapshots) == 2
    assert saved_state["schema"] == CELL_RECORDED_OBSERVATION_STATE_SCHEMA
    assert saved_state["next_offset"] == source.stat().st_size


def test_recorded_observation_ingest_is_incremental(tmp_path: Path) -> None:
    source = tmp_path / "observations.jsonl"
    journal = tmp_path / "cells.jsonl"
    state = tmp_path / "state.json"
    source.write_text(_event(1).to_json_line(), encoding="utf-8")

    first = ingest_recorded_observation_events_to_cell_journal(source, journal, state)
    second = ingest_recorded_observation_events_to_cell_journal(source, journal, state)

    assert first.written_count == 1
    assert second.written_count == 0
    assert read_cell_snapshot_jsonl(journal).snapshots[0].cell_id == "task:task-1"


def test_recorded_observation_ingest_reads_only_new_appended_lines(tmp_path: Path) -> None:
    source = tmp_path / "observations.jsonl"
    journal = tmp_path / "cells.jsonl"
    state = tmp_path / "state.json"
    source.write_text(_event(1).to_json_line(), encoding="utf-8")
    ingest_recorded_observation_events_to_cell_journal(source, journal, state)

    with source.open("a", encoding="utf-8") as handle:
        handle.write(_event(2, "task.completed").to_json_line())

    result = ingest_recorded_observation_events_to_cell_journal(source, journal, state)
    replay = read_cell_snapshot_jsonl(journal)

    assert result.written_count == 1
    assert [snapshot.cell_id for snapshot in replay.snapshots] == ["task:task-1", "task:task-2"]


def test_recorded_observation_read_best_effort_drops_bad_lines(tmp_path: Path) -> None:
    source = tmp_path / "observations.jsonl"
    source.write_text(_event(1).to_json_line() + "not-json\n", encoding="utf-8")

    result = read_recorded_observation_events_from_offset(source)

    assert result.attempted_lines == 2
    assert len(result.events) == 1
    assert result.dropped_count == 1
    assert result.errors


def test_recorded_observation_state_resets_when_source_changes(tmp_path: Path) -> None:
    source_a = tmp_path / "a.jsonl"
    source_b = tmp_path / "b.jsonl"
    state = tmp_path / "state.json"
    source_a.write_text(_event(1).to_json_line(), encoding="utf-8")
    source_b.write_text(_event(2).to_json_line(), encoding="utf-8")

    ingest_recorded_observation_events_to_cell_journal(source_a, tmp_path / "cells.jsonl", state)
    loaded = load_recorded_observation_ingest_state(state, source_path=source_b)

    assert loaded.source_path == str(source_b)
    assert loaded.next_offset == 0

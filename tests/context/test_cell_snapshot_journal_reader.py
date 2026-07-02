from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.cell_snapshot import CellSnapshot
from context.cell_snapshot_journal import CellSnapshotJournalWriter
from context.cell_snapshot_journal_reader import (
    CELL_SNAPSHOT_JOURNAL_READER_SCHEMA,
    iter_cell_snapshot_jsonl,
    read_cell_snapshot_jsonl,
    tail_cell_snapshot_jsonl,
)


def _snapshot(index: int, *, state: str = "running") -> CellSnapshot:
    return CellSnapshot(
        cell_id=f"cell-{index}",
        source_task_id=f"task-{index}",
        source_component_id="component-a",
        source_class="llm.answer",
        score=0.5 + index,
        age=float(index),
        cost=float(index * 2),
        lifecycle_state=state,
        observed_at=f"2026-07-03T10:00:0{index}Z",
    )


def test_journal_reader_replays_jsonl_in_order(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    CellSnapshotJournalWriter(path).append_many([_snapshot(1), _snapshot(2, state="completed")])

    result = read_cell_snapshot_jsonl(path)

    assert result.ok is True
    assert result.schema == CELL_SNAPSHOT_JOURNAL_READER_SCHEMA
    assert [snapshot.cell_id for snapshot in result.snapshots] == ["cell-1", "cell-2"]


def test_journal_iterator_replays_valid_lines(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    CellSnapshotJournalWriter(path).append_many([_snapshot(1), _snapshot(2)])

    snapshots = tuple(iter_cell_snapshot_jsonl(path))

    assert [snapshot.cell_id for snapshot in snapshots] == ["cell-1", "cell-2"]


def test_journal_reader_skips_invalid_lines_best_effort(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    path.write_text(_snapshot(1).to_json_line() + "not json\n" + _snapshot(2).to_json_line(), encoding="utf-8")

    result = read_cell_snapshot_jsonl(path)

    assert result.ok is False
    assert result.attempted_lines == 3
    assert [snapshot.cell_id for snapshot in result.snapshots] == ["cell-1", "cell-2"]
    assert result.dropped_count == 1
    assert result.errors


def test_journal_reader_strict_mode_raises_on_invalid_line(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    path.write_text(_snapshot(1).to_json_line() + "not json\n", encoding="utf-8")

    with pytest.raises(ValueError):
        read_cell_snapshot_jsonl(path, strict=True)


def test_journal_reader_missing_file_is_best_effort(tmp_path: Path) -> None:
    result = read_cell_snapshot_jsonl(tmp_path / "missing.jsonl")

    assert result.snapshots == ()
    assert result.errors


def test_journal_reader_limit_stops_after_valid_snapshot_count(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    CellSnapshotJournalWriter(path).append_many([_snapshot(1), _snapshot(2), _snapshot(3)])

    result = read_cell_snapshot_jsonl(path, limit=2)

    assert [snapshot.cell_id for snapshot in result.snapshots] == ["cell-1", "cell-2"]


def test_journal_tail_reads_only_new_complete_lines(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    writer = CellSnapshotJournalWriter(path)
    writer.append(_snapshot(1))

    first = tail_cell_snapshot_jsonl(path)
    assert [snapshot.cell_id for snapshot in first.snapshots] == ["cell-1"]

    writer.append(_snapshot(2))
    second = tail_cell_snapshot_jsonl(path, offset=first.next_offset)

    assert second.start_offset == first.next_offset
    assert [snapshot.cell_id for snapshot in second.snapshots] == ["cell-2"]


def test_journal_tail_does_not_consume_incomplete_line(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    path.write_text(_snapshot(1).to_json_line(), encoding="utf-8")
    offset = path.stat().st_size

    path.write_text(path.read_text(encoding="utf-8") + json.dumps(_snapshot(2).to_json_dict()), encoding="utf-8")

    result = tail_cell_snapshot_jsonl(path, offset=offset)

    assert result.snapshots == ()
    assert result.next_offset == offset


def test_journal_tail_max_lines_bounds_work(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    CellSnapshotJournalWriter(path).append_many([_snapshot(1), _snapshot(2), _snapshot(3)])

    result = tail_cell_snapshot_jsonl(path, max_lines=2)

    assert result.attempted_lines == 2
    assert [snapshot.cell_id for snapshot in result.snapshots] == ["cell-1", "cell-2"]

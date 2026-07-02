from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.cell_snapshot import CellSnapshot
from context.cell_snapshot_journal import (
    CELL_SNAPSHOT_JOURNAL_SCHEMA,
    CellSnapshotJournalWriter,
    write_cell_snapshots_jsonl,
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


def test_cell_snapshot_journal_appends_json_lines(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    result = CellSnapshotJournalWriter(path).append(_snapshot(1))

    lines = path.read_text(encoding="utf-8").splitlines()

    assert result.ok is True
    assert result.schema == CELL_SNAPSHOT_JOURNAL_SCHEMA
    assert len(lines) == 1
    assert json.loads(lines[0])["schema"] == "missipy.cell.v1"
    assert json.loads(lines[0])["cell_id"] == "cell-1"


def test_cell_snapshot_journal_preserves_append_order(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    writer = CellSnapshotJournalWriter(path)

    writer.append_many([_snapshot(1), _snapshot(2, state="completed")])

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["cell_id"] for row in rows] == ["cell-1", "cell-2"]
    assert rows[1]["lifecycle_state"] == "completed"


def test_cell_snapshot_journal_creates_parent_directory(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "cells.jsonl"

    result = write_cell_snapshots_jsonl(path, [_snapshot(1)])

    assert result.written_count == 1
    assert path.exists()


def test_cell_snapshot_journal_is_best_effort_for_invalid_items(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    writer = CellSnapshotJournalWriter(path)

    result = writer.append_many([_snapshot(1), object()])  # type: ignore[list-item]

    assert result.attempted_count == 2
    assert result.written_count == 1
    assert result.dropped_count == 1
    assert result.errors


def test_cell_snapshot_journal_strict_mode_rejects_invalid_items(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    writer = CellSnapshotJournalWriter(path, strict=True)

    with pytest.raises(TypeError):
        writer.append_many([object()])  # type: ignore[list-item]


def test_cell_snapshot_journal_best_effort_on_write_error(tmp_path: Path) -> None:
    writer = CellSnapshotJournalWriter(tmp_path)

    result = writer.append(_snapshot(1))

    assert result.written_count == 0
    assert result.dropped_count == 1
    assert result.errors

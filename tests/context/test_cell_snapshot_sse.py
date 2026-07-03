from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.cell_snapshot import CellSnapshot
from context.cell_snapshot_journal import CellSnapshotJournalWriter
from context.cell_snapshot_sse import (
    CELL_SNAPSHOT_SSE_EVENT_NAME,
    CELL_SNAPSHOT_SSE_SCHEMA,
    CellSnapshotSseEvent,
    cell_journal_to_sse_text,
    format_sse_event,
    snapshot_to_sse_event,
    snapshots_to_sse_text,
)


def _snapshot(index: int) -> CellSnapshot:
    return CellSnapshot(
        cell_id=f"cell-{index}",
        source_task_id=f"task-{index}",
        source_class="llm.answer",
        score=0.8,
        age=float(index),
        cost=2.0,
        lifecycle_state="running",
        observed_at=f"2026-07-03T10:00:0{index}Z",
    )


def test_cell_snapshot_sse_event_declares_versioned_schema() -> None:
    event = snapshot_to_sse_event(_snapshot(1), sequence=7)

    assert event.schema == CELL_SNAPSHOT_SSE_SCHEMA
    assert event.schema == "missipy.cell_snapshot_sse.v1"
    assert event.event_name == CELL_SNAPSHOT_SSE_EVENT_NAME
    assert event.event_id == "7"


def test_cell_snapshot_sse_event_formats_sse_text() -> None:
    text = snapshot_to_sse_event(_snapshot(1), sequence=0).to_sse_text()

    assert text.startswith("id: 0\nevent: cell_snapshot\ndata: ")
    assert text.endswith("\n\n")
    payload = json.loads(text.split("data: ", 1)[1])
    assert payload["schema"] == "missipy.cell_snapshot_sse.v1"
    assert payload["snapshot"]["schema"] == "missipy.cell.v1"


def test_format_sse_event_rejects_multiline_id_or_event_name() -> None:
    with pytest.raises(ValueError):
        format_sse_event(event_name="cell\nsnapshot", event_id="1", data="{}")
    with pytest.raises(ValueError):
        format_sse_event(event_name="cell_snapshot", event_id="1\n2", data="{}")


def test_snapshots_to_sse_text_preserves_sequence_order() -> None:
    text = snapshots_to_sse_text([_snapshot(1), _snapshot(2)], start_sequence=10)

    assert "id: 10" in text
    assert "id: 11" in text
    assert text.index("id: 10") < text.index("id: 11")


def test_cell_journal_to_sse_text_reads_existing_journal(tmp_path: Path) -> None:
    path = tmp_path / "cells.jsonl"
    CellSnapshotJournalWriter(path).append_many([_snapshot(1), _snapshot(2)])

    text = cell_journal_to_sse_text(path, limit=1)

    assert "id: 0" in text
    assert "cell-1" in text
    assert "cell-2" not in text


def test_cell_snapshot_sse_event_rejects_wrong_schema() -> None:
    with pytest.raises(ValueError, match="unsupported cell snapshot SSE schema"):
        CellSnapshotSseEvent(event_id="1", data=_snapshot(1), schema="missipy.cell_snapshot_sse.v2")

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from context.cell_snapshot import (
    CELL_SNAPSHOT_SCHEMA,
    CellSnapshot,
)


def test_cell_snapshot_uses_versioned_schema() -> None:
    snapshot = CellSnapshot(
        cell_id="cell-1",
        source_task_id="task-1",
        source_component_id="component-1",
        source_class="llm.answer",
        score=0.92,
        age=12.5,
        cost=4.0,
        lifecycle_state="running",
        observed_at="2026-07-03T10:00:00Z",
    )

    assert snapshot.schema == CELL_SNAPSHOT_SCHEMA
    assert snapshot.schema == "missipy.cell.v1"


def test_cell_snapshot_is_immutable() -> None:
    snapshot = CellSnapshot(
        cell_id="cell-1",
        source_class="ingest.batch",
        score=1.0,
        age=0.0,
        cost=0.0,
        lifecycle_state="created",
        observed_at="2026-07-03T10:00:00Z",
    )

    with pytest.raises(FrozenInstanceError):
        snapshot.score = 0.0  # type: ignore[misc]


def test_cell_snapshot_round_trips_json_line() -> None:
    snapshot = CellSnapshot(
        cell_id="cell-1",
        source_task_id="task-1",
        source_component_id="component-1",
        source_class="llm.answer",
        score=0.8,
        age=3.0,
        cost=2.5,
        lifecycle_state="completed",
        observed_at="2026-07-03T10:00:00Z",
    )

    restored = CellSnapshot.from_json_line(snapshot.to_json_line())

    assert restored == snapshot


def test_cell_snapshot_rejects_unknown_schema() -> None:
    with pytest.raises(ValueError, match="unsupported cell snapshot schema"):
        CellSnapshot.from_mapping(
            {
                "schema": "missipy.cell.v2",
                "cell_id": "cell-1",
                "source_class": "llm.answer",
                "score": 1,
                "age": 0,
                "cost": 0,
                "lifecycle_state": "created",
                "observed_at": "2026-07-03T10:00:00Z",
            }
        )


@pytest.mark.parametrize("field", ["cell_id", "source_class", "lifecycle_state", "observed_at"])
def test_cell_snapshot_rejects_empty_required_strings(field: str) -> None:
    payload = {
        "cell_id": "cell-1",
        "source_class": "llm.answer",
        "score": 1.0,
        "age": 0.0,
        "cost": 0.0,
        "lifecycle_state": "created",
        "observed_at": "2026-07-03T10:00:00Z",
    }
    payload[field] = ""

    with pytest.raises(ValueError):
        CellSnapshot(**payload)


@pytest.mark.parametrize("field", ["age", "cost"])
def test_cell_snapshot_rejects_negative_non_negative_fields(field: str) -> None:
    payload = {
        "cell_id": "cell-1",
        "source_class": "llm.answer",
        "score": 1.0,
        "age": 0.0,
        "cost": 0.0,
        "lifecycle_state": "created",
        "observed_at": "2026-07-03T10:00:00Z",
    }
    payload[field] = -1.0

    with pytest.raises(ValueError):
        CellSnapshot(**payload)


def test_cell_snapshot_rejects_unknown_lifecycle_state() -> None:
    with pytest.raises(ValueError, match="unsupported lifecycle_state"):
        CellSnapshot(
            cell_id="cell-1",
            source_class="llm.answer",
            score=1.0,
            age=0.0,
            cost=0.0,
            lifecycle_state="mutating",
            observed_at="2026-07-03T10:00:00Z",
        )

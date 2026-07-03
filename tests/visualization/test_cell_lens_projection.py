from __future__ import annotations

from context.cell_snapshot import CellSnapshot
from visualization.cell_lens_projection import (
    CELL_LENS_PROJECTION_SCHEMA,
    latest_snapshot_by_cell,
    project_cell_snapshot,
    project_cell_snapshots,
)


def _snapshot(cell_id: str, age: float, state: str = "running") -> CellSnapshot:
    return CellSnapshot(
        cell_id=cell_id,
        source_class="llm.answer",
        score=1.0,
        age=age,
        cost=4.0,
        lifecycle_state=state,
        observed_at=f"2026-07-03T10:00:{int(age):02d}Z",
    )


def test_projection_is_stable_for_same_cell() -> None:
    first = project_cell_snapshot(_snapshot("cell-1", 1.0))
    second = project_cell_snapshot(_snapshot("cell-1", 10.0))

    assert first.schema == CELL_LENS_PROJECTION_SCHEMA
    assert (first.x, first.y) == (second.x, second.y)


def test_projection_size_grows_with_cost() -> None:
    low = CellSnapshot(
        cell_id="cell-1",
        source_class="llm.answer",
        score=1.0,
        age=1.0,
        cost=1.0,
        lifecycle_state="running",
        observed_at="2026-07-03T10:00:00Z",
    )
    high = CellSnapshot(
        cell_id="cell-2",
        source_class="llm.answer",
        score=1.0,
        age=1.0,
        cost=100.0,
        lifecycle_state="running",
        observed_at="2026-07-03T10:00:00Z",
    )

    assert project_cell_snapshot(high).size > project_cell_snapshot(low).size


def test_projection_can_keep_latest_snapshot_per_cell() -> None:
    snapshots = [_snapshot("cell-1", 1.0), _snapshot("cell-1", 2.0), _snapshot("cell-2", 1.0)]

    latest = latest_snapshot_by_cell(snapshots)
    points = project_cell_snapshots(snapshots)

    assert latest["cell-1"].age == 2.0
    assert len(points) == 2

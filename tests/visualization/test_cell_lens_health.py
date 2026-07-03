from __future__ import annotations

from context.cell_snapshot import CellSnapshot
from visualization.cell_lens_health import (
    CELL_LENS_HEALTH_SCHEMA,
    estimate_cell_health,
)


def _snapshot(source_class: str, age: float, state: str = "running") -> CellSnapshot:
    return CellSnapshot(
        cell_id="cell-1",
        source_class=source_class,
        score=1.0,
        age=age,
        cost=1.0,
        lifecycle_state=state,
        observed_at="2026-07-03T10:00:00Z",
    )


def test_health_uses_expected_lifetime_not_raw_duration() -> None:
    slow_llm = estimate_cell_health(_snapshot("llm.answer", age=20.0))
    slow_short_task = estimate_cell_health(_snapshot("scheduler.short_task", age=20.0))

    assert slow_llm.status == "healthy"
    assert slow_short_task.status in {"stale", "degraded"}
    assert slow_llm.health_score > slow_short_task.health_score


def test_health_marks_terminal_states_as_terminal() -> None:
    health = estimate_cell_health(_snapshot("llm.answer", age=1.0, state="failed"))

    assert health.schema == CELL_LENS_HEALTH_SCHEMA
    assert health.status == "terminal"
    assert health.health_score == 0.0


def test_health_accepts_custom_expected_lifetime() -> None:
    snapshot = _snapshot("custom.long", age=40.0)

    health = estimate_cell_health(snapshot, expected_lifetimes={"custom.long": 100.0})

    assert health.status == "healthy"
    assert health.expected_lifetime == 100.0

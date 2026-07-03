from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from context.cell_snapshot import CellSnapshot


CELL_LENS_HEALTH_SCHEMA = "missipy.cell_lens_health.v1"


DEFAULT_EXPECTED_LIFETIMES = {
    "scheduler.short_task": 2.0,
    "llm.answer": 45.0,
    "ingest.batch": 120.0,
    "recorder.write": 5.0,
}


@dataclass(frozen=True, slots=True)
class CellHealth:
    """Observation-only health estimate for a cell snapshot."""

    cell_id: str
    source_class: str
    age: float
    expected_lifetime: float
    lifetime_ratio: float
    health_score: float
    status: str
    lifecycle_state: str
    schema: str = CELL_LENS_HEALTH_SCHEMA

    def to_json_dict(self) -> dict[str, object]:
        return {
            "age": self.age,
            "cell_id": self.cell_id,
            "expected_lifetime": self.expected_lifetime,
            "health_score": self.health_score,
            "lifecycle_state": self.lifecycle_state,
            "lifetime_ratio": self.lifetime_ratio,
            "schema": self.schema,
            "source_class": self.source_class,
            "status": self.status,
        }


def estimate_cell_health(
    snapshot: CellSnapshot,
    *,
    expected_lifetimes: Mapping[str, float] | None = None,
    default_expected_lifetime: float = 30.0,
) -> CellHealth:
    """Estimate health by deviation from expected lifetime.

    This is deliberately not a fitness function and not a command decision. It
    is a visualization/readout estimate.
    """

    lifetimes = expected_lifetimes or DEFAULT_EXPECTED_LIFETIMES
    expected = float(lifetimes.get(snapshot.source_class, default_expected_lifetime))
    if expected <= 0:
        raise ValueError("expected lifetime must be > 0")

    ratio = snapshot.age / expected
    health_score = _health_score_from_ratio(ratio=ratio, lifecycle_state=snapshot.lifecycle_state)
    status = _status_from_score(score=health_score, ratio=ratio, lifecycle_state=snapshot.lifecycle_state)

    return CellHealth(
        cell_id=snapshot.cell_id,
        source_class=snapshot.source_class,
        age=snapshot.age,
        expected_lifetime=expected,
        lifetime_ratio=round(ratio, 6),
        health_score=round(health_score, 6),
        status=status,
        lifecycle_state=snapshot.lifecycle_state,
    )


def _health_score_from_ratio(*, ratio: float, lifecycle_state: str) -> float:
    if lifecycle_state in {"failed", "cancelled", "dropped"}:
        return 0.0
    if ratio <= 1.0:
        return 1.0
    if ratio <= 1.5:
        return max(0.55, 1.0 - ((ratio - 1.0) * 0.90))
    if ratio <= 2.5:
        return max(0.15, 0.55 - ((ratio - 1.5) * 0.40))
    return 0.05


def _status_from_score(*, score: float, ratio: float, lifecycle_state: str) -> str:
    if lifecycle_state in {"failed", "cancelled", "dropped"}:
        return "terminal"
    if score >= 0.85:
        return "healthy"
    if score >= 0.55:
        return "late"
    if ratio >= 2.5:
        return "stale"
    return "degraded"

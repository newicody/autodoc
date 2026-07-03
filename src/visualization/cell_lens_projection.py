from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Iterable, Mapping

from context.cell_snapshot import CellSnapshot
from visualization.cell_lens_health import CellHealth, estimate_cell_health


CELL_LENS_PROJECTION_SCHEMA = "missipy.cell_lens_projection.v1"


@dataclass(frozen=True, slots=True)
class CellRenderPoint:
    """Renderer-neutral point derived from a cell snapshot."""

    cell_id: str
    source_class: str
    lifecycle_state: str
    x: float
    y: float
    z: float
    size: float
    health_score: float
    status: str
    age: float
    cost: float
    schema: str = CELL_LENS_PROJECTION_SCHEMA

    def to_json_dict(self) -> dict[str, object]:
        return {
            "age": self.age,
            "cell_id": self.cell_id,
            "cost": self.cost,
            "health_score": self.health_score,
            "lifecycle_state": self.lifecycle_state,
            "schema": self.schema,
            "size": self.size,
            "source_class": self.source_class,
            "status": self.status,
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }


def latest_snapshot_by_cell(snapshots: Iterable[CellSnapshot]) -> dict[str, CellSnapshot]:
    latest: dict[str, CellSnapshot] = {}
    for snapshot in snapshots:
        latest[snapshot.cell_id] = snapshot
    return latest


def project_cell_snapshot(
    snapshot: CellSnapshot,
    *,
    health: CellHealth | None = None,
    expected_lifetimes: Mapping[str, float] | None = None,
) -> CellRenderPoint:
    current_health = health or estimate_cell_health(snapshot, expected_lifetimes=expected_lifetimes)
    x, y = _stable_unit_position(snapshot.cell_id, snapshot.source_class)
    z = _lifecycle_z(snapshot.lifecycle_state)
    size = _size_from_cost(snapshot.cost)

    return CellRenderPoint(
        cell_id=snapshot.cell_id,
        source_class=snapshot.source_class,
        lifecycle_state=snapshot.lifecycle_state,
        x=x,
        y=y,
        z=z,
        size=size,
        health_score=current_health.health_score,
        status=current_health.status,
        age=snapshot.age,
        cost=snapshot.cost,
    )


def project_cell_snapshots(
    snapshots: Iterable[CellSnapshot],
    *,
    expected_lifetimes: Mapping[str, float] | None = None,
    latest_only: bool = True,
) -> tuple[CellRenderPoint, ...]:
    materialized: Iterable[CellSnapshot]
    if latest_only:
        materialized = latest_snapshot_by_cell(snapshots).values()
    else:
        materialized = snapshots

    return tuple(
        project_cell_snapshot(snapshot, expected_lifetimes=expected_lifetimes)
        for snapshot in materialized
    )


def _stable_unit_position(cell_id: str, source_class: str) -> tuple[float, float]:
    digest = hashlib.sha256(f"{source_class}:{cell_id}".encode("utf-8")).digest()
    angle_raw = int.from_bytes(digest[0:8], "big") / float(2**64 - 1)
    radius_raw = int.from_bytes(digest[8:16], "big") / float(2**64 - 1)

    angle = angle_raw * math.tau
    radius = math.sqrt(radius_raw)

    return (round(math.cos(angle) * radius, 6), round(math.sin(angle) * radius, 6))


def _lifecycle_z(lifecycle_state: str) -> float:
    order = {
        "created": 0.0,
        "queued": 0.1,
        "running": 0.2,
        "waiting": 0.3,
        "completed": 0.4,
        "failed": 0.5,
        "cancelled": 0.5,
        "dropped": 0.5,
    }
    return order.get(lifecycle_state, 0.0)


def _size_from_cost(cost: float) -> float:
    return round(4.0 + min(16.0, math.sqrt(max(cost, 0.0)) * 1.6), 6)

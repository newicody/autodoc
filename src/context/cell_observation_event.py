from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from context.cell_snapshot import CellSnapshot


CELL_OBSERVATION_EVENT_SCHEMA = "missipy.cell_observation_event.v1"

CELL_OBSERVATION_EVENT_TYPES = (
    "task.created",
    "task.queued",
    "task.running",
    "task.waiting",
    "task.completed",
    "task.failed",
    "task.cancelled",
    "task.dropped",
    "component.observed",
)

_STATE_BY_EVENT_TYPE = {
    "task.created": "created",
    "task.queued": "queued",
    "task.running": "running",
    "task.waiting": "waiting",
    "task.completed": "completed",
    "task.failed": "failed",
    "task.cancelled": "cancelled",
    "task.dropped": "dropped",
    "component.observed": "running",
}


@dataclass(frozen=True, slots=True)
class CellObservationEvent:
    """Immutable recorded observation input for deriving a cell snapshot."""

    event_id: str
    event_type: str
    source_class: str
    observed_at: str
    score: float
    age: float
    cost: float
    cell_id: str = ""
    source_task_id: str = ""
    source_component_id: str = ""
    lifecycle_state: str = ""
    schema: str = CELL_OBSERVATION_EVENT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != CELL_OBSERVATION_EVENT_SCHEMA:
            raise ValueError(f"unsupported cell observation event schema: {self.schema!r}")
        _require_non_empty("event_id", self.event_id)
        _require_non_empty("event_type", self.event_type)
        _require_non_empty("source_class", self.source_class)
        _require_non_empty("observed_at", self.observed_at)
        if self.event_type not in CELL_OBSERVATION_EVENT_TYPES:
            raise ValueError(f"unsupported event_type: {self.event_type!r}")
        if self.age < 0:
            raise ValueError("age must be >= 0")
        if self.cost < 0:
            raise ValueError("cost must be >= 0")

    def snapshot_cell_id(self) -> str:
        if self.cell_id:
            return self.cell_id
        if self.source_task_id:
            return f"task:{self.source_task_id}"
        if self.source_component_id:
            return f"component:{self.source_component_id}"
        return f"event:{self.event_id}"

    def snapshot_lifecycle_state(self) -> str:
        return self.lifecycle_state or _STATE_BY_EVENT_TYPE[self.event_type]

    def to_cell_snapshot(self) -> CellSnapshot:
        return CellSnapshot(
            cell_id=self.snapshot_cell_id(),
            source_task_id=self.source_task_id,
            source_component_id=self.source_component_id,
            source_class=self.source_class,
            score=float(self.score),
            age=float(self.age),
            cost=float(self.cost),
            lifecycle_state=self.snapshot_lifecycle_state(),
            observed_at=self.observed_at,
        )

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "age": self.age,
            "cell_id": self.cell_id,
            "cost": self.cost,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "lifecycle_state": self.lifecycle_state,
            "observed_at": self.observed_at,
            "schema": self.schema,
            "score": self.score,
            "source_class": self.source_class,
            "source_component_id": self.source_component_id,
            "source_task_id": self.source_task_id,
        }

    def to_json_line(self) -> str:
        return json.dumps(self.to_json_dict(), ensure_ascii=False, sort_keys=True) + "\n"

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "CellObservationEvent":
        schema = str(mapping.get("schema", ""))
        if schema != CELL_OBSERVATION_EVENT_SCHEMA:
            raise ValueError(f"unsupported cell observation event schema: {schema!r}")
        return cls(
            event_id=str(mapping["event_id"]),
            event_type=str(mapping["event_type"]),
            source_class=str(mapping["source_class"]),
            observed_at=str(mapping["observed_at"]),
            score=float(mapping["score"]),
            age=float(mapping["age"]),
            cost=float(mapping["cost"]),
            cell_id=str(mapping.get("cell_id", "")),
            source_task_id=str(mapping.get("source_task_id", "")),
            source_component_id=str(mapping.get("source_component_id", "")),
            lifecycle_state=str(mapping.get("lifecycle_state", "")),
            schema=schema,
        )

    @classmethod
    def from_json_line(cls, line: str) -> "CellObservationEvent":
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError("cell observation event JSON line must contain an object")
        return cls.from_mapping(payload)


def derive_cell_snapshots_from_observation_events(
    events: Iterable[CellObservationEvent],
) -> tuple[CellSnapshot, ...]:
    return tuple(event.to_cell_snapshot() for event in events)


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")

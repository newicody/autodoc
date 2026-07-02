from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Mapping


CELL_SNAPSHOT_SCHEMA = "missipy.cell.v1"

CELL_LIFECYCLE_STATES = (
    "created",
    "queued",
    "running",
    "waiting",
    "completed",
    "failed",
    "cancelled",
    "dropped",
)


@dataclass(frozen=True, slots=True)
class CellSnapshot:
    """Immutable observation snapshot for a task/component activity cell.

    A cell snapshot is a read-only observation contract. It is derived from
    task/component events and can be consumed by desktop visualization, mobile
    views, replay tools, or analysis scripts.

    It is not a command, not an action request, and not a mutable runtime handle.
    """

    cell_id: str
    source_class: str
    lifecycle_state: str
    observed_at: str
    score: float
    age: float
    cost: float
    source_task_id: str = ""
    source_component_id: str = ""
    schema: str = CELL_SNAPSHOT_SCHEMA

    def __post_init__(self) -> None:
        _require_non_empty("schema", self.schema)
        if self.schema != CELL_SNAPSHOT_SCHEMA:
            raise ValueError(f"unsupported cell snapshot schema: {self.schema!r}")

        _require_non_empty("cell_id", self.cell_id)
        _require_non_empty("source_class", self.source_class)
        _require_non_empty("lifecycle_state", self.lifecycle_state)
        _require_non_empty("observed_at", self.observed_at)

        if self.lifecycle_state not in CELL_LIFECYCLE_STATES:
            raise ValueError(f"unsupported lifecycle_state: {self.lifecycle_state!r}")

        _require_finite_number("score", self.score)
        _require_finite_number("age", self.age)
        _require_finite_number("cost", self.cost)

        if self.age < 0:
            raise ValueError("age must be >= 0")
        if self.cost < 0:
            raise ValueError("cost must be >= 0")

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "age": self.age,
            "cell_id": self.cell_id,
            "cost": self.cost,
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
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "CellSnapshot":
        schema = str(mapping.get("schema", ""))
        if schema != CELL_SNAPSHOT_SCHEMA:
            raise ValueError(f"unsupported cell snapshot schema: {schema!r}")

        return cls(
            cell_id=str(mapping["cell_id"]),
            source_class=str(mapping["source_class"]),
            lifecycle_state=str(mapping["lifecycle_state"]),
            observed_at=str(mapping["observed_at"]),
            score=float(mapping["score"]),
            age=float(mapping["age"]),
            cost=float(mapping["cost"]),
            source_task_id=str(mapping.get("source_task_id", "")),
            source_component_id=str(mapping.get("source_component_id", "")),
            schema=schema,
        )

    @classmethod
    def from_json_line(cls, line: str) -> "CellSnapshot":
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError("cell snapshot JSON line must contain an object")
        return cls.from_mapping(payload)


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")


def _require_finite_number(name: str, value: float) -> None:
    if not isinstance(value, (float, int)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{name} must be finite")

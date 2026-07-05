"""ControlProxy route generation table for mmap route updates.

This module implements phase 0091-r2. It adds the small table the
ControlProxy side needs before g2/g3 route updates can be safe:

    route_id -> current_generation

The generation table is incremented only when a new route generation is materialized.
Normal Scheduler handshakes, route writes, route reads and
notifier wakeups do not allocate a generation. The active mmap/shm-like data
surface is never resized in place: g1 remains its own ring.bin, g2 receives a
new ring.bin, and a later phase can drain and close older generations.

Boundaries deliberately kept out of this module:
- No CLI.
- No OpenRC service and no resident daemon.
- No watcher or inotify loop.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher or Component tick contract modification.
- No policy/zone/scope decision in ControlProxy.
- ControlProxy does not decide security.
- Scheduler/policy/zone remain the authority.
- No live mmap resize.
- No inter-process lock yet.
- Not /dev/shm-only; the current implementation is file-backed mmap and can
  later point to a /dev/shm runtime root.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Literal, Mapping

from runtime.controlfs_manifest import normalize_route_id
from runtime.controlproxy_prepare import RoutePrepareDecision
from runtime.mmap_fixed_slot_route import (
    MmapFixedSlotRoute,
    create_mmap_route_from_decision,
    route_dir_for_handle,
)

ROUTE_GENERATION_TABLE_SCHEMA = "missipy.controlproxy.route_generation_table.v1"
ROUTE_GENERATION_RECORD_SCHEMA = "missipy.controlproxy.route_generation_record.v1"

GenerationState = Literal["candidate", "active", "draining", "closed"]
_GENERATION_STATES = {"candidate", "active", "draining", "closed"}
_CREATE_ACTIONS = {"create_route_generation", "create_next_generation"}


class RouteGenerationTableError(RuntimeError):
    """Raised when route generation state cannot be allocated or persisted."""


@dataclass(frozen=True, slots=True)
class RouteGenerationRecord:
    """One concrete materialized route generation."""

    schema: str
    route_id: str
    generation: int
    route_handle: str
    state: GenerationState
    task_id: str
    zone: str
    slot_size: int
    slot_count: int
    max_frame_bytes: int
    runtime_route_dir: str
    ring_path: str
    mmap_status_path: str
    controlfs_generation_status_path: str
    source_request_id: str
    created_at: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "RouteGenerationRecord":
        schema = _require_str(raw, "schema")
        if schema != ROUTE_GENERATION_RECORD_SCHEMA:
            raise RouteGenerationTableError("unsupported route generation record schema")
        state = _require_str(raw, "state")
        if state not in _GENERATION_STATES:
            raise RouteGenerationTableError("unsupported route generation state")
        return cls(
            schema=schema,
            route_id=normalize_route_id(_require_str(raw, "route_id")),
            generation=_require_positive_int(raw, "generation"),
            route_handle=_require_route_handle(raw, "route_handle"),
            state=state,  # type: ignore[arg-type]
            task_id=_require_str(raw, "task_id"),
            zone=_require_str(raw, "zone"),
            slot_size=_require_positive_int(raw, "slot_size"),
            slot_count=_require_positive_int(raw, "slot_count"),
            max_frame_bytes=_require_positive_int(raw, "max_frame_bytes"),
            runtime_route_dir=_require_str(raw, "runtime_route_dir"),
            ring_path=_require_str(raw, "ring_path"),
            mmap_status_path=_require_str(raw, "mmap_status_path"),
            controlfs_generation_status_path=_require_str(
                raw,
                "controlfs_generation_status_path",
            ),
            source_request_id=_require_str(raw, "source_request_id"),
            created_at=_require_str(raw, "created_at"),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "route_id": self.route_id,
            "generation": self.generation,
            "route_handle": self.route_handle,
            "state": self.state,
            "task_id": self.task_id,
            "zone": self.zone,
            "slot_size": self.slot_size,
            "slot_count": self.slot_count,
            "max_frame_bytes": self.max_frame_bytes,
            "runtime_route_dir": self.runtime_route_dir,
            "ring_path": self.ring_path,
            "mmap_status_path": self.mmap_status_path,
            "controlfs_generation_status_path": self.controlfs_generation_status_path,
            "source_request_id": self.source_request_id,
            "created_at": self.created_at,
        }


@dataclass(frozen=True, slots=True)
class RouteGenerationTable:
    """Persistent generation table for one logical route_id."""

    schema: str
    route_id: str
    active_generation: int | None
    next_generation: int
    generations: tuple[RouteGenerationRecord, ...]

    @classmethod
    def empty(cls, route_id: str) -> "RouteGenerationTable":
        return cls(
            schema=ROUTE_GENERATION_TABLE_SCHEMA,
            route_id=normalize_route_id(route_id),
            active_generation=None,
            next_generation=1,
            generations=(),
        )

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "RouteGenerationTable":
        schema = _require_str(raw, "schema")
        if schema != ROUTE_GENERATION_TABLE_SCHEMA:
            raise RouteGenerationTableError("unsupported route generation table schema")
        records_raw = raw.get("generations", [])
        if not isinstance(records_raw, list):
            raise RouteGenerationTableError("generations must be a list")
        records = tuple(RouteGenerationRecord.from_mapping(item) for item in records_raw)
        route_id = normalize_route_id(_require_str(raw, "route_id"))
        for record in records:
            if record.route_id != route_id:
                raise RouteGenerationTableError("generation record route_id mismatch")
        active_generation = _optional_positive_int(raw, "active_generation")
        next_generation = _require_positive_int(raw, "next_generation")
        if active_generation is not None and active_generation not in {record.generation for record in records}:
            raise RouteGenerationTableError("active_generation must reference an existing generation")
        if records and next_generation <= max(record.generation for record in records):
            raise RouteGenerationTableError("next_generation must be greater than existing generations")
        return cls(
            schema=schema,
            route_id=route_id,
            active_generation=active_generation,
            next_generation=next_generation,
            generations=records,
        )

    def to_mapping(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": self.schema,
            "route_id": self.route_id,
            "next_generation": self.next_generation,
            "generations": [record.to_mapping() for record in self.generations],
        }
        if self.active_generation is not None:
            payload["active_generation"] = self.active_generation
        return payload

    def record_candidate(self, record: RouteGenerationRecord) -> "RouteGenerationTable":
        if record.route_id != self.route_id:
            raise RouteGenerationTableError("candidate route_id mismatch")
        if record.state != "candidate":
            raise RouteGenerationTableError("new generation records must start as candidate")
        if record.generation != self.next_generation:
            raise RouteGenerationTableError("candidate generation must equal table next_generation")
        if record.generation in {item.generation for item in self.generations}:
            raise RouteGenerationTableError("generation already exists")
        return RouteGenerationTable(
            schema=self.schema,
            route_id=self.route_id,
            active_generation=self.active_generation,
            next_generation=record.generation + 1,
            generations=tuple((*self.generations, record)),
        )


@dataclass(frozen=True, slots=True)
class RouteGenerationCandidateResult:
    """Result of one candidate generation materialization."""

    table: RouteGenerationTable
    record: RouteGenerationRecord

    def to_mapping(self) -> dict[str, Any]:
        return {
            "table": self.table.to_mapping(),
            "record": self.record.to_mapping(),
        }


def route_generation_state_path(controlfs_root: Path | str, route_id: str) -> Path:
    """Return active/routes/<route_id>/generation_state.json."""

    return Path(controlfs_root) / "active" / "routes" / normalize_route_id(route_id) / "generation_state.json"


def route_generation_status_path(controlfs_root: Path | str, route_id: str, generation: int) -> Path:
    """Return active/routes/<route_id>/generations/gN/status.json."""

    gen = _validate_generation(generation)
    return (
        Path(controlfs_root)
        / "active"
        / "routes"
        / normalize_route_id(route_id)
        / "generations"
        / f"g{gen}"
        / "status.json"
    )


def route_handle_for_generation(route_id: str, generation: int) -> str:
    """Return the deterministic runtime handle route@gN for a generation."""

    gen = _validate_generation(generation)
    return f"{normalize_route_id(route_id)}@g{gen}"


def load_route_generation_table(controlfs_root: Path | str, route_id: str) -> RouteGenerationTable:
    """Load the persisted route generation table or return an empty table."""

    path = route_generation_state_path(controlfs_root, route_id)
    if not path.exists():
        return RouteGenerationTable.empty(route_id)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RouteGenerationTableError("route generation table JSON must be an object")
    return RouteGenerationTable.from_mapping(raw)


def write_route_generation_table(
    controlfs_root: Path | str,
    table: RouteGenerationTable,
) -> Path:
    """Persist the route generation table as deterministic JSON."""

    path = route_generation_state_path(controlfs_root, table.route_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(table.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def materialize_route_generation_candidate(
    *,
    controlfs_root: Path | str,
    runtime_root: Path | str,
    decision: RoutePrepareDecision,
) -> RouteGenerationCandidateResult:
    """Create the next mmap route generation and persist the ControlProxy table.

    The function consumes a Scheduler-authorized ControlProxy prepare decision.
    It does not resize an existing ring. It requires the decision generation to
    match the persisted table next_generation, creates route@gN/ring.bin, records
    gN as candidate, then increments the table to N+1.
    """

    _validate_decision_for_new_generation(decision)
    generation = _validate_generation(decision.next_generation)
    expected_handle = route_handle_for_generation(decision.route_id, generation)
    if decision.route_handle != expected_handle:
        raise RouteGenerationTableError("decision route_handle does not match table generation handle")
    table = load_route_generation_table(controlfs_root, decision.route_id)
    if generation != table.next_generation:
        raise RouteGenerationTableError("decision next_generation does not match table next_generation")
    ring_path = route_dir_for_handle(runtime_root, expected_handle) / "ring.bin"
    if ring_path.exists():
        raise RouteGenerationTableError("route generation ring already exists")
    route: MmapFixedSlotRoute | None = None
    try:
        route = create_mmap_route_from_decision(runtime_root, decision, replace=False)
        stats = route.stats()
        status_path = route_generation_status_path(controlfs_root, decision.route_id, generation)
        record = RouteGenerationRecord(
            schema=ROUTE_GENERATION_RECORD_SCHEMA,
            route_id=decision.route_id,
            generation=generation,
            route_handle=expected_handle,
            state="candidate",
            task_id=decision.task_id,
            zone=decision.zone,
            slot_size=stats.slot_size,
            slot_count=stats.slot_count,
            max_frame_bytes=_validate_generation(decision.max_frame_bytes, field="max_frame_bytes"),
            runtime_route_dir=str(route_dir_for_handle(runtime_root, expected_handle)),
            ring_path=stats.ring_path,
            mmap_status_path=stats.status_path,
            controlfs_generation_status_path=str(status_path),
            source_request_id=decision.request_id,
            created_at=decision.decided_at,
        )
        next_table = table.record_candidate(record)
        _write_generation_record(record)
        write_route_generation_table(controlfs_root, next_table)
        return RouteGenerationCandidateResult(table=next_table, record=record)
    finally:
        if route is not None:
            route.close()


def next_generation_for_route(controlfs_root: Path | str, route_id: str) -> int:
    """Return the next allocatable generation for a route."""

    return load_route_generation_table(controlfs_root, route_id).next_generation


def _write_generation_record(record: RouteGenerationRecord) -> None:
    path = Path(record.controlfs_generation_status_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validate_decision_for_new_generation(decision: RoutePrepareDecision) -> None:
    if decision.status != "ready":
        raise RouteGenerationTableError("only ready decisions can materialize a generation")
    if decision.action not in _CREATE_ACTIONS:
        raise RouteGenerationTableError("only create_route_generation/create_next_generation allocate generations")
    if decision.route_handle is None:
        raise RouteGenerationTableError("ready generation decision must include route_handle")
    if decision.slot_size is None or decision.slot_count is None or decision.max_frame_bytes is None:
        raise RouteGenerationTableError("ready generation decision must include sizing")
    _validate_generation(decision.next_generation)


def _validate_generation(value: int | None, *, field: str = "generation") -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise RouteGenerationTableError(f"{field} must be a positive integer")
    return value


def _require_str(raw: Mapping[str, Any], field: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value:
        raise RouteGenerationTableError(f"{field} must be a non-empty string")
    return value


def _require_positive_int(raw: Mapping[str, Any], field: str) -> int:
    value = raw.get(field)
    return _validate_generation(value, field=field)


def _optional_positive_int(raw: Mapping[str, Any], field: str) -> int | None:
    value = raw.get(field)
    if value is None:
        return None
    return _validate_generation(value, field=field)


def _require_route_handle(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if "/" in value or "\\" in value or ".." in value:
        raise RouteGenerationTableError(f"{field} must not contain path traversal")
    return value

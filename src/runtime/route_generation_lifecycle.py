"""ControlProxy route generation drain/closed lifecycle helpers.

This module implements phase 0092. It consumes the route_id ->
current_generation table introduced in 0091-r2 and adds explicit lifecycle
transitions for materialized mmap/shm-like route generations:

    candidate -> active -> draining -> closed -> cleanup closed generation

The cleanup path only removes runtime files for closed generations. It never
resizes a live mmap route, never closes an active route implicitly, and never
starts a resident loop. The caller is responsible for invoking these functions
after Scheduler/policy/zone have authorized the lifecycle action.

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
- Cleanup is limited to closed generations only.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
import shutil
from typing import Any, Literal

from runtime.controlfs_manifest import normalize_route_id
from runtime.mmap_fixed_slot_route import route_dir_for_handle
from runtime.route_generation_table import (
    GenerationState,
    RouteGenerationRecord,
    RouteGenerationTable,
    RouteGenerationTableError,
    load_route_generation_table,
    route_generation_status_path,
    write_route_generation_table,
)

ROUTE_GENERATION_CLEANUP_SCHEMA = "missipy.controlproxy.route_generation_cleanup.v1"

LifecycleAction = Literal["activate", "draining", "closed", "cleanup_closed"]


class RouteGenerationLifecycleError(RouteGenerationTableError):
    """Raised when a route generation lifecycle transition is invalid."""


@dataclass(frozen=True, slots=True)
class RouteGenerationLifecycleResult:
    """Stable result for a route generation lifecycle transition."""

    action: LifecycleAction
    table: RouteGenerationTable
    record: RouteGenerationRecord
    previous_state: GenerationState

    def to_mapping(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "previous_state": self.previous_state,
            "record": self.record.to_mapping(),
            "table": self.table.to_mapping(),
        }


@dataclass(frozen=True, slots=True)
class ClosedRouteGenerationCleanupResult:
    """Stable result for closed generation runtime cleanup."""

    schema: str
    route_id: str
    generation: int
    route_handle: str
    runtime_route_dir: str
    cleanup_status_path: str
    removed_runtime_route_dir: bool
    cleaned_at: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "route_id": self.route_id,
            "generation": self.generation,
            "route_handle": self.route_handle,
            "runtime_route_dir": self.runtime_route_dir,
            "cleanup_status_path": self.cleanup_status_path,
            "removed_runtime_route_dir": self.removed_runtime_route_dir,
            "cleaned_at": self.cleaned_at,
        }


def route_generation_cleanup_path(controlfs_root: Path | str, route_id: str, generation: int) -> Path:
    """Return active/routes/<route_id>/generations/gN/cleanup.json."""

    gen = _validate_generation(generation)
    return (
        Path(controlfs_root)
        / "active"
        / "routes"
        / normalize_route_id(route_id)
        / "generations"
        / f"g{gen}"
        / "cleanup.json"
    )


def activate_route_generation(
    *,
    controlfs_root: Path | str,
    route_id: str,
    generation: int,
) -> RouteGenerationLifecycleResult:
    """Mark one candidate route generation as active.

    This is an explicit lifecycle transition. It does not select policy and it
    does not drain an existing active generation implicitly.
    """

    table = load_route_generation_table(controlfs_root, route_id)
    record = _record_for_generation(table, generation)
    if record.state != "candidate":
        raise RouteGenerationLifecycleError("only candidate generations can become active")
    active = _active_record(table)
    if active is not None and active.generation != record.generation:
        raise RouteGenerationLifecycleError("another active generation must be drained first")
    return _transition_generation(
        controlfs_root=controlfs_root,
        table=table,
        record=record,
        next_state="active",
        active_generation=record.generation,
        action="activate",
    )


def mark_route_generation_draining(
    *,
    controlfs_root: Path | str,
    route_id: str,
    generation: int,
) -> RouteGenerationLifecycleResult:
    """Mark an active generation as draining."""

    table = load_route_generation_table(controlfs_root, route_id)
    record = _record_for_generation(table, generation)
    if record.state != "active":
        raise RouteGenerationLifecycleError("only active generations can become draining")
    return _transition_generation(
        controlfs_root=controlfs_root,
        table=table,
        record=record,
        next_state="draining",
        active_generation=None if table.active_generation == record.generation else table.active_generation,
        action="draining",
    )


def mark_route_generation_closed(
    *,
    controlfs_root: Path | str,
    route_id: str,
    generation: int,
) -> RouteGenerationLifecycleResult:
    """Mark a draining generation as closed."""

    table = load_route_generation_table(controlfs_root, route_id)
    record = _record_for_generation(table, generation)
    if record.state != "draining":
        raise RouteGenerationLifecycleError("only draining generations can become closed")
    return _transition_generation(
        controlfs_root=controlfs_root,
        table=table,
        record=record,
        next_state="closed",
        active_generation=None if table.active_generation == record.generation else table.active_generation,
        action="closed",
    )


def cleanup_closed_route_generation(
    *,
    controlfs_root: Path | str,
    runtime_root: Path | str,
    route_id: str,
    generation: int,
    cleaned_at: str = "2026-07-05T00:00:00Z",
) -> ClosedRouteGenerationCleanupResult:
    """Remove runtime files for one closed generation and write cleanup status.

    The function refuses to remove candidate, active or draining generations. It
    also verifies that the persisted runtime route directory matches the expected
    runtime_root/routes/<route_handle> directory before deletion.
    """

    table = load_route_generation_table(controlfs_root, route_id)
    record = _record_for_generation(table, generation)
    if record.state != "closed":
        raise RouteGenerationLifecycleError("cleanup is allowed for closed generations only")
    runtime_route_dir = _validated_runtime_route_dir(runtime_root, record)
    removed = False
    if runtime_route_dir.exists():
        shutil.rmtree(runtime_route_dir)
        removed = True
    result = ClosedRouteGenerationCleanupResult(
        schema=ROUTE_GENERATION_CLEANUP_SCHEMA,
        route_id=record.route_id,
        generation=record.generation,
        route_handle=record.route_handle,
        runtime_route_dir=str(runtime_route_dir),
        cleanup_status_path=str(route_generation_cleanup_path(controlfs_root, record.route_id, record.generation)),
        removed_runtime_route_dir=removed,
        cleaned_at=_validate_timestamp(cleaned_at),
    )
    _write_cleanup_result(result)
    return result


def _transition_generation(
    *,
    controlfs_root: Path | str,
    table: RouteGenerationTable,
    record: RouteGenerationRecord,
    next_state: GenerationState,
    active_generation: int | None,
    action: LifecycleAction,
) -> RouteGenerationLifecycleResult:
    updated = replace(record, state=next_state)
    next_table = _replace_record(table, updated, active_generation=active_generation)
    _write_generation_record(controlfs_root, updated)
    write_route_generation_table(controlfs_root, next_table)
    return RouteGenerationLifecycleResult(
        action=action,
        table=next_table,
        record=updated,
        previous_state=record.state,
    )


def _replace_record(
    table: RouteGenerationTable,
    record: RouteGenerationRecord,
    *,
    active_generation: int | None,
) -> RouteGenerationTable:
    generations = []
    replaced = False
    for item in table.generations:
        if item.generation == record.generation:
            generations.append(record)
            replaced = True
        else:
            generations.append(item)
    if not replaced:
        raise RouteGenerationLifecycleError("generation record not found")
    candidate = RouteGenerationTable(
        schema=table.schema,
        route_id=table.route_id,
        active_generation=active_generation,
        next_generation=table.next_generation,
        generations=tuple(generations),
    )
    return RouteGenerationTable.from_mapping(candidate.to_mapping())


def _record_for_generation(table: RouteGenerationTable, generation: int) -> RouteGenerationRecord:
    gen = _validate_generation(generation)
    for record in table.generations:
        if record.generation == gen:
            return record
    raise RouteGenerationLifecycleError("generation record not found")


def _active_record(table: RouteGenerationTable) -> RouteGenerationRecord | None:
    active_records = [record for record in table.generations if record.state == "active"]
    if len(active_records) > 1:
        raise RouteGenerationLifecycleError("route generation table has multiple active generations")
    if table.active_generation is not None:
        record = _record_for_generation(table, table.active_generation)
        if record.state != "active":
            raise RouteGenerationLifecycleError("active_generation does not reference an active generation")
        return record
    return active_records[0] if active_records else None


def _write_generation_record(controlfs_root: Path | str, record: RouteGenerationRecord) -> None:
    path = route_generation_status_path(controlfs_root, record.route_id, record.generation)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_cleanup_result(result: ClosedRouteGenerationCleanupResult) -> None:
    path = Path(result.cleanup_status_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _validated_runtime_route_dir(runtime_root: Path | str, record: RouteGenerationRecord) -> Path:
    expected = route_dir_for_handle(runtime_root, record.route_handle)
    actual = Path(record.runtime_route_dir)
    if actual.resolve(strict=False) != expected.resolve(strict=False):
        raise RouteGenerationLifecycleError("runtime route dir does not match runtime_root/route_handle")
    return expected


def _validate_generation(value: int | None) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise RouteGenerationLifecycleError("generation must be a positive integer")
    return value


def _validate_timestamp(value: str) -> str:
    if not isinstance(value, str) or "T" not in value or "Z" not in value:
        raise RouteGenerationLifecycleError("cleaned_at must look like an UTC timestamp")
    return value

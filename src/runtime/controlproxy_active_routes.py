"""ControlProxy active route materializer.

This module implements phase 0081.

It bridges the 0079-r2/r3 ControlProxy route preparation protocol with the
0080-r2 file-backed mmap fixed-slot route.

Real implementation direction:

    ControlProxy = ControlFS declarative surface + RouteProxy materializer.

The active route materializer takes:
- a ready ControlProxy RoutePrepareDecision
- the desired RouteManifest that Scheduler/ControlProxy already accepted

and writes:
- mmap runtime route files under <runtime_root>/routes/<route_handle>/
- ControlFS active route manifest under active/routes/<route_id>/manifest.json
- ControlFS active route status under active/routes/<route_id>/status.json

It deliberately does not:
- create POSIX shared memory with shm_open
- require /dev/shm
- create semaphores
- create eventfd
- create futex
- start a ControlProxy daemon
- watch ControlFS with inotify
- call Scheduler
- issue route leases
- implement lease handoff
- resize live mmap routes
- implement inter-process safety
- implement VisPy

This is an importable materialization primitive, not a CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from runtime.controlfs_manifest import RouteManifest, normalize_route_id
from runtime.controlproxy_prepare import RoutePrepareDecision
from runtime.mmap_fixed_slot_route import (
    MmapFixedSlotRoute,
    create_mmap_route_from_decision,
    route_dir_for_handle,
)
from runtime.routeproxy_reconciler import RouteProxyPlan, build_routeproxy_plan


ACTIVE_ROUTE_STATUS_SCHEMA = "missipy.controlproxy.active_route_status.v1"
ACTIVE_ROUTE_IMPLEMENTATION_STAGE = "file_backed_mmap_fixed_slot"


class ActiveRouteMaterializationError(RuntimeError):
    """Raised when a ControlProxy active route cannot be materialized."""


@dataclass(frozen=True)
class ActiveRouteRecord:
    """A materialized route record linking ControlFS active state to mmap files."""

    schema: str
    route_id: str
    route_handle: str
    task_id: str
    zone: str
    state: str
    implementation_stage: str
    runtime_route_dir: str
    ring_path: str
    mmap_status_path: str
    active_manifest_path: str
    active_status_path: str
    slot_size: int
    slot_count: int
    max_frame_bytes: int
    notify: str
    overflow_policy: str
    route_ready_at: str
    lease_state: str = "not_leased"

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "route_id": self.route_id,
            "route_handle": self.route_handle,
            "task_id": self.task_id,
            "zone": self.zone,
            "state": self.state,
            "implementation_stage": self.implementation_stage,
            "runtime_route_dir": self.runtime_route_dir,
            "ring_path": self.ring_path,
            "mmap_status_path": self.mmap_status_path,
            "active_manifest_path": self.active_manifest_path,
            "active_status_path": self.active_status_path,
            "slot_size": self.slot_size,
            "slot_count": self.slot_count,
            "max_frame_bytes": self.max_frame_bytes,
            "notify": self.notify,
            "overflow_policy": self.overflow_policy,
            "route_ready_at": self.route_ready_at,
            "lease_state": self.lease_state,
        }


def active_route_dir(controlfs_root: Path | str, route_id: str) -> Path:
    """Return ControlFS active/routes/<route_id> after route_id validation."""

    return Path(controlfs_root) / "active" / "routes" / normalize_route_id(route_id)


def active_manifest_path(controlfs_root: Path | str, route_id: str) -> Path:
    """Return ControlFS active route manifest path."""

    return active_route_dir(controlfs_root, route_id) / "manifest.json"


def active_status_path(controlfs_root: Path | str, route_id: str) -> Path:
    """Return ControlFS active route status path."""

    return active_route_dir(controlfs_root, route_id) / "status.json"


def materialize_active_route(
    *,
    controlfs_root: Path | str,
    runtime_root: Path | str,
    decision: RoutePrepareDecision,
    desired_manifest: RouteManifest,
    replace: bool = True,
    close_route: bool = True,
) -> ActiveRouteRecord:
    """Materialize a ready ControlProxy decision into mmap and ControlFS active state.

    The desired_manifest is copied into active/routes/<route_id>/manifest.json.
    This keeps existing RouteProxy dry-run reconciliation compatible: after
    materialization, desired and active route manifests can compare as noop.
    """

    if decision.status != "ready":
        raise ActiveRouteMaterializationError("only ready decisions can become active routes")
    if decision.route_handle is None:
        raise ActiveRouteMaterializationError("ready decision must have route_handle")
    if decision.route_id != desired_manifest.route_id:
        raise ActiveRouteMaterializationError("decision route_id does not match desired manifest")
    if decision.task_id != desired_manifest.task_id:
        raise ActiveRouteMaterializationError("decision task_id does not match desired manifest")
    if decision.slot_size is None or decision.slot_count is None or decision.max_frame_bytes is None:
        raise ActiveRouteMaterializationError("ready decision must include slot_size, slot_count and max_frame_bytes")
    if desired_manifest.slot_size != decision.slot_size:
        raise ActiveRouteMaterializationError("desired manifest slot_size must match ControlProxy decision")
    if desired_manifest.slot_count != decision.slot_count:
        raise ActiveRouteMaterializationError("desired manifest slot_count must match ControlProxy decision")
    if desired_manifest.max_frame_bytes != decision.max_frame_bytes:
        raise ActiveRouteMaterializationError("desired manifest max_frame_bytes must match ControlProxy decision")

    route: MmapFixedSlotRoute | None = None
    try:
        route = create_mmap_route_from_decision(runtime_root, decision, replace=replace)
        mmap_stats = route.stats()

        active_dir = active_route_dir(controlfs_root, decision.route_id)
        active_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = active_manifest_path(controlfs_root, decision.route_id)
        status_path = active_status_path(controlfs_root, decision.route_id)

        manifest_path.write_text(
            json.dumps(desired_manifest.to_mapping(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        record = ActiveRouteRecord(
            schema=ACTIVE_ROUTE_STATUS_SCHEMA,
            route_id=decision.route_id,
            route_handle=decision.route_handle,
            task_id=decision.task_id,
            zone=decision.zone,
            state="active",
            implementation_stage=ACTIVE_ROUTE_IMPLEMENTATION_STAGE,
            runtime_route_dir=str(route_dir_for_handle(runtime_root, decision.route_handle)),
            ring_path=mmap_stats.ring_path,
            mmap_status_path=mmap_stats.status_path,
            active_manifest_path=str(manifest_path),
            active_status_path=str(status_path),
            slot_size=decision.slot_size,
            slot_count=decision.slot_count,
            max_frame_bytes=decision.max_frame_bytes,
            notify=decision.notify or "none",
            overflow_policy=decision.overflow_policy or "reject",
            route_ready_at=decision.decided_at,
        )
        write_active_route_status(record)
        return record
    finally:
        if close_route and route is not None:
            route.close()


def write_active_route_status(record: ActiveRouteRecord) -> None:
    """Write ControlFS active/routes/<route_id>/status.json."""

    path = Path(record.active_status_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_mapping(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_active_route_status(path: Path | str) -> ActiveRouteRecord:
    """Load an active route status JSON file."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema") != ACTIVE_ROUTE_STATUS_SCHEMA:
        raise ActiveRouteMaterializationError("unsupported active route status schema")
    return ActiveRouteRecord(
        schema=str(raw["schema"]),
        route_id=str(raw["route_id"]),
        route_handle=str(raw["route_handle"]),
        task_id=str(raw["task_id"]),
        zone=str(raw["zone"]),
        state=str(raw["state"]),
        implementation_stage=str(raw["implementation_stage"]),
        runtime_route_dir=str(raw["runtime_route_dir"]),
        ring_path=str(raw["ring_path"]),
        mmap_status_path=str(raw["mmap_status_path"]),
        active_manifest_path=str(raw["active_manifest_path"]),
        active_status_path=str(raw["active_status_path"]),
        slot_size=int(raw["slot_size"]),
        slot_count=int(raw["slot_count"]),
        max_frame_bytes=int(raw["max_frame_bytes"]),
        notify=str(raw["notify"]),
        overflow_policy=str(raw["overflow_policy"]),
        route_ready_at=str(raw["route_ready_at"]),
        lease_state=str(raw.get("lease_state", "not_leased")),
    )


def materialize_active_routes(
    *,
    controlfs_root: Path | str,
    runtime_root: Path | str,
    pairs: Iterable[tuple[RoutePrepareDecision, RouteManifest]],
    replace: bool = True,
) -> tuple[ActiveRouteRecord, ...]:
    """Materialize several ready decisions into active route records."""

    records: list[ActiveRouteRecord] = []
    for decision, manifest in pairs:
        if decision.status == "ready":
            records.append(
                materialize_active_route(
                    controlfs_root=controlfs_root,
                    runtime_root=runtime_root,
                    decision=decision,
                    desired_manifest=manifest,
                    replace=replace,
                )
            )
    return tuple(records)


def build_post_materialization_plan(controlfs_root: Path | str) -> RouteProxyPlan:
    """Build a dry-run plan after materialization.

    Expected behavior for fully materialized desired routes: noop.
    """

    return build_routeproxy_plan(controlfs_root, include_noop=True)


def active_route_summary(records: Iterable[ActiveRouteRecord]) -> dict[str, Any]:
    """Return compact summary for tests or future views."""

    items = [record.to_mapping() for record in records]
    return {
        "active_route_count": len(items),
        "route_handles": [item["route_handle"] for item in items],
        "routes": items,
    }

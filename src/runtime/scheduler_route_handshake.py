"""Scheduler-facing route handshake.

This module implements phase 0085.

It provides importable functions that a Scheduler can call directly:

    prepare_route_for_scheduler(...)

Flow:

    tick_controlproxy()
    -> active route exists
    -> acquire route lease
    -> activate route lease
    -> publish handshake facts to event.bus/context.bus
    -> return route_handle + lease_id

This is not the Scheduler implementation. It is a Scheduler-facing handshake
primitive for the already-authorized caller.

It deliberately does not:
- create a daemon
- start a service
- use OpenRC
- run forever
- watch ControlFS
- sleep or poll
- implement the Scheduler event loop
- decide security policy
- bypass zone/scope policy
- write RouteMessage frames
- notify eventfd
- drain routes
- resize live mmap routes
- implement inter-process locks
- implement VisPy
- add a CLI

It is a synchronous function boundary, not a resident process.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from runtime.controlproxy_active_routes import active_status_path
from runtime.controlproxy_pump import ControlProxyPumpResult, tick_controlproxy
from runtime.controlproxy_route_lease import (
    RouteLease,
    RouteLeaseError,
    RouteLeaseTransitionError,
    acquire_route_lease,
    activate_route_lease,
    lease_path,
    load_route_lease,
)
from runtime.controlfs_manifest import normalize_route_id
from runtime.shm_runtime_schema import (
    CONTEXT_BUS_MESSAGE_SCHEMA,
    EVENT_BUS_MESSAGE_SCHEMA,
    ContextBusMessage,
    EventBusMessage,
)


SCHEDULER_ROUTE_HANDSHAKE_SCHEMA = "missipy.scheduler.route_handshake.v1"
SCHEDULER_ROUTE_HANDSHAKE_EVENT_SCHEMA = "missipy.scheduler.route_handshake_event.v1"
SCHEDULER_ROUTE_HANDSHAKE_CONTEXT_SCHEMA = "missipy.scheduler.route_handshake_context.v1"
DEFAULT_HANDSHAKE_AT = "2026-07-04T20:00:00Z"


class SchedulerRouteHandshakeError(RuntimeError):
    """Raised when Scheduler-facing route handshake cannot complete."""


@dataclass(frozen=True)
class SchedulerRouteHandshakeResult:
    """Return object for prepare_route_for_scheduler."""

    schema: str
    route_id: str
    route_handle: str
    task_id: str
    holder: str
    scope: str
    lease_id: str
    lease_state: str
    active_status_path: str
    lease_path: str
    ring_path: str
    mmap_status_path: str
    reused_existing_lease: bool
    pump_materialized_count: int
    pump_skipped_count: int
    pump_error_count: int
    bus_event_count: int
    bus_context_count: int
    prepared_at: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "route_id": self.route_id,
            "route_handle": self.route_handle,
            "task_id": self.task_id,
            "holder": self.holder,
            "scope": self.scope,
            "lease_id": self.lease_id,
            "lease_state": self.lease_state,
            "active_status_path": self.active_status_path,
            "lease_path": self.lease_path,
            "ring_path": self.ring_path,
            "mmap_status_path": self.mmap_status_path,
            "reused_existing_lease": self.reused_existing_lease,
            "pump_materialized_count": self.pump_materialized_count,
            "pump_skipped_count": self.pump_skipped_count,
            "pump_error_count": self.pump_error_count,
            "bus_event_count": self.bus_event_count,
            "bus_context_count": self.bus_context_count,
            "prepared_at": self.prepared_at,
        }


def prepare_route_for_scheduler(
    *,
    controlfs_root: Path | str,
    runtime_root: Path | str,
    route_id: str,
    holder: str = "scheduler",
    scope: str = "route.write",
    lease_id: str | None = None,
    ttl_seconds: int = 300,
    prepared_at: str = DEFAULT_HANDSHAKE_AT,
    activate: bool = True,
    publish_bus: bool = True,
) -> SchedulerRouteHandshakeResult:
    """Prepare a route for Scheduler use.

    This function is idempotent for the same holder/scope while the lease is
    already leased or active. A different holder/scope is rejected.

    Security policy is intentionally not decided here. The caller must already
    be the authorized Scheduler path.
    """

    safe_route_id = normalize_route_id(route_id)
    pump_result = tick_controlproxy(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        tick_id=f"tick:scheduler-handshake:{safe_route_id}",
        ticked_at=prepared_at,
        publish_bus=publish_bus,
    )
    if pump_result.error_count:
        raise SchedulerRouteHandshakeError("ControlProxy pump reported errors")

    status_path = active_status_path(controlfs_root, safe_route_id)
    if not status_path.exists():
        raise SchedulerRouteHandshakeError(f"route is not active after pump: {safe_route_id}")

    status = _load_status(status_path)
    existing = _load_existing_lease(controlfs_root, safe_route_id)
    reused = False

    if existing is None:
        lease = acquire_route_lease(
            controlfs_root=controlfs_root,
            route_id=safe_route_id,
            holder=holder,
            scope=scope,
            lease_id=lease_id,
            ttl_seconds=ttl_seconds,
            acquired_at=prepared_at,
        )
    else:
        _ensure_same_holder_scope(existing, holder=holder, scope=scope)
        if existing.state == "closed":
            raise SchedulerRouteHandshakeError("cannot reuse a closed route lease")
        lease = existing
        reused = True

    if activate:
        if lease.state == "leased":
            activate_route_lease(
                controlfs_root=controlfs_root,
                route_id=safe_route_id,
                transitioned_at=prepared_at,
            )
            lease = load_route_lease(controlfs_root, safe_route_id)
        elif lease.state == "active":
            pass
        else:
            raise RouteLeaseTransitionError(f"cannot prepare route from lease state {lease.state}")

    status = _load_status(status_path)
    result = SchedulerRouteHandshakeResult(
        schema=SCHEDULER_ROUTE_HANDSHAKE_SCHEMA,
        route_id=safe_route_id,
        route_handle=str(status["route_handle"]),
        task_id=str(status["task_id"]),
        holder=holder,
        scope=scope,
        lease_id=lease.lease_id,
        lease_state=lease.state,
        active_status_path=str(status_path),
        lease_path=str(lease_path(controlfs_root, safe_route_id)),
        ring_path=str(status["ring_path"]),
        mmap_status_path=str(status["mmap_status_path"]),
        reused_existing_lease=reused,
        pump_materialized_count=pump_result.materialized_count,
        pump_skipped_count=pump_result.skipped_count,
        pump_error_count=pump_result.error_count,
        bus_event_count=pump_result.bus_event_count,
        bus_context_count=pump_result.bus_context_count,
        prepared_at=prepared_at,
    )

    if publish_bus:
        event_count, context_count = publish_scheduler_handshake_to_bus(
            runtime_root=runtime_root,
            result=result,
            prepared_at=prepared_at,
        )
        result = SchedulerRouteHandshakeResult(
            schema=result.schema,
            route_id=result.route_id,
            route_handle=result.route_handle,
            task_id=result.task_id,
            holder=result.holder,
            scope=result.scope,
            lease_id=result.lease_id,
            lease_state=result.lease_state,
            active_status_path=result.active_status_path,
            lease_path=result.lease_path,
            ring_path=result.ring_path,
            mmap_status_path=result.mmap_status_path,
            reused_existing_lease=result.reused_existing_lease,
            pump_materialized_count=result.pump_materialized_count,
            pump_skipped_count=result.pump_skipped_count,
            pump_error_count=result.pump_error_count,
            bus_event_count=result.bus_event_count + event_count,
            bus_context_count=result.bus_context_count + context_count,
            prepared_at=result.prepared_at,
        )

    return result


def publish_scheduler_handshake_to_bus(
    *,
    runtime_root: Path | str,
    result: SchedulerRouteHandshakeResult,
    prepared_at: str = DEFAULT_HANDSHAKE_AT,
) -> tuple[int, int]:
    """Append Scheduler route handshake facts to event.bus/context.bus."""

    root = Path(runtime_root)
    root.mkdir(parents=True, exist_ok=True)
    payload = result.to_mapping()

    event = EventBusMessage.from_mapping(
        {
            "schema": EVENT_BUS_MESSAGE_SCHEMA,
            "event_id": f"evt:scheduler-route-handshake:{result.route_id}",
            "topic": "scheduler.route.handshake.ready",
            "source": "scheduler_route_handshake",
            "occurred_at": prepared_at,
            "zone": "scheduler",
            "payload_schema": SCHEDULER_ROUTE_HANDSHAKE_EVENT_SCHEMA,
            "payload": payload,
        }
    )
    context = ContextBusMessage.from_mapping(
        {
            "schema": CONTEXT_BUS_MESSAGE_SCHEMA,
            "context_id": result.task_id,
            "context_version": 1,
            "topic": "scheduler.route.lease.active",
            "source": "scheduler_route_handshake",
            "occurred_at": prepared_at,
            "zone": "scheduler",
            "payload_schema": SCHEDULER_ROUTE_HANDSHAKE_CONTEXT_SCHEMA,
            "payload": payload,
        }
    )

    _append_jsonl(root / "event.bus.jsonl", event.to_mapping())
    _append_jsonl(root / "context.bus.jsonl", context.to_mapping())
    return 1, 1


def _load_status(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    required = {"route_id", "route_handle", "task_id", "ring_path", "mmap_status_path"}
    missing = sorted(required.difference(raw))
    if missing:
        raise SchedulerRouteHandshakeError("active status missing fields: " + ", ".join(missing))
    return raw


def _load_existing_lease(controlfs_root: Path | str, route_id: str) -> RouteLease | None:
    path = lease_path(controlfs_root, route_id)
    if not path.exists():
        return None
    return load_route_lease(controlfs_root, route_id)


def _ensure_same_holder_scope(lease: RouteLease, *, holder: str, scope: str) -> None:
    if lease.holder != holder or lease.scope != scope:
        raise SchedulerRouteHandshakeError(
            "route already leased by different holder/scope: "
            f"{lease.holder}/{lease.scope}"
        )


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(row), sort_keys=True, separators=(",", ":")))
        handle.write("\n")

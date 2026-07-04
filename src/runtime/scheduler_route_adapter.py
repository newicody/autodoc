"""Scheduler route adapter.

This module implements phase 0086.

It is the minimal adapter boundary between an already-authorized Scheduler route
request and the Scheduler-facing route handshake from 0085.

Flow:

    SchedulerRouteRequest
    -> verify authorized=True and policy_decision_id exists
    -> prepare_route_for_scheduler(...)
    -> SchedulerRouteReply
    -> publish adapter facts to event.bus/context.bus

This adapter is for the existing Scheduler boundary, but it is not the Scheduler
loop itself.

Compatibility rule phrase: not the Scheduler loop itself.

It deliberately does not:
- create a daemon
- start a service
- use OpenRC
- run forever
- watch ControlFS
- sleep or poll
- implement the Scheduler event loop
- implement PriorityQueue
- implement Dispatcher
- call PolicyEngine
- decide security policy
- bypass zone/scope policy
- generate desired manifests
- write RouteMessage frames
- notify eventfd
- drain routes
- resize live mmap routes
- implement inter-process locks
- implement VisPy
- add a CLI

No CLI.
It is a synchronous adapter function, not a resident process.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from runtime.controlfs_manifest import normalize_route_id
from runtime.scheduler_route_handshake import (
    DEFAULT_HANDSHAKE_AT,
    SCHEDULER_ROUTE_HANDSHAKE_SCHEMA,
    SchedulerRouteHandshakeResult,
    prepare_route_for_scheduler,
)
from runtime.shm_runtime_schema import (
    CONTEXT_BUS_MESSAGE_SCHEMA,
    EVENT_BUS_MESSAGE_SCHEMA,
    ContextBusMessage,
    EventBusMessage,
)


SCHEDULER_ROUTE_REQUEST_SCHEMA = "missipy.scheduler.route_adapter_request.v1"
SCHEDULER_ROUTE_REPLY_SCHEMA = "missipy.scheduler.route_adapter_reply.v1"
SCHEDULER_ROUTE_ADAPTER_EVENT_SCHEMA = "missipy.scheduler.route_adapter_event.v1"
SCHEDULER_ROUTE_ADAPTER_CONTEXT_SCHEMA = "missipy.scheduler.route_adapter_context.v1"


class SchedulerRouteAdapterError(RuntimeError):
    """Raised when a Scheduler route adapter request is invalid."""


@dataclass(frozen=True)
class SchedulerRouteRequest:
    """Already-authorized route request from the Scheduler boundary."""

    schema: str
    request_id: str
    route_id: str
    task_id: str
    holder: str
    scope: str
    authorized: bool
    policy_decision_id: str
    ttl_seconds: int
    activate: bool
    requested_at: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "SchedulerRouteRequest":
        if raw.get("schema") != SCHEDULER_ROUTE_REQUEST_SCHEMA:
            raise SchedulerRouteAdapterError("unsupported Scheduler route request schema")
        request = cls(
            schema=str(raw["schema"]),
            request_id=_require_id(raw, "request_id"),
            route_id=normalize_route_id(_require_str(raw, "route_id")),
            task_id=_require_id(raw, "task_id"),
            holder=_require_id(raw, "holder"),
            scope=_require_scope(raw, "scope"),
            authorized=_require_bool(raw, "authorized"),
            policy_decision_id=_require_id(raw, "policy_decision_id"),
            ttl_seconds=_require_positive_int(raw, "ttl_seconds"),
            activate=_require_bool(raw, "activate"),
            requested_at=_require_timestamp(raw, "requested_at"),
        )
        if not request.authorized:
            raise SchedulerRouteAdapterError("Scheduler route request must already be authorized")
        return request

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "request_id": self.request_id,
            "route_id": self.route_id,
            "task_id": self.task_id,
            "holder": self.holder,
            "scope": self.scope,
            "authorized": self.authorized,
            "policy_decision_id": self.policy_decision_id,
            "ttl_seconds": self.ttl_seconds,
            "activate": self.activate,
            "requested_at": self.requested_at,
        }


@dataclass(frozen=True)
class SchedulerRouteReply:
    """Typed reply returned to the Scheduler boundary."""

    schema: str
    request_id: str
    status: str
    route_id: str
    route_handle: str
    task_id: str
    holder: str
    scope: str
    lease_id: str
    lease_state: str
    policy_decision_id: str
    ring_path: str
    mmap_status_path: str
    active_status_path: str
    lease_path: str
    reused_existing_lease: bool
    bus_event_count: int
    bus_context_count: int
    replied_at: str

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "request_id": self.request_id,
            "status": self.status,
            "route_id": self.route_id,
            "route_handle": self.route_handle,
            "task_id": self.task_id,
            "holder": self.holder,
            "scope": self.scope,
            "lease_id": self.lease_id,
            "lease_state": self.lease_state,
            "policy_decision_id": self.policy_decision_id,
            "ring_path": self.ring_path,
            "mmap_status_path": self.mmap_status_path,
            "active_status_path": self.active_status_path,
            "lease_path": self.lease_path,
            "reused_existing_lease": self.reused_existing_lease,
            "bus_event_count": self.bus_event_count,
            "bus_context_count": self.bus_context_count,
            "replied_at": self.replied_at,
        }


def handle_scheduler_route_request(
    *,
    controlfs_root: Path | str,
    runtime_root: Path | str,
    request: SchedulerRouteRequest | Mapping[str, Any],
    publish_bus: bool = True,
) -> SchedulerRouteReply:
    """Handle one already-authorized Scheduler route request.

    This function is the adapter seam for the existing Scheduler boundary.
    It calls prepare_route_for_scheduler() but does not implement the Scheduler
    loop, queue, dispatcher or policy decision.
    """

    parsed = request if isinstance(request, SchedulerRouteRequest) else SchedulerRouteRequest.from_mapping(request)
    handshake = prepare_route_for_scheduler(
        controlfs_root=controlfs_root,
        runtime_root=runtime_root,
        route_id=parsed.route_id,
        holder=parsed.holder,
        scope=parsed.scope,
        ttl_seconds=parsed.ttl_seconds,
        prepared_at=parsed.requested_at,
        activate=parsed.activate,
        publish_bus=publish_bus,
    )
    _ensure_handshake_matches_request(parsed, handshake)

    reply = SchedulerRouteReply(
        schema=SCHEDULER_ROUTE_REPLY_SCHEMA,
        request_id=parsed.request_id,
        status="ready",
        route_id=handshake.route_id,
        route_handle=handshake.route_handle,
        task_id=handshake.task_id,
        holder=handshake.holder,
        scope=handshake.scope,
        lease_id=handshake.lease_id,
        lease_state=handshake.lease_state,
        policy_decision_id=parsed.policy_decision_id,
        ring_path=handshake.ring_path,
        mmap_status_path=handshake.mmap_status_path,
        active_status_path=handshake.active_status_path,
        lease_path=handshake.lease_path,
        reused_existing_lease=handshake.reused_existing_lease,
        bus_event_count=handshake.bus_event_count,
        bus_context_count=handshake.bus_context_count,
        replied_at=parsed.requested_at,
    )

    if publish_bus:
        event_count, context_count = publish_scheduler_adapter_reply_to_bus(
            runtime_root=runtime_root,
            request=parsed,
            reply=reply,
        )
        reply = SchedulerRouteReply(
            schema=reply.schema,
            request_id=reply.request_id,
            status=reply.status,
            route_id=reply.route_id,
            route_handle=reply.route_handle,
            task_id=reply.task_id,
            holder=reply.holder,
            scope=reply.scope,
            lease_id=reply.lease_id,
            lease_state=reply.lease_state,
            policy_decision_id=reply.policy_decision_id,
            ring_path=reply.ring_path,
            mmap_status_path=reply.mmap_status_path,
            active_status_path=reply.active_status_path,
            lease_path=reply.lease_path,
            reused_existing_lease=reply.reused_existing_lease,
            bus_event_count=reply.bus_event_count + event_count,
            bus_context_count=reply.bus_context_count + context_count,
            replied_at=reply.replied_at,
        )

    return reply


def publish_scheduler_adapter_reply_to_bus(
    *,
    runtime_root: Path | str,
    request: SchedulerRouteRequest,
    reply: SchedulerRouteReply,
) -> tuple[int, int]:
    """Publish Scheduler adapter facts to event.bus/context.bus."""

    root = Path(runtime_root)
    root.mkdir(parents=True, exist_ok=True)
    payload = {
        "request": request.to_mapping(),
        "reply": reply.to_mapping(),
    }

    event = EventBusMessage.from_mapping(
        {
            "schema": EVENT_BUS_MESSAGE_SCHEMA,
            "event_id": f"evt:scheduler-route-adapter:{request.request_id}",
            "topic": "scheduler.route.adapter.ready",
            "source": "scheduler_route_adapter",
            "occurred_at": request.requested_at,
            "zone": "scheduler",
            "payload_schema": SCHEDULER_ROUTE_ADAPTER_EVENT_SCHEMA,
            "payload": payload,
        }
    )
    context = ContextBusMessage.from_mapping(
        {
            "schema": CONTEXT_BUS_MESSAGE_SCHEMA,
            "context_id": request.task_id,
            "context_version": 1,
            "topic": "scheduler.route.adapter.reply",
            "source": "scheduler_route_adapter",
            "occurred_at": request.requested_at,
            "zone": "scheduler",
            "payload_schema": SCHEDULER_ROUTE_ADAPTER_CONTEXT_SCHEMA,
            "payload": payload,
        }
    )

    _append_jsonl(root / "event.bus.jsonl", event.to_mapping())
    _append_jsonl(root / "context.bus.jsonl", context.to_mapping())
    return 1, 1


def scheduler_route_request_mapping(
    *,
    request_id: str,
    route_id: str,
    task_id: str,
    holder: str = "scheduler",
    scope: str = "route.write",
    policy_decision_id: str,
    ttl_seconds: int = 300,
    activate: bool = True,
    requested_at: str = DEFAULT_HANDSHAKE_AT,
) -> dict[str, Any]:
    """Convenience constructor for tests and future Scheduler integration."""

    return {
        "schema": SCHEDULER_ROUTE_REQUEST_SCHEMA,
        "request_id": request_id,
        "route_id": route_id,
        "task_id": task_id,
        "holder": holder,
        "scope": scope,
        "authorized": True,
        "policy_decision_id": policy_decision_id,
        "ttl_seconds": ttl_seconds,
        "activate": activate,
        "requested_at": requested_at,
    }


def _ensure_handshake_matches_request(
    request: SchedulerRouteRequest,
    handshake: SchedulerRouteHandshakeResult,
) -> None:
    if handshake.schema != SCHEDULER_ROUTE_HANDSHAKE_SCHEMA:
        raise SchedulerRouteAdapterError("unexpected handshake schema")
    if handshake.route_id != request.route_id:
        raise SchedulerRouteAdapterError("handshake route_id does not match request")
    if handshake.task_id != request.task_id:
        raise SchedulerRouteAdapterError("handshake task_id does not match request")
    if handshake.holder != request.holder:
        raise SchedulerRouteAdapterError("handshake holder does not match request")
    if handshake.scope != request.scope:
        raise SchedulerRouteAdapterError("handshake scope does not match request")


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(row), sort_keys=True, separators=(",", ":")))
        handle.write("\n")


def _require_str(raw: Mapping[str, Any], field: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value:
        raise SchedulerRouteAdapterError(f"{field} must be a non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise SchedulerRouteAdapterError(f"{field} must not contain path traversal")
    return value


def _require_id(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if not value.replace("_", "").replace(".", "").replace(":", "").replace("-", "").isalnum():
        raise SchedulerRouteAdapterError(f"{field} contains invalid characters")
    return value


def _require_scope(raw: Mapping[str, Any], field: str) -> str:
    value = _require_id(raw, field)
    if "." not in value:
        raise SchedulerRouteAdapterError(f"{field} should use subsystem.permission form")
    return value


def _require_bool(raw: Mapping[str, Any], field: str) -> bool:
    value = raw.get(field)
    if not isinstance(value, bool):
        raise SchedulerRouteAdapterError(f"{field} must be a boolean")
    return value


def _require_positive_int(raw: Mapping[str, Any], field: str) -> int:
    value = raw.get(field)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise SchedulerRouteAdapterError(f"{field} must be a positive integer")
    return value


def _require_timestamp(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if "T" not in value or "Z" not in value:
        raise SchedulerRouteAdapterError(f"{field} must look like a UTC timestamp")
    return value

"""ControlProxy route prepare handshake and bus projection.

This module implements 0079-r2.

Architecture vocabulary:

    ControlProxy = ControlFS declarative state + RouteProxy materializer.

This module deliberately does not:
- create shared memory
- implement mmap
- resize a live mmap ring
- create semaphores
- create eventfd/futex
- start a daemon
- watch ControlFS with inotify
- mutate active routes
- call Scheduler
- implement VisPy

It locks the protocol:

    Scheduler receives a short prepare frame with required_frame_bytes.
    Scheduler validates and writes/intends a ControlFS route request.
    ControlProxy applies zone policy and sizing classes.
    ControlProxy publishes ready/denied state on event.bus/context.bus.
    Scheduler can then answer the producer, which sends the full RouteMessage.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Sequence

from runtime.controlfs_manifest import RouteManifest, normalize_route_id
from runtime.route_frame_codec import encode_route_message_frame
from runtime.shm_runtime_schema import (
    CONTEXT_BUS_MESSAGE_SCHEMA,
    EVENT_BUS_MESSAGE_SCHEMA,
    ROUTE_MESSAGE_SCHEMA,
    ContextBusMessage,
    EventBusMessage,
    RouteMessage,
)


ROUTE_PREPARE_REQUEST_SCHEMA = "missipy.controlproxy.route_prepare_request.v1"
ROUTE_PREPARE_STATUS_SCHEMA = "missipy.controlproxy.route_prepare_status.v1"
ROUTE_PREPARE_EVENT_SCHEMA = "missipy.controlproxy.route_prepare_event.v1"
ROUTE_PREPARE_CONTEXT_SCHEMA = "missipy.controlproxy.route_prepare_context.v1"

DEFAULT_SLOT_CLASSES = (512, 1024, 2048, 4096, 8192, 16384, 32768, 65536)
DEFAULT_OCCURRED_AT = "2026-07-04T20:00:00Z"

PrepareAction = Literal["reuse_active", "create_route_generation", "create_next_generation", "deny"]
PrepareStatus = Literal["ready", "denied"]


class ControlProxyPrepareError(ValueError):
    """Raised when a ControlProxy prepare object is invalid."""


@dataclass(frozen=True)
class RoutePrepareRequest:
    """Short pre-frame sent before the full route payload."""

    schema: str
    request_id: str
    route_id: str
    task_id: str
    zone: str
    scope: str
    producer: str
    consumer: str
    required_frame_bytes: int
    message_schema: str
    payload_kind: str
    ttl_seconds: int
    requested_by: str
    requested_at: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "RoutePrepareRequest":
        required = {
            "schema",
            "request_id",
            "route_id",
            "task_id",
            "zone",
            "scope",
            "producer",
            "consumer",
            "required_frame_bytes",
            "message_schema",
            "payload_kind",
            "ttl_seconds",
            "requested_by",
            "requested_at",
        }
        missing = sorted(required.difference(raw))
        if missing:
            raise ControlProxyPrepareError("prepare request missing fields: " + ", ".join(missing))

        schema = _require_str(raw, "schema")
        if schema != ROUTE_PREPARE_REQUEST_SCHEMA:
            raise ControlProxyPrepareError(f"unsupported prepare request schema: {schema!r}")

        return cls(
            schema=schema,
            request_id=_require_id(raw, "request_id"),
            route_id=normalize_route_id(_require_str(raw, "route_id")),
            task_id=_require_id(raw, "task_id"),
            zone=_require_id(raw, "zone"),
            scope=_require_scope(raw, "scope"),
            producer=_require_id(raw, "producer"),
            consumer=_require_id(raw, "consumer"),
            required_frame_bytes=_require_positive_int(raw, "required_frame_bytes"),
            message_schema=_require_missipy_schema(raw, "message_schema"),
            payload_kind=_require_id(raw, "payload_kind"),
            ttl_seconds=_require_positive_int(raw, "ttl_seconds"),
            requested_by=_require_id(raw, "requested_by"),
            requested_at=_require_timestamp(raw, "requested_at"),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "request_id": self.request_id,
            "route_id": self.route_id,
            "task_id": self.task_id,
            "zone": self.zone,
            "scope": self.scope,
            "producer": self.producer,
            "consumer": self.consumer,
            "required_frame_bytes": self.required_frame_bytes,
            "message_schema": self.message_schema,
            "payload_kind": self.payload_kind,
            "ttl_seconds": self.ttl_seconds,
            "requested_by": self.requested_by,
            "requested_at": self.requested_at,
        }


@dataclass(frozen=True)
class ControlProxyZonePolicy:
    """Sizing and timing policy for a zone."""

    zone: str
    max_slot_size: int = 65536
    default_slot_count: int = 16
    max_ring_bytes: int = 1024 * 1024
    max_prepare_ms: int = 25
    drain_timeout_ms: int = 100
    lease_switch_timeout_ms: int = 10
    notify: str = "semaphore"
    overflow_policy: str = "reject"
    headroom_bytes: int = 256

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "ControlProxyZonePolicy":
        return cls(
            zone=_require_id(raw, "zone"),
            max_slot_size=_optional_positive_int(raw, "max_slot_size", 65536),
            default_slot_count=_optional_positive_int(raw, "default_slot_count", 16),
            max_ring_bytes=_optional_positive_int(raw, "max_ring_bytes", 1024 * 1024),
            max_prepare_ms=_optional_positive_int(raw, "max_prepare_ms", 25),
            drain_timeout_ms=_optional_positive_int(raw, "drain_timeout_ms", 100),
            lease_switch_timeout_ms=_optional_positive_int(raw, "lease_switch_timeout_ms", 10),
            notify=_optional_id(raw, "notify", "semaphore"),
            overflow_policy=_optional_id(raw, "overflow_policy", "reject"),
            headroom_bytes=_optional_non_negative_int(raw, "headroom_bytes", 256),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "zone": self.zone,
            "max_slot_size": self.max_slot_size,
            "default_slot_count": self.default_slot_count,
            "max_ring_bytes": self.max_ring_bytes,
            "max_prepare_ms": self.max_prepare_ms,
            "drain_timeout_ms": self.drain_timeout_ms,
            "lease_switch_timeout_ms": self.lease_switch_timeout_ms,
            "notify": self.notify,
            "overflow_policy": self.overflow_policy,
            "headroom_bytes": self.headroom_bytes,
        }


@dataclass(frozen=True)
class RoutePrepareDecision:
    """ControlProxy decision after applying zone policy to a prepare request."""

    schema: str
    request_id: str
    route_id: str
    route_handle: str | None
    task_id: str
    zone: str
    status: PrepareStatus
    action: PrepareAction
    reason: str
    required_frame_bytes: int
    current_generation: int | None
    next_generation: int | None
    current_slot_size: int | None
    slot_size: int | None
    slot_count: int | None
    max_frame_bytes: int | None
    max_ring_bytes: int
    max_prepare_ms: int
    drain_timeout_ms: int
    lease_switch_timeout_ms: int
    notify: str | None
    overflow_policy: str | None
    decided_at: str

    def to_mapping(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": self.schema,
            "request_id": self.request_id,
            "route_id": self.route_id,
            "task_id": self.task_id,
            "zone": self.zone,
            "status": self.status,
            "action": self.action,
            "reason": self.reason,
            "required_frame_bytes": self.required_frame_bytes,
            "max_ring_bytes": self.max_ring_bytes,
            "max_prepare_ms": self.max_prepare_ms,
            "drain_timeout_ms": self.drain_timeout_ms,
            "lease_switch_timeout_ms": self.lease_switch_timeout_ms,
            "decided_at": self.decided_at,
        }
        for key, value in {
            "route_handle": self.route_handle,
            "current_generation": self.current_generation,
            "next_generation": self.next_generation,
            "current_slot_size": self.current_slot_size,
            "slot_size": self.slot_size,
            "slot_count": self.slot_count,
            "max_frame_bytes": self.max_frame_bytes,
            "notify": self.notify,
            "overflow_policy": self.overflow_policy,
        }.items():
            if value is not None:
                payload[key] = value
        return payload


def default_zone_policies() -> dict[str, ControlProxyZonePolicy]:
    """Return conservative default policies for local runtime zones."""

    return {
        "workers": ControlProxyZonePolicy(zone="workers", max_slot_size=65536, default_slot_count=16),
        "context": ControlProxyZonePolicy(zone="context", max_slot_size=65536, default_slot_count=16),
        "scheduler": ControlProxyZonePolicy(zone="scheduler", max_slot_size=32768, default_slot_count=16),
        "ui": ControlProxyZonePolicy(zone="ui", max_slot_size=16384, default_slot_count=8),
        "audit": ControlProxyZonePolicy(zone="audit", max_slot_size=32768, default_slot_count=16),
    }


def choose_slot_size(
    required_frame_bytes: int,
    *,
    headroom_bytes: int = 256,
    slot_classes: Sequence[int] = DEFAULT_SLOT_CLASSES,
) -> int:
    """Choose the smallest slot class that can carry required_frame_bytes."""

    if required_frame_bytes < 1:
        raise ControlProxyPrepareError("required_frame_bytes must be positive")
    required = required_frame_bytes + headroom_bytes
    for slot_size in slot_classes:
        if required <= slot_size:
            return slot_size
    return required


def route_prepare_request_from_message(
    message: RouteMessage | Mapping[str, Any],
    *,
    task_id: str,
    zone: str,
    scope: str,
    requested_by: str = "scheduler",
    requested_at: str = DEFAULT_OCCURRED_AT,
    ttl_seconds: int = 300,
) -> RoutePrepareRequest:
    """Build a short prepare request by measuring the encoded full message."""

    parsed = message if isinstance(message, RouteMessage) else RouteMessage.from_mapping(message)
    frame_size = len(encode_route_message_frame(parsed))
    return RoutePrepareRequest.from_mapping(
        {
            "schema": ROUTE_PREPARE_REQUEST_SCHEMA,
            "request_id": f"prep:{parsed.message_id}",
            "route_id": parsed.route_id,
            "task_id": task_id,
            "zone": zone,
            "scope": scope,
            "producer": parsed.source,
            "consumer": parsed.target,
            "required_frame_bytes": frame_size,
            "message_schema": ROUTE_MESSAGE_SCHEMA,
            "payload_kind": parsed.kind,
            "ttl_seconds": ttl_seconds,
            "requested_by": requested_by,
            "requested_at": requested_at,
        }
    )


def decide_route_prepare(
    request: RoutePrepareRequest,
    *,
    active_manifest: RouteManifest | None = None,
    zone_policies: Mapping[str, ControlProxyZonePolicy] | None = None,
    decided_at: str = DEFAULT_OCCURRED_AT,
) -> RoutePrepareDecision:
    """Apply zone policy and decide route readiness."""

    policies = zone_policies or default_zone_policies()
    policy = policies.get(request.zone)
    if policy is None:
        return _denied(request, reason=f"zone {request.zone!r} has no ControlProxy policy", decided_at=decided_at)

    if request.required_frame_bytes > policy.max_slot_size:
        return _denied(
            request,
            reason="required_frame_bytes exceeds zone max_slot_size",
            policy=policy,
            decided_at=decided_at,
        )

    slot_size = choose_slot_size(
        request.required_frame_bytes,
        headroom_bytes=policy.headroom_bytes,
    )
    if slot_size > policy.max_slot_size:
        return _denied(
            request,
            reason="chosen slot_size exceeds zone max_slot_size",
            policy=policy,
            decided_at=decided_at,
        )

    ring_bytes = slot_size * policy.default_slot_count
    if ring_bytes > policy.max_ring_bytes:
        return _denied(
            request,
            reason="ring byte budget exceeds zone max_ring_bytes",
            policy=policy,
            slot_size=slot_size,
            decided_at=decided_at,
        )

    current_generation = 1 if active_manifest is not None else None
    current_slot_size = active_manifest.slot_size if active_manifest is not None else None

    if active_manifest is not None and (active_manifest.slot_size or 0) >= request.required_frame_bytes:
        action: PrepareAction = "reuse_active"
        next_generation = current_generation
        reason = "active route can carry required frame"
    elif active_manifest is None:
        action = "create_route_generation"
        next_generation = 1
        reason = "no active route exists; create first generation"
    else:
        action = "create_next_generation"
        next_generation = (current_generation or 1) + 1
        reason = "active route too small; create next route generation"

    route_handle = f"{request.route_id}@g{next_generation}"

    return RoutePrepareDecision(
        schema=ROUTE_PREPARE_STATUS_SCHEMA,
        request_id=request.request_id,
        route_id=request.route_id,
        route_handle=route_handle,
        task_id=request.task_id,
        zone=request.zone,
        status="ready",
        action=action,
        reason=reason,
        required_frame_bytes=request.required_frame_bytes,
        current_generation=current_generation,
        next_generation=next_generation,
        current_slot_size=current_slot_size,
        slot_size=slot_size,
        slot_count=policy.default_slot_count,
        max_frame_bytes=slot_size,
        max_ring_bytes=policy.max_ring_bytes,
        max_prepare_ms=policy.max_prepare_ms,
        drain_timeout_ms=policy.drain_timeout_ms,
        lease_switch_timeout_ms=policy.lease_switch_timeout_ms,
        notify=policy.notify,
        overflow_policy=policy.overflow_policy,
        decided_at=decided_at,
    )


def controlproxy_decision_to_event(decision: RoutePrepareDecision) -> EventBusMessage:
    """Project a ControlProxy decision to event.bus for Recorder and VisPy."""

    topic = "controlproxy.route.ready" if decision.status == "ready" else "controlproxy.route.denied"
    return EventBusMessage.from_mapping(
        {
            "schema": EVENT_BUS_MESSAGE_SCHEMA,
            "event_id": f"evt:{decision.request_id}",
            "topic": topic,
            "source": "controlproxy",
            "occurred_at": decision.decided_at,
            "zone": "control",
            "payload_schema": ROUTE_PREPARE_EVENT_SCHEMA,
            "payload": decision.to_mapping(),
        }
    )


def controlproxy_decision_to_context(decision: RoutePrepareDecision) -> ContextBusMessage:
    """Project a ControlProxy decision to context.bus for live state views."""

    return ContextBusMessage.from_mapping(
        {
            "schema": CONTEXT_BUS_MESSAGE_SCHEMA,
            "context_id": decision.task_id,
            "context_version": decision.next_generation or 1,
            "topic": "controlproxy.route.state",
            "source": "controlproxy",
            "occurred_at": decision.decided_at,
            "zone": "control",
            "payload_schema": ROUTE_PREPARE_CONTEXT_SCHEMA,
            "payload": decision.to_mapping(),
        }
    )


def write_controlproxy_decisions_to_fake_bus(
    runtime_root: Path | str,
    decisions: Iterable[RoutePrepareDecision],
    *,
    append: bool = True,
) -> dict[str, int]:
    """Write ControlProxy state to fake event.bus/context.bus JSONL files."""

    root = Path(runtime_root)
    root.mkdir(parents=True, exist_ok=True)
    decision_items = tuple(decisions)
    event_items = [controlproxy_decision_to_event(decision) for decision in decision_items]
    context_items = [controlproxy_decision_to_context(decision) for decision in decision_items]

    _write_jsonl(root / "event.bus.jsonl", (item.to_mapping() for item in event_items), append=append)
    _write_jsonl(root / "context.bus.jsonl", (item.to_mapping() for item in context_items), append=append)

    return {
        "decision_count": len(decision_items),
        "event_count": len(event_items),
        "context_count": len(context_items),
    }


def _denied(
    request: RoutePrepareRequest,
    *,
    reason: str,
    policy: ControlProxyZonePolicy | None = None,
    slot_size: int | None = None,
    decided_at: str,
) -> RoutePrepareDecision:
    max_ring_bytes = policy.max_ring_bytes if policy is not None else 0
    max_prepare_ms = policy.max_prepare_ms if policy is not None else 1
    drain_timeout_ms = policy.drain_timeout_ms if policy is not None else 1
    lease_switch_timeout_ms = policy.lease_switch_timeout_ms if policy is not None else 1
    return RoutePrepareDecision(
        schema=ROUTE_PREPARE_STATUS_SCHEMA,
        request_id=request.request_id,
        route_id=request.route_id,
        route_handle=None,
        task_id=request.task_id,
        zone=request.zone,
        status="denied",
        action="deny",
        reason=reason,
        required_frame_bytes=request.required_frame_bytes,
        current_generation=None,
        next_generation=None,
        current_slot_size=None,
        slot_size=slot_size,
        slot_count=policy.default_slot_count if policy is not None else None,
        max_frame_bytes=slot_size,
        max_ring_bytes=max_ring_bytes,
        max_prepare_ms=max_prepare_ms,
        drain_timeout_ms=drain_timeout_ms,
        lease_switch_timeout_ms=lease_switch_timeout_ms,
        notify=policy.notify if policy is not None else None,
        overflow_policy=policy.overflow_policy if policy is not None else None,
        decided_at=decided_at,
    )


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]], *, append: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append and path.exists() else "w"
    with path.open(mode, encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def _require_str(raw: Mapping[str, Any], field: str) -> str:
    value = raw[field]
    if not isinstance(value, str) or not value:
        raise ControlProxyPrepareError(f"{field} must be a non-empty string")
    if "/" in value or "\\" in value or ".." in value:
        raise ControlProxyPrepareError(f"{field} must not contain path traversal")
    return value


def _optional_str(raw: Mapping[str, Any], field: str) -> str | None:
    value = raw.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ControlProxyPrepareError(f"{field} must be a string")
    return value


def _require_id(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if not value.replace("_", "").replace(".", "").replace(":", "").replace("-", "").isalnum():
        raise ControlProxyPrepareError(f"{field} contains invalid characters")
    return value


def _optional_id(raw: Mapping[str, Any], field: str, default: str) -> str:
    if field not in raw or raw[field] is None:
        return default
    return _require_id(raw, field)


def _require_scope(raw: Mapping[str, Any], field: str) -> str:
    value = _require_id(raw, field)
    if "." not in value:
        raise ControlProxyPrepareError(f"{field} should use subsystem.permission form")
    return value


def _require_missipy_schema(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if not value.startswith("missipy."):
        raise ControlProxyPrepareError(f"{field} must start with missipy.")
    return value


def _require_timestamp(raw: Mapping[str, Any], field: str) -> str:
    value = _require_str(raw, field)
    if "T" not in value or "Z" not in value:
        raise ControlProxyPrepareError(f"{field} must look like an UTC timestamp")
    return value


def _require_positive_int(raw: Mapping[str, Any], field: str) -> int:
    value = raw[field]
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ControlProxyPrepareError(f"{field} must be a positive integer")
    return value


def _optional_positive_int(raw: Mapping[str, Any], field: str, default: int) -> int:
    if field not in raw or raw[field] is None:
        return default
    return _require_positive_int(raw, field)


def _optional_non_negative_int(raw: Mapping[str, Any], field: str, default: int) -> int:
    if field not in raw or raw[field] is None:
        return default
    value = raw[field]
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ControlProxyPrepareError(f"{field} must be a non-negative integer")
    return value


def _optional_int(raw: Mapping[str, Any], field: str) -> int | None:
    value = raw.get(field)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ControlProxyPrepareError(f"{field} must be an integer")
    return value

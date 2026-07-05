"""Thin ControlProxy Scheduler handler binding for RouteRuntimeManager.

Phase 0104 wires the already-existing Dispatcher handler injection point to the
RouteRuntimeManager introduced in 0103. The binding is intentionally narrow:

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher or PolicyEngine modification.
- Dispatcher remains EventType -> Handler only.
- Handler remains an adapter thin enough to call RouteRuntimeManager.
- RouteRuntimeManager owns route runtime work.
- ControlProxy does not manage global priorities.
- ControlProxy does not decide policy or zone authority.
- No EventBus creation and no bus duplication.
- Route mmap/eventfd is a data plane, not EventBus.
- Specialist branch owns business logic.

The Scheduler-facing payload must already carry the policy/zone dispatch filter
fields from 0098 and a RoutePrepareDecision from the prepare path. This module
only validates that the envelope and decision agree, then delegates the runtime
effect to RouteRuntimeManager.handle_prepare_decision().
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from runtime.controlproxy_prepare import (
    ROUTE_PREPARE_STATUS_SCHEMA,
    RoutePrepareDecision,
)
from runtime.route_dispatch_filter_envelope import (
    RouteDispatchFilterEnvelope,
    require_route_dispatch_filter_envelope,
)
from runtime.route_runtime_manager import (
    RouteRuntimeManager,
    RouteRuntimeManagerResult,
)

RouteRuntimeRequestHandler = Callable[[object], RouteRuntimeManagerResult]


class ControlProxyRouteRuntimeHandlerError(ValueError):
    """Raised when a Scheduler route payload cannot be delegated safely."""


@dataclass(frozen=True, slots=True)
class ControlProxyRouteRuntimeHandlerRequest:
    """Validated Scheduler payload for the ControlProxy runtime route handler."""

    envelope: RouteDispatchFilterEnvelope
    decision: RoutePrepareDecision
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.envelope.route_id != self.decision.route_id:
            raise ControlProxyRouteRuntimeHandlerError(
                "dispatch envelope route_id must match route prepare decision"
            )
        if self.envelope.zone != self.decision.zone:
            raise ControlProxyRouteRuntimeHandlerError(
                "dispatch envelope zone must match route prepare decision"
            )
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @classmethod
    def from_payload(cls, payload: object) -> "ControlProxyRouteRuntimeHandlerRequest":
        """Build a validated runtime-handler request from a Scheduler payload."""

        envelope = require_route_dispatch_filter_envelope(payload)
        decision_payload = _read_field(payload, "decision")
        if decision_payload is None:
            raise ControlProxyRouteRuntimeHandlerError(
                "route runtime handler payload requires a decision field"
            )
        decision = route_prepare_decision_from_payload(decision_payload)
        return cls(
            envelope=envelope,
            decision=decision,
            metadata=_read_mapping_field(payload, "metadata"),
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "envelope": self.envelope.to_mapping(),
            "decision": self.decision.to_mapping(),
            "metadata": dict(self.metadata),
            "purpose": "thin Handler adapter to RouteRuntimeManager",
        }


def build_controlproxy_route_runtime_request_handler(
    manager: RouteRuntimeManager,
) -> RouteRuntimeRequestHandler:
    """Return the callable injected into ControlProxySchedulerRouteRequestHandler.

    The returned callable is the official 0104 bridge:

    Dispatcher -> ControlProxySchedulerRouteRequestHandler -> this callable ->
    RouteRuntimeManager.
    """

    def handle(payload: object) -> RouteRuntimeManagerResult:
        request = ControlProxyRouteRuntimeHandlerRequest.from_payload(payload)
        return manager.handle_prepare_decision(request.decision)

    return handle


def handle_controlproxy_route_runtime_request(
    payload: object,
    *,
    manager: RouteRuntimeManager,
) -> RouteRuntimeManagerResult:
    """Handle one Scheduler route payload by delegating to RouteRuntimeManager."""

    return build_controlproxy_route_runtime_request_handler(manager)(payload)


def route_prepare_decision_from_payload(payload: object) -> RoutePrepareDecision:
    """Parse a RoutePrepareDecision from an object or mapping payload."""

    if isinstance(payload, RoutePrepareDecision):
        return payload
    raw = _decision_mapping(payload)
    schema = _require_str(raw, "schema")
    if schema != ROUTE_PREPARE_STATUS_SCHEMA:
        raise ControlProxyRouteRuntimeHandlerError(
            f"unsupported route prepare decision schema: {schema!r}"
        )
    return RoutePrepareDecision(
        schema=schema,
        request_id=_require_str(raw, "request_id"),
        route_id=_require_str(raw, "route_id"),
        route_handle=_optional_str(raw, "route_handle"),
        task_id=_require_str(raw, "task_id"),
        zone=_require_str(raw, "zone"),
        status=_require_str(raw, "status"),  # type: ignore[arg-type]
        action=_require_str(raw, "action"),  # type: ignore[arg-type]
        reason=_require_str(raw, "reason"),
        required_frame_bytes=_require_int(raw, "required_frame_bytes"),
        current_generation=_optional_int(raw, "current_generation"),
        next_generation=_optional_int(raw, "next_generation"),
        current_slot_size=_optional_int(raw, "current_slot_size"),
        slot_size=_optional_int(raw, "slot_size"),
        slot_count=_optional_int(raw, "slot_count"),
        max_frame_bytes=_optional_int(raw, "max_frame_bytes"),
        max_ring_bytes=_require_int(raw, "max_ring_bytes"),
        max_prepare_ms=_require_int(raw, "max_prepare_ms"),
        drain_timeout_ms=_require_int(raw, "drain_timeout_ms"),
        lease_switch_timeout_ms=_require_int(raw, "lease_switch_timeout_ms"),
        notify=_optional_str(raw, "notify"),
        overflow_policy=_optional_str(raw, "overflow_policy"),
        decided_at=_require_str(raw, "decided_at"),
    )


def _decision_mapping(payload: object) -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        return payload
    to_mapping = getattr(payload, "to_mapping", None)
    if callable(to_mapping):
        raw = to_mapping()
        if isinstance(raw, Mapping):
            return raw
    fields = (
        "schema",
        "request_id",
        "route_id",
        "route_handle",
        "task_id",
        "zone",
        "status",
        "action",
        "reason",
        "required_frame_bytes",
        "current_generation",
        "next_generation",
        "current_slot_size",
        "slot_size",
        "slot_count",
        "max_frame_bytes",
        "max_ring_bytes",
        "max_prepare_ms",
        "drain_timeout_ms",
        "lease_switch_timeout_ms",
        "notify",
        "overflow_policy",
        "decided_at",
    )
    raw = {name: getattr(payload, name, None) for name in fields}
    if raw["schema"] is None:
        raise ControlProxyRouteRuntimeHandlerError(
            "route prepare decision payload must be a mapping, RoutePrepareDecision, "
            "or object exposing RoutePrepareDecision fields"
        )
    return raw


def _read_field(payload: object, field_name: str) -> Any:
    if isinstance(payload, Mapping):
        return payload.get(field_name)
    return getattr(payload, field_name, None)


def _read_mapping_field(payload: object, field_name: str) -> Mapping[str, Any]:
    value = _read_field(payload, field_name)
    if isinstance(value, Mapping):
        return value
    return {}


def _require_str(raw: Mapping[str, Any], field_name: str) -> str:
    value = raw.get(field_name)
    if not isinstance(value, str) or not value:
        raise ControlProxyRouteRuntimeHandlerError(
            f"route prepare decision field {field_name} must be a non-empty string"
        )
    return value


def _optional_str(raw: Mapping[str, Any], field_name: str) -> str | None:
    value = raw.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ControlProxyRouteRuntimeHandlerError(
            f"route prepare decision field {field_name} must be a string"
        )
    return value


def _require_int(raw: Mapping[str, Any], field_name: str) -> int:
    value = raw.get(field_name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ControlProxyRouteRuntimeHandlerError(
            f"route prepare decision field {field_name} must be an integer"
        )
    return value


def _optional_int(raw: Mapping[str, Any], field_name: str) -> int | None:
    value = raw.get(field_name)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ControlProxyRouteRuntimeHandlerError(
            f"route prepare decision field {field_name} must be an integer when present"
        )
    return value


__all__ = (
    "ControlProxyRouteRuntimeHandlerError",
    "ControlProxyRouteRuntimeHandlerRequest",
    "RouteRuntimeRequestHandler",
    "build_controlproxy_route_runtime_request_handler",
    "handle_controlproxy_route_runtime_request",
    "route_prepare_decision_from_payload",
)

"""Future route bridge boundary descriptors for NetworkBridge/HardwareBridge.

Phase 0112 introduces a bounded declaration layer for future bridge work.  It
intentionally does not implement network I/O, hardware I/O, sockets, devices,
daemons or services.  The bridge boundary records what a later bridge may be
allowed to connect to the route data plane after the normal micro-kernel path
has selected a handler.

Locked intent:
- NetworkBridge/HardwareBridge are future adapters behind Handler -> RouteRuntimeManager.
- Bridge declarations do not bypass Scheduler, PolicyEngine, PriorityQueue,
  Dispatcher or Handler.
- Bridge declarations do not calculate priority and do not decide policy/zone.
- Route mmap/eventfd remains the data plane, not EventBus.
- EventBus remains observation only.
- No ControlProxyBus.
- No RouteBus.
- No VisualizationBus.
- No sockets opened.
- No devices opened.
- No CLI.
- No OpenRC service and no resident daemon.
- No watcher.
- stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Mapping

ROUTE_BRIDGE_BOUNDARY_SCHEMA = "missipy.controlproxy.route_bridge_boundary.v1"
ROUTE_BRIDGE_PLAN_SCHEMA = "missipy.controlproxy.route_bridge_plan.v1"

RouteBridgeKind = Literal["network", "hardware"]
RouteBridgePlanStatus = Literal["declared", "disabled"]


class RouteBridgeBoundaryError(ValueError):
    """Raised when a future route bridge declaration is incoherent."""


@dataclass(frozen=True, slots=True)
class RouteBridgeBoundarySpec:
    """Declarative boundary for a future NetworkBridge or HardwareBridge.

    The spec is metadata only.  It does not open a socket, does not open a
    device, does not subscribe to EventBus, does not create a new bus and does
    not schedule work.  A later handler may use it to choose an adapter after
    Scheduler -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher
    -> Handler has already selected the route-runtime capability.
    """

    bridge_id: str
    kind: RouteBridgeKind
    route_id: str
    zone: str
    enabled: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty(self.bridge_id, "bridge_id")
        if self.kind not in {"network", "hardware"}:
            raise RouteBridgeBoundaryError("kind must be network or hardware")
        _require_non_empty(self.route_id, "route_id")
        _require_non_empty(self.zone, "zone")
        if not isinstance(self.enabled, bool):
            raise RouteBridgeBoundaryError("enabled must be a bool")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": ROUTE_BRIDGE_BOUNDARY_SCHEMA,
            "bridge_id": self.bridge_id,
            "kind": self.kind,
            "route_id": self.route_id,
            "zone": self.zone,
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class RouteBridgePlan:
    """Stable no-side-effect plan for a future route bridge adapter."""

    schema: str
    status: RouteBridgePlanStatus
    spec: RouteBridgeBoundarySpec
    effect: str
    reason: str

    def __post_init__(self) -> None:
        if self.schema != ROUTE_BRIDGE_PLAN_SCHEMA:
            raise RouteBridgeBoundaryError("unsupported route bridge plan schema")
        if self.status not in {"declared", "disabled"}:
            raise RouteBridgeBoundaryError("unsupported route bridge plan status")
        _require_non_empty(self.effect, "effect")
        _require_non_empty(self.reason, "reason")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "status": self.status,
            "spec": self.spec.to_mapping(),
            "effect": self.effect,
            "reason": self.reason,
        }


def build_route_bridge_plan(spec: RouteBridgeBoundarySpec) -> RouteBridgePlan:
    """Return a stable plan for a future bridge without performing I/O.

    A disabled declaration is the default and safest representation.  Even when
    enabled=True is carried by the spec, 0112 still returns an explicit
    no-runtime-effect plan because the real NetworkBridge/HardwareBridge adapter
    is not implemented in this phase.
    """

    status: RouteBridgePlanStatus = "declared" if spec.enabled else "disabled"
    reason = (
        "bridge declaration accepted; real adapter is not implemented in 0112"
        if spec.enabled
        else "bridge declaration recorded disabled; no runtime adapter is selected"
    )
    return RouteBridgePlan(
        schema=ROUTE_BRIDGE_PLAN_SCHEMA,
        status=status,
        spec=spec,
        effect="none",
        reason=reason,
    )


def route_bridge_spec_from_mapping(raw: Mapping[str, Any]) -> RouteBridgeBoundarySpec:
    """Load RouteBridgeBoundarySpec from a stable mapping."""

    schema = _require_str(raw, "schema")
    if schema != ROUTE_BRIDGE_BOUNDARY_SCHEMA:
        raise RouteBridgeBoundaryError("unsupported route bridge boundary schema")
    metadata = raw.get("metadata", {})
    if not isinstance(metadata, Mapping):
        raise RouteBridgeBoundaryError("metadata must be a mapping")
    return RouteBridgeBoundarySpec(
        bridge_id=_require_str(raw, "bridge_id"),
        kind=_require_kind(raw, "kind"),
        route_id=_require_str(raw, "route_id"),
        zone=_require_str(raw, "zone"),
        enabled=_require_bool(raw, "enabled"),
        metadata=dict(metadata),
    )


def _require_non_empty(value: str, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise RouteBridgeBoundaryError(f"{name} is required")


def _require_str(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise RouteBridgeBoundaryError(f"{key} is required")
    return value


def _require_bool(raw: Mapping[str, Any], key: str) -> bool:
    value = raw.get(key)
    if not isinstance(value, bool):
        raise RouteBridgeBoundaryError(f"{key} must be a bool")
    return value


def _require_kind(raw: Mapping[str, Any], key: str) -> RouteBridgeKind:
    value = _require_str(raw, key)
    if value not in {"network", "hardware"}:
        raise RouteBridgeBoundaryError("kind must be network or hardware")
    return value  # type: ignore[return-value]

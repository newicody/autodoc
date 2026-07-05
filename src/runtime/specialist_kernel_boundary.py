"""Typed specialist-to-kernel boundary for durable capabilities.

Phase 0110 locks how the specialist branch connects to the simplified
micro-kernel path without becoming a second Scheduler and without calling the
route runtime directly.

The specialist branch owns business logic, reasoning and transformation.  It
produces a typed command envelope.  The effect still enters the kernel path:

SpecialistKernelCommand -> Scheduler.emit() -> PolicyEngine.decide()
-> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler

If the command eventually needs route runtime work, the Handler is the only
thin adapter allowed to call RouteRuntimeManager.  There is no direct
Specialist -> RouteRuntimeManager call.

Invariants:

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher.
- No Scheduler.run() modification.
- No Dispatcher, PriorityQueue, PolicyEngine or EventBus modification.
- Dispatcher = EventType -> Handler only.
- PolicyEngine = minimal admission before queue.
- PriorityQueue = deterministic execution order.
- Specialist branch owns business logic.
- Handler -> RouteRuntimeManager.
- RouteRuntimeManager owns route runtime work.
- EventBus = observation only.
- Route mmap/eventfd = data plane, not EventBus.
- No ControlProxyBus.
- No RouteBus.
- No VisualizationBus.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal

SPECIALIST_KERNEL_COMMAND_SCHEMA = "missipy.specialist.kernel_command.v1"
SPECIALIST_KERNEL_BOUNDARY_PLAN_SCHEMA = "missipy.specialist.kernel_boundary_plan.v1"

SpecialistKernelCommandKind = Literal[
    "route_runtime_prepare",
    "context_request",
    "inference_request",
    "specialist_result",
]

_ALLOWED_COMMAND_KINDS: frozenset[str] = frozenset(
    {
        "route_runtime_prepare",
        "context_request",
        "inference_request",
        "specialist_result",
    }
)

_KERNEL_PATH: tuple[str, ...] = (
    "SpecialistKernelCommand -> Scheduler.emit()",
    "PolicyEngine.decide()",
    "PriorityQueue",
    "Scheduler.run()",
    "Dispatcher",
    "Handler",
)

_FORBIDDEN_DIRECT_BOUNDARIES: tuple[str, ...] = (
    "Specialist -> RouteRuntimeManager",
    "Specialist -> ControlFS",
    "Specialist -> mmap/eventfd data plane",
    "Specialist -> EventBus command path",
    "ControlProxyBus",
    "RouteBus",
    "VisualizationBus",
)


class SpecialistKernelBoundaryError(ValueError):
    """Raised when a specialist boundary object is incoherent."""


@dataclass(frozen=True, slots=True)
class SpecialistKernelCommand:
    """Typed command produced by a specialist branch.

    The command is not an Event and does not execute anything by itself.  A
    separate adapter may wrap it in an Event and call Scheduler.emit().  This
    keeps the specialist on the durable kernel path without giving it direct
    ownership of Scheduler, Dispatcher, EventBus or RouteRuntimeManager.
    """

    schema: str
    specialist_id: str
    command_kind: SpecialistKernelCommandKind
    intent: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    route_id: str | None = None
    zone: str | None = None

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_KERNEL_COMMAND_SCHEMA:
            raise SpecialistKernelBoundaryError("unsupported specialist kernel command schema")
        if not self.specialist_id:
            raise SpecialistKernelBoundaryError("specialist_id is required")
        if self.command_kind not in _ALLOWED_COMMAND_KINDS:
            raise SpecialistKernelBoundaryError(f"unsupported specialist command kind: {self.command_kind}")
        if not self.intent:
            raise SpecialistKernelBoundaryError("intent is required")
        if self.command_kind == "route_runtime_prepare":
            if not self.route_id:
                raise SpecialistKernelBoundaryError("route_id is required for route_runtime_prepare")
            if not self.zone:
                raise SpecialistKernelBoundaryError("zone is required for route_runtime_prepare")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))

    def to_mapping(self) -> dict[str, Any]:
        """Return a stable JSON-like projection for tests, reports and replay."""

        return {
            "schema": self.schema,
            "specialist_id": self.specialist_id,
            "command_kind": self.command_kind,
            "intent": self.intent,
            "route_id": self.route_id,
            "zone": self.zone,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True, slots=True)
class SpecialistKernelBoundaryPlan:
    """Stable projection describing how a specialist command must travel."""

    schema: str
    command: SpecialistKernelCommand
    kernel_path: tuple[str, ...]
    next_boundary: str
    runtime_boundary: str | None
    forbidden_direct_boundaries: tuple[str, ...]
    status: str

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_KERNEL_BOUNDARY_PLAN_SCHEMA:
            raise SpecialistKernelBoundaryError("unsupported specialist kernel boundary plan schema")
        if not self.kernel_path:
            raise SpecialistKernelBoundaryError("kernel_path must not be empty")
        if self.next_boundary != "Scheduler.emit()":
            raise SpecialistKernelBoundaryError("next_boundary must be Scheduler.emit()")
        if self.command.command_kind == "route_runtime_prepare":
            if self.runtime_boundary != "Handler -> RouteRuntimeManager":
                raise SpecialistKernelBoundaryError(
                    "route runtime commands must converge through Handler -> RouteRuntimeManager"
                )
        if not self.forbidden_direct_boundaries:
            raise SpecialistKernelBoundaryError("forbidden_direct_boundaries must not be empty")
        if self.status != "kernel_path_required":
            raise SpecialistKernelBoundaryError("status must be kernel_path_required")

    def to_mapping(self) -> dict[str, Any]:
        """Return a deterministic mapping for observation and tests."""

        return {
            "schema": self.schema,
            "command": self.command.to_mapping(),
            "kernel_path": list(self.kernel_path),
            "next_boundary": self.next_boundary,
            "runtime_boundary": self.runtime_boundary,
            "forbidden_direct_boundaries": list(self.forbidden_direct_boundaries),
            "status": self.status,
        }


def build_specialist_kernel_boundary_plan(
    command: SpecialistKernelCommand,
) -> SpecialistKernelBoundaryPlan:
    """Build the required kernel-path plan for one specialist command.

    This function is deliberately pure.  It does not create an Event, emit to
    Scheduler, publish on EventBus, touch ControlFS or call RouteRuntimeManager.
    """

    runtime_boundary = (
        "Handler -> RouteRuntimeManager"
        if command.command_kind == "route_runtime_prepare"
        else None
    )
    return SpecialistKernelBoundaryPlan(
        schema=SPECIALIST_KERNEL_BOUNDARY_PLAN_SCHEMA,
        command=command,
        kernel_path=_KERNEL_PATH,
        next_boundary="Scheduler.emit()",
        runtime_boundary=runtime_boundary,
        forbidden_direct_boundaries=_FORBIDDEN_DIRECT_BOUNDARIES,
        status="kernel_path_required",
    )


def specialist_route_runtime_prepare_command(
    *,
    specialist_id: str,
    route_id: str,
    zone: str,
    intent: str,
    payload: Mapping[str, Any] | None = None,
) -> SpecialistKernelCommand:
    """Create a route-runtime command without bypassing the kernel path."""

    return SpecialistKernelCommand(
        schema=SPECIALIST_KERNEL_COMMAND_SCHEMA,
        specialist_id=specialist_id,
        command_kind="route_runtime_prepare",
        intent=intent,
        route_id=route_id,
        zone=zone,
        payload={} if payload is None else payload,
    )


__all__ = (
    "SPECIALIST_KERNEL_BOUNDARY_PLAN_SCHEMA",
    "SPECIALIST_KERNEL_COMMAND_SCHEMA",
    "SpecialistKernelBoundaryError",
    "SpecialistKernelBoundaryPlan",
    "SpecialistKernelCommand",
    "SpecialistKernelCommandKind",
    "build_specialist_kernel_boundary_plan",
    "specialist_route_runtime_prepare_command",
)

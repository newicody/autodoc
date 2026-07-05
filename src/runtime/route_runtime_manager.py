"""Route runtime manager for ControlProxy / ControlFS route primitives.

Phase 0103 introduces a single importable runtime facade around the route
helpers added in the previous phases.  The manager intentionally stays below
Scheduler, PolicyEngine, PriorityQueue, Dispatcher and Handler:

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher or inotify loop.
- No Scheduler.run() modification.
- No PriorityQueue, Dispatcher or Component tick contract modification.
- No global priority management.
- No policy decision and no zone authority in ControlProxy.
- No EventBus creation and no bus duplication.
- Route mmap/eventfd is a data plane, not EventBus.
- EventBus remains observation only.
- Dispatcher remains EventType -> Handler only.
- PolicyEngine remains minimal admission before queue.
- Specialist branch owns business logic.

RouteRuntimeManager is not a scheduler-like coordinator.  It receives an
already-decided RoutePrepareDecision and performs only route runtime work:
locked generation materialization, lifecycle transitions, closed-generation
cleanup and deterministic table reads.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

from runtime.controlproxy_prepare import RoutePrepareDecision
from runtime.route_generation_lifecycle import (
    ClosedRouteGenerationCleanupResult,
    RouteGenerationLifecycleResult,
    activate_route_generation,
    cleanup_closed_route_generation,
    mark_route_generation_closed,
    mark_route_generation_draining,
)
from runtime.route_generation_locked_materializer import (
    materialize_route_generation_candidate_with_lock,
)
from runtime.route_generation_table import (
    RouteGenerationCandidateResult,
    RouteGenerationTable,
    load_route_generation_table,
)

ROUTE_RUNTIME_MANAGER_RESULT_SCHEMA = "missipy.controlproxy.route_runtime_manager_result.v1"

RouteRuntimeManagerAction = Literal[
    "denied",
    "reuse_active_route",
    "materialize_generation",
    "activate_generation",
    "mark_draining",
    "mark_closed",
    "cleanup_closed",
    "load_table",
]


class RouteRuntimeManagerError(ValueError):
    """Raised when the runtime manager receives an incoherent route request."""


@dataclass(frozen=True, slots=True)
class RouteRuntimeManagerConfig:
    """Explicit roots for ControlFS and route runtime data plane files.

    Placement is intentionally explicit.  The manager does not discover
    /dev/shm, does not select a backend implicitly and does not own a bus.
    Callers pass the runtime_root they want to use.
    """

    controlfs_root: Path | str
    runtime_root: Path | str
    blocking_lock: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "controlfs_root", Path(self.controlfs_root))
        object.__setattr__(self, "runtime_root", Path(self.runtime_root))
        if not isinstance(self.blocking_lock, bool):
            raise RouteRuntimeManagerError("blocking_lock must be a bool")


@dataclass(frozen=True, slots=True)
class RouteRuntimeManagerResult:
    """Stable projection returned by RouteRuntimeManager methods."""

    schema: str
    action: RouteRuntimeManagerAction
    route_id: str
    generation: int | None
    status: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != ROUTE_RUNTIME_MANAGER_RESULT_SCHEMA:
            raise RouteRuntimeManagerError("unsupported route runtime manager result schema")
        if not self.route_id:
            raise RouteRuntimeManagerError("route_id is required")
        if not self.status:
            raise RouteRuntimeManagerError("status is required")
        if self.generation is not None and self.generation < 1:
            raise RouteRuntimeManagerError("generation must be positive when provided")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "action": self.action,
            "route_id": self.route_id,
            "generation": self.generation,
            "status": self.status,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True, slots=True)
class RouteRuntimeManager:
    """Single runtime facade for ControlProxy / ControlFS route operations."""

    config: RouteRuntimeManagerConfig

    @classmethod
    def from_roots(
        cls,
        *,
        controlfs_root: Path | str,
        runtime_root: Path | str,
        blocking_lock: bool = True,
    ) -> "RouteRuntimeManager":
        """Build a manager from explicit ControlFS and runtime roots."""

        return cls(
            RouteRuntimeManagerConfig(
                controlfs_root=controlfs_root,
                runtime_root=runtime_root,
                blocking_lock=blocking_lock,
            )
        )

    @property
    def controlfs_root(self) -> Path:
        return Path(self.config.controlfs_root)

    @property
    def runtime_root(self) -> Path:
        return Path(self.config.runtime_root)

    def handle_prepare_decision(
        self,
        decision: RoutePrepareDecision,
        *,
        blocking: bool | None = None,
    ) -> RouteRuntimeManagerResult:
        """Apply the runtime effect described by an already-decided prepare result.

        This method does not authorize work and does not calculate priority.  It
        reads the status/action already carried by the RoutePrepareDecision and
        maps it to one route-runtime operation.
        """

        if decision.status == "denied" or decision.action == "deny":
            return self._denied_result(decision)
        if decision.action == "reuse_active":
            return self._reuse_active_result(decision)
        if decision.action in {"create_route_generation", "create_next_generation"}:
            return self.materialize_generation(decision, blocking=blocking)
        raise RouteRuntimeManagerError(f"unsupported route runtime action: {decision.action}")

    def materialize_generation(
        self,
        decision: RoutePrepareDecision,
        *,
        blocking: bool | None = None,
    ) -> RouteRuntimeManagerResult:
        """Materialize one mmap/shm-like route generation under the route lock."""

        result = materialize_route_generation_candidate_with_lock(
            controlfs_root=self.controlfs_root,
            runtime_root=self.runtime_root,
            decision=decision,
            blocking=self.config.blocking_lock if blocking is None else blocking,
        )
        return _result_from_candidate(result)

    def activate_generation(self, *, route_id: str, generation: int) -> RouteRuntimeManagerResult:
        """Mark a candidate generation active."""

        result = activate_route_generation(
            controlfs_root=self.controlfs_root,
            route_id=route_id,
            generation=generation,
        )
        return _result_from_lifecycle("activate_generation", result)

    def mark_draining(self, *, route_id: str, generation: int) -> RouteRuntimeManagerResult:
        """Mark an active generation draining."""

        result = mark_route_generation_draining(
            controlfs_root=self.controlfs_root,
            route_id=route_id,
            generation=generation,
        )
        return _result_from_lifecycle("mark_draining", result)

    def mark_closed(self, *, route_id: str, generation: int) -> RouteRuntimeManagerResult:
        """Mark a draining generation closed."""

        result = mark_route_generation_closed(
            controlfs_root=self.controlfs_root,
            route_id=route_id,
            generation=generation,
        )
        return _result_from_lifecycle("mark_closed", result)

    def cleanup_closed(
        self,
        *,
        route_id: str,
        generation: int,
        cleaned_at: str = "2026-07-05T00:00:00Z",
    ) -> RouteRuntimeManagerResult:
        """Remove runtime files for one closed generation."""

        result = cleanup_closed_route_generation(
            controlfs_root=self.controlfs_root,
            runtime_root=self.runtime_root,
            route_id=route_id,
            generation=generation,
            cleaned_at=cleaned_at,
        )
        return _result_from_cleanup(result)

    def load_table(self, route_id: str) -> RouteRuntimeManagerResult:
        """Return the current persisted route generation table."""

        table = load_route_generation_table(self.controlfs_root, route_id)
        return RouteRuntimeManagerResult(
            schema=ROUTE_RUNTIME_MANAGER_RESULT_SCHEMA,
            action="load_table",
            route_id=table.route_id,
            generation=table.active_generation,
            status="loaded",
            payload=table.to_mapping(),
        )

    def _denied_result(self, decision: RoutePrepareDecision) -> RouteRuntimeManagerResult:
        return RouteRuntimeManagerResult(
            schema=ROUTE_RUNTIME_MANAGER_RESULT_SCHEMA,
            action="denied",
            route_id=decision.route_id,
            generation=decision.next_generation,
            status="no_runtime_effect",
            payload=decision.to_mapping(),
        )

    def _reuse_active_result(self, decision: RoutePrepareDecision) -> RouteRuntimeManagerResult:
        return RouteRuntimeManagerResult(
            schema=ROUTE_RUNTIME_MANAGER_RESULT_SCHEMA,
            action="reuse_active_route",
            route_id=decision.route_id,
            generation=decision.current_generation or decision.next_generation,
            status="no_runtime_effect",
            payload=decision.to_mapping(),
        )


def _result_from_candidate(result: RouteGenerationCandidateResult) -> RouteRuntimeManagerResult:
    return RouteRuntimeManagerResult(
        schema=ROUTE_RUNTIME_MANAGER_RESULT_SCHEMA,
        action="materialize_generation",
        route_id=result.record.route_id,
        generation=result.record.generation,
        status=result.record.state,
        payload=result.to_mapping(),
    )


def _result_from_lifecycle(
    action: Literal["activate_generation", "mark_draining", "mark_closed"],
    result: RouteGenerationLifecycleResult,
) -> RouteRuntimeManagerResult:
    return RouteRuntimeManagerResult(
        schema=ROUTE_RUNTIME_MANAGER_RESULT_SCHEMA,
        action=action,
        route_id=result.record.route_id,
        generation=result.record.generation,
        status=result.record.state,
        payload=result.to_mapping(),
    )


def _result_from_cleanup(result: ClosedRouteGenerationCleanupResult) -> RouteRuntimeManagerResult:
    status = "removed" if result.removed_runtime_route_dir else "already_absent"
    return RouteRuntimeManagerResult(
        schema=ROUTE_RUNTIME_MANAGER_RESULT_SCHEMA,
        action="cleanup_closed",
        route_id=result.route_id,
        generation=result.generation,
        status=status,
        payload=result.to_mapping(),
    )


__all__ = (
    "ROUTE_RUNTIME_MANAGER_RESULT_SCHEMA",
    "RouteRuntimeManager",
    "RouteRuntimeManagerAction",
    "RouteRuntimeManagerConfig",
    "RouteRuntimeManagerError",
    "RouteRuntimeManagerResult",
)

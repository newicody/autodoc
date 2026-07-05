"""Compatibility registry for pre-RouteRuntimeManager ControlProxy helpers.

0109 is a cleanup boundary, not a new runtime coordinator.  It records the
legacy Scheduler-facing ControlProxy helper symbols that must remain available
while the code converges on the simplified path locked by 0101-0108:

Scheduler -> PolicyEngine -> PriorityQueue -> Scheduler.run() -> Dispatcher -> Handler
Handler -> RouteRuntimeManager

The registry is deliberately declarative:

- No CLI.
- No OpenRC service and no resident daemon.
- No watcher.
- No Scheduler.run() modification.
- No Dispatcher, PriorityQueue or PolicyEngine modification.
- Dispatcher = EventType -> Handler only.
- PolicyEngine = minimal admission before queue.
- PriorityQueue = deterministic execution order.
- Handler -> RouteRuntimeManager.
- Specialist branch owns business logic.
- EventBus = observation only.
- Route mmap/eventfd = data plane, not EventBus.
- No ControlProxyBus.
- No RouteBus.
- No VisualizationBus.
- No scheduler-like ControlProxy coordinator.

The intent is to stop extending legacy wrappers.  Future patches may route those
symbols through the thin Handler -> RouteRuntimeManager path when that can be
done without breaking existing callers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Literal

CONTROLPROXY_COMPATIBILITY_WRAPPERS_SCHEMA = (
    "missipy.controlproxy.compatibility_wrappers.v1"
)

CompatibilityStatus = Literal[
    "keep_for_compatibility",
    "do_not_extend",
    "future_deprecate_after_integration",
]


class ControlProxyCompatibilityWrapperError(ValueError):
    """Raised when a compatibility-wrapper query is incoherent."""


@dataclass(frozen=True, slots=True)
class ControlProxyCompatibilityWrapper:
    """Declarative description of one legacy ControlProxy wrapper symbol."""

    schema: str
    legacy_symbol: str
    legacy_module_candidates: tuple[str, ...]
    current_boundary: str
    replacement_boundary: str
    replacement_module: str
    replacement_symbol: str
    status: CompatibilityStatus
    reason: str

    def __post_init__(self) -> None:
        if self.schema != CONTROLPROXY_COMPATIBILITY_WRAPPERS_SCHEMA:
            raise ControlProxyCompatibilityWrapperError(
                "unsupported ControlProxy compatibility wrapper schema"
            )
        if not self.legacy_symbol:
            raise ControlProxyCompatibilityWrapperError("legacy_symbol is required")
        if not self.legacy_module_candidates:
            raise ControlProxyCompatibilityWrapperError(
                "legacy_module_candidates must not be empty"
            )
        if self.current_boundary != "compatibility_wrapper":
            raise ControlProxyCompatibilityWrapperError(
                "current_boundary must be compatibility_wrapper"
            )
        if self.replacement_boundary != "Handler -> RouteRuntimeManager":
            raise ControlProxyCompatibilityWrapperError(
                "replacement_boundary must be Handler -> RouteRuntimeManager"
            )
        if not self.replacement_module or not self.replacement_symbol:
            raise ControlProxyCompatibilityWrapperError(
                "replacement module and symbol are required"
            )
        if not self.reason:
            raise ControlProxyCompatibilityWrapperError("reason is required")

    def to_mapping(self) -> dict[str, object]:
        """Return a stable mapping for docs/tests/introspection."""

        return {
            "schema": self.schema,
            "legacy_symbol": self.legacy_symbol,
            "legacy_module_candidates": list(self.legacy_module_candidates),
            "current_boundary": self.current_boundary,
            "replacement_boundary": self.replacement_boundary,
            "replacement_module": self.replacement_module,
            "replacement_symbol": self.replacement_symbol,
            "status": self.status,
            "reason": self.reason,
        }


CONTROLPROXY_COMPATIBILITY_WRAPPERS: tuple[ControlProxyCompatibilityWrapper, ...] = (
    ControlProxyCompatibilityWrapper(
        schema=CONTROLPROXY_COMPATIBILITY_WRAPPERS_SCHEMA,
        legacy_symbol="prepare_route_for_scheduler",
        legacy_module_candidates=(
            "runtime.controlproxy_scheduler_prepare",
            "runtime.controlproxy_prepare_scheduler",
            "runtime.controlproxy_scheduler",
            "runtime.control_proxy_scheduler",
        ),
        current_boundary="compatibility_wrapper",
        replacement_boundary="Handler -> RouteRuntimeManager",
        replacement_module="runtime.controlproxy_route_runtime_handler",
        replacement_symbol="build_controlproxy_route_runtime_request_handler",
        status="do_not_extend",
        reason=(
            "0085 prepare_route_for_scheduler remains a compatibility wrapper; "
            "new runtime effects must converge on the thin Handler -> RouteRuntimeManager path."
        ),
    ),
    ControlProxyCompatibilityWrapper(
        schema=CONTROLPROXY_COMPATIBILITY_WRAPPERS_SCHEMA,
        legacy_symbol="handle_scheduler_route_request",
        legacy_module_candidates=(
            "runtime.controlproxy_scheduler_adapter",
            "runtime.controlproxy_scheduler",
            "runtime.controlproxy_route_adapter",
            "runtime.controlproxy_route_scheduler",
            "runtime.control_proxy_scheduler_adapter",
            "runtime.control_proxy_scheduler",
            "runtime.control_proxy_route_adapter",
            "runtime.control_proxy_route_scheduler",
        ),
        current_boundary="compatibility_wrapper",
        replacement_boundary="Handler -> RouteRuntimeManager",
        replacement_module="runtime.controlproxy_route_runtime_handler",
        replacement_symbol="handle_controlproxy_route_runtime_request",
        status="do_not_extend",
        reason=(
            "0086 handle_scheduler_route_request remains a compatibility wrapper; "
            "new callers should use the 0104 thin handler binding with an explicit RouteRuntimeManager."
        ),
    ),
)


def list_controlproxy_compatibility_wrappers() -> tuple[ControlProxyCompatibilityWrapper, ...]:
    """Return the immutable registry of legacy ControlProxy compatibility wrappers."""

    return CONTROLPROXY_COMPATIBILITY_WRAPPERS


def controlproxy_compatibility_wrapper_map() -> Mapping[str, Mapping[str, object]]:
    """Return a mapping keyed by legacy symbol.

    The mapping is read-only at the top level so tests and tools can inspect the
    cleanup state without becoming an owner of the compatibility registry.
    """

    return MappingProxyType(
        {wrapper.legacy_symbol: wrapper.to_mapping() for wrapper in CONTROLPROXY_COMPATIBILITY_WRAPPERS}
    )


def require_controlproxy_compatibility_wrapper(
    legacy_symbol: str,
) -> ControlProxyCompatibilityWrapper:
    """Return one registered compatibility wrapper or raise a clear error."""

    if not legacy_symbol:
        raise ControlProxyCompatibilityWrapperError("legacy_symbol is required")
    for wrapper in CONTROLPROXY_COMPATIBILITY_WRAPPERS:
        if wrapper.legacy_symbol == legacy_symbol:
            return wrapper
    raise ControlProxyCompatibilityWrapperError(
        f"unknown ControlProxy compatibility wrapper: {legacy_symbol}"
    )


__all__ = (
    "CONTROLPROXY_COMPATIBILITY_WRAPPERS",
    "CONTROLPROXY_COMPATIBILITY_WRAPPERS_SCHEMA",
    "CompatibilityStatus",
    "ControlProxyCompatibilityWrapper",
    "ControlProxyCompatibilityWrapperError",
    "controlproxy_compatibility_wrapper_map",
    "list_controlproxy_compatibility_wrappers",
    "require_controlproxy_compatibility_wrapper",
)

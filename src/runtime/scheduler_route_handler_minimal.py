"""Minimal Scheduler route handler.

0131 is the first handler-shaped bridge between Scheduler-owned command data and
RouteProxyRuntime frame IO.  It does not mutate the Scheduler run loop, instantiate a
Scheduler, import Dispatcher/Policy/Queue, or create a daemon.  A caller that is
already inside the Scheduler/Dispatcher/Handler path can pass immutable route
frame items here; the handler asks RouteProxyRuntime for writer permits and
writes frames under /dev/shm or an explicit test root.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any

from runtime.route_proxy_runtime_minimal import (
    RouteProxyRuntimeError,
    RouteProxyRuntimePolicy,
    RouteProxyRuntimeState,
    list_observation_facts,
    prepare_route_proxy_runtime,
    request_writer_permit,
    write_route_frame,
)

_HANDLER_COMMAND_SCHEMA = "missipy.scheduler.route_handler_command.v1"
_HANDLER_FRAME_SCHEMA = "missipy.scheduler.route_frame_request.v1"
_HANDLER_RESULT_SCHEMA = "missipy.scheduler.route_handler_result.v1"

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_ALLOWED_COMMAND_PREFIXES = ("scheduler-command:", "command:")
_ALLOWED_HANDLER_PREFIXES = ("handler:",)
_ALLOWED_ROUTE_PREFIXES = ("route:", "route-frame:", "route-zone:", "vector-route:")
_ALLOWED_OWNER_PREFIXES = ("specialist:", "worker:", "scheduler-command:", "proxy:")
_ALLOWED_CONTEXT_PREFIXES = ("sql:", "ctx:", "ctx-result:", "cycle-state:")
_ALLOWED_FRAME_KINDS = (
    "specialist_demand",
    "specialist_opinion",
    "vector_embedding_request",
    "vector_projection_request",
    "runtime_probe",
)


@dataclass(frozen=True, slots=True)
class SchedulerRouteFrameRequest:
    """One frame request produced by a Scheduler-dispatched handler path."""

    route_ref: str
    owner_ref: str
    context_ref: str
    context_generation: int
    priority: int
    frame_kind: str
    payload: dict[str, Any]
    write_allowed: bool = True
    denial_reason: str | None = None

    def __post_init__(self) -> None:
        _require_typed_ref("route_ref", self.route_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        _require_typed_ref("owner_ref", self.owner_ref, required_prefixes=_ALLOWED_OWNER_PREFIXES)
        _require_typed_ref("context_ref", self.context_ref, required_prefixes=_ALLOWED_CONTEXT_PREFIXES)
        _require_positive_int("context_generation", self.context_generation, allow_zero=False)
        _require_priority(self.priority)
        if self.frame_kind not in _ALLOWED_FRAME_KINDS:
            raise RouteProxyRuntimeError("frame_kind must be one of the locked handler frame kinds")
        if not isinstance(self.payload, dict):
            raise RouteProxyRuntimeError("payload must be a dict")
        if self.write_allowed and self.denial_reason is not None:
            raise RouteProxyRuntimeError("denial_reason must be None when write_allowed is true")
        if not self.write_allowed:
            _require_non_empty("denial_reason", self.denial_reason or "")

    def enriched_payload(self) -> dict[str, Any]:
        data = dict(self.payload)
        data.setdefault("frame_kind", self.frame_kind)
        data.setdefault("route_ref", self.route_ref)
        data.setdefault("context_ref", self.context_ref)
        data.setdefault("context_generation", self.context_generation)
        return data

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _HANDLER_FRAME_SCHEMA,
            "route_ref": self.route_ref,
            "owner_ref": self.owner_ref,
            "context_ref": self.context_ref,
            "context_generation": self.context_generation,
            "priority": self.priority,
            "frame_kind": self.frame_kind,
            "payload": self.payload,
            "write_allowed": self.write_allowed,
            "denial_reason": self.denial_reason,
            "scheduler_is_orchestrator": True,
            "route_proxy_runtime_executes_io": True,
        }


@dataclass(frozen=True, slots=True)
class SchedulerRouteHandlerCommand:
    """Immutable command payload consumed by the minimal route handler."""

    command_ref: str
    handler_ref: str
    route_root_ref: str
    frame_requests: tuple[SchedulerRouteFrameRequest, ...]
    runtime_policy: RouteProxyRuntimePolicy | None = None
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("command_ref", self.command_ref, required_prefixes=_ALLOWED_COMMAND_PREFIXES)
        _require_typed_ref("handler_ref", self.handler_ref, required_prefixes=_ALLOWED_HANDLER_PREFIXES)
        _require_typed_ref("route_root_ref", self.route_root_ref, required_prefixes=_ALLOWED_ROUTE_PREFIXES)
        if not self.frame_requests:
            raise RouteProxyRuntimeError("frame_requests must not be empty")
        object.__setattr__(self, "frame_requests", tuple(self.frame_requests))
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _HANDLER_COMMAND_SCHEMA,
            "command_ref": self.command_ref,
            "handler_ref": self.handler_ref,
            "route_root_ref": self.route_root_ref,
            "frame_requests": [request.to_mapping() for request in self.frame_requests],
            "runtime_policy": None if self.runtime_policy is None else self.runtime_policy.to_mapping(),
            "metadata": dict(self.metadata),
            "scheduler_is_orchestrator": True,
            "handler_is_executor": True,
            "scheduler_run_modified": False,
        }


@dataclass(frozen=True, slots=True)
class SchedulerRouteHandlerResult:
    """Result returned after the handler writes or denies route frame items."""

    command_ref: str
    handler_ref: str
    runtime_root: Path
    written_route_refs: tuple[str, ...]
    denied_route_refs: tuple[str, ...]
    frame_paths: tuple[Path, ...]
    observation_facts: tuple[dict[str, Any], ...]

    def __post_init__(self) -> None:
        _require_typed_ref("command_ref", self.command_ref, required_prefixes=_ALLOWED_COMMAND_PREFIXES)
        _require_typed_ref("handler_ref", self.handler_ref, required_prefixes=_ALLOWED_HANDLER_PREFIXES)
        object.__setattr__(self, "written_route_refs", _normalize_refs("written_route_refs", self.written_route_refs, allow_empty=True, required_prefixes=_ALLOWED_ROUTE_PREFIXES))
        object.__setattr__(self, "denied_route_refs", _normalize_refs("denied_route_refs", self.denied_route_refs, allow_empty=True, required_prefixes=_ALLOWED_ROUTE_PREFIXES))
        object.__setattr__(self, "frame_paths", tuple(self.frame_paths))
        object.__setattr__(self, "observation_facts", tuple(self.observation_facts))

    @property
    def wrote_anything(self) -> bool:
        return bool(self.written_route_refs)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _HANDLER_RESULT_SCHEMA,
            "command_ref": self.command_ref,
            "handler_ref": self.handler_ref,
            "runtime_root": str(self.runtime_root),
            "written_route_refs": list(self.written_route_refs),
            "denied_route_refs": list(self.denied_route_refs),
            "frame_paths": [str(path) for path in self.frame_paths],
            "observation_facts": list(self.observation_facts),
            "wrote_anything": self.wrote_anything,
            "scheduler_is_orchestrator": True,
            "handler_is_executor": True,
            "event_bus_observation_only": True,
            "dev_shm_data_plane": True,
        }


def handle_scheduler_route_command(
    command: SchedulerRouteHandlerCommand,
    *,
    runtime_state: RouteProxyRuntimeState | None = None,
) -> SchedulerRouteHandlerResult:
    """Execute one minimal Scheduler route command through RouteProxyRuntime."""

    state = runtime_state or prepare_route_proxy_runtime(command.runtime_policy)
    written: list[str] = []
    denied: list[str] = []
    paths: list[Path] = []
    for request in command.frame_requests:
        permit = request_writer_permit(
            state,
            route_ref=request.route_ref,
            owner_ref=request.owner_ref,
            context_ref=request.context_ref,
            context_generation=request.context_generation,
            priority=request.priority,
            write_allowed=request.write_allowed,
            denial_reason=request.denial_reason,
        )
        if not permit.write_allowed:
            denied.append(request.route_ref)
            continue
        result = write_route_frame(state, permit, request.enriched_payload())
        written.append(request.route_ref)
        paths.append(result.frame_path)
    return SchedulerRouteHandlerResult(
        command_ref=command.command_ref,
        handler_ref=command.handler_ref,
        runtime_root=state.route_root,
        written_route_refs=tuple(written),
        denied_route_refs=tuple(denied),
        frame_paths=tuple(paths),
        observation_facts=list_observation_facts(state),
    )


def build_single_frame_route_command(
    *,
    command_ref: str,
    route_ref: str,
    owner_ref: str,
    context_ref: str,
    context_generation: int,
    priority: int,
    frame_kind: str,
    payload: dict[str, Any],
    runtime_policy: RouteProxyRuntimePolicy | None = None,
) -> SchedulerRouteHandlerCommand:
    """Convenience builder for tests and the first Scheduler handler wiring."""

    request = SchedulerRouteFrameRequest(
        route_ref=route_ref,
        owner_ref=owner_ref,
        context_ref=context_ref,
        context_generation=context_generation,
        priority=priority,
        frame_kind=frame_kind,
        payload=payload,
    )
    return SchedulerRouteHandlerCommand(
        command_ref=command_ref,
        handler_ref="handler:scheduler-route-minimal",
        route_root_ref="route:runtime/root",
        frame_requests=(request,),
        runtime_policy=runtime_policy,
        metadata=(("phase", "0131"), ("scheduler_run_modified", "false")),
    )


def _require_typed_ref(name: str, value: str, *, required_prefixes: tuple[str, ...] | None = None) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.match(value):
        raise RouteProxyRuntimeError(f"{name} must be a typed ref")
    if required_prefixes is not None and not value.startswith(required_prefixes):
        raise RouteProxyRuntimeError(f"{name} must start with one of: {', '.join(required_prefixes)}")


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise RouteProxyRuntimeError(f"{name} must not be empty")


def _require_positive_int(name: str, value: int, *, allow_zero: bool) -> None:
    if not isinstance(value, int):
        raise RouteProxyRuntimeError(f"{name} must be an integer")
    if allow_zero:
        if value < 0:
            raise RouteProxyRuntimeError(f"{name} must be >= 0")
    elif value <= 0:
        raise RouteProxyRuntimeError(f"{name} must be > 0")


def _require_priority(value: int) -> None:
    _require_positive_int("priority", value, allow_zero=True)
    if value > 10_000:
        raise RouteProxyRuntimeError("priority must be between 0 and 10000")


def _normalize_refs(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
    required_prefixes: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    refs = tuple(dict.fromkeys(values))
    if not refs and not allow_empty:
        raise RouteProxyRuntimeError(f"{name} must not be empty")
    for ref in refs:
        _require_typed_ref(name, ref, required_prefixes=required_prefixes)
    return refs


def _normalize_metadata(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        normalized.append((key.strip(), value.strip()))
    return tuple(normalized)

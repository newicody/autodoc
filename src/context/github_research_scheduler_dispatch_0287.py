"""Emit one authorized GitHub research route through the existing Scheduler.

The r16-r8 unit produces an authorized SchedulerRouteRequest but deliberately
does not dispatch it.  This unit closes that boundary in process:

    authorized research intake
    -> existing Dispatcher registration
    -> existing Scheduler.emit()
    -> existing ControlProxy Scheduler handler
    -> typed route reply

It never constructs or starts a Scheduler, Dispatcher, EventBus, PolicyEngine,
ControlProxy, laboratory, SQL backend, Qdrant client, OpenVINO executor, daemon,
or worker.  The runtime owner must provide already-composed
ImportedActionsRuntimePorts and must already be running its Scheduler.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from context.github_research_scheduler_intake_0287 import (
    SCHEMA as RESEARCH_SCHEDULER_INTAKE_SCHEMA,
)
from context.love_imported_actions_runtime_contract_0287 import (
    ImportedActionsRuntimePorts,
    validate_imported_actions_runtime_ports,
)
from contracts.event import Event, EventType, Request
from runtime.controlproxy_scheduler_handler import (
    ControlProxySchedulerRouteRequestHandler,
)
from runtime.scheduler_route_adapter import (
    SCHEDULER_ROUTE_REPLY_SCHEMA,
    SchedulerRouteRequest,
)

SCHEMA = "missipy.github.research_scheduler_dispatch.v1"
EVENT_SCHEMA = "missipy.github.research_scheduler_route_event.v1"
SOURCE_REF = "github.research.scheduler-intake"
DESTINATION_REF = "scheduler"


class GitHubResearchSchedulerDispatchError(RuntimeError):
    """Raised when an authorized research cannot enter the live Scheduler."""


@dataclass(frozen=True, slots=True)
class GitHubResearchSchedulerDispatchCommand:
    """In-process dispatch request using an already-composed live runtime."""

    runtime_ports: ImportedActionsRuntimePorts
    scheduler_intake: Mapping[str, Any]
    timeout_seconds: float = 5.0
    priority: int = 60
    register_handler: bool = True
    route_request_handler: Callable[[object], object] | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.scheduler_intake, Mapping):
            raise TypeError("scheduler_intake must be a mapping")
        if isinstance(self.timeout_seconds, bool) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        if (
            isinstance(self.priority, bool)
            or not isinstance(self.priority, int)
            or self.priority < -1_000
            or self.priority > 1_000_000
        ):
            raise ValueError("priority is outside the Scheduler policy range")
        if (
            self.route_request_handler is not None
            and not callable(self.route_request_handler)
        ):
            raise TypeError("route_request_handler must be callable")


@dataclass(frozen=True, slots=True)
class GitHubResearchSchedulerDispatchResult:
    """Readback proving that the existing Scheduler completed the route event."""

    valid: bool
    status: str
    issues: tuple[str, ...]
    request_id: str = ""
    event_id: str = ""
    policy_decision_id: str = ""
    registration_action: str = ""
    route_reply: Mapping[str, Any] = field(default_factory=dict)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "valid": self.valid,
            "status": self.status,
            "issues": list(self.issues),
            "request_id": self.request_id,
            "event_id": self.event_id,
            "policy_decision_id": self.policy_decision_id,
            "registration_action": self.registration_action,
            "route_reply": dict(self.route_reply),
            "event_schema": EVENT_SCHEMA,
            "event_type": "SCHEDULER_ROUTE_REQUEST",
            "existing_runtime_ports_reused": True,
            "existing_scheduler_reused": True,
            "existing_dispatcher_reused": True,
            "existing_controlproxy_handler_reused": True,
            "scheduler_created": False,
            "scheduler_started": False,
            "scheduler_modified": False,
            "scheduler_dispatch_started": bool(self.event_id),
            "scheduler_dispatch_completed": self.valid,
            "eventbus_observation_available": bool(self.event_id),
            "laboratory_execution_started": False,
            "specialist_execution_started": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "github_mutation_performed": False,
        }


def register_existing_scheduler_route_handler(
    runtime_ports: ImportedActionsRuntimePorts,
    *,
    route_request_handler: Callable[[object], object] | None = None,
) -> str:
    """Register the existing ControlProxy handler without replacing another one.

    Returns ``registered`` for the first registration or ``replay`` when the
    canonical handler is already bound to the route event type.
    """

    ports = validate_imported_actions_runtime_ports(runtime_ports)
    dispatcher = ports.dispatcher
    handlers = getattr(dispatcher, "handlers", None)
    current = (
        handlers.get(EventType.SCHEDULER_ROUTE_REQUEST)
        if isinstance(handlers, Mapping)
        else None
    )
    if current is not None:
        if isinstance(current, ControlProxySchedulerRouteRequestHandler):
            return "replay"
        raise GitHubResearchSchedulerDispatchError(
            "SCHEDULER_ROUTE_REQUEST already has a different handler"
        )

    dispatcher.register(
        EventType.SCHEDULER_ROUTE_REQUEST,
        ControlProxySchedulerRouteRequestHandler(
            route_request_handler=route_request_handler,
        ),
    )
    return "registered"


async def dispatch_authorized_research_through_existing_scheduler(
    command: GitHubResearchSchedulerDispatchCommand,
) -> GitHubResearchSchedulerDispatchResult:
    """Emit and await one authorized route request through the live Scheduler."""

    ports = validate_imported_actions_runtime_ports(command.runtime_ports)
    intake = dict(command.scheduler_intake)
    issues = _validate_scheduler_intake(intake)
    if issues:
        return _invalid("rejected", issues)

    route_raw = intake.get("scheduler_route_request")
    assert isinstance(route_raw, Mapping)  # established by validation
    try:
        route_request = SchedulerRouteRequest.from_mapping(route_raw)
    except (TypeError, ValueError, RuntimeError) as exc:
        return _invalid("route-request-invalid", (str(exc),))

    scheduler = ports.scheduler
    running = getattr(scheduler, "running", None)
    if running is False:
        return _invalid(
            "scheduler-not-running",
            (
                "the existing Scheduler must already be running; "
                "r16-r9 will not start a second Scheduler",
            ),
            request_id=route_request.request_id,
            policy_decision_id=route_request.policy_decision_id,
        )

    registration_action = ""
    if command.register_handler:
        try:
            registration_action = register_existing_scheduler_route_handler(
                ports,
                route_request_handler=command.route_request_handler,
            )
        except (TypeError, ValueError, RuntimeError) as exc:
            return _invalid(
                "handler-registration-failed",
                (str(exc),),
                request_id=route_request.request_id,
                policy_decision_id=route_request.policy_decision_id,
            )

    loop = asyncio.get_running_loop()
    future: asyncio.Future[Any] = loop.create_future()
    event = Event(
        EventType.SCHEDULER_ROUTE_REQUEST,
        source=SOURCE_REF,
        dest=DESTINATION_REF,
        payload=route_request.to_mapping(),
        priority=command.priority,
        correlation_id=route_request.request_id,
        request=Request(reply=future, timeout=command.timeout_seconds),
        metadata={
            "schema": EVENT_SCHEMA,
            "repository": "newicody/projects",
            "policy_decision_id": route_request.policy_decision_id,
            "request_id": route_request.request_id,
            "laboratory_execution_started": False,
        },
    )

    try:
        await scheduler.emit(event)
        reply = await asyncio.wait_for(
            future,
            timeout=command.timeout_seconds,
        )
    except TimeoutError:
        return _invalid(
            "scheduler-timeout",
            ("the existing Scheduler did not resolve the route request in time",),
            request_id=route_request.request_id,
            event_id=event.id,
            policy_decision_id=route_request.policy_decision_id,
            registration_action=registration_action,
        )
    except Exception as exc:  # preserve the handler/kernel failure as evidence
        return _invalid(
            "scheduler-dispatch-failed",
            (f"{type(exc).__name__}: {exc}",),
            request_id=route_request.request_id,
            event_id=event.id,
            policy_decision_id=route_request.policy_decision_id,
            registration_action=registration_action,
        )

    reply_mapping = _reply_mapping(reply)
    reply_issues = _validate_route_reply(reply_mapping, route_request)
    if reply_issues:
        return _invalid(
            "route-reply-invalid",
            reply_issues,
            request_id=route_request.request_id,
            event_id=event.id,
            policy_decision_id=route_request.policy_decision_id,
            registration_action=registration_action,
            route_reply=reply_mapping,
        )

    return GitHubResearchSchedulerDispatchResult(
        valid=True,
        status="route-ready",
        issues=(),
        request_id=route_request.request_id,
        event_id=event.id,
        policy_decision_id=route_request.policy_decision_id,
        registration_action=registration_action,
        route_reply=reply_mapping,
    )


def _validate_scheduler_intake(value: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if value.get("schema") != RESEARCH_SCHEDULER_INTAKE_SCHEMA:
        issues.append("unsupported research Scheduler intake schema")
    if value.get("valid") is not True:
        issues.append("research Scheduler intake must be valid")
    if value.get("authorized") is not True:
        issues.append("research Scheduler intake must be authorized")
    if value.get("status") != "scheduler-request-ready":
        issues.append("research Scheduler intake status must be scheduler-request-ready")
    if value.get("scheduler_dispatch_started") is not False:
        issues.append("Scheduler dispatch has already started")
    if value.get("laboratory_execution_started") is not False:
        issues.append("laboratory execution has already started")

    route = value.get("scheduler_route_request")
    if not isinstance(route, Mapping):
        issues.append("scheduler_route_request must be an object")
        return issues
    policy = value.get("policy_decision")
    if not isinstance(policy, Mapping):
        issues.append("policy_decision must be an object")
        return issues
    if policy.get("decision") != "approve":
        issues.append("policy decision must be approve")
    if policy.get("automatic") is not True:
        issues.append("automatic policy proof is required")
    if route.get("authorized") is not True:
        issues.append("Scheduler route request must already be authorized")
    if route.get("policy_decision_id") != policy.get("policy_decision_id"):
        issues.append("route request and policy decision identifiers differ")
    return issues


def _reply_mapping(reply: object) -> dict[str, Any]:
    if isinstance(reply, Mapping):
        return dict(reply)
    to_mapping = getattr(reply, "to_mapping", None)
    if callable(to_mapping):
        mapped = to_mapping()
        if isinstance(mapped, Mapping):
            return dict(mapped)
    return {"unrecognized_reply_type": type(reply).__name__}


def _validate_route_reply(
    reply: Mapping[str, Any],
    request: SchedulerRouteRequest,
) -> tuple[str, ...]:
    issues: list[str] = []
    if reply.get("schema") != SCHEDULER_ROUTE_REPLY_SCHEMA:
        issues.append("unexpected Scheduler route reply schema")
    if reply.get("status") != "ready":
        issues.append("Scheduler route reply status must be ready")
    if reply.get("request_id") != request.request_id:
        issues.append("Scheduler route reply request_id mismatch")
    if reply.get("route_id") != request.route_id:
        issues.append("Scheduler route reply route_id mismatch")
    if reply.get("task_id") != request.task_id:
        issues.append("Scheduler route reply task_id mismatch")
    if reply.get("policy_decision_id") != request.policy_decision_id:
        issues.append("Scheduler route reply policy_decision_id mismatch")
    return tuple(issues)


def _invalid(
    status: str,
    issues: tuple[str, ...] | list[str],
    *,
    request_id: str = "",
    event_id: str = "",
    policy_decision_id: str = "",
    registration_action: str = "",
    route_reply: Mapping[str, Any] | None = None,
) -> GitHubResearchSchedulerDispatchResult:
    return GitHubResearchSchedulerDispatchResult(
        valid=False,
        status=status,
        issues=tuple(dict.fromkeys(str(item) for item in issues if str(item))),
        request_id=request_id,
        event_id=event_id,
        policy_decision_id=policy_decision_id,
        registration_action=registration_action,
        route_reply=dict(route_reply or {}),
    )


__all__ = (
    "EVENT_SCHEMA",
    "GitHubResearchSchedulerDispatchCommand",
    "GitHubResearchSchedulerDispatchError",
    "GitHubResearchSchedulerDispatchResult",
    "SCHEMA",
    "dispatch_authorized_research_through_existing_scheduler",
    "register_existing_scheduler_route_handler",
)

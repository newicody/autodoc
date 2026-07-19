"""Authorized route request queue handoff.

0179 takes authorized scheduler intake plans produced from context.bus facts and
materializes them as a local JSONL handoff queue.

Path:

    context.bus.jsonl
    -> 0178 context bus scheduler intake reader
    -> authorized SchedulerRouteRequest mapping
    -> SchedulerRouteRequest.from_mapping(...)
    -> scheduler.route_requests.jsonl

Boundary:

- This module requires an explicit policy_decision_id.
- This module validates each queued item with SchedulerRouteRequest.from_mapping.
- This module does not call handle_scheduler_route_request.
- This module does not instantiate Scheduler.
- This module does not modify Scheduler.run().
- This module does not instantiate EventBus.
- This module does not write ControlProxy/RouteProxy frames.
- This module does not write to VisPy.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from context.github_artifact_context_bus_scheduler_intake import (
    read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl,
)
from runtime.scheduler_route_adapter import SchedulerRouteRequest


AUTHORIZED_ROUTE_REQUEST_QUEUE_SCHEMA = "missipy.scheduler.authorized_route_request_queue.v1"
GITHUB_RESEARCH_SCHEDULER_INTAKE_REPORT_SCHEMA = (
    "missipy.github.research_scheduler_intake_report.v1"
)
GITHUB_RESEARCH_SCHEDULER_INTAKE_SCHEMA = "missipy.github.research_scheduler_intake.v1"
GITHUB_RESEARCH_SCHEDULER_QUEUE_HANDOFF_SCHEMA = (
    "missipy.github.research_scheduler_intake_queue_handoff.v1"
)
DEFAULT_ROUTE_REQUEST_QUEUE_NAME = "scheduler.route_requests.jsonl"


class AuthorizedRouteRequestQueueError(ValueError):
    """Raised when authorized route request handoff is unsafe."""


@dataclass(frozen=True, slots=True)
class AuthorizedRouteRequestQueueReport:
    """Result of appending authorized route requests to a local handoff queue."""

    schema: str
    queue_path: str
    queued_count: int
    policy_decision_id: str
    authorized_only: bool
    scheduler_modified: bool
    handler_called: bool
    frames_written: bool

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "queue_path": self.queue_path,
            "queued_count": self.queued_count,
            "policy_decision_id": self.policy_decision_id,
            "authorized_only": self.authorized_only,
            "scheduler_modified": self.scheduler_modified,
            "handler_called": self.handler_called,
            "frames_written": self.frames_written,
        }


@dataclass(frozen=True, slots=True)
class AuthorizedGitHubResearchSchedulerQueueReport:
    """Result of one explicit GitHub research intake queue handoff."""

    schema: str
    valid: bool
    status: str
    queue_path: str
    request_id: str
    route_id: str
    task_id: str
    policy_decision_id: str
    repository: str
    run_id: str
    action: str
    queued_count: int
    replayed_count: int
    authorized_only: bool
    scheduler_modified: bool
    scheduler_started: bool
    dispatcher_used: bool
    eventbus_used: bool
    handler_called: bool
    frames_written: bool

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "status": self.status,
            "queue_path": self.queue_path,
            "request_id": self.request_id,
            "route_id": self.route_id,
            "task_id": self.task_id,
            "policy_decision_id": self.policy_decision_id,
            "repository": self.repository,
            "run_id": self.run_id,
            "action": self.action,
            "queued_count": self.queued_count,
            "replayed_count": self.replayed_count,
            "authorized_only": self.authorized_only,
            "scheduler_modified": self.scheduler_modified,
            "scheduler_started": self.scheduler_started,
            "dispatcher_used": self.dispatcher_used,
            "eventbus_used": self.eventbus_used,
            "handler_called": self.handler_called,
            "frames_written": self.frames_written,
        }


def append_authorized_github_research_scheduler_intake(
    *,
    scheduler_intake_report: Mapping[str, Any],
    runtime_root: Path | str,
    policy_decision_id: str,
    repository: str,
    run_id: str | int,
    queue_name: str = DEFAULT_ROUTE_REQUEST_QUEUE_NAME,
) -> AuthorizedGitHubResearchSchedulerQueueReport:
    """Queue exactly one authorized GitHub research Scheduler request.

    This is the process-boundary handoff from the artifact intake command to
    the canonical local Scheduler server. It validates and durably appends one
    existing ``SchedulerRouteRequest`` mapping. It does not start a Scheduler,
    use the kernel Dispatcher, publish an EventBus command, call a handler, or
    start a laboratory.
    """

    if not isinstance(scheduler_intake_report, Mapping):
        raise AuthorizedRouteRequestQueueError(
            "scheduler_intake_report must be an object"
        )

    policy = _require_policy_decision_id(policy_decision_id)
    expected_repository = _require_repository(repository)
    expected_run_id = _require_run_id(run_id)
    report = dict(scheduler_intake_report)

    if report.get("schema") != GITHUB_RESEARCH_SCHEDULER_INTAKE_REPORT_SCHEMA:
        raise AuthorizedRouteRequestQueueError(
            "unsupported GitHub research Scheduler intake report schema"
        )
    if report.get("valid") is not True:
        raise AuthorizedRouteRequestQueueError(
            "GitHub research Scheduler intake report must be valid"
        )
    if report.get("status") != "scheduler-requests-ready":
        raise AuthorizedRouteRequestQueueError(
            "GitHub research Scheduler intake report is not ready"
        )

    results = report.get("results")
    if not isinstance(results, list) or len(results) != 1:
        raise AuthorizedRouteRequestQueueError(
            "exactly one GitHub research Scheduler intake result is required"
        )
    result = results[0]
    if not isinstance(result, Mapping):
        raise AuthorizedRouteRequestQueueError(
            "GitHub research Scheduler intake result must be an object"
        )

    _validate_authorized_github_research_intake_result(result)
    route_candidate = result.get("research_route_candidate")
    assert isinstance(route_candidate, Mapping)
    if route_candidate.get("repository") != expected_repository:
        raise AuthorizedRouteRequestQueueError("repository mismatch")
    if str(route_candidate.get("run_id", "")) != expected_run_id:
        raise AuthorizedRouteRequestQueueError("run_id mismatch")

    policy_decision = result.get("policy_decision")
    assert isinstance(policy_decision, Mapping)
    if policy_decision.get("policy_decision_id") != policy:
        raise AuthorizedRouteRequestQueueError("policy_decision_id mismatch")

    route_raw = result.get("scheduler_route_request")
    assert isinstance(route_raw, Mapping)
    request = SchedulerRouteRequest.from_mapping(route_raw)
    if not request.authorized:
        raise AuthorizedRouteRequestQueueError(
            "only authorized SchedulerRouteRequest items may be queued"
        )
    if request.policy_decision_id != policy:
        raise AuthorizedRouteRequestQueueError(
            "queued policy_decision_id mismatch"
        )

    queue_path = _resolve_queue_path(Path(runtime_root), queue_name)
    action = _append_request_idempotently(queue_path, request)
    queued_count = 1 if action == "queued" else 0
    replayed_count = 1 if action == "replay" else 0

    return AuthorizedGitHubResearchSchedulerQueueReport(
        schema=GITHUB_RESEARCH_SCHEDULER_QUEUE_HANDOFF_SCHEMA,
        valid=True,
        status=(
            "queued-for-canonical-scheduler"
            if action == "queued"
            else "already-queued"
        ),
        queue_path=str(queue_path),
        request_id=request.request_id,
        route_id=request.route_id,
        task_id=request.task_id,
        policy_decision_id=policy,
        repository=expected_repository,
        run_id=expected_run_id,
        action=action,
        queued_count=queued_count,
        replayed_count=replayed_count,
        authorized_only=True,
        scheduler_modified=False,
        scheduler_started=False,
        dispatcher_used=False,
        eventbus_used=False,
        handler_called=False,
        frames_written=False,
    )


def append_authorized_route_requests_from_context_bus(
    *,
    context_bus_path: Path | str,
    runtime_root: Path | str,
    policy_decision_id: str,
    priority: int = 50,
    queue_name: str = DEFAULT_ROUTE_REQUEST_QUEUE_NAME,
) -> AuthorizedRouteRequestQueueReport:
    """Append authorized SchedulerRouteRequest mappings to a local JSONL queue.

    This is a handoff queue only. The function validates and appends authorized
    route requests. It does not execute them.
    """

    policy = _require_policy_decision_id(policy_decision_id)
    root = Path(runtime_root)
    queue_path = _resolve_queue_path(root, queue_name)
    plans = read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl(
        Path(context_bus_path),
        policy_decision_id=policy,
        authorized=True,
        priority=priority,
    )

    queued_count = 0
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as handle:
        for plan in plans:
            if plan.scheduler_route_request is None:
                raise AuthorizedRouteRequestQueueError("authorized intake plan did not contain SchedulerRouteRequest")
            request = SchedulerRouteRequest.from_mapping(plan.scheduler_route_request)
            if not request.authorized:
                raise AuthorizedRouteRequestQueueError("only authorized SchedulerRouteRequest items may be queued")
            if request.policy_decision_id != policy:
                raise AuthorizedRouteRequestQueueError("queued policy_decision_id mismatch")
            handle.write(json.dumps(request.to_mapping(), sort_keys=True, separators=(",", ":")) + "\n")
            queued_count += 1

    return AuthorizedRouteRequestQueueReport(
        schema=AUTHORIZED_ROUTE_REQUEST_QUEUE_SCHEMA,
        queue_path=str(queue_path),
        queued_count=queued_count,
        policy_decision_id=policy,
        authorized_only=True,
        scheduler_modified=False,
        handler_called=False,
        frames_written=False,
    )


def iter_authorized_route_request_queue(path: Path | str) -> Iterable[SchedulerRouteRequest]:
    """Read queued SchedulerRouteRequest objects from a JSONL handoff queue."""

    queue_path = Path(path)
    with queue_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise AuthorizedRouteRequestQueueError(
                    f"invalid route request queue JSON at {queue_path}:{line_number}"
                ) from exc
            if not isinstance(item, Mapping):
                raise AuthorizedRouteRequestQueueError(
                    f"route request queue line must be an object at {queue_path}:{line_number}"
                )
            request = SchedulerRouteRequest.from_mapping(item)
            if not request.authorized:
                raise AuthorizedRouteRequestQueueError("route request queue contains unauthorized item")
            yield request


def _validate_authorized_github_research_intake_result(
    value: Mapping[str, Any],
) -> None:
    if value.get("schema") != GITHUB_RESEARCH_SCHEDULER_INTAKE_SCHEMA:
        raise AuthorizedRouteRequestQueueError(
            "unsupported GitHub research Scheduler intake schema"
        )
    if value.get("valid") is not True:
        raise AuthorizedRouteRequestQueueError(
            "GitHub research Scheduler intake must be valid"
        )
    if value.get("authorized") is not True:
        raise AuthorizedRouteRequestQueueError(
            "GitHub research Scheduler intake must be authorized"
        )
    if value.get("status") != "scheduler-request-ready":
        raise AuthorizedRouteRequestQueueError(
            "GitHub research Scheduler intake is not ready"
        )
    if value.get("scheduler_dispatch_started") is not False:
        raise AuthorizedRouteRequestQueueError(
            "Scheduler dispatch must not have started before queue handoff"
        )
    if value.get("laboratory_execution_started") is not False:
        raise AuthorizedRouteRequestQueueError(
            "laboratory execution must not have started before queue handoff"
        )

    for field_name in (
        "research_route_candidate",
        "policy_decision",
        "scheduler_route_request",
    ):
        if not isinstance(value.get(field_name), Mapping):
            raise AuthorizedRouteRequestQueueError(
                f"{field_name} must be an object"
            )


def _append_request_idempotently(
    queue_path: Path,
    request: SchedulerRouteRequest,
) -> str:
    expected = request.to_mapping()
    if queue_path.exists():
        for current in iter_authorized_route_request_queue(queue_path):
            if current.request_id != request.request_id:
                continue
            if current.to_mapping() != expected:
                raise AuthorizedRouteRequestQueueError(
                    "request_id collision with a different queued payload"
                )
            return "replay"

    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(expected, sort_keys=True, separators=(",", ":")))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    return "queued"


def _require_repository(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuthorizedRouteRequestQueueError("repository is required")
    stripped = value.strip()
    parts = stripped.split("/")
    if len(parts) != 2 or not all(parts):
        raise AuthorizedRouteRequestQueueError(
            "repository must use owner/name format"
        )
    for part in parts:
        allowed = part.replace("_", "").replace(".", "").replace("-", "")
        if not allowed.isalnum():
            raise AuthorizedRouteRequestQueueError(
                "repository contains invalid characters"
            )
    return stripped


def _require_run_id(value: str | int) -> str:
    if isinstance(value, bool):
        raise AuthorizedRouteRequestQueueError("run_id must be numeric")
    stripped = str(value).strip()
    if not stripped.isdigit():
        raise AuthorizedRouteRequestQueueError("run_id must be numeric")
    return stripped


def _resolve_queue_path(runtime_root: Path, queue_name: str) -> Path:
    if not queue_name or "/" in queue_name or "\\" in queue_name or ".." in queue_name:
        raise AuthorizedRouteRequestQueueError("queue_name must be a local filename")
    if not queue_name.endswith(".jsonl"):
        raise AuthorizedRouteRequestQueueError("queue_name must end with .jsonl")
    return runtime_root / queue_name


def _require_policy_decision_id(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuthorizedRouteRequestQueueError("policy_decision_id is required")
    stripped = value.strip()
    allowed = stripped.replace("_", "").replace(".", "").replace(":", "").replace("-", "")
    if not allowed.isalnum():
        raise AuthorizedRouteRequestQueueError("policy_decision_id contains invalid characters")
    return stripped

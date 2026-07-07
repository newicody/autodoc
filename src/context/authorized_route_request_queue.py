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
from pathlib import Path
from typing import Any, Iterable, Mapping

from context.github_artifact_context_bus_scheduler_intake import (
    read_github_artifact_scheduler_intake_plans_from_context_bus_jsonl,
)
from runtime.scheduler_route_adapter import SchedulerRouteRequest


AUTHORIZED_ROUTE_REQUEST_QUEUE_SCHEMA = "missipy.scheduler.authorized_route_request_queue.v1"
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

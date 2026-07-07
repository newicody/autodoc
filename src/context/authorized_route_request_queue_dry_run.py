"""Authorized route request queue dry-run audit.

0180 reads the local scheduler.route_requests.jsonl handoff queue produced by
0179 and audits whether queued SchedulerRouteRequest items are structurally
ready for a later handler handoff.

This is dry-run only.

Path:

    scheduler.route_requests.jsonl
    -> iter_authorized_route_request_queue(...)
    -> SchedulerRouteRequest objects
    -> readiness/audit report

Boundary:

- This module does not call handle_scheduler_route_request.
- This module does not import the route handler as an executable dependency.
- This module does not instantiate Scheduler.
- This module does not modify Scheduler.run().
- This module does not instantiate EventBus.
- This module does not write ControlProxy or RouteProxy frames.
- This module does not write to VisPy.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from context.authorized_route_request_queue import iter_authorized_route_request_queue
from runtime.scheduler_route_adapter import SchedulerRouteRequest


ROUTE_REQUEST_QUEUE_DRY_RUN_AUDIT_SCHEMA = "missipy.scheduler.route_request_queue_dry_run_audit.v1"

EXPECTED_HANDLER_SURFACES = (
    "src/runtime/scheduler_route_adapter.py",
    "src/runtime/scheduler_route_handler_minimal.py",
    "src/runtime/scheduler_route_handshake.py",
    "src/runtime/controlproxy_scheduler_handler.py",
)


class RouteRequestQueueDryRunAuditError(ValueError):
    """Raised when a dry-run audit cannot be completed safely."""


@dataclass(frozen=True, slots=True)
class RouteRequestQueueDryRunItem:
    """One queued route request dry-run result."""

    index: int
    request_id: str
    route_id: str
    task_id: str
    authorized: bool
    policy_decision_id: str | None
    ready_for_later_handler_handoff: bool
    issues: tuple[str, ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "request_id": self.request_id,
            "route_id": self.route_id,
            "task_id": self.task_id,
            "authorized": self.authorized,
            "policy_decision_id": self.policy_decision_id,
            "ready_for_later_handler_handoff": self.ready_for_later_handler_handoff,
            "issues": list(self.issues),
        }


@dataclass(frozen=True, slots=True)
class RouteRequestQueueDryRunAuditReport:
    """Dry-run audit report for a route request handoff queue."""

    schema: str
    queue_path: str
    item_count: int
    ready_count: int
    blocked_count: int
    handler_surfaces: Mapping[str, bool]
    items: tuple[RouteRequestQueueDryRunItem, ...]
    dry_run_only: bool
    scheduler_modified: bool
    handler_called: bool
    frames_written: bool

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "queue_path": self.queue_path,
            "item_count": self.item_count,
            "ready_count": self.ready_count,
            "blocked_count": self.blocked_count,
            "handler_surfaces": dict(self.handler_surfaces),
            "items": [item.to_mapping() for item in self.items],
            "dry_run_only": self.dry_run_only,
            "scheduler_modified": self.scheduler_modified,
            "handler_called": self.handler_called,
            "frames_written": self.frames_written,
        }


def audit_authorized_route_request_queue_dry_run(
    queue_path: Path | str,
    *,
    repo_root: Path | str | None = None,
) -> RouteRequestQueueDryRunAuditReport:
    """Validate and audit queued authorized route requests without executing them."""

    queue = Path(queue_path)
    root = Path(repo_root) if repo_root is not None else _infer_repo_root()
    handler_surfaces = _handler_surface_presence(root)

    items = tuple(
        _audit_request(index, request)
        for index, request in enumerate(iter_authorized_route_request_queue(queue), start=1)
    )
    ready_count = sum(1 for item in items if item.ready_for_later_handler_handoff)
    blocked_count = len(items) - ready_count
    return RouteRequestQueueDryRunAuditReport(
        schema=ROUTE_REQUEST_QUEUE_DRY_RUN_AUDIT_SCHEMA,
        queue_path=str(queue),
        item_count=len(items),
        ready_count=ready_count,
        blocked_count=blocked_count,
        handler_surfaces=handler_surfaces,
        items=items,
        dry_run_only=True,
        scheduler_modified=False,
        handler_called=False,
        frames_written=False,
    )


def _audit_request(index: int, request: SchedulerRouteRequest) -> RouteRequestQueueDryRunItem:
    issues: list[str] = []
    if not request.authorized:
        issues.append("request is not authorized")
    if not request.policy_decision_id:
        issues.append("missing policy_decision_id")
    if not request.route_id:
        issues.append("missing route_id")
    if not request.task_id:
        issues.append("missing task_id")
    ready = not issues
    return RouteRequestQueueDryRunItem(
        index=index,
        request_id=request.request_id,
        route_id=request.route_id,
        task_id=request.task_id,
        authorized=request.authorized,
        policy_decision_id=request.policy_decision_id,
        ready_for_later_handler_handoff=ready,
        issues=tuple(issues),
    )


def _handler_surface_presence(repo_root: Path) -> dict[str, bool]:
    return {relative: (repo_root / relative).exists() for relative in EXPECTED_HANDLER_SURFACES}


def _infer_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]

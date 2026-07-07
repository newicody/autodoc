#!/usr/bin/env python3
"""Build a dry-run SchedulerRouteRequest to SchedulerRouteHandlerCommand plan.

0184 is a planning tool only.

It reads scheduler.route_requests.jsonl through the existing 0179 queue reader
and builds reviewable keyword arguments for the existing
build_single_frame_route_command surface discovered by 0183.

It does not import runtime handler modules.
It does not call build_single_frame_route_command.
It does not call handle_scheduler_route_command.
It does not call handle_scheduler_route_request.
It does not modify Scheduler.run.
It does not instantiate Scheduler.
It does not instantiate EventBus.
It does not write RouteProxy or ControlProxy frames.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.authorized_route_request_queue import iter_authorized_route_request_queue  # noqa: E402


ROUTE_REQUEST_TO_COMMAND_DRY_RUN_PLAN_SCHEMA = "missipy.route_request.to_command_dry_run_plan.v1"
DEFAULT_OUTPUT_NAME = "route_request_to_command_dry_run_plan.jsonl"
TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
DEFAULT_FRAME_KIND = "runtime_probe"


class RouteRequestToCommandDryRunPlanError(ValueError):
    """Raised when the dry-run request-to-command plan is unsafe."""


def build_route_request_to_command_dry_run_plan(
    *,
    queue_path: Path | str,
    output_path: Path | str | None = None,
    frame_kind: str = DEFAULT_FRAME_KIND,
) -> dict[str, Any]:
    """Build dry-run command-builder keyword plans from authorized route requests."""

    queue = Path(queue_path)
    items: list[dict[str, Any]] = []
    for index, request in enumerate(iter_authorized_route_request_queue(queue), start=1):
        item = _request_to_command_builder_item(index, request, frame_kind=frame_kind)
        items.append(item)

    if output_path is not None:
        _write_plan_jsonl(Path(output_path), items)

    ready_count = sum(1 for item in items if item["ready_for_later_command_builder_call"])
    return {
        "schema": ROUTE_REQUEST_TO_COMMAND_DRY_RUN_PLAN_SCHEMA,
        "queue_path": str(queue),
        "output_path": str(output_path) if output_path is not None else None,
        "item_count": len(items),
        "ready_count": ready_count,
        "blocked_count": len(items) - ready_count,
        "items": items,
        "dry_run_only": True,
        "runtime_imports_executed": False,
        "builder_called": False,
        "handler_called": False,
        "scheduler_modified": False,
        "frames_written": False,
    }


def _request_to_command_builder_item(index: int, request: Any, *, frame_kind: str) -> dict[str, Any]:
    request_mapping = request.to_mapping()
    command_ref = _typed_ref("scheduler-command", request.task_id)
    route_ref = _typed_ref("route", request.route_id)
    owner_ref = _typed_ref("scheduler-command", request.task_id)
    context_ref = _typed_ref("ctx", request.request_id)
    context_generation = 1
    priority = _request_priority(request_mapping)
    payload = {
        "source_schema": request_mapping.get("schema"),
        "request_id": request.request_id,
        "route_id": request.route_id,
        "task_id": request.task_id,
        "holder": request_mapping.get("holder"),
        "scope": request_mapping.get("scope"),
        "policy_decision_id": request.policy_decision_id,
        "authorized": request.authorized,
        "dry_run_planned_by": ROUTE_REQUEST_TO_COMMAND_DRY_RUN_PLAN_SCHEMA,
    }

    builder_kwargs = {
        "command_ref": command_ref,
        "route_ref": route_ref,
        "owner_ref": owner_ref,
        "context_ref": context_ref,
        "context_generation": context_generation,
        "priority": priority,
        "frame_kind": frame_kind,
        "payload": payload,
        "runtime_policy": None,
    }

    issues = _validate_builder_kwargs(builder_kwargs)
    if not request.authorized:
        issues.append("request is not authorized")
    if not request.policy_decision_id:
        issues.append("missing policy_decision_id")

    return {
        "index": index,
        "request_id": request.request_id,
        "route_id": request.route_id,
        "task_id": request.task_id,
        "policy_decision_id": request.policy_decision_id,
        "authorized": request.authorized,
        "builder_surface": "build_single_frame_route_command",
        "handler_surface": "handle_scheduler_route_command",
        "builder_kwargs": builder_kwargs,
        "ready_for_later_command_builder_call": not issues,
        "issues": issues,
    }


def _request_priority(mapping: Mapping[str, Any]) -> int:
    value = mapping.get("priority")
    if isinstance(value, int):
        return max(0, min(10000, value))
    return 50


def _typed_ref(prefix: str, raw: object) -> str:
    value = str(raw or "").strip()
    if not value:
        value = "missing"
    if TYPED_REF_RE.match(value):
        return value
    safe = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", value).strip("-")
    if not safe:
        safe = "missing"
    return f"{prefix}:{safe}"


def _validate_builder_kwargs(kwargs: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    for name in ("command_ref", "route_ref", "owner_ref", "context_ref"):
        value = kwargs.get(name)
        if not isinstance(value, str) or not TYPED_REF_RE.match(value):
            issues.append(f"{name} is not a typed ref")
    generation = kwargs.get("context_generation")
    if not isinstance(generation, int) or generation <= 0:
        issues.append("context_generation must be a positive integer")
    priority = kwargs.get("priority")
    if not isinstance(priority, int) or priority < 0 or priority > 10000:
        issues.append("priority must be between 0 and 10000")
    if kwargs.get("frame_kind") != DEFAULT_FRAME_KIND:
        issues.append("frame_kind must remain runtime_probe in 0184")
    if not isinstance(kwargs.get("payload"), dict):
        issues.append("payload must be a dict")
    return issues


def _write_plan_jsonl(path: Path, items: list[Mapping[str, Any]]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise RouteRequestToCommandDryRunPlanError("output filename must be route_request_to_command_dry_run_plan.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(dict(item), sort_keys=True, separators=(",", ":")) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build dry-run SchedulerRouteRequest to SchedulerRouteHandlerCommand plan.")
    parser.add_argument("--queue", required=True, help="Path to scheduler.route_requests.jsonl.")
    parser.add_argument("--output", help="Optional route_request_to_command_dry_run_plan.jsonl output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = build_route_request_to_command_dry_run_plan(
        queue_path=Path(args.queue),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"item_count: {report['item_count']}")
        print(f"ready_count: {report['ready_count']}")
        print(f"blocked_count: {report['blocked_count']}")
        print("dry_run_only: True")
        print("builder_called: False")
        print("handler_called: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

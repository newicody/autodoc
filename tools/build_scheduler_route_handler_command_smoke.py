#!/usr/bin/env python3
"""Smoke-build SchedulerRouteHandlerCommand objects from a dry-run plan.

0185 is a command-builder smoke only.

It reads route_request_to_command_dry_run_plan.jsonl from 0184, imports only the
existing build_single_frame_route_command builder surface, builds immutable
SchedulerRouteHandlerCommand objects, and optionally writes
scheduler_route_handler_command_smoke.jsonl.

It does not call handle_scheduler_route_command.
It does not call handle_scheduler_route_request.
It does not prepare RouteProxyRuntime.
It does not write RouteProxy or ControlProxy frames.
It does not modify Scheduler.run.
It does not instantiate Scheduler.
It does not instantiate EventBus.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime.scheduler_route_handler_minimal import (  # noqa: E402
    SchedulerRouteHandlerCommand,
    build_single_frame_route_command,
)


SCHEDULER_ROUTE_HANDLER_COMMAND_BUILDER_SMOKE_SCHEMA = "missipy.scheduler.route_handler.command_builder_smoke.v1"
DEFAULT_INPUT_NAME = "route_request_to_command_dry_run_plan.jsonl"
DEFAULT_OUTPUT_NAME = "scheduler_route_handler_command_smoke.jsonl"


class SchedulerRouteHandlerCommandBuilderSmokeError(ValueError):
    """Raised when command-builder smoke input is unsafe."""


def build_scheduler_route_handler_command_smoke(
    *,
    plan_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build SchedulerRouteHandlerCommand mappings from a reviewed dry-run plan."""

    plan = Path(plan_path)
    items = list(_read_plan_items(plan))
    smoke_items: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        smoke_items.append(_smoke_build_item(index, item))

    if output_path is not None:
        _write_smoke_jsonl(Path(output_path), smoke_items)

    built_count = sum(1 for item in smoke_items if item["command_built"])
    blocked_count = len(smoke_items) - built_count
    return {
        "schema": SCHEDULER_ROUTE_HANDLER_COMMAND_BUILDER_SMOKE_SCHEMA,
        "plan_path": str(plan),
        "output_path": str(output_path) if output_path is not None else None,
        "item_count": len(smoke_items),
        "built_count": built_count,
        "blocked_count": blocked_count,
        "items": smoke_items,
        "builder_imported": True,
        "builder_called": True,
        "handler_called": False,
        "routeproxy_prepared": False,
        "scheduler_modified": False,
        "frames_written": False,
    }


def _smoke_build_item(index: int, item: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not item.get("ready_for_later_command_builder_call"):
        issues.append("plan item is not ready for command builder call")
    if item.get("builder_surface") != "build_single_frame_route_command":
        issues.append("unexpected builder surface")
    if item.get("handler_surface") != "handle_scheduler_route_command":
        issues.append("unexpected handler surface")
    raw_kwargs = item.get("builder_kwargs")
    if not isinstance(raw_kwargs, Mapping):
        issues.append("builder_kwargs must be an object")
        raw_kwargs = {}

    command_mapping: dict[str, Any] | None = None
    command_type: str | None = None
    if not issues:
        try:
            command = build_single_frame_route_command(**dict(raw_kwargs))
        except Exception as exc:  # smoke reports validation errors, it does not hide them
            issues.append(f"builder validation failed: {exc}")
        else:
            if not isinstance(command, SchedulerRouteHandlerCommand):
                issues.append("builder did not return SchedulerRouteHandlerCommand")
            else:
                command_type = type(command).__name__
                command_mapping = command.to_mapping()

    return {
        "index": index,
        "source_request_id": item.get("request_id"),
        "source_route_id": item.get("route_id"),
        "source_task_id": item.get("task_id"),
        "policy_decision_id": item.get("policy_decision_id"),
        "builder_surface": "build_single_frame_route_command",
        "handler_surface": "handle_scheduler_route_command",
        "command_type": command_type,
        "command_mapping": command_mapping,
        "command_built": command_mapping is not None and not issues,
        "ready_for_later_handler_call": command_mapping is not None and not issues,
        "issues": issues,
    }


def _read_plan_items(path: Path) -> Iterable[dict[str, Any]]:
    if path.name != DEFAULT_INPUT_NAME:
        raise SchedulerRouteHandlerCommandBuilderSmokeError("input filename must be route_request_to_command_dry_run_plan.jsonl")
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise SchedulerRouteHandlerCommandBuilderSmokeError(
                    f"invalid plan JSON at {path}:{line_number}"
                ) from exc
            if not isinstance(item, dict):
                raise SchedulerRouteHandlerCommandBuilderSmokeError(
                    f"plan line must be an object at {path}:{line_number}"
                )
            yield item


def _write_smoke_jsonl(path: Path, items: list[Mapping[str, Any]]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise SchedulerRouteHandlerCommandBuilderSmokeError("output filename must be scheduler_route_handler_command_smoke.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(dict(item), sort_keys=True, separators=(",", ":")) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-build SchedulerRouteHandlerCommand from 0184 plan.")
    parser.add_argument("--plan", required=True, help="Path to route_request_to_command_dry_run_plan.jsonl.")
    parser.add_argument("--output", help="Optional scheduler_route_handler_command_smoke.jsonl output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = build_scheduler_route_handler_command_smoke(
        plan_path=Path(args.plan),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"item_count: {report['item_count']}")
        print(f"built_count: {report['built_count']}")
        print(f"blocked_count: {report['blocked_count']}")
        print("builder_called: True")
        print("handler_called: False")
        print("frames_written: False")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

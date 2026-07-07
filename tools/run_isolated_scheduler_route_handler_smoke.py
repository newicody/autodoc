#!/usr/bin/env python3
"""Run an isolated Scheduler route handler smoke.

0187 is the first controlled handler smoke.

It reads isolated_handler_execution_plan.jsonl from 0186, reconstructs a
SchedulerRouteHandlerCommand through the existing build_single_frame_route_command
builder, constructs RouteProxyRuntimePolicy with the explicit isolated root, and
calls handle_scheduler_route_command only for ready plan items.

It must write only inside the isolated runtime root from the plan.
It must not modify Scheduler.run.
It must not instantiate Scheduler.
It must not instantiate EventBus.
It must not write ControlProxy frames.
It must not call GitHub API or use network.
"""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime.route_proxy_runtime_minimal import RouteProxyRuntimePolicy  # noqa: E402
from runtime.scheduler_route_handler_minimal import (  # noqa: E402
    SchedulerRouteHandlerResult,
    build_single_frame_route_command,
    handle_scheduler_route_command,
)


ISOLATED_SCHEDULER_ROUTE_HANDLER_SMOKE_SCHEMA = "missipy.scheduler.route_handler.isolated_smoke.v1"
DEFAULT_INPUT_NAME = "isolated_handler_execution_plan.jsonl"
DEFAULT_OUTPUT_NAME = "isolated_scheduler_route_handler_smoke.jsonl"


class IsolatedSchedulerRouteHandlerSmokeError(ValueError):
    """Raised when the isolated handler smoke cannot run safely."""


def run_isolated_scheduler_route_handler_smoke(
    *,
    plan_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Run the existing route handler inside the explicit isolated runtime root."""

    plan = Path(plan_path)
    items = [_run_item(index, item) for index, item in enumerate(_read_plan_items(plan), start=1)]

    if output_path is not None:
        _write_smoke_jsonl(Path(output_path), items)

    executed_count = sum(1 for item in items if item["handler_called"])
    written_count = sum(len(item["written_route_refs"]) for item in items)
    blocked_count = sum(1 for item in items if not item["handler_called"])
    return {
        "schema": ISOLATED_SCHEDULER_ROUTE_HANDLER_SMOKE_SCHEMA,
        "plan_path": str(plan),
        "output_path": str(output_path) if output_path is not None else None,
        "item_count": len(items),
        "executed_count": executed_count,
        "blocked_count": blocked_count,
        "written_count": written_count,
        "items": items,
        "handler_called": executed_count > 0,
        "routeproxy_prepared": executed_count > 0,
        "frames_written": written_count > 0,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "eventbus_instantiated": False,
        "network_used": False,
    }


def _run_item(index: int, item: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not item.get("ready_for_later_isolated_handler_call"):
        issues.append("plan item is not ready for isolated handler call")
    if item.get("handler_call_allowed_by_0186") is not False:
        issues.append("0186 plan must not grant execution directly")
    isolated_root = Path(str(item.get("isolated_runtime_root") or ""))
    if not _safe_isolated_root(isolated_root):
        issues.append("isolated_runtime_root is unsafe")

    runtime_policy_kwargs = item.get("runtime_policy_kwargs")
    if not isinstance(runtime_policy_kwargs, Mapping):
        issues.append("runtime_policy_kwargs must be an object")
        runtime_policy_kwargs = {}

    command_mapping = item.get("command_mapping")
    if not isinstance(command_mapping, Mapping):
        issues.append("command_mapping must be an object")
        command_mapping = {}

    frame_requests = command_mapping.get("frame_requests")
    if not isinstance(frame_requests, list) or len(frame_requests) != 1 or not isinstance(frame_requests[0], Mapping):
        issues.append("0187 supports exactly one frame request")
        frame = {}
    else:
        frame = frame_requests[0]

    if issues:
        return _blocked_item(index, item, issues)

    policy = _build_runtime_policy(runtime_policy_kwargs, isolated_root)
    command = build_single_frame_route_command(
        command_ref=str(command_mapping["command_ref"]),
        route_ref=str(frame["route_ref"]),
        owner_ref=str(frame["owner_ref"]),
        context_ref=str(frame["context_ref"]),
        context_generation=int(frame["context_generation"]),
        priority=int(frame["priority"]),
        frame_kind=str(frame["frame_kind"]),
        payload=dict(frame["payload"]),
        runtime_policy=policy,
    )
    result = handle_scheduler_route_command(command)
    if not isinstance(result, SchedulerRouteHandlerResult):
        raise IsolatedSchedulerRouteHandlerSmokeError("handler did not return SchedulerRouteHandlerResult")

    result_mapping = result.to_mapping()
    runtime_root = Path(str(result_mapping.get("runtime_root")))
    if not _is_within(runtime_root, isolated_root):
        raise IsolatedSchedulerRouteHandlerSmokeError("handler runtime_root escaped isolated_runtime_root")

    frame_paths = [Path(str(path)) for path in result_mapping.get("frame_paths", [])]
    for path in frame_paths:
        if not _is_within(path, isolated_root):
            raise IsolatedSchedulerRouteHandlerSmokeError("handler frame path escaped isolated_runtime_root")

    return {
        "index": index,
        "source_request_id": item.get("source_request_id"),
        "source_route_id": item.get("source_route_id"),
        "source_task_id": item.get("source_task_id"),
        "policy_decision_id": item.get("policy_decision_id"),
        "command_ref": command_mapping.get("command_ref"),
        "isolated_runtime_root": str(isolated_root),
        "handler_surface": "handle_scheduler_route_command",
        "handler_called": True,
        "routeproxy_prepared": True,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "written_route_refs": list(result_mapping.get("written_route_refs", [])),
        "denied_route_refs": list(result_mapping.get("denied_route_refs", [])),
        "frame_paths": [str(path) for path in frame_paths],
        "result_mapping": result_mapping,
        "issues": [],
    }


def _blocked_item(index: int, item: Mapping[str, Any], issues: list[str]) -> dict[str, Any]:
    return {
        "index": index,
        "source_request_id": item.get("source_request_id"),
        "source_route_id": item.get("source_route_id"),
        "source_task_id": item.get("source_task_id"),
        "policy_decision_id": item.get("policy_decision_id"),
        "command_ref": item.get("command_ref"),
        "isolated_runtime_root": str(item.get("isolated_runtime_root")),
        "handler_surface": "handle_scheduler_route_command",
        "handler_called": False,
        "routeproxy_prepared": False,
        "controlproxy_frames_written": False,
        "scheduler_modified": False,
        "written_route_refs": [],
        "denied_route_refs": [],
        "frame_paths": [],
        "result_mapping": None,
        "issues": issues,
    }


def _build_runtime_policy(raw_kwargs: Mapping[str, Any], isolated_root: Path) -> RouteProxyRuntimePolicy:
    signature = inspect.signature(RouteProxyRuntimePolicy)
    accepted = set(signature.parameters)
    kwargs: dict[str, Any] = {}
    for key, value in raw_kwargs.items():
        if key in accepted:
            if key.endswith("root") or key.endswith("_root") or key.endswith("_dir") or key.endswith("_path"):
                kwargs[key] = Path(str(value))
            else:
                kwargs[key] = value
    if "route_root" in accepted:
        kwargs["route_root"] = isolated_root
    if "runtime_root" in accepted:
        kwargs["runtime_root"] = isolated_root
    if "allow_test_root" in accepted:
        kwargs["allow_test_root"] = True
    if "require_dev_shm" in accepted:
        kwargs["require_dev_shm"] = False
    if "proxy_ref" in accepted and "proxy_ref" not in kwargs:
        kwargs["proxy_ref"] = "proxy:0187-isolated-handler-smoke"
    if "namespace" in accepted and "namespace" not in kwargs:
        kwargs["namespace"] = "0187-isolated-handler-smoke"
    return RouteProxyRuntimePolicy(**kwargs)


def _read_plan_items(path: Path) -> Iterable[dict[str, Any]]:
    if path.name != DEFAULT_INPUT_NAME:
        raise IsolatedSchedulerRouteHandlerSmokeError("input filename must be isolated_handler_execution_plan.jsonl")
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise IsolatedSchedulerRouteHandlerSmokeError(f"invalid plan JSON at {path}:{line_number}") from exc
            if not isinstance(item, dict):
                raise IsolatedSchedulerRouteHandlerSmokeError(f"plan line must be an object at {path}:{line_number}")
            yield item


def _write_smoke_jsonl(path: Path, items: list[Mapping[str, Any]]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise IsolatedSchedulerRouteHandlerSmokeError("output filename must be isolated_scheduler_route_handler_smoke.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for item in items:
            handle.write(json.dumps(dict(item), sort_keys=True, separators=(",", ":")) + "\n")


def _safe_isolated_root(path: Path) -> bool:
    if not path.is_absolute():
        return False
    resolved = path.resolve()
    if resolved == Path("/"):
        return False
    forbidden = {Path("/dev"), Path("/dev/shm"), Path("/proc"), Path("/sys"), Path("/run")}
    return all(resolved != forbidden_path for forbidden_path in forbidden)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run isolated Scheduler route handler smoke.")
    parser.add_argument("--plan", required=True, help="Path to isolated_handler_execution_plan.jsonl.")
    parser.add_argument("--output", help="Optional isolated_scheduler_route_handler_smoke.jsonl output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = run_isolated_scheduler_route_handler_smoke(
        plan_path=Path(args.plan),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"item_count: {report['item_count']}")
        print(f"executed_count: {report['executed_count']}")
        print(f"blocked_count: {report['blocked_count']}")
        print(f"written_count: {report['written_count']}")
        print(f"handler_called: {report['handler_called']}")
        print(f"frames_written: {report['frames_written']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

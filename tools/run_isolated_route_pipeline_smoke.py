#!/usr/bin/env python3
"""Run the isolated route pipeline smoke end to end.

0189 is an isolated pipeline smoke. It reuses the existing staged surfaces:

- 0179 authorized route request queue handoff
- 0184 route request to command dry-run plan
- 0185 SchedulerRouteHandlerCommand builder smoke
- 0186 isolated handler execution plan
- 0187 isolated Scheduler route handler smoke
- 0188 isolated Scheduler route handler readback smoke

It executes the existing handler only through the 0187 isolated smoke stage and
only with the explicit isolated runtime root.

It must not modify Scheduler.run.
It must not instantiate Scheduler.
It must not instantiate EventBus.
It must not write ControlProxy frames.
It must not call GitHub API or use network.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.authorized_route_request_queue import append_authorized_route_requests_from_context_bus  # noqa: E402


ISOLATED_ROUTE_PIPELINE_SMOKE_SCHEMA = "missipy.route_pipeline.isolated_smoke.v1"
DEFAULT_OUTPUT_NAME = "isolated_route_pipeline_smoke.json"
POLICY_SCOPED_QUEUE_NAME = "scheduler.route_requests.policy_scoped.jsonl"


class IsolatedRoutePipelineSmokeError(ValueError):
    """Raised when the isolated pipeline smoke cannot run safely."""


def run_isolated_route_pipeline_smoke(
    *,
    context_bus_path: Path | str,
    runtime_root: Path | str,
    policy_decision_id: str,
    isolated_runtime_root: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Run the complete isolated route pipeline smoke using existing stages."""

    runtime = Path(runtime_root)
    isolated_root = Path(isolated_runtime_root)
    if not isolated_root.is_absolute():
        raise IsolatedRoutePipelineSmokeError("isolated_runtime_root must be absolute")
    runtime.mkdir(parents=True, exist_ok=True)

    stage_0184 = _load_tool("build_route_request_to_command_dry_run_plan.py", "stage_0184_route_request_to_command")
    stage_0185 = _load_tool("build_scheduler_route_handler_command_smoke.py", "stage_0185_command_builder_smoke")
    stage_0186 = _load_tool("build_isolated_handler_execution_plan.py", "stage_0186_isolated_plan")
    stage_0187 = _load_tool("run_isolated_scheduler_route_handler_smoke.py", "stage_0187_isolated_handler")
    stage_0188 = _load_tool("readback_isolated_scheduler_route_handler_smoke.py", "stage_0188_readback")

    queue_report = append_authorized_route_requests_from_context_bus(
        context_bus_path=Path(context_bus_path),
        runtime_root=runtime,
        policy_decision_id=policy_decision_id,
    )
    queue_path = Path(queue_report.queue_path)
    policy_scoped_queue_path = runtime / POLICY_SCOPED_QUEUE_NAME
    policy_scoped_count = _write_policy_scoped_queue(
        source_queue_path=queue_path,
        scoped_queue_path=policy_scoped_queue_path,
        policy_decision_id=policy_decision_id,
    )

    command_plan_path = runtime / "route_request_to_command_dry_run_plan.jsonl"
    command_plan_report = stage_0184.build_route_request_to_command_dry_run_plan(
        queue_path=policy_scoped_queue_path,
        output_path=command_plan_path,
    )

    command_smoke_path = runtime / "scheduler_route_handler_command_smoke.jsonl"
    command_smoke_report = stage_0185.build_scheduler_route_handler_command_smoke(
        plan_path=command_plan_path,
        output_path=command_smoke_path,
    )

    isolated_plan_path = runtime / "isolated_handler_execution_plan.jsonl"
    isolated_plan_report = stage_0186.build_isolated_handler_execution_plan(
        smoke_path=command_smoke_path,
        repo_root=ROOT,
        isolated_runtime_root=isolated_root,
        output_path=isolated_plan_path,
    )

    handler_smoke_path = runtime / "isolated_scheduler_route_handler_smoke.jsonl"
    handler_smoke_report = stage_0187.run_isolated_scheduler_route_handler_smoke(
        plan_path=isolated_plan_path,
        output_path=handler_smoke_path,
    )

    readback_smoke_path = runtime / "isolated_scheduler_route_handler_readback_smoke.jsonl"
    readback_smoke_report = stage_0188.run_isolated_scheduler_route_handler_readback_smoke(
        smoke_path=handler_smoke_path,
        output_path=readback_smoke_path,
    )

    report = {
        "schema": ISOLATED_ROUTE_PIPELINE_SMOKE_SCHEMA,
        "context_bus_path": str(context_bus_path),
        "runtime_root": str(runtime),
        "isolated_runtime_root": str(isolated_root),
        "policy_decision_id": policy_decision_id,
        "artifacts": {
            "queue": str(queue_path),
            "policy_scoped_queue": str(policy_scoped_queue_path),
            "route_request_to_command_plan": str(command_plan_path),
            "command_builder_smoke": str(command_smoke_path),
            "isolated_handler_execution_plan": str(isolated_plan_path),
            "isolated_handler_smoke": str(handler_smoke_path),
            "isolated_handler_readback_smoke": str(readback_smoke_path),
        },
        "stage_reports": {
            "0179_authorized_route_request_queue": queue_report.to_mapping(),
            "0184_route_request_to_command_plan": _compact_stage_report(command_plan_report),
            "0185_command_builder_smoke": _compact_stage_report(command_smoke_report),
            "0186_isolated_handler_execution_plan": _compact_stage_report(isolated_plan_report),
            "0187_isolated_handler_smoke": _compact_stage_report(handler_smoke_report),
            "0188_isolated_readback_smoke": _compact_stage_report(readback_smoke_report),
        },
        "queued_count": queue_report.queued_count,
        "policy_scoped_queued_count": policy_scoped_count,
        "command_plan_ready_count": int(command_plan_report.get("ready_count", 0)),
        "command_built_count": int(command_smoke_report.get("built_count", 0)),
        "handler_executed_count": int(handler_smoke_report.get("executed_count", 0)),
        "frames_written_count": int(handler_smoke_report.get("written_count", 0)),
        "readback_count": int(readback_smoke_report.get("readback_count", 0)),
        "pipeline_success": _pipeline_success(
            queued_count=queue_report.queued_count,
            policy_scoped_queued_count=policy_scoped_count,
            command_plan_report=command_plan_report,
            command_smoke_report=command_smoke_report,
            handler_smoke_report=handler_smoke_report,
            readback_smoke_report=readback_smoke_report,
        ),
        "scheduler_modified": False,
        "eventbus_instantiated": False,
        "controlproxy_frames_written": False,
        "network_used": False,
    }

    if output_path is not None:
        _write_report(Path(output_path), report)

    return report


def _pipeline_success(
    *,
    queued_count: int,
    policy_scoped_queued_count: int,
    command_plan_report: dict[str, Any],
    command_smoke_report: dict[str, Any],
    handler_smoke_report: dict[str, Any],
    readback_smoke_report: dict[str, Any],
) -> bool:
    return (
        queued_count > 0
        and policy_scoped_queued_count == queued_count
        and command_plan_report.get("blocked_count") == 0
        and int(command_plan_report.get("ready_count", 0)) == policy_scoped_queued_count
        and int(command_smoke_report.get("built_count", 0)) == policy_scoped_queued_count
        and int(handler_smoke_report.get("executed_count", 0)) == policy_scoped_queued_count
        and command_smoke_report.get("blocked_count") == 0
        and handler_smoke_report.get("blocked_count") == 0
        and readback_smoke_report.get("blocked_count") == 0
        and int(handler_smoke_report.get("written_count", 0)) > 0
        and int(readback_smoke_report.get("readback_count", 0)) == int(handler_smoke_report.get("written_count", 0))
        and handler_smoke_report.get("scheduler_modified") is False
        and readback_smoke_report.get("scheduler_modified") is False
        and handler_smoke_report.get("controlproxy_frames_written") is False
        and readback_smoke_report.get("controlproxy_frames_written") is False
        and handler_smoke_report.get("network_used") is False
        and readback_smoke_report.get("network_used") is False
    )


def _write_policy_scoped_queue(
    *,
    source_queue_path: Path,
    scoped_queue_path: Path,
    policy_decision_id: str,
) -> int:
    if scoped_queue_path.name != POLICY_SCOPED_QUEUE_NAME:
        raise IsolatedRoutePipelineSmokeError("policy scoped queue filename must be scheduler.route_requests.policy_scoped.jsonl")
    count = 0
    scoped_queue_path.parent.mkdir(parents=True, exist_ok=True)
    with source_queue_path.open("r", encoding="utf-8") as source, scoped_queue_path.open("w", encoding="utf-8") as target:
        for line_number, line in enumerate(source, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                item = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise IsolatedRoutePipelineSmokeError(
                    f"invalid route request queue JSON at {source_queue_path}:{line_number}"
                ) from exc
            if not isinstance(item, Mapping):
                raise IsolatedRoutePipelineSmokeError(
                    f"route request queue line must be an object at {source_queue_path}:{line_number}"
                )
            if item.get("policy_decision_id") != policy_decision_id:
                continue
            target.write(json.dumps(dict(item), sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    if count == 0:
        raise IsolatedRoutePipelineSmokeError("policy scoped queue is empty")
    return count


def _compact_stage_report(report: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key in (
        "schema",
        "item_count",
        "queued_count",
        "ready_count",
        "built_count",
        "executed_count",
        "written_count",
        "readback_count",
        "blocked_count",
        "handler_called",
        "frames_written",
        "scheduler_modified",
        "controlproxy_frames_written",
        "network_used",
        "output_path",
        "queue_path",
        "plan_path",
        "smoke_path",
        "policy_scoped_queued_count",
    ):
        if key in report:
            compact[key] = report[key]
    return compact


def _load_tool(filename: str, name: str) -> ModuleType:
    path = ROOT / "tools" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise IsolatedRoutePipelineSmokeError(f"could not load tool module: {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_report(path: Path, report: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise IsolatedRoutePipelineSmokeError("output filename must be isolated_route_pipeline_smoke.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run isolated route pipeline smoke end to end.")
    parser.add_argument("--context-bus", required=True, help="Path to context.bus.jsonl.")
    parser.add_argument("--runtime-root", required=True, help="Runtime root for pipeline artifacts.")
    parser.add_argument("--policy-decision-id", required=True, help="Explicit policy decision id.")
    parser.add_argument("--isolated-runtime-root", required=True, help="Absolute isolated RouteProxy runtime root.")
    parser.add_argument("--output", help="Optional isolated_route_pipeline_smoke.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = run_isolated_route_pipeline_smoke(
        context_bus_path=Path(args.context_bus),
        runtime_root=Path(args.runtime_root),
        policy_decision_id=args.policy_decision_id,
        isolated_runtime_root=Path(args.isolated_runtime_root),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"queued_count: {report['queued_count']}")
        print(f"policy_scoped_queued_count: {report['policy_scoped_queued_count']}")
        print(f"command_built_count: {report['command_built_count']}")
        print(f"handler_executed_count: {report['handler_executed_count']}")
        print(f"frames_written_count: {report['frames_written_count']}")
        print(f"readback_count: {report['readback_count']}")
        print(f"pipeline_success: {report['pipeline_success']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Execute controlled dev RouteProxy smoke by reusing the existing pipeline tool.

0199 is the Bloc B controlled dev RouteProxy smoke execution patch.

It reads controlled_dev_routeproxy_smoke_plan.json from 0198 and executes the
existing tools/run_isolated_route_pipeline_smoke.py surface with the plan target
roots and policy_decision_id.

It must reuse the existing 0198 plan artifact and the existing
tools/run_isolated_route_pipeline_smoke.py execution surface. It must not
introduce a new runtime handler, adapter, bus, RouteProxy runtime, ControlProxy
runtime, SQL backend, Qdrant backend, GitHub client, graph renderer, or
inference path.

Execution locks are phase gates, not permanent prohibitions.
P0199 explicitly unlocks controlled-dev-routeproxy-smoke execution for this
phase only.
It must write RouteProxy frames only under target_isolated_runtime_root.

P0199 does not import runtime handler modules directly.
P0199 does not modify Scheduler.run.
P0199 does not instantiate Scheduler directly.
P0199 does not instantiate EventBus directly.
P0199 does not write ControlProxy frames.
P0199 does not call GitHub API or use network.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


CONTROLLED_DEV_ROUTE_PROXY_SMOKE_EXECUTION_SCHEMA = "missipy.route_pipeline.controlled_dev_routeproxy_smoke_execution.v1"
EXPECTED_PLAN_SCHEMA = "missipy.route_pipeline.controlled_dev_routeproxy_smoke_plan.v1"
EXPECTED_EXECUTION_TOOL = "tools/run_isolated_route_pipeline_smoke.py"
DEFAULT_OUTPUT_NAME = "controlled_dev_routeproxy_smoke_execution.json"
PIPELINE_OUTPUT_NAME = "isolated_route_pipeline_smoke.json"


class ControlledDevRouteProxySmokeExecutionError(ValueError):
    """Raised when the controlled dev smoke execution input is unsafe."""


def run_controlled_dev_routeproxy_smoke(
    *,
    controlled_dev_plan_path: Path | str,
    context_bus_path: Path | str,
    output_path: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Execute the existing isolated route pipeline smoke in the controlled dev root."""

    plan_path = Path(controlled_dev_plan_path)
    context_bus = Path(context_bus_path)
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    plan = _read_json_file(plan_path)

    issues: list[str] = []
    warnings: list[str] = []
    _audit_plan(plan, issues, warnings)
    _audit_context_bus(context_bus, issues)

    target_runtime_root = Path(str(plan.get("target_runtime_root", "")))
    target_isolated_runtime_root = Path(str(plan.get("target_isolated_runtime_root", "")))
    pipeline_output = target_runtime_root / PIPELINE_OUTPUT_NAME
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be controlled_dev_routeproxy_smoke_execution.json")
    if target_runtime_root.is_absolute() and final_output.is_absolute():
        if not _is_within_or_equal(final_output, target_runtime_root):
            issues.append("execution report output must be inside target_runtime_root")
    if target_runtime_root.is_absolute() and pipeline_output.is_absolute():
        if not _is_within_or_equal(pipeline_output, target_runtime_root):
            issues.append("pipeline output must be inside target_runtime_root")

    if issues:
        report = _build_report(
            plan_path=plan_path,
            context_bus=context_bus,
            plan=plan,
            command=[],
            pipeline_output=pipeline_output,
            subprocess_returncode=None,
            subprocess_stdout="",
            subprocess_stderr="",
            smoke={},
            issues=issues,
            warnings=warnings,
        )
        if output_path is not None:
            _write_report(final_output, report)
        return report

    command = [
        sys.executable,
        str(root / EXPECTED_EXECUTION_TOOL),
        "--context-bus",
        str(context_bus),
        "--runtime-root",
        str(target_runtime_root),
        "--policy-decision-id",
        str(plan["policy_decision_id"]),
        "--isolated-runtime-root",
        str(target_isolated_runtime_root),
        "--output",
        str(pipeline_output),
        "--format",
        "json",
    ]

    completed = subprocess.run(
        command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    smoke: dict[str, Any] = {}
    if pipeline_output.exists():
        try:
            smoke = _read_json_file(pipeline_output)
        except Exception as exc:  # pragma: no cover - defensive reporting
            issues.append(f"unable to read pipeline output: {exc}")
    else:
        issues.append("pipeline output was not created")

    if completed.returncode != 0:
        issues.append(f"pipeline tool returned non-zero exit status: {completed.returncode}")
    if smoke and smoke.get("pipeline_success") is not True:
        issues.append("pipeline_success must be true")
    if smoke and smoke.get("policy_scoped_queued_count") != smoke.get("queued_count"):
        issues.append("policy scoped queued count must match queued count")
    if smoke and smoke.get("controlproxy_frames_written") is not False:
        issues.append("ControlProxy frames must not be written")
    if smoke and smoke.get("scheduler_modified") is not False:
        issues.append("Scheduler must not be modified")
    if smoke and smoke.get("network_used") is not False:
        issues.append("network must not be used")

    report = _build_report(
        plan_path=plan_path,
        context_bus=context_bus,
        plan=plan,
        command=command,
        pipeline_output=pipeline_output,
        subprocess_returncode=completed.returncode,
        subprocess_stdout=completed.stdout,
        subprocess_stderr=completed.stderr,
        smoke=smoke,
        issues=issues,
        warnings=warnings,
    )
    _write_report(final_output, report)
    return report


def _audit_plan(plan: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if plan.get("schema") != EXPECTED_PLAN_SCHEMA:
        issues.append("controlled dev smoke plan schema mismatch")
    if plan.get("plan_ready") is not True:
        issues.append("plan_ready must be true")
    if plan.get("execution_allowed_by_0198") is not False:
        issues.append("execution_allowed_by_0198 must remain false")
    if plan.get("execution_can_be_unlocked_by_p0199") is not True:
        issues.append("execution_can_be_unlocked_by_p0199 must be true")
    if plan.get("execution_tool_to_reuse") != EXPECTED_EXECUTION_TOOL:
        issues.append("execution_tool_to_reuse must be tools/run_isolated_route_pipeline_smoke.py")
    if not isinstance(plan.get("policy_decision_id"), str) or not plan.get("policy_decision_id"):
        issues.append("policy_decision_id must be present")
    elif not str(plan.get("policy_decision_id")).startswith("policy:allow:"):
        issues.append("policy_decision_id must start with policy:allow:")
    if plan.get("issues") not in ([], None):
        issues.append("controlled dev smoke plan issues must be empty")
    if isinstance(plan.get("warnings"), list) and plan.get("warnings"):
        warnings.extend(str(item) for item in plan.get("warnings", []))
    if plan.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    for key in ("target_runtime_root", "target_isolated_runtime_root"):
        if not isinstance(plan.get(key), str) or not plan.get(key):
            issues.append(f"{key} must be present")
    _audit_target_roots(plan, issues)


def _audit_target_roots(plan: Mapping[str, Any], issues: list[str]) -> None:
    target_runtime_root = Path(str(plan.get("target_runtime_root", "")))
    target_isolated_runtime_root = Path(str(plan.get("target_isolated_runtime_root", "")))
    if not target_runtime_root.is_absolute():
        issues.append("target_runtime_root must be absolute")
    if not target_isolated_runtime_root.is_absolute():
        issues.append("target_isolated_runtime_root must be absolute")
    if target_runtime_root == target_isolated_runtime_root:
        issues.append("target_runtime_root and target_isolated_runtime_root must be distinct")
    if target_runtime_root.is_absolute() and target_isolated_runtime_root.is_absolute():
        if not _is_within_or_equal(target_isolated_runtime_root, target_runtime_root):
            issues.append("target_isolated_runtime_root must be inside target_runtime_root")


def _audit_context_bus(context_bus: Path, issues: list[str]) -> None:
    if not context_bus.is_absolute():
        issues.append("context bus path must be absolute")
    if not context_bus.exists():
        issues.append("context bus path must exist")
    if context_bus.name != "context.bus.jsonl":
        issues.append("context bus filename must be context.bus.jsonl")


def _build_report(
    *,
    plan_path: Path,
    context_bus: Path,
    plan: Mapping[str, Any],
    command: list[str],
    pipeline_output: Path,
    subprocess_returncode: int | None,
    subprocess_stdout: str,
    subprocess_stderr: str,
    smoke: Mapping[str, Any],
    issues: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    return {
        "schema": CONTROLLED_DEV_ROUTE_PROXY_SMOKE_EXECUTION_SCHEMA,
        "bloc": "B",
        "bloc_name": "controlled-dev-smoke",
        "controlled_dev_plan_path": str(plan_path),
        "context_bus_path": str(context_bus),
        "policy_decision_id": plan.get("policy_decision_id"),
        "target_runtime_root": plan.get("target_runtime_root"),
        "target_isolated_runtime_root": plan.get("target_isolated_runtime_root"),
        "execution_tool_reused": EXPECTED_EXECUTION_TOOL,
        "execution_unlocked_by_p0199": True,
        "execution_allowed_by_0199": True,
        "execution_scope": "controlled-dev-routeproxy-smoke",
        "pipeline_output": str(pipeline_output),
        "subprocess_command": command,
        "subprocess_returncode": subprocess_returncode,
        "subprocess_stdout": subprocess_stdout,
        "subprocess_stderr": subprocess_stderr,
        "pipeline_success": smoke.get("pipeline_success") is True,
        "queued_count": smoke.get("queued_count"),
        "policy_scoped_queued_count": smoke.get("policy_scoped_queued_count"),
        "command_plan_ready_count": smoke.get("command_plan_ready_count"),
        "command_built_count": smoke.get("command_built_count"),
        "handler_executed_count": smoke.get("handler_executed_count"),
        "frames_written_count": smoke.get("frames_written_count"),
        "readback_count": smoke.get("readback_count"),
        "issues": issues,
        "warnings": warnings,
        "execution_success": not issues and smoke.get("pipeline_success") is True,
        "existing_surfaces_reused": True,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "new_github_client_added": False,
        "runtime_imports_executed_by_wrapper": False,
        "existing_pipeline_tool_executed": subprocess_returncode is not None,
        "handler_called": bool(smoke.get("handler_called") or smoke.get("handler_executed_count")),
        "routeproxy_prepared": bool(smoke.get("routeproxy_prepared") or smoke.get("handler_executed_count")),
        "read_route_frame_called": bool(smoke.get("read_route_frame_called") or smoke.get("readback_count")),
        "writer_permits_requested": bool(smoke.get("writer_permits_requested") or smoke.get("frames_written_count")),
        "frames_written": bool(smoke.get("frames_written") or smoke.get("frames_written_count")),
        "controlproxy_frames_written": bool(smoke.get("controlproxy_frames_written")),
        "scheduler_modified": bool(smoke.get("scheduler_modified")),
        "eventbus_instantiated": bool(smoke.get("eventbus_instantiated")),
        "network_used": bool(smoke.get("network_used")),
        "requires_p0200_post_execution_audit": True,
    }


def _is_within_or_equal(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ControlledDevRouteProxySmokeExecutionError("input must be a JSON object")
    return raw


def _write_report(path: Path, report: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ControlledDevRouteProxySmokeExecutionError("output filename must be controlled_dev_routeproxy_smoke_execution.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run controlled dev RouteProxy smoke.")
    parser.add_argument("--controlled-dev-plan", required=True, help="Path to controlled_dev_routeproxy_smoke_plan.json.")
    parser.add_argument("--context-bus", required=True, help="Path to context.bus.jsonl.")
    parser.add_argument("--output", help="Optional controlled_dev_routeproxy_smoke_execution.json output path.")
    parser.add_argument("--repo-root", help="Repository root, defaults to tool parent.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    report = run_controlled_dev_routeproxy_smoke(
        controlled_dev_plan_path=Path(args.controlled_dev_plan),
        context_bus_path=Path(args.context_bus),
        output_path=Path(args.output) if args.output else None,
        repo_root=Path(args.repo_root) if args.repo_root else None,
    )

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"execution_success: {report['execution_success']}")
        print(f"execution_allowed_by_0199: {report['execution_allowed_by_0199']}")
        print(f"pipeline_success: {report['pipeline_success']}")
        print(f"frames_written_count: {report['frames_written_count']}")
        print(f"readback_count: {report['readback_count']}")
        print(f"requires_p0200_post_execution_audit: {report['requires_p0200_post_execution_audit']}")
        print(f"issues: {len(report['issues'])}")
    return 0 if report["execution_success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

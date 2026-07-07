#!/usr/bin/env python3
"""Run and accept controlled Scheduler hook smoke from the 0202 dry-run plan.

0203 is the Bloc C controlled Scheduler hook smoke and acceptance patch.

It reads scheduler_hook_dry_run_plan.json from 0202, reuses the existing
tools/run_isolated_route_pipeline_smoke.py execution surface, and writes
controlled_scheduler_hook_smoke_acceptance.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0203 must reuse the 0202 dry-run plan and audited existing surfaces.

0203 explicitly unlocks controlled Scheduler hook smoke execution for this
phase only.

0203 must not add a new Scheduler hook implementation.
0203 must not introduce a new runtime handler, adapter, bus, Scheduler,
RouteProxy runtime, ControlProxy runtime, SQL backend, Qdrant backend, GitHub
client, graph renderer, or inference path.

0203 does not execute Scheduler.run.
0203 does not modify Scheduler.run.
0203 does not import runtime handler modules directly.
0203 does not write ControlProxy frames.
0203 does not call GitHub API or use network.
0203 requires RouteProxy writes to stay inside target_isolated_runtime_root.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


CONTROLLED_SCHEDULER_HOOK_SMOKE_ACCEPTANCE_SCHEMA = (
    "missipy.scheduler.controlled_hook_smoke_acceptance.v1"
)
EXPECTED_PLAN_SCHEMA = "missipy.scheduler.hook_dry_run_plan.v1"
EXPECTED_EXECUTION_TOOL = "tools/run_isolated_route_pipeline_smoke.py"
DEFAULT_OUTPUT_NAME = "controlled_scheduler_hook_smoke_acceptance.json"
DEFAULT_PIPELINE_OUTPUT_NAME = "controlled_scheduler_hook_smoke_pipeline.json"

FALSE_PLAN_FLAGS = (
    "runtime_imports_executed_by_0202",
    "scheduler_run_executed",
    "handler_called_by_0202",
    "routeproxy_prepared_by_0202",
    "read_route_frame_called_by_0202",
    "writer_permits_requested_by_0202",
    "frames_written_by_0202",
    "controlproxy_frames_written_by_0202",
    "eventbus_instantiated_by_0202",
    "network_used_by_0202",
)

FALSE_NEW_SURFACE_FLAGS = (
    "new_runtime_handler_added",
    "new_adapter_added",
    "new_bus_added",
    "new_scheduler_added",
    "new_routeproxy_runtime_added",
    "new_controlproxy_runtime_added",
    "new_sql_backend_added",
    "new_qdrant_backend_added",
    "new_github_client_added",
    "new_graph_renderer_added",
    "new_inference_path_added",
)


class ControlledSchedulerHookSmokeAcceptanceError(ValueError):
    """Raised when controlled Scheduler hook smoke cannot run safely."""


def run_controlled_scheduler_hook_smoke_acceptance(
    *,
    scheduler_hook_plan_path: Path | str,
    context_bus_path: Path | str,
    policy_decision_id: str,
    output_path: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Run controlled Scheduler hook smoke via the existing isolated route pipeline."""

    plan_path = Path(scheduler_hook_plan_path)
    context_bus = Path(context_bus_path)
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[1]
    plan = _read_json_file(plan_path)

    issues: list[str] = []
    warnings: list[str] = []

    _audit_plan(plan, issues, warnings)
    _audit_policy_decision_id(policy_decision_id, issues)
    _audit_context_bus(context_bus, issues)

    target_runtime_root = Path(str(plan.get("target_runtime_root", "")))
    target_isolated_runtime_root = Path(str(plan.get("target_isolated_runtime_root", "")))
    pipeline_output = target_runtime_root / DEFAULT_PIPELINE_OUTPUT_NAME
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME

    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be controlled_scheduler_hook_smoke_acceptance.json")
    if target_runtime_root.is_absolute() and final_output.is_absolute():
        if not _is_within_or_equal(final_output, target_runtime_root):
            issues.append("acceptance output must be inside target_runtime_root")
    if target_runtime_root.is_absolute() and pipeline_output.is_absolute():
        if not _is_within_or_equal(pipeline_output, target_runtime_root):
            issues.append("pipeline output must be inside target_runtime_root")

    if issues:
        report = _build_acceptance(
            plan_path=plan_path,
            context_bus=context_bus,
            policy_decision_id=policy_decision_id,
            plan=plan,
            command=[],
            pipeline_output=pipeline_output,
            subprocess_returncode=None,
            subprocess_stdout="",
            subprocess_stderr="",
            pipeline={},
            issues=issues,
            warnings=warnings,
        )
        if output_path is not None:
            _write_acceptance(final_output, report)
        return report

    command = [
        sys.executable,
        str(root / EXPECTED_EXECUTION_TOOL),
        "--context-bus",
        str(context_bus),
        "--runtime-root",
        str(target_runtime_root),
        "--policy-decision-id",
        policy_decision_id,
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

    pipeline: dict[str, Any] = {}
    if pipeline_output.exists():
        pipeline = _read_json_file(pipeline_output)
    else:
        issues.append("controlled Scheduler hook smoke pipeline output was not created")

    if completed.returncode != 0:
        issues.append(f"pipeline tool returned non-zero exit status: {completed.returncode}")

    _audit_pipeline_result(pipeline, issues)

    acceptance = _build_acceptance(
        plan_path=plan_path,
        context_bus=context_bus,
        policy_decision_id=policy_decision_id,
        plan=plan,
        command=command,
        pipeline_output=pipeline_output,
        subprocess_returncode=completed.returncode,
        subprocess_stdout=completed.stdout,
        subprocess_stderr=completed.stderr,
        pipeline=pipeline,
        issues=issues,
        warnings=warnings,
    )
    _write_acceptance(final_output, acceptance)
    return acceptance


def _audit_plan(plan: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if plan.get("schema") != EXPECTED_PLAN_SCHEMA:
        issues.append("scheduler hook dry-run plan schema mismatch")
    if plan.get("scheduler_hook_dry_run_plan_ready") is not True:
        issues.append("scheduler_hook_dry_run_plan_ready must be true")
    if plan.get("execution_allowed_by_0202") is not False:
        issues.append("execution_allowed_by_0202 must be false")
    if plan.get("scheduler_run_execution_allowed") is not False:
        issues.append("scheduler_run_execution_allowed must be false")
    if plan.get("p0203_may_execute_controlled_scheduler_hook") is not True:
        issues.append("p0203_may_execute_controlled_scheduler_hook must be true")
    if plan.get("planned_next_patch") != "0203-controlled_scheduler_hook_smoke_acceptance":
        issues.append("planned_next_patch must be 0203-controlled_scheduler_hook_smoke_acceptance")
    if plan.get("issues") not in ([], None):
        issues.append("scheduler hook dry-run plan issues must be empty")
    if isinstance(plan.get("warnings"), list) and plan.get("warnings"):
        warnings.extend(str(item) for item in plan.get("warnings", []))
    if plan.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    for flag in FALSE_PLAN_FLAGS:
        if plan.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if plan.get(flag) is not False:
            issues.append(f"{flag} must be false")
    _audit_target_roots(plan, issues)
    _audit_reuse_sequence(plan, issues)


def _audit_reuse_sequence(plan: Mapping[str, Any], issues: list[str]) -> None:
    steps = plan.get("reuse_sequence")
    if not isinstance(steps, list) or not steps:
        issues.append("reuse_sequence must be present")
        return
    expected = [
        "map_authorized_request",
        "prepare_route",
        "build_command",
        "execute_minimal_handler",
        "readback",
    ]
    observed = [item.get("step") for item in steps if isinstance(item, Mapping)]
    for step in expected:
        if step not in observed:
            issues.append(f"reuse_sequence missing step: {step}")


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


def _audit_policy_decision_id(policy_decision_id: str, issues: list[str]) -> None:
    if not isinstance(policy_decision_id, str) or not policy_decision_id:
        issues.append("policy_decision_id must be present")
        return
    if not policy_decision_id.startswith("policy:allow:"):
        issues.append("policy_decision_id must start with policy:allow:")
    if "scheduler-hook" not in policy_decision_id and "0203" not in policy_decision_id:
        issues.append("policy_decision_id must identify scheduler-hook or 0203 scope")


def _audit_context_bus(context_bus: Path, issues: list[str]) -> None:
    if not context_bus.is_absolute():
        issues.append("context bus path must be absolute")
    if not context_bus.exists():
        issues.append("context bus path must exist")
    if context_bus.name != "context.bus.jsonl":
        issues.append("context bus filename must be context.bus.jsonl")


def _audit_pipeline_result(pipeline: Mapping[str, Any], issues: list[str]) -> None:
    if not pipeline:
        return
    if pipeline.get("schema") != "missipy.route_pipeline.isolated_smoke.v1":
        issues.append("pipeline schema mismatch")
    if pipeline.get("pipeline_success") is not True:
        issues.append("pipeline_success must be true")
    if pipeline.get("queued_count") != pipeline.get("policy_scoped_queued_count"):
        issues.append("queued_count must match policy_scoped_queued_count")
    if pipeline.get("command_plan_ready_count") != 1:
        issues.append("command_plan_ready_count must be 1")
    if pipeline.get("command_built_count") != 1:
        issues.append("command_built_count must be 1")
    if pipeline.get("handler_executed_count") != 1:
        issues.append("handler_executed_count must be 1")
    if pipeline.get("frames_written_count") != 1:
        issues.append("frames_written_count must be 1")
    if pipeline.get("readback_count") != 1:
        issues.append("readback_count must be 1")
    if pipeline.get("controlproxy_frames_written") is not False:
        issues.append("ControlProxy frames must remain false")
    if pipeline.get("scheduler_modified") is not False:
        issues.append("Scheduler modified must remain false")
    if pipeline.get("eventbus_instantiated") is not False:
        issues.append("EventBus instantiated must remain false")
    if pipeline.get("network_used") is not False:
        issues.append("network used must remain false")


def _build_acceptance(
    *,
    plan_path: Path,
    context_bus: Path,
    policy_decision_id: str,
    plan: Mapping[str, Any],
    command: list[str],
    pipeline_output: Path,
    subprocess_returncode: int | None,
    subprocess_stdout: str,
    subprocess_stderr: str,
    pipeline: Mapping[str, Any],
    issues: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    accepted = not issues and pipeline.get("pipeline_success") is True
    return {
        "schema": CONTROLLED_SCHEDULER_HOOK_SMOKE_ACCEPTANCE_SCHEMA,
        "bloc": "C",
        "bloc_name": "scheduler-hook-controlled",
        "scheduler_hook_plan_path": str(plan_path),
        "scheduler_hook_plan_schema": plan.get("schema"),
        "context_bus_path": str(context_bus),
        "policy_decision_id": policy_decision_id,
        "accepted_baseline": "controlled-scheduler-hook-routeproxy-write-read-v1",
        "controlled_dev_baseline_ref": plan.get("controlled_dev_baseline_ref"),
        "target_runtime_root": plan.get("target_runtime_root"),
        "target_isolated_runtime_root": plan.get("target_isolated_runtime_root"),
        "execution_tool_reused": EXPECTED_EXECUTION_TOOL,
        "controlled_scheduler_hook_smoke_executed": subprocess_returncode is not None,
        "controlled_scheduler_hook_smoke_accepted": accepted,
        "bloc_c_complete": accepted,
        "phase_re_evaluated": True,
        "next_bloc": "D",
        "next_bloc_name": "controlproxy-contract-and-priority",
        "next_recommended_patch": "0204-controlproxy_contract_audit",
        "execution_unlocked_by_0203": True,
        "execution_allowed_by_0203": True,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "new_scheduler_hook_implementation_added": False,
        "pipeline_output": str(pipeline_output),
        "subprocess_command": command,
        "subprocess_returncode": subprocess_returncode,
        "subprocess_stdout": subprocess_stdout,
        "subprocess_stderr": subprocess_stderr,
        "pipeline_success": pipeline.get("pipeline_success") is True,
        "queued_count": pipeline.get("queued_count"),
        "policy_scoped_queued_count": pipeline.get("policy_scoped_queued_count"),
        "command_plan_ready_count": pipeline.get("command_plan_ready_count"),
        "command_built_count": pipeline.get("command_built_count"),
        "handler_executed_count": pipeline.get("handler_executed_count"),
        "frames_written_count": pipeline.get("frames_written_count"),
        "readback_count": pipeline.get("readback_count"),
        "provenance_repair_items": list(plan.get("provenance_repair_items", []))
        if isinstance(plan.get("provenance_repair_items"), list)
        else [],
        "issues": issues,
        "warnings": warnings,
        "existing_surfaces_reused": True,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_scheduler_added": False,
        "new_routeproxy_runtime_added": False,
        "new_controlproxy_runtime_added": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "new_github_client_added": False,
        "new_graph_renderer_added": False,
        "new_inference_path_added": False,
        "runtime_imports_executed_by_0203_wrapper": False,
        "handler_called": bool(pipeline.get("handler_executed_count")),
        "routeproxy_prepared": bool(pipeline.get("handler_executed_count")),
        "read_route_frame_called": bool(pipeline.get("readback_count")),
        "writer_permits_requested": bool(pipeline.get("frames_written_count")),
        "frames_written": bool(pipeline.get("frames_written_count")),
        "controlproxy_frames_written": bool(pipeline.get("controlproxy_frames_written")),
        "scheduler_modified": bool(pipeline.get("scheduler_modified")),
        "eventbus_instantiated": bool(pipeline.get("eventbus_instantiated")),
        "network_used": bool(pipeline.get("network_used")),
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
        raise ControlledSchedulerHookSmokeAcceptanceError("input must be a JSON object")
    return raw


def _write_acceptance(path: Path, acceptance: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ControlledSchedulerHookSmokeAcceptanceError(
            "output filename must be controlled_scheduler_hook_smoke_acceptance.json"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(acceptance, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run controlled Scheduler hook smoke acceptance.")
    parser.add_argument("--scheduler-hook-plan", required=True, help="Path to scheduler_hook_dry_run_plan.json.")
    parser.add_argument("--context-bus", required=True, help="Path to context.bus.jsonl.")
    parser.add_argument("--policy-decision-id", required=True, help="Explicit policy decision id for P0203.")
    parser.add_argument("--output", help="Optional controlled_scheduler_hook_smoke_acceptance.json output path.")
    parser.add_argument("--repo-root", help="Repository root, defaults to tool parent.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    acceptance = run_controlled_scheduler_hook_smoke_acceptance(
        scheduler_hook_plan_path=Path(args.scheduler_hook_plan),
        context_bus_path=Path(args.context_bus),
        policy_decision_id=args.policy_decision_id,
        output_path=Path(args.output) if args.output else None,
        repo_root=Path(args.repo_root) if args.repo_root else None,
    )

    if args.format == "json":
        print(json.dumps(acceptance, indent=2, sort_keys=True))
    else:
        print(f"controlled_scheduler_hook_smoke_accepted: {acceptance['controlled_scheduler_hook_smoke_accepted']}")
        print(f"bloc_c_complete: {acceptance['bloc_c_complete']}")
        print(f"execution_allowed_by_0203: {acceptance['execution_allowed_by_0203']}")
        print(f"scheduler_run_executed: {acceptance['scheduler_run_executed']}")
        print(f"next_bloc: {acceptance['next_bloc']}")
        print(f"issues: {len(acceptance['issues'])}")
    return 0 if acceptance["controlled_scheduler_hook_smoke_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

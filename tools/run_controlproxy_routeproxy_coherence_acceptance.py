#!/usr/bin/env python3
"""Run and accept ControlProxy/RouteProxy coherence from the 0205 plan.

0206 is the Bloc D ControlProxy RouteProxy coherence acceptance patch.

It reads controlproxy_stale_priority_zone_smoke_plan.json from 0205, reuses the
existing tools/run_isolated_route_pipeline_smoke.py execution surface, and
writes controlproxy_routeproxy_coherence_acceptance.json.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0206 must reuse the 0205 stale priority zone smoke plan and audited existing surfaces.

0206 explicitly unlocks controlled stale priority zone coherence smoke execution
for this phase only.

0206 must not add a new ControlProxy runtime.
0206 must not add a new RouteProxy runtime.
0206 must not add a new Scheduler hook implementation.
0206 must not introduce a new runtime handler, adapter, bus, Scheduler, SQL
backend, Qdrant backend, GitHub client, graph renderer, or inference path.

0206 does not execute Scheduler.run.
0206 does not modify Scheduler.run.
0206 does not import runtime handler modules directly.
0206 does not write ControlProxy frames.
0206 does not call mark_route_frame_stale directly.
0206 does not call GitHub API or use network.
0206 requires RouteProxy writes to stay inside target_isolated_runtime_root.

ControlProxy remains coordination, not business authority.
Scheduler/policy/zone remain authority.
RouteProxy remains the fast data-plane frame surface.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


CONTROLPROXY_ROUTEPROXY_COHERENCE_ACCEPTANCE_SCHEMA = (
    "missipy.controlproxy.routeproxy_coherence_acceptance.v1"
)
EXPECTED_PLAN_SCHEMA = "missipy.controlproxy.stale_priority_zone_smoke_plan.v1"
EXPECTED_EXECUTION_TOOL = "tools/run_isolated_route_pipeline_smoke.py"
DEFAULT_OUTPUT_NAME = "controlproxy_routeproxy_coherence_acceptance.json"
PIPELINE_OUTPUT_NAME = "isolated_route_pipeline_smoke.json"

FALSE_PLAN_FLAGS = (
    "runtime_imports_executed_by_0205",
    "scheduler_run_executed",
    "scheduler_run_modified",
    "handler_called_by_0205",
    "routeproxy_prepared_by_0205",
    "mark_route_frame_stale_called_by_0205",
    "read_route_frame_called_by_0205",
    "writer_permits_requested_by_0205",
    "frames_written_by_0205",
    "controlproxy_frames_written_by_0205",
    "eventbus_instantiated_by_0205",
    "network_used_by_0205",
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


class ControlProxyRouteProxyCoherenceAcceptanceError(ValueError):
    """Raised when ControlProxy/RouteProxy coherence acceptance is unsafe."""


def run_controlproxy_routeproxy_coherence_acceptance(
    *,
    stale_priority_zone_plan_path: Path | str,
    context_bus_path: Path | str,
    policy_decision_id: str,
    output_path: Path | str | None = None,
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Run controlled coherence smoke via the existing isolated route pipeline."""

    plan_path = Path(stale_priority_zone_plan_path)
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
    pipeline_output = target_runtime_root / PIPELINE_OUTPUT_NAME
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME

    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be controlproxy_routeproxy_coherence_acceptance.json")
    if target_runtime_root.is_absolute() and final_output.is_absolute():
        if not _is_within_or_equal(final_output, target_runtime_root):
            issues.append("acceptance output must be inside target_runtime_root")

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
        issues.append("coherence pipeline output was not created")

    if completed.returncode != 0:
        issues.append(f"pipeline tool returned non-zero exit status: {completed.returncode}")

    _audit_pipeline_result(pipeline, plan, issues)

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
        issues.append("stale priority zone smoke plan schema mismatch")
    if plan.get("controlproxy_stale_priority_zone_smoke_plan_ready") is not True:
        issues.append("controlproxy_stale_priority_zone_smoke_plan_ready must be true")
    if plan.get("execution_allowed_by_0205") is not False:
        issues.append("execution_allowed_by_0205 must be false")
    if plan.get("controlproxy_frame_write_allowed_by_0205") is not False:
        issues.append("controlproxy_frame_write_allowed_by_0205 must be false")
    if plan.get("routeproxy_frame_write_allowed_by_0205") is not False:
        issues.append("routeproxy_frame_write_allowed_by_0205 must be false")
    if plan.get("p0206_may_execute_controlled_stale_priority_zone_smoke") is not True:
        issues.append("p0206_may_execute_controlled_stale_priority_zone_smoke must be true")
    if plan.get("planned_next_patch") != "0206-controlproxy_routeproxy_coherence_acceptance":
        issues.append("planned_next_patch must be 0206-controlproxy_routeproxy_coherence_acceptance")
    if plan.get("issues") not in ([], None):
        issues.append("stale priority zone smoke plan issues must be empty")
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
    if not policy_decision_id:
        issues.append("policy_decision_id must be present")
    if not policy_decision_id.startswith("policy:allow:"):
        issues.append("policy_decision_id must start with policy:allow:")
    if "0206" not in policy_decision_id and "stale" not in policy_decision_id:
        issues.append("policy_decision_id must identify stale priority zone or 0206 scope")


def _audit_context_bus(context_bus: Path, issues: list[str]) -> None:
    if not context_bus.is_absolute():
        issues.append("context bus path must be absolute")
    if not context_bus.exists():
        issues.append("context bus path must exist")
    if context_bus.name != "context.bus.jsonl":
        issues.append("context bus filename must be context.bus.jsonl")


def _audit_pipeline_result(pipeline: Mapping[str, Any], plan: Mapping[str, Any], issues: list[str]) -> None:
    if not pipeline:
        return
    if pipeline.get("schema") != "missipy.route_pipeline.isolated_smoke.v1":
        issues.append("pipeline schema mismatch")
    if pipeline.get("pipeline_success") is not True:
        issues.append("pipeline_success must be true")
    for key in (
        "queued_count",
        "policy_scoped_queued_count",
        "command_plan_ready_count",
        "command_built_count",
        "handler_executed_count",
        "frames_written_count",
        "readback_count",
    ):
        if pipeline.get(key) != 1:
            issues.append(f"{key} must be 1")
    if pipeline.get("controlproxy_frames_written") is not False:
        issues.append("ControlProxy frames must remain false")
    if pipeline.get("scheduler_modified") is not False:
        issues.append("Scheduler modified must remain false")
    if pipeline.get("eventbus_instantiated") is not False:
        issues.append("EventBus instantiated must remain false")
    if pipeline.get("network_used") is not False:
        issues.append("network used must remain false")
    isolated = Path(str(pipeline.get("isolated_runtime_root", "")))
    expected = Path(str(plan.get("target_isolated_runtime_root", "")))
    if isolated != expected:
        issues.append("pipeline isolated_runtime_root must match target_isolated_runtime_root")


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
        "schema": CONTROLPROXY_ROUTEPROXY_COHERENCE_ACCEPTANCE_SCHEMA,
        "bloc": "D",
        "bloc_name": "controlproxy-contract-and-priority",
        "stale_priority_zone_plan_path": str(plan_path),
        "stale_priority_zone_plan_schema": plan.get("schema"),
        "context_bus_path": str(context_bus),
        "policy_decision_id": policy_decision_id,
        "accepted_baseline": "controlproxy-routeproxy-stale-priority-zone-coherence-v1",
        "target_runtime_root": plan.get("target_runtime_root"),
        "target_isolated_runtime_root": plan.get("target_isolated_runtime_root"),
        "execution_tool_reused": EXPECTED_EXECUTION_TOOL,
        "controlproxy_routeproxy_coherence_executed": subprocess_returncode is not None,
        "controlproxy_routeproxy_coherence_accepted": accepted,
        "stale_priority_zone_contract_accepted": accepted,
        "bloc_d_complete": accepted,
        "phase_re_evaluated": True,
        "next_bloc": "E",
        "next_bloc_name": "sql-qdrant-provenance-repair",
        "next_recommended_patch": "0207-provenance_repair_audit",
        "execution_unlocked_by_0206": True,
        "execution_allowed_by_0206": True,
        "controlproxy_frame_write_allowed_by_0206": False,
        "routeproxy_frame_write_allowed_by_0206": True,
        "scheduler_run_executed": False,
        "scheduler_run_modified": False,
        "new_controlproxy_runtime_added": False,
        "new_routeproxy_runtime_added": False,
        "new_scheduler_hook_implementation_added": False,
        "mark_route_frame_stale_called_by_0206": False,
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
        "contract_decisions": list(plan.get("contract_decisions", []))
        if isinstance(plan.get("contract_decisions"), list)
        else [],
        "issues": issues,
        "warnings": warnings,
        "existing_surfaces_reused": True,
        "new_runtime_handler_added": False,
        "new_adapter_added": False,
        "new_bus_added": False,
        "new_scheduler_added": False,
        "new_sql_backend_added": False,
        "new_qdrant_backend_added": False,
        "new_github_client_added": False,
        "new_graph_renderer_added": False,
        "new_inference_path_added": False,
        "runtime_imports_executed_by_0206_wrapper": False,
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
        raise ControlProxyRouteProxyCoherenceAcceptanceError("input must be a JSON object")
    return raw


def _write_acceptance(path: Path, acceptance: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise ControlProxyRouteProxyCoherenceAcceptanceError(
            "output filename must be controlproxy_routeproxy_coherence_acceptance.json"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(acceptance, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run ControlProxy/RouteProxy coherence acceptance.")
    parser.add_argument("--stale-priority-zone-plan", required=True, help="Path to controlproxy_stale_priority_zone_smoke_plan.json.")
    parser.add_argument("--context-bus", required=True, help="Path to context.bus.jsonl.")
    parser.add_argument("--policy-decision-id", required=True, help="Explicit policy decision id for P0206.")
    parser.add_argument("--output", help="Optional controlproxy_routeproxy_coherence_acceptance.json output path.")
    parser.add_argument("--repo-root", help="Repository root, defaults to tool parent.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    acceptance = run_controlproxy_routeproxy_coherence_acceptance(
        stale_priority_zone_plan_path=Path(args.stale_priority_zone_plan),
        context_bus_path=Path(args.context_bus),
        policy_decision_id=args.policy_decision_id,
        output_path=Path(args.output) if args.output else None,
        repo_root=Path(args.repo_root) if args.repo_root else None,
    )

    if args.format == "json":
        print(json.dumps(acceptance, indent=2, sort_keys=True))
    else:
        print(f"controlproxy_routeproxy_coherence_accepted: {acceptance['controlproxy_routeproxy_coherence_accepted']}")
        print(f"bloc_d_complete: {acceptance['bloc_d_complete']}")
        print(f"execution_allowed_by_0206: {acceptance['execution_allowed_by_0206']}")
        print(f"controlproxy_frames_written: {acceptance['controlproxy_frames_written']}")
        print(f"next_bloc: {acceptance['next_bloc']}")
        print(f"issues: {len(acceptance['issues'])}")
    return 0 if acceptance["controlproxy_routeproxy_coherence_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Plan a Scheduler hook dry-run from the 0201 surface audit.

0202 is the Bloc C Scheduler hook dry-run plan only.

It reads scheduler_integration_surface_audit.json from 0201 and writes
scheduler_hook_dry_run_plan.json. It plans how a later controlled scheduler hook
smoke may reuse existing surfaces.

Reuse/adapt existing surfaces first.
doc/code-rules/code_rule.md remains the primary rule.
0202 must reuse the 0201 surface audit.
0202 must not add a new Scheduler hook implementation.

0202 must not introduce a new runtime handler, adapter, bus, Scheduler,
RouteProxy runtime, ControlProxy runtime, SQL backend, Qdrant backend, GitHub
client, graph renderer, or inference path.

source_baseline_ref or source_entry_digest missing is carried as a provenance repair item.

0202 does not execute Scheduler.run.
0202 does not import runtime handler modules.
0202 does not call handle_scheduler_route_command.
0202 does not call handle_scheduler_route_request.
0202 does not call prepare_route_proxy_runtime.
0202 does not call read_route_frame.
0202 does not request writer permits.
0202 does not call write_route_frame.
0202 does not write ControlProxy or RouteProxy frames.
0202 does not call GitHub API or use network.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


SCHEDULER_HOOK_DRY_RUN_PLAN_SCHEMA = "missipy.scheduler.hook_dry_run_plan.v1"
EXPECTED_AUDIT_SCHEMA = "missipy.scheduler.integration_surface_audit.v1"
DEFAULT_OUTPUT_NAME = "scheduler_hook_dry_run_plan.json"

REQUIRED_REUSE_PATHS = (
    "src/runtime/scheduler_route_adapter.py",
    "src/runtime/scheduler_route_handler_minimal.py",
    "src/runtime/scheduler_route_handshake.py",
)

OPTIONAL_REUSE_CANDIDATE_PATHS = (
    "src/runtime/controlproxy_scheduler_handler.py",
    "src/runtime/route_proxy_runtime_minimal.py",
    "src/runtime/shm_runtime_schema.py",
)

FALSE_AUDIT_FLAGS = (
    "runtime_imports_executed_by_0201",
    "scheduler_run_executed",
    "handler_called_by_0201",
    "routeproxy_prepared_by_0201",
    "read_route_frame_called_by_0201",
    "writer_permits_requested_by_0201",
    "frames_written_by_0201",
    "controlproxy_frames_written_by_0201",
    "eventbus_instantiated_by_0201",
    "network_used_by_0201",
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


class SchedulerHookDryRunPlanError(ValueError):
    """Raised when the Scheduler hook dry-run plan input is unsafe."""


def plan_scheduler_hook_dry_run(
    *,
    surface_audit_path: Path | str,
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Build a Scheduler hook dry-run plan without executing or importing runtime code."""

    audit_path = Path(surface_audit_path)
    audit = _read_json_file(audit_path)
    issues: list[str] = []
    warnings: list[str] = []

    _audit_surface_audit(audit, issues, warnings)
    reuse_paths = _audit_reuse_paths(audit, issues)

    target_runtime_root = Path(str(audit.get("target_runtime_root", "")))
    final_output = Path(output_path) if output_path is not None else target_runtime_root / DEFAULT_OUTPUT_NAME
    if final_output.name != DEFAULT_OUTPUT_NAME:
        issues.append("output filename must be scheduler_hook_dry_run_plan.json")

    provenance_repair_items = []
    if audit.get("provenance_warning"):
        provenance_repair_items.append(str(audit.get("provenance_warning")))

    plan = {
        "schema": SCHEDULER_HOOK_DRY_RUN_PLAN_SCHEMA,
        "bloc": "C",
        "bloc_name": "scheduler-hook-controlled",
        "surface_audit_path": str(audit_path),
        "surface_audit_schema": audit.get("schema"),
        "accepted_baseline": audit.get("accepted_baseline"),
        "controlled_dev_baseline_ref": audit.get("controlled_dev_baseline_ref"),
        "policy_decision_id": audit.get("policy_decision_id"),
        "target_runtime_root": audit.get("target_runtime_root"),
        "target_isolated_runtime_root": audit.get("target_isolated_runtime_root"),
        "recommended_integration_path": audit.get("recommended_integration_path"),
        "scheduler_hook_dry_run_plan_ready": not issues,
        "execution_allowed_by_0202": False,
        "scheduler_run_execution_allowed": False,
        "p0203_may_execute_controlled_scheduler_hook": not issues,
        "planned_next_patch": "0203-controlled_scheduler_hook_smoke_acceptance",
        "reuse_sequence": [
            {
                "step": "map_authorized_request",
                "surface": "src/runtime/scheduler_route_adapter.py",
                "symbol": "scheduler_route_request_mapping",
                "purpose": "reuse existing SchedulerRouteRequest mapping",
            },
            {
                "step": "prepare_route",
                "surface": "src/runtime/scheduler_route_handshake.py",
                "symbol": "prepare_route_for_scheduler",
                "purpose": "reuse existing route preparation handshake",
            },
            {
                "step": "build_command",
                "surface": "src/runtime/scheduler_route_handler_minimal.py",
                "symbol": "build_single_frame_route_command",
                "purpose": "reuse existing command builder",
            },
            {
                "step": "execute_minimal_handler",
                "surface": "src/runtime/scheduler_route_handler_minimal.py",
                "symbol": "handle_scheduler_route_command",
                "purpose": "reuse existing minimal handler in controlled smoke only",
            },
            {
                "step": "readback",
                "surface": "src/runtime/scheduler_route_handler_minimal.py",
                "symbol": "read_scheduler_route_handler_result_frames",
                "purpose": "reuse existing readback surface",
            },
        ],
        "required_reuse_paths": list(REQUIRED_REUSE_PATHS),
        "optional_existing_surface_candidates": list(OPTIONAL_REUSE_CANDIDATE_PATHS),
        "existing_surface_paths_from_audit": reuse_paths,
        "dry_run_boundaries": [
            "P0202 does not execute Scheduler.run",
            "P0202 does not import runtime handler modules",
            "P0202 does not write RouteProxy frames",
            "P0202 does not write ControlProxy frames",
            "P0202 does not create a new Scheduler hook implementation",
        ],
        "p0203_execution_unlock_requirements": [
            "explicit controlled scheduler hook smoke patch",
            "explicit policy_decision_id",
            "reuse adapter -> command builder -> minimal handler -> readback",
            "no new runtime handler before proving existing surfaces insufficient",
            "RouteProxy writes restricted to target_isolated_runtime_root",
            "ControlProxy frames remain false",
            "Scheduler.run modification remains false unless a later dedicated patch audits and authorizes it",
            "post-smoke acceptance in the same P0203 patch or a declared follow-up",
        ],
        "provenance_repair_items": provenance_repair_items,
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
        "runtime_imports_executed_by_0202": False,
        "scheduler_run_executed": False,
        "handler_called_by_0202": False,
        "routeproxy_prepared_by_0202": False,
        "read_route_frame_called_by_0202": False,
        "writer_permits_requested_by_0202": False,
        "frames_written_by_0202": False,
        "controlproxy_frames_written_by_0202": False,
        "eventbus_instantiated_by_0202": False,
        "network_used_by_0202": False,
    }

    if output_path is not None:
        _write_plan(final_output, plan)

    return plan


def _audit_surface_audit(audit: Mapping[str, Any], issues: list[str], warnings: list[str]) -> None:
    if audit.get("schema") != EXPECTED_AUDIT_SCHEMA:
        issues.append("surface audit schema mismatch")
    if audit.get("integration_surface_audit_success") is not True:
        issues.append("integration_surface_audit_success must be true")
    if audit.get("scheduler_hook_plan_allowed_next") is not True:
        issues.append("scheduler_hook_plan_allowed_next must be true")
    if audit.get("next_recommended_patch") != "0202-scheduler_hook_dry_run_plan":
        issues.append("next_recommended_patch must be 0202-scheduler_hook_dry_run_plan")
    if audit.get("issues") not in ([], None):
        issues.append("surface audit issues must be empty")
    if isinstance(audit.get("warnings"), list) and audit.get("warnings"):
        warnings.extend(str(item) for item in audit.get("warnings", []))
    if audit.get("existing_surfaces_reused") is not True:
        issues.append("existing_surfaces_reused must be true")
    if audit.get("existing_surface_count") != 6:
        issues.append("existing_surface_count must be 6")
    if not isinstance(audit.get("policy_decision_id"), str) or not audit.get("policy_decision_id"):
        issues.append("policy_decision_id must be present")
    for flag in FALSE_AUDIT_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")
    for flag in FALSE_NEW_SURFACE_FLAGS:
        if audit.get(flag) is not False:
            issues.append(f"{flag} must be false")

    recommended = audit.get("recommended_integration_path")
    if not isinstance(recommended, Mapping):
        issues.append("recommended_integration_path must be present")
    elif recommended.get("path") != "adapter -> command builder -> minimal handler -> readback":
        issues.append("recommended integration path mismatch")


def _audit_reuse_paths(audit: Mapping[str, Any], issues: list[str]) -> list[str]:
    reports = audit.get("surface_reports")
    if not isinstance(reports, list):
        issues.append("surface_reports must be a list")
        return []
    by_path: dict[str, Mapping[str, Any]] = {}
    for report in reports:
        if isinstance(report, Mapping) and isinstance(report.get("path"), str):
            by_path[str(report["path"])] = report
    for path in REQUIRED_REUSE_PATHS + OPTIONAL_REUSE_CANDIDATE_PATHS:
        report = by_path.get(path)
        if not report:
            issues.append(f"missing surface report for {path}")
            continue
        if report.get("exists") is not True:
            issues.append(f"surface does not exist: {path}")
        if report.get("missing_required_symbols") not in ([], None):
            issues.append(f"surface has missing required symbols: {path}")
        if report.get("use_before_new_code") is not True:
            issues.append(f"surface must be marked use_before_new_code: {path}")
    return sorted(by_path)


def _read_json_file(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise SchedulerHookDryRunPlanError("input must be a JSON object")
    return raw


def _write_plan(path: Path, plan: dict[str, Any]) -> None:
    if path.name != DEFAULT_OUTPUT_NAME:
        raise SchedulerHookDryRunPlanError("output filename must be scheduler_hook_dry_run_plan.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan Scheduler hook dry-run.")
    parser.add_argument("--surface-audit", required=True, help="Path to scheduler_integration_surface_audit.json.")
    parser.add_argument("--output", help="Optional scheduler_hook_dry_run_plan.json output path.")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args(argv)

    plan = plan_scheduler_hook_dry_run(
        surface_audit_path=Path(args.surface_audit),
        output_path=Path(args.output) if args.output else None,
    )

    if args.format == "json":
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"scheduler_hook_dry_run_plan_ready: {plan['scheduler_hook_dry_run_plan_ready']}")
        print(f"execution_allowed_by_0202: {plan['execution_allowed_by_0202']}")
        print(f"p0203_may_execute_controlled_scheduler_hook: {plan['p0203_may_execute_controlled_scheduler_hook']}")
        print(f"planned_next_patch: {plan['planned_next_patch']}")
        print(f"issues: {len(plan['issues'])}")
        print(f"warnings: {len(plan['warnings'])}")
    return 0 if plan["scheduler_hook_dry_run_plan_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
